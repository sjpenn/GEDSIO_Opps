"""
Shredding Service

Handles breaking down large document content into smaller, manageable chunks
for AI processing and retrieval.
"""

from typing import List, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from fedops_core.db.models import DocumentChunk, StoredFile
from fedops_core.services.advanced_parser import ParsedElement
import re

class ShreddingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.chunk_size = 1000
        self.chunk_overlap = 200

    async def shred_document(self, stored_file_id: int, content: Union[str, List[ParsedElement]]) -> int:
        """
        Shreds the content of a stored file into chunks and saves them to the database.
        Accepts either raw string content (legacy) or a list of ParsedElements (advanced).
        Returns the number of chunks created.
        """
        if not content:
            return 0

        chunks = []
        if isinstance(content, list):
            chunks = self._chunk_elements(content)
        else:
            # Legacy string handling
            text_chunks = self._split_text(content)
            for i, text in enumerate(text_chunks):
                chunks.append({
                    "content": text,
                    "page_number": None,
                    "section": None,
                    "metadata": {"length": len(text)}
                })
        
        count = 0
        for i, chunk_data in enumerate(chunks):
            chunk = DocumentChunk(
                stored_file_id=stored_file_id,
                chunk_index=i,
                content=chunk_data["content"],
                page_number=chunk_data.get("page_number"),
                section=chunk_data.get("section"),
                metadata_=chunk_data.get("metadata")
            )
            self.db.add(chunk)
            count += 1
            
        await self.db.commit()
        return count

    def _chunk_elements(self, elements: List[ParsedElement]) -> List[Dict]:
        """
        Chunks a list of parsed elements into logical blocks.
        Preserves page numbers and detects sections.
        """
        chunks = []
        current_chunk_text = ""
        current_page = None
        current_section = None
        
        # Improved regex for section headers (handles "SECTION L", "Section A", "section l:", etc.)
        section_pattern = re.compile(r'(?:SECTION|Section|section)\s+([A-M])', re.IGNORECASE)
        
        for el in elements:
            # If page changes and we have content, force a new chunk BEFORE processing new element
            # This ensures the chunk gets the section from BEFORE we process the new section header
            if current_page is not None and el.page_number != current_page and current_chunk_text:
                chunks.append({
                    "content": current_chunk_text.strip(),
                    "page_number": current_page,
                    "section": current_section,
                    "metadata": {"length": len(current_chunk_text)}
                })
                current_chunk_text = ""
                # DO NOT RESET current_section here - sections carry forward
            
            current_page = el.page_number
            
            # NOW update current section if element text matches
            match = section_pattern.search(el.text)
            if match:
                current_section = match.group(1).upper()
            
            # Append text to current chunk
            if current_chunk_text:
                current_chunk_text += " "
            current_chunk_text += el.text
            
            # Check size limit - be more aggressive about splitting
            if len(current_chunk_text) >= self.chunk_size:
                # Try to find a good break point
                # Look for the last sentence or period
                break_point = current_chunk_text.rfind('. ', 0, self.chunk_size)
                if break_point == -1 or break_point < self.chunk_size // 2:
                    # No good break, just split at chunk size
                    break_point = self.chunk_size
                else:
                    break_point += 2  # Include the period and space
                
                # Create chunk with first part
                chunks.append({
                    "content": current_chunk_text[:break_point].strip(),
                    "page_number": current_page,
                    "section": current_section,
                    "metadata": {"length": break_point}
                })
                # Keep remainder with overlap
                overlap_start = max(0, break_point - self.chunk_overlap)
                current_chunk_text = current_chunk_text[overlap_start:]
                
        # Add remaining text
        if current_chunk_text and current_chunk_text.strip():
            chunks.append({
                "content": current_chunk_text.strip(),
                "page_number": current_page,
                "section": current_section,
                "metadata": {"length": len(current_chunk_text)}
            })
            
        return chunks

    def _split_text(self, text: str) -> List[str]:
        """
        Splits text into chunks with overlap.
        Simple implementation - in production use a robust library like LangChain's RecursiveCharacterTextSplitter.
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = start + self.chunk_size
            
            # If we are not at the end, try to find a natural break point
            if end < text_len:
                # Look for the last period, newline, or space within the overlap zone
                # to avoid breaking words or sentences if possible.
                # We look back from 'end' up to 'chunk_overlap' characters.
                
                # Try to find a paragraph break
                last_newline = text.rfind('\n', start, end)
                if last_newline != -1 and last_newline > start + self.chunk_size // 2:
                    end = last_newline + 1
                else:
                    # Try to find a sentence break
                    last_period = text.rfind('. ', start, end)
                    if last_period != -1 and last_period > start + self.chunk_size // 2:
                        end = last_period + 2
                    else:
                        # Try to find a space
                        last_space = text.rfind(' ', start, end)
                        if last_space != -1 and last_space > start + self.chunk_size // 2:
                            end = last_space + 1
            
            chunk = text[start:end]
            chunks.append(chunk)
            
            # Move start forward, subtracting overlap
            start = end - self.chunk_overlap
            
            # Ensure we always make progress
            if start >= end:
                start = end
                
        return chunks
