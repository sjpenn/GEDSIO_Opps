#!/usr/bin/env bash
# Test different USASpending API filter parameters

echo "===== Test 1: recipient_search_text (array) with UEI ====="
curl -s -X POST https://api.usaspending.gov/api/v2/search/spending_by_award/ \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "recipient_search_text": ["FGUNSYM8J426"],
      "award_type_codes": ["A", "B", "C", "D"]
    },
    "fields": ["Award ID", "Recipient Name"],
    "limit": 2
  }' | python3 -m json.tool | grep -A 3 "results"

echo -e "\n\n===== Test 2: keyword filter with UEI ====="
curl -s -X POST https://api.usaspending.gov/api/v2/search/spending_by_award/ \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "keywords": ["FGU NSYM8J426"],
      "award_type_codes": ["A", "B", "C", "D"]
    },
    "fields": ["Award ID", "Recipient Name"],
    "limit": 2
  }' | python3 -m json.tool | grep -A 3 "results"

echo -e "\n\n===== Test 3: Search for recipient name instead (Boeing) ====="
curl -s -X POST https://api.usaspending.gov/api/v2/search/spending_by_award/ \
  -H "Content-Type: application/json" \
  -d '{
    "filters": {
      "recipient_search_text": ["BOEING"],
      "award_type_codes": ["A", "B", "C", "D"],
      "time_period": [{"start_date": "2023-01-01", "end_date": "2024-12-31"}]
    },
    "fields": ["Award ID", "Recipient Name", "Award Amount"],
    "limit": 3
  }' | python3 -m json.tool | head -40
