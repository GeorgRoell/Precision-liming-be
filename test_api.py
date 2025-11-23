import requests
import json

# Base URL
BASE_URL = "https://nextfarming-api-545668369577.us-central1.run.app"

# 1. Login
print("=== Testing Login ===")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={"username": "demo", "password": "demo123"}
)
print(f"Status: {login_response.status_code}")
token_data = login_response.json()
print(f"Response: {json.dumps(token_data, indent=2)}")

token = token_data["access_token"]
print(f"\n✓ Got token: {token[:50]}...")

# 2. Test VDLUFA Calculation
print("\n=== Testing VDLUFA Calculation ===")
calc_response = requests.post(
    f"{BASE_URL}/liming/calculate/vdlufa",
    headers={"Authorization": f"Bearer {token}"},
    json={
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
    }
)

print(f"Status: {calc_response.status_code}")
if calc_response.status_code == 200:
    result = calc_response.json()
    print(f"✓ Calculation successful!")
    print(f"\nSummary:")
    print(f"  - Method: {result['summary']['method']}")
    print(f"  - Total samples: {result['summary']['total_samples']}")
    print(f"  - Average lime requirement: {result['summary']['average_lime_kg_ha']:.2f} kg/ha")
    print(f"\nFirst result:")
    first = result['results'][0]
    print(f"  - Field: {first['field_name']}")
    print(f"  - Current pH: {first['current_ph']}")
    print(f"  - Target pH: {first['target_ph']}")
    print(f"  - Lime requirement: {first['lime_requirement_kg_ha']:.2f} kg/ha")
else:
    print(f"✗ Error: {calc_response.text}")

print("\n=== All Tests Complete ===")
