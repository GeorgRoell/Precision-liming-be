#!/bin/bash
# Test script for NextFarming API

# 1. Login and get token
echo "=== Testing Login ==="
TOKEN_RESPONSE=$(curl -s -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "demo123"}')

TOKEN=$(echo $TOKEN_RESPONSE | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo "Token: ${TOKEN:0:50}..."

# 2. Test VDLUFA Calculation
echo -e "\n=== Testing VDLUFA Calculation ==="
curl -s -X POST "http://localhost:8000/liming/calculate/vdlufa" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "soil_data": [{
      "ph_value": 5.2,
      "soil_texture": "sandy loam",
      "area": 10.5,
      "field_name": "Test Field",
      "zone_name": "Zone 1"
    }],
    "crop_type": "Standard crops",
    "lime_type": "CaCO3",
    "liming_mode": "pH Improvement"
  }' | python -m json.tool

echo -e "\n=== Test Complete ==="
