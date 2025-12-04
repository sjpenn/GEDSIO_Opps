from unittest.mock import AsyncMock
from fedops_core.services.shredding_service import ShreddingService
from fedops_core.services.advanced_parser import ParsedElement

# Direct test without pytest
mock_db = AsyncMock()
service = ShreddingService(mock_db)

elements = [
    ParsedElement("SECTION L", "Title", page_number=5),
    ParsedElement("Instructions for proposal preparation.", "NarrativeText", page_number=5),
    ParsedElement("SECTION M", "Title", page_number=8),
    ParsedElement("Evaluation criteria for this proposal.", "NarrativeText", page_number=8),
]

chunks = service._chunk_elements(elements)

print(f"Total chunks: {len(chunks)}")
for i, chunk in enumerate(chunks):
    print(f"Chunk {i}: section={chunk.get('section')}, page={chunk.get('page_number')}, content={chunk.get('content')[:60]}...")

section_l_chunks = [c for c in chunks if c.get('section') == 'L']
section_m_chunks = [c for c in chunks if c.get('section') == 'M']

print(f"\nSection L chunks: {len(section_l_chunks)}")
print(f"Section M chunks: {len(section_m_chunks)}")
