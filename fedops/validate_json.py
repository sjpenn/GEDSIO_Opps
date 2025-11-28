import json
import sys

try:
    with open('workspace_response.json', 'r') as f:
        data = json.load(f)
    print("✅ JSON is valid")
    print(f"Keys: {list(data.keys())}")
    print(f"Proposal ID: {data.get('proposal', {}).get('id')}")
    print(f"Requirements count: {len(data.get('requirements', []))}")
    print(f"Artifacts count: {len(data.get('artifacts', []))}")
    print(f"Documents count: {len(data.get('documents', []))}")
except Exception as e:
    print(f"❌ JSON is invalid: {e}")
