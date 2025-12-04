from unstructured.partition.auto import partition
from unstructured.documents.elements import NarrativeText, Title
import os

# Create a dummy text file to test partition
with open("test_doc.txt", "w") as f:
    f.write("SECTION L\n\nThis is a test paragraph.\n\nSECTION M\n\nEvaluation criteria.")

try:
    elements = partition(filename="test_doc.txt")
    print(f"Successfully partitioned text file. Found {len(elements)} elements.")
    for el in elements:
        print(f"Type: {type(el).__name__}, Text: {el.text}, Metadata: {el.metadata.to_dict()}")

except Exception as e:
    print(f"Error partitioning: {e}")

# If there are PDFs in uploads, try one (commented out for safety until I see the list)
# elements = partition(filename="uploads/some_file.pdf")
