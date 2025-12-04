from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_agents.base_agent import BaseAgent
from fedops_core.db.models import Opportunity, StoredFile
from fedops_core.services.ai_service import AIService
from fedops_core.services.document_extractor import DocumentExtractor
from fedops_core.prompts import SOLICITATION_SUMMARY_PROMPT, determine_document_type, DocumentType

class DocumentAnalysisAgent(BaseAgent):
    def __init__(self, db: AsyncSession):
        super().__init__("DocumentAnalysisAgent", db)

    async def execute(self, opportunity_id: int, **kwargs) -> Dict[str, Any]:
        await self.log_activity(opportunity_id, "START_DOC_ANALYSIS", "IN_PROGRESS")
        
        try:
            # Fetch opportunity data
            result = await self.db.execute(select(Opportunity).where(Opportunity.id == opportunity_id))
            opp = result.scalar_one_or_none()
            
            if not opp:
                raise ValueError(f"Opportunity {opportunity_id} not found")
            
            # Check if extracted_data was passed from orchestrator
            extracted_data = kwargs.get('extracted_data')
            
            if not extracted_data:
                # If not provided, extract it now
                await self.log_activity(opportunity_id, "EXTRACTING_DOCUMENTS", "IN_PROGRESS")
                
                # Fetch Document Files
                files_result = await self.db.execute(select(StoredFile).where(StoredFile.opportunity_id == opportunity_id))
                files = files_result.scalars().all()
                
                # Prepare file list for DocumentExtractor
                file_list = [
                    {"file_path": file.file_path, "filename": file.filename}
                    for file in files
                ]
                
                # Extract structured data from all documents
                doc_extractor = DocumentExtractor()
                extracted_data = await doc_extractor.extract_all_documents(file_list)
                
                await self.log_activity(opportunity_id, "EXTRACTION_COMPLETE", "SUCCESS", {
                    "sections_extracted": [k for k, v in extracted_data.items() if v and k != 'source_documents'],
                    "source_docs": len(extracted_data.get('source_documents', []))
                })
            
            # Build context from extracted data for AI analysis
            context_parts = []
            
            # Add extracted Section L data (submission instructions)
            if extracted_data.get('section_l'):
                context_parts.append(f"## Section L (Instructions):\n{str(extracted_data['section_l'])[:5000]}")
            
            # Add extracted Section M data (evaluation criteria)
            if extracted_data.get('section_m'):
                context_parts.append(f"## Section M (Evaluation):\n{str(extracted_data['section_m'])[:5000]}")
            
            # Add extracted SOW data
            if extracted_data.get('sow'):
                context_parts.append(f"## Statement of Work:\n{str(extracted_data['sow'])[:5000]}")
            
            # Add extracted Section H data (special requirements)
            if extracted_data.get('section_h'):
                context_parts.append(f"## Section H (Requirements):\n{str(extracted_data['section_h'])[:5000]}")
            
            extracted_context = "\n\n".join(context_parts) if context_parts else "No structured data extracted."
            
            # Call AI service for solicitation summary and analysis
            ai_service = AIService()
            prompt = SOLICITATION_SUMMARY_PROMPT.format(
                title=opp.title or "N/A",
                department=opp.department or "N/A",
                naics_code=opp.naics_code or "N/A",
                set_aside=opp.type_of_set_aside or "None",
                description=opp.description or "No description available",
                response_deadline=str(opp.response_deadline) if opp.response_deadline else "Not specified"
            )
            prompt += f"\n\n## Extracted Structured Data:\n{extracted_context[:50000]}"
            
            ai_analysis = await ai_service.analyze_opportunity(prompt)
            
            # Combine extracted data with AI analysis
            combined_details = {
                # Extracted facts from documents
                "extracted_data": {
                    "section_l": extracted_data.get('section_l'),
                    "section_m": extracted_data.get('section_m'),
                    "section_h": extracted_data.get('section_h'),
                    "sow": extracted_data.get('sow'),
                },
                # AI-generated analysis and insights
                "ai_analysis": ai_analysis,
                # Source document references
                "source_documents": extracted_data.get('source_documents', [])
            }
            
            # For backward compatibility, also include AI analysis fields at top level
            combined_details.update(ai_analysis)

            # --- NEW: Locate quotes in source documents ---
            try:
                # 1. Load file contents
                file_contents = {}
                # We need to fetch files again to get content if we don't have it
                # We already fetched 'files' earlier
                for file in files:
                    content = None
                    if file.parsed_content:
                        content = file.parsed_content
                    elif file.file_path:
                        try:
                            with open(file.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content = f.read()
                        except Exception as e:
                            print(f"Error reading file {file.filename}: {e}")
                    
                    if content:
                        file_contents[file.filename] = content
                
                # 2. Locate quotes
                self._locate_quotes(combined_details, file_contents)
                
            except Exception as e:
                print(f"Error locating quotes: {e}")
                # Don't fail the whole analysis if quote location fails
            # ----------------------------------------------
            
            # Extract key information for logging
            requirements_count = len(ai_analysis.get("key_dates", [])) + len(ai_analysis.get("key_personnel", []))
            
            await self.log_activity(opportunity_id, "END_DOC_ANALYSIS", "SUCCESS", {
                "requirements_count": requirements_count,
                "summary_length": len(ai_analysis.get("summary", "")),
                "source_docs": len(extracted_data.get('source_documents', [])),
                "sections_extracted": [k for k, v in extracted_data.items() if v and k != 'source_documents']
            })
            
            return {
                "status": "success",
                "solicitation_details": combined_details,
                "requirements_count": requirements_count,
                "source_documents": extracted_data.get('source_documents', []),
                "extracted_data": extracted_data  # Pass to other agents
            }

        except Exception as e:
            await self.log_activity(opportunity_id, "DOC_ANALYSIS_ERROR", "FAILURE", {"error": str(e)})
            # Return fallback structure
            return {
                "status": "error",
                "solicitation_details": {
                    "summary": f"Solicitation analysis failed: {str(e)}", 
                    "key_dates": [], 
                    "key_personnel": [],
                    "agency_goals": [],
                    "extracted_data": None,
                    "ai_analysis": None,
                    "source_documents": []
                },
                "requirements_count": 0,
                "extracted_data": None
            }

    def _locate_quotes(self, data: Any, file_contents: Dict[str, str]) -> Any:
        """
        Recursively traverse data to find 'source_quote' fields and add 'source_location'.
        """
        if isinstance(data, dict):
            # Check if this dict has a source_quote
            if "source_quote" in data and isinstance(data["source_quote"], str):
                quote = data["source_quote"]
                # Search for quote in file contents
                location = self._find_quote_in_files(quote, file_contents)
                if location:
                    data["source_location"] = location
            
            # Recurse into values
            for key, value in data.items():
                self._locate_quotes(value, file_contents)
                
        elif isinstance(data, list):
            for item in data:
                self._locate_quotes(item, file_contents)
        
        return data

    def _find_quote_in_files(self, quote: str, file_contents: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Find a quote in the provided file contents."""
        if not quote or len(quote) < 5:
            return None
            
        for filename, content in file_contents.items():
            # 1. Exact match
            idx = content.find(quote)
            if idx != -1:
                return {"filename": filename, "start": idx, "end": idx + len(quote)}
            
            # 2. Case insensitive match
            idx_lower = content.lower().find(quote.lower())
            if idx_lower != -1:
                 return {"filename": filename, "start": idx_lower, "end": idx_lower + len(quote)}
                 
            # 3. First 50 chars match (if quote is long)
            if len(quote) > 50:
                short_quote = quote[:50]
                idx = content.find(short_quote)
                if idx != -1:
                     return {"filename": filename, "start": idx, "end": idx + len(short_quote)}
        
        return None
