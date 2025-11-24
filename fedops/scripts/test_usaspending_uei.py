#!/usr/bin/env python3
"""
Test script to debug USASpending API UEI search
Tests different filter configurations to find the correct way to search by UEI
"""
import httpx
import json
import asyncio

async def test_usaspending_api():
    """Test the actual USASpendingClient implementation"""
    
    # Test with the actual client
    print("=" * 80)
    print("TEST: Using actual USASpendingClient")
    print("=" * 80)
    
    from fedops_sources.usaspending import USASpendingClient
    
    # Known entity with awards - Boeing
    test_uei = "J99Y67D6XBM3"  
    
    client = USASpendingClient()
    awards = await client.get_awards_by_uei(test_uei, limit=5)
    
    print(f"Results count: {len(awards)}")
    if awards:
        print("✅ SUCCESS: Awards found!")
        print(f"\nFirst award:")
        print(f"  Award ID: {awards[0].get('Award ID')}")
        print(f"  Recipient: {awards[0].get('Recipient Name')}")
        print(f"  Amount: ${awards[0].get('Award Amount'):,.2f}")
        print(f"  Agency: {awards[0].get('Awarding Agency')}")
    else:
        print("❌ FAILED: No awards found")
    
    return len(awards) > 0


if __name__ == "__main__":
    result = asyncio.run(test_usaspending_api())
    exit(0 if result else 1)
