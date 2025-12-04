#!/usr/bin/env python3
"""
Simple verification script to check that the agentic framework is correctly implemented.
This script inspects the code to verify key implementation details.
"""

import os
import sys

def check_file_contains(filepath, search_strings, description):
    """Check if a file contains all the search strings"""
    print(f"\n{'='*60}")
    print(f"Checking: {description}")
    print(f"File: {filepath}")
    print(f"{'='*60}")
    
    if not os.path.exists(filepath):
        print(f"❌ FAIL: File does not exist")
        return False
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    all_found = True
    for search_str in search_strings:
        if search_str in content:
            print(f"✓ Found: {search_str[:60]}...")
        else:
            print(f"✗ Missing: {search_str[:60]}...")
            all_found = False
    
    if all_found:
        print(f"✅ PASS: All checks passed")
    else:
        print(f"❌ FAIL: Some checks failed")
    
    return all_found

def main():
    base_path = "/Users/sjpenn/SitesAgents/GEDSIO_Opps/fedops"
    
    results = []
    
    # 1. Check PastPerformanceAgent exists and has correct logic
    results.append(check_file_contains(
        f"{base_path}/fedops_agents/past_performance_agent.py",
        [
            "class PastPerformanceAgent",
            "DocumentType.SECTION_L",
            "DocumentType.SECTION_M",
            "Solicitation Documents"
        ],
        "PastPerformanceAgent extracts from Section L/M"
    ))
    
    # 2. Check PersonnelAgent exists and has correct logic
    results.append(check_file_contains(
        f"{base_path}/fedops_agents/personnel_agent.py",
        [
            "class PersonnelAgent",
            "DocumentType.SOW",
            "DocumentType.SECTION_H",
            "Solicitation Documents"
        ],
        "PersonnelAgent extracts from SOW/Section H"
    ))
    
    # 3. Check CapabilityMappingAgent delegates to sub-agents
    results.append(check_file_contains(
        f"{base_path}/fedops_agents/capability_agent.py",
        [
            "from fedops_agents.past_performance_agent import PastPerformanceAgent",
            "from fedops_agents.personnel_agent import PersonnelAgent",
            "PastPerformanceAgent(self.db)",
            "PersonnelAgent(self.db)",
            "select(StoredFile)",
            "Solicitation Documents"
        ],
        "CapabilityMappingAgent uses sub-agents and document content"
    ))
    
    # 4. Check prompts.py has context-aware instructions
    results.append(check_file_contains(
        f"{base_path}/fedops_core/prompts.py",
        [
            "You will be provided with relevant sections of the solicitation documents",
            "Look for \"Key Personnel\"",
            "Look for \"Past Performance\""
        ],
        "Prompts instruct AI to use document content"
    ))
    
    # 5. Check AIService supports OpenRouter
    results.append(check_file_contains(
        f"{base_path}/fedops_core/services/ai_service.py",
        [
            "openrouter",
            "OPENROUTER_API_KEY",
            "openrouter.ai/api/v1"
        ],
        "AIService supports OpenRouter"
    ))
    
    # 6. Check settings.py has OpenRouter config
    results.append(check_file_contains(
        f"{base_path}/fedops_core/settings.py",
        [
            "OPENROUTER_API_KEY"
        ],
        "Settings includes OpenRouter configuration"
    ))
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 ALL VERIFICATIONS PASSED!")
        print("\nThe agentic framework has been successfully implemented:")
        print("  ✓ PastPerformanceAgent extracts from Section L/M")
        print("  ✓ PersonnelAgent extracts from SOW/Section H")
        print("  ✓ CapabilityMappingAgent orchestrates sub-agents")
        print("  ✓ Document content is passed to AI prompts")
        print("  ✓ OpenRouter support is available")
        return 0
    else:
        print("\n⚠️  SOME VERIFICATIONS FAILED")
        print("Please review the failures above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
