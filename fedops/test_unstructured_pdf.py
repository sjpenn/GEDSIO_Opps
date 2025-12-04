from unstructured.partition.auto import partition
import os

pdf_path = "uploads/1240BE26Q0009.pdf"

try:
    print(f"Partitioning {pdf_path}...")
    elements = partition(filename=pdf_path)
    print(f"Successfully partitioned PDF. Found {len(elements)} elements.")
    
    # Print first 10 elements to check metadata
    for i, el in enumerate(elements[:10]):
        print(f"[{i}] Type: {type(el).__name__}, Page: {el.metadata.page_number}, Text: {el.text[:50]}...")

    # Check for Section headers
    print("\nChecking for Section headers...")
    for el in elements:
        if "SECTION" in el.text.upper():
            print(f"Found potential header: {el.text} (Type: {type(el).__name__}, Page: {el.metadata.page_number})")

except Exception as e:
    print(f"Error partitioning PDF: {e}")
