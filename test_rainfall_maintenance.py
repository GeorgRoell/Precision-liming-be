"""Test rainfall-based pH Maintenance calculation."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from calculators.liming import LimingPrescription
from utils.rainfall_lookup import calculate_caco3_loss, get_annual_rainfall

print("=" * 70)
print("RAINFALL-BASED PH MAINTENANCE TEST")
print("=" * 70)
print()

# Test scenario: Field near Regensburg with pH 6.5
test_location = {
    'name': 'Regensburg Field',
    'longitude': 12.1,
    'latitude': 49.0
}

test_samples = [
    {
        'soil_texture': 'Sand',
        'ph': 5.5,
        'rainfall_mm': 658
    },
    {
        'soil_texture': 'Sandiger Schl Lehm',
        'ph': 6.5,
        'rainfall_mm': 658
    },
    {
        'soil_texture': 'Toniger Lehm b.Ton',
        'ph': 7.0,
        'rainfall_mm': 658
    }
]

print(f"Location: {test_location['name']}")
print(f"Coordinates: {test_location['longitude']}°E, {test_location['latitude']}°N")
print()

# Get rainfall for location
rainfall = get_annual_rainfall(test_location['longitude'], test_location['latitude'])
print(f"Annual Rainfall: {rainfall} mm/year")
print()
print("=" * 70)
print()

# Test CaCO3 loss calculation for different soil textures and pH levels
print("CaCO3 LOSS CALCULATIONS")
print("-" * 70)
print(f"{'Soil Texture':<25} {'pH':<6} {'CaCO3 Loss (kg/ha/year)':<25}")
print("-" * 70)

for sample in test_samples:
    caco3_loss_data = calculate_caco3_loss(
        precipitation_mm=sample['rainfall_mm'],
        soil_texture=sample['soil_texture'],
        ph=sample['ph']
    )

    if caco3_loss_data:
        print(f"{sample['soil_texture']:<25} {sample['ph']:<6.1f} {caco3_loss_data['caco3_loss']:<25.1f}")

print()
print("=" * 70)
print()

# Test pH Maintenance calculation WITH and WITHOUT rainfall data
print("PH MAINTENANCE COMPARISON")
print("-" * 70)
print("Comparing traditional (0.1 pH drop) vs rainfall-based maintenance")
print()

# Create test sample data
test_sample_with_boundary = {
    'id': 'test_zone_1',
    'name': 'Test Zone 1',
    'field_id': 'test_field',
    'field_name': 'Test Field',
    'zone_name': 'Zone 1',
    'area': 10.5,
    'ph_value': 6.5,
    'soil_texture': 'Sandiger Schl Lehm',
    'boundary': {
        'type': 'Polygon',
        'coordinates': [[
            [12.0, 49.0],
            [12.2, 49.0],
            [12.2, 49.1],
            [12.0, 49.1],
            [12.0, 49.0]
        ]]
    }
}

# Test with pH Maintenance mode
calculator = LimingPrescription(method="VDLUFA")

method_params = {
    'crop_type': 'Standard crops',
    'lime_type': 'CaO',
    'liming_mode': 'pH Maintenance',
    'default_soil_texture': 'Sandiger Schl Lehm'
}

print("Soil: Sandiger Schl Lehm (Sandy Loam)")
print(f"pH: {test_sample_with_boundary['ph_value']}")
print(f"Lime Type: {method_params['lime_type']}")
print()

results = calculator.calculate_prescription([test_sample_with_boundary], method_params)

if results:
    result = results[0]
    print(f"Rainfall: {result.get('annual_rainfall_mm', 'N/A')} mm/year")
    print(f"CaCO3 Loss: {result.get('caco3_loss_kg_ha_year', 'N/A')} kg/ha/year")
    print(f"Lime Requirement: {result['lime_requirement_kg_ha']:.1f} kg/ha CaO")
    print(f"Applied Mode: {result['applied_mode']}")
    print()

# Compare with sample WITHOUT boundary (no rainfall data)
test_sample_no_boundary = test_sample_with_boundary.copy()
del test_sample_no_boundary['boundary']

print("-" * 70)
print("Without rainfall data (traditional method):")
print()

results_traditional = calculator.calculate_prescription([test_sample_no_boundary], method_params)

if results_traditional:
    result_trad = results_traditional[0]
    print(f"Rainfall: {result_trad.get('annual_rainfall_mm', 'N/A')}")
    print(f"CaCO3 Loss: {result_trad.get('caco3_loss_kg_ha_year', 'N/A')}")
    print(f"Lime Requirement: {result_trad['lime_requirement_kg_ha']:.1f} kg/ha CaO")
    print(f"Applied Mode: {result_trad['applied_mode']}")
    print()

print("=" * 70)
print()

# Test with different rainfall amounts
print("SENSITIVITY TO RAINFALL")
print("-" * 70)
print(f"{'Rainfall (mm)':<20} {'CaCO3 Loss (kg/ha)':<25} {'CaO Req (kg/ha)':<20}")
print("-" * 70)

from utils.rainfall_lookup import calculate_caco3_loss

rainfall_scenarios = [400, 600, 800, 1000, 1200]
soil_texture = 'Sandiger Schl Lehm'
ph = 6.5

for rainfall_mm in rainfall_scenarios:
    caco3_data = calculate_caco3_loss(rainfall_mm, soil_texture, ph)
    if caco3_data:
        # Convert CaCO3 to CaO (CaO factor = 1.0, CaCO3 factor = 1.785)
        caco3_loss = caco3_data['caco3_loss']
        cao_requirement = caco3_loss / 1.785  # Approximate conversion
        print(f"{rainfall_mm:<20} {caco3_loss:<25.1f} {cao_requirement:<20.1f}")

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
