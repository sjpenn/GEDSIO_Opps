from typing import List, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fedops_core.db.engine import get_db
from fedops_core.db.models import Opportunity, StoredFile, OpportunityScore
from fedops_core.services.file_service import FileService
from fedops_core.services.opportunity_extractor import OpportunityExtractor
from datetime import datetime
import zipfile
import tempfile
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/opportunities/analyze-upload")
async def analyze_uploaded_opportunity(
    files: List[UploadFile] = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Comprehensive analysis of uploaded opportunity documents.
    
    This endpoint:
    1. Uploads and processes files temporarily
    2. Extracts metadata using AI
    3. Creates temporary opportunity record
    4. Runs full agent analysis pipeline
    5. Returns extracted data + analysis results
    
    Used for preview before creating the opportunity.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    try:
        from fedops_core.services.file_service import FileService
        from fedops_agents.orchestrator import OrchestratorAgent
        
        # Save files temporarily and extract metadata
        temp_dir = tempfile.mkdtemp()
        temp_paths = []
        temp_file_records = []
        
        logger.info(f"Analyzing {len(files)} uploaded files")
        
        # Process uploaded files
        for upload_file in files:
            # Handle ZIP files by extracting them
            if upload_file.filename.lower().endswith('.zip'):
                zip_path = os.path.join(temp_dir, upload_file.filename)
                with open(zip_path, 'wb') as f:
                    content = await upload_file.read()
                    f.write(content)
                
                # Extract ZIP contents
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Add all extracted files
                    for root, dirs, filenames in os.walk(temp_dir):
                        for filename in filenames:
                            if not filename.startswith('.') and filename != upload_file.filename:
                                temp_paths.append(os.path.join(root, filename))
                except zipfile.BadZipFile:
                    logger.error(f"Invalid ZIP file: {upload_file.filename}")
            else:
                # Save individual file
                file_path = os.path.join(temp_dir, upload_file.filename)
                with open(file_path, 'wb') as f:
                    content = await upload_file.read()
                    f.write(content)
                temp_paths.append(file_path)
        
        if not temp_paths:
            raise HTTPException(status_code=400, detail="No valid files found")
        
        logger.info(f"Processing {len(temp_paths)} files for analysis")
        
        # Extract metadata using AI
        extractor = OpportunityExtractor()
        extracted_data = await extractor.extract_from_files(temp_paths)
        
        logger.info("Metadata extraction complete")
        
        # Create temporary opportunity record for analysis
        # Use extracted data with fallbacks
        temp_opportunity = Opportunity(
            notice_id=f"TEMP_{datetime.utcnow().timestamp()}",
            title=extracted_data.get("title", {}).get("value") or "Temporary Analysis",
            solicitation_number=extracted_data.get("solicitation_number", {}).get("value"),
            department=extracted_data.get("department", {}).get("value"),
            naics_code=extracted_data.get("naics_code", {}).get("value"),
            type_of_set_aside=extracted_data.get("type_of_set_aside", {}).get("value"),
            description=extracted_data.get("description", {}).get("value"),
            response_deadline=extracted_data.get("response_deadline", {}).get("value"),
            posted_date=extracted_data.get("posted_date", {}).get("value") or datetime.utcnow(),
            type=extracted_data.get("type", {}).get("value") or "Solicitation",
            source="Manual",
            active="Yes"
        )
        
        db.add(temp_opportunity)
        await db.flush()  # Get ID without committing
        
        logger.info(f"Created temporary opportunity record: {temp_opportunity.id}")
        
        # Save files to database temporarily
        file_service = FileService(db)
        for file_path in temp_paths:
            filename = os.path.basename(file_path)
            
            # Create stored file record
            stored_file = StoredFile(
                opportunity_id=temp_opportunity.id,
                filename=filename,
                file_path=file_path,
                file_type=filename.split('.')[-1] if '.' in filename else 'unknown'
            )
            db.add(stored_file)
            temp_file_records.append(stored_file)
        
        await db.flush()
        
        logger.info(f"Saved {len(temp_file_records)} temporary file records")
        
        # Run full agent analysis pipeline
        logger.info("Starting agent analysis pipeline")
        orchestrator = OrchestratorAgent(db)
        analysis_result = await orchestrator.execute(temp_opportunity.id)
        
        logger.info("Agent analysis complete")
        
        # Fetch the generated score
        score_stmt = select(OpportunityScore).where(OpportunityScore.opportunity_id == temp_opportunity.id)
        score_result = await db.execute(score_stmt)
        score = score_result.scalar_one_or_none()
        
        # Build comprehensive response
        response = {
            "status": "success",
            "extracted_metadata": extracted_data,
            "analysis": {
                "compliance_status": temp_opportunity.compliance_status,
                "scores": {
                    "strategic_alignment": score.strategic_alignment_score if score else 0,
                    "financial_viability": score.financial_viability_score if score else 0,
                    "contract_risk": score.contract_risk_score if score else 0,
                    "internal_capacity": score.internal_capacity_score if score else 0,
                    "data_integrity": score.data_integrity_score if score else 0,
                    "weighted_score": score.weighted_score if score else 0
                },
                "qualification": {
                    "decision": score.go_no_go_decision if score else "REVIEW",
                    "details": score.details if score else {}
                }
            },
            "temp_opportunity_id": temp_opportunity.id,
            "temp_file_ids": [f.id for f in temp_file_records],
            "files_processed": len(temp_paths)
        }
        
        # Rollback to not save temporary data
        await db.rollback()
        
        # Clean up temp files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        logger.info("Analysis complete, returning results")
        
        return response
        
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Error analyzing uploaded opportunity: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to analyze opportunity: {str(e)}")


@router.post("/opportunities/extract-metadata")
async def extract_metadata_from_files(
    files: List[UploadFile] = File(...),
):
    """
    Extract opportunity metadata from uploaded files using AI.
    
    This endpoint analyzes documents and returns extracted metadata
    without creating an opportunity record. Used for preview/auto-fill.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")
    
    try:
        # Save files temporarily
        temp_dir = tempfile.mkdtemp()
        temp_paths = []
        
        for upload_file in files:
            # Handle ZIP files by extracting them
            if upload_file.filename.lower().endswith('.zip'):
                zip_path = os.path.join(temp_dir, upload_file.filename)
                with open(zip_path, 'wb') as f:
                    content = await upload_file.read()
                    f.write(content)
                
                # Extract ZIP contents
                try:
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Add all extracted files
                    for root, dirs, filenames in os.walk(temp_dir):
                        for filename in filenames:
                            if not filename.startswith('.') and filename != upload_file.filename:
                                temp_paths.append(os.path.join(root, filename))
                except zipfile.BadZipFile:
                    logger.error(f"Invalid ZIP file: {upload_file.filename}")
            else:
                # Save individual file
                file_path = os.path.join(temp_dir, upload_file.filename)
                with open(file_path, 'wb') as f:
                    content = await upload_file.read()
                    f.write(content)
                temp_paths.append(file_path)
        
        if not temp_paths:
            raise HTTPException(status_code=400, detail="No valid files found")
        
        # Extract metadata using AI
        extractor = OpportunityExtractor()
        extracted_data = await extractor.extract_from_files(temp_paths)
        
        # Clean up temp files
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        return {
            "status": "success",
            "extracted_data": extracted_data,
            "files_processed": len(temp_paths)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting metadata: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to extract metadata: {str(e)}")


@router.post("/opportunities/upload")
async def upload_opportunity(
    # Required fields
    title: str = Form(...),
    source: str = Form(...),  # eBuy, eFast, SeaPort, Manual, etc.
    
    # Optional core fields
    solicitation_number: Optional[str] = Form(None),
    rfp_number: Optional[str] = Form(None),  # Alias for solicitation_number
    department: Optional[str] = Form(None),
    sub_tier: Optional[str] = Form(None),
    office: Optional[str] = Form(None),
    type: Optional[str] = Form("Solicitation"),
    naics_code: Optional[str] = Form(None),
    type_of_set_aside: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    response_deadline: Optional[str] = Form(None),  # ISO date string
    posted_date: Optional[str] = Form(None),  # ISO date string
    
    # Incumbent/Predecessor contract fields
    incumbent_vendor: Optional[str] = Form(None),
    incumbent_contract_number: Optional[str] = Form(None),
    incumbent_value: Optional[str] = Form(None),
    incumbent_expiration_date: Optional[str] = Form(None),  # ISO date string
    
    # Files
    files: List[UploadFile] = File(default=[]),
    
    # Database session
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a manual opportunity with files (including ZIP archives).
    
    This endpoint allows users to manually add opportunities from sources like
    eBuy, eFast, SeaPort, or other platforms that don't have API access.
    """
    try:
        # Use rfp_number if provided and solicitation_number is not
        if rfp_number and not solicitation_number:
            solicitation_number = rfp_number
        
        # Generate notice_id for manual uploads
        notice_id = f"{source.upper()}-{solicitation_number or datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Check if opportunity already exists
        stmt = select(Opportunity).where(Opportunity.notice_id == notice_id)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Opportunity with notice_id {notice_id} already exists"
            )
        
        # Parse dates
        posted_date_parsed = None
        if posted_date:
            try:
                posted_date_parsed = datetime.fromisoformat(posted_date.replace('Z', '+00:00'))
            except ValueError:
                posted_date_parsed = datetime.utcnow()
        else:
            posted_date_parsed = datetime.utcnow()
        
        response_deadline_parsed = None
        if response_deadline:
            try:
                response_deadline_parsed = datetime.fromisoformat(response_deadline.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        incumbent_expiration_parsed = None
        if incumbent_expiration_date:
            try:
                incumbent_expiration_parsed = datetime.fromisoformat(incumbent_expiration_date.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # Create opportunity record
        opportunity = Opportunity(
            notice_id=notice_id,
            title=title,
            solicitation_number=solicitation_number,
            department=department,
            sub_tier=sub_tier,
            office=office,
            posted_date=posted_date_parsed,
            type=type,
            naics_code=naics_code,
            type_of_set_aside=type_of_set_aside,
            description=description,
            response_deadline=response_deadline_parsed,
            source=source,
            active="Yes",
            
            # Incumbent fields
            incumbent_vendor=incumbent_vendor,
            incumbent_contract_number=incumbent_contract_number,
            incumbent_value=incumbent_value,
            incumbent_expiration_date=incumbent_expiration_parsed
        )
        
        db.add(opportunity)
        await db.flush()  # Get the ID without committing
        
        # Process uploaded files
        file_service = FileService(db)
        uploaded_files = []
        extracted_files = []
        
        for upload_file in files:
            # Check if it's a ZIP file
            if upload_file.filename.lower().endswith('.zip'):
                # Extract ZIP contents
                logger.info(f"Extracting ZIP file: {upload_file.filename}")
                extracted = await extract_zip_and_upload(
                    upload_file, 
                    opportunity.id, 
                    file_service
                )
                extracted_files.extend(extracted)
            else:
                # Upload individual file
                stored_file = await file_service.upload_file(
                    upload_file, 
                    opportunity.id
                )
                uploaded_files.append(stored_file)
        
        await db.commit()
        await db.refresh(opportunity)
        
        return {
            "message": "Opportunity uploaded successfully",
            "opportunity_id": opportunity.id,
            "notice_id": opportunity.notice_id,
            "files_uploaded": len(uploaded_files),
            "files_extracted_from_zip": len(extracted_files),
            "total_files": len(uploaded_files) + len(extracted_files)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading opportunity: {str(e)}", exc_info=True)
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload opportunity: {str(e)}")


async def extract_zip_and_upload(
    zip_file: UploadFile,
    opportunity_id: int,
    file_service: FileService
) -> List[StoredFile]:
    """
    Extract a ZIP file and upload all contents to the opportunity.
    
    Returns list of StoredFile objects for each extracted file.
    """
    extracted_files = []
    
    # Create a temporary directory for extraction
    with tempfile.TemporaryDirectory() as temp_dir:
        # Save uploaded ZIP to temp location
        zip_path = os.path.join(temp_dir, zip_file.filename)
        with open(zip_path, 'wb') as f:
            content = await zip_file.read()
            f.write(content)
        
        # Extract ZIP contents
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_dir)
            
            # Upload each extracted file
            for root, dirs, files in os.walk(temp_dir):
                for filename in files:
                    # Skip the original ZIP file itself
                    if filename == zip_file.filename:
                        continue
                    
                    # Skip hidden files and system files
                    if filename.startswith('.') or filename.startswith('__MACOSX'):
                        continue
                    
                    file_path = os.path.join(root, filename)
                    
                    # Create an UploadFile-like object from the extracted file
                    with open(file_path, 'rb') as f:
                        file_content = f.read()
                    
                    # Get relative path for nested files
                    rel_path = os.path.relpath(file_path, temp_dir)
                    clean_filename = rel_path.replace(os.sep, '_')  # Flatten nested structure
                    
                    # Create a temporary UploadFile for the service
                    from io import BytesIO
                    temp_upload = UploadFile(
                        filename=clean_filename,
                        file=BytesIO(file_content)
                    )
                    
                    stored_file = await file_service.upload_file(
                        temp_upload,
                        opportunity_id
                    )
                    extracted_files.append(stored_file)
                    
        except zipfile.BadZipFile:
            logger.error(f"Invalid ZIP file: {zip_file.filename}")
            raise HTTPException(status_code=400, detail=f"Invalid ZIP file: {zip_file.filename}")
    
    return extracted_files


@router.get("/opportunities/{opportunity_id}/incumbent")
async def get_incumbent_details(
    opportunity_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get incumbent/predecessor contract details for an opportunity."""
    stmt = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await db.execute(stmt)
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    return {
        "opportunity_id": opportunity.id,
        "incumbent_vendor": opportunity.incumbent_vendor,
        "incumbent_contract_number": opportunity.incumbent_contract_number,
        "incumbent_value": opportunity.incumbent_value,
        "incumbent_expiration_date": opportunity.incumbent_expiration_date,
        "previous_sow_document_id": opportunity.previous_sow_document_id
    }


@router.put("/opportunities/{opportunity_id}/incumbent")
async def update_incumbent_details(
    opportunity_id: int,
    incumbent_vendor: Optional[str] = Form(None),
    incumbent_contract_number: Optional[str] = Form(None),
    incumbent_value: Optional[str] = Form(None),
    incumbent_expiration_date: Optional[str] = Form(None),
    previous_sow_file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db)
):
    """Update incumbent/predecessor contract details for an opportunity."""
    stmt = select(Opportunity).where(Opportunity.id == opportunity_id)
    result = await db.execute(stmt)
    opportunity = result.scalar_one_or_none()
    
    if not opportunity:
        raise HTTPException(status_code=404, detail="Opportunity not found")
    
    # Update fields if provided
    if incumbent_vendor is not None:
        opportunity.incumbent_vendor = incumbent_vendor
    if incumbent_contract_number is not None:
        opportunity.incumbent_contract_number = incumbent_contract_number
    if incumbent_value is not None:
        opportunity.incumbent_value = incumbent_value
    if incumbent_expiration_date is not None:
        try:
            opportunity.incumbent_expiration_date = datetime.fromisoformat(
                incumbent_expiration_date.replace('Z', '+00:00')
            )
        except ValueError:
            pass
    
    # Upload previous SOW if provided
    if previous_sow_file:
        file_service = FileService(db)
        stored_file = await file_service.upload_file(previous_sow_file, opportunity_id)
        opportunity.previous_sow_document_id = stored_file.id
    
    await db.commit()
    await db.refresh(opportunity)
    
    return {
        "message": "Incumbent details updated successfully",
        "opportunity_id": opportunity.id
    }
