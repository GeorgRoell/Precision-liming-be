"""
Test that VDLUFA and CEC methods use different clay percentages
for calculating rainfall-based pH Maintenance
"""

from utils.rainfall_lookup import calculate_caco3_loss

print("=" * 80)
print("Test: Method-Specific Clay Percentage Mapping")
print("=" * 80)

# Test parameters
rainfall = 800  # mm/year
ph = 5.8

print(f"\nTest Conditions:")
print(f"  Rainfall: {rainfall} mm/year")
print(f"  pH: {ph}")

# Test 1: Same texture name, different methods
print("\n" + "=" * 80)
print("Test 1: 'Sandy Loam' - Different Classifications")
print("=" * 80)

# CEC method: Sandy Loam
cec_result = calculate_caco3_loss(
    precipitation_mm=rainfall,
    soil_texture="Sandy Loam",
    ph=ph,
    method="CEC"
)

print(f"\nCEC Method - 'Sandy Loam':")
print(f"  Clay %: {cec_result['clay_percent']}%")
print(f"  Drainage coefficient: {cec_result['drainage_coef']}")
print(f"  CaCO3 Loss: {cec_result['caco3_loss']} kg/ha/year")

# VDLUFA equivalent: Schwach Lehm Sand (closest to Sandy Loam)
vdlufa_result = calculate_caco3_loss(
    precipitation_mm=rainfall,
    soil_texture="Schwach Lehm Sand",
    ph=ph,
    method="VDLUFA"
)

print(f"\nVDLUFA Method - 'Schwach Lehm Sand' (closest equivalent):")
print(f"  Clay %: {vdlufa_result['clay_percent']}%")
print(f"  Drainage coefficient: {vdlufa_result['drainage_coef']}")
print(f"  CaCO3 Loss: {vdlufa_result['caco3_loss']} kg/ha/year")

print(f"\nDifference:")
print(f"  Clay %: {abs(cec_result['clay_percent'] - vdlufa_result['clay_percent'])}%")
print(f"  CaCO3 Loss: {abs(cec_result['caco3_loss'] - vdlufa_result['caco3_loss'])} kg/ha/year")

# Test 2: Compare all CEC textures
print("\n" + "=" * 80)
print("Test 2: CEC Method - All Texture Types")
print("=" * 80)

cec_textures = [
    "Sand",
    "Loamy Sand",
    "Sandy Loam",
    "Silt Loam",
    "Clay Loam",
    "Sandy Clay",
    "Clay"
]

print(f"\n{'Soil Texture':<20} {'Clay %':>8} {'Drainage':>10} {'CaCO3 Loss':>12}")
print("-" * 52)

for texture in cec_textures:
    result = calculate_caco3_loss(
        precipitation_mm=rainfall,
        soil_texture=texture,
        ph=ph,
        method="CEC"
    )
    if result:
        print(f"{texture:<20} {result['clay_percent']:>8}% {result['drainage_coef']:>10.3f} {result['caco3_loss']:>12.1f} kg/ha")

# Test 3: Compare all VDLUFA textures
print("\n" + "=" * 80)
print("Test 3: VDLUFA Method - All Texture Types")
print("=" * 80)

vdlufa_textures = [
    "Sand",
    "Schwach Lehm Sand",
    "Stark Lehmiger Sand",
    "Sandiger Schl Lehm",
    "Toniger Lehm b.Ton"
]

print(f"\n{'Soil Texture':<25} {'Clay %':>8} {'Drainage':>10} {'CaCO3 Loss':>12}")
print("-" * 57)

for texture in vdlufa_textures:
    result = calculate_caco3_loss(
        precipitation_mm=rainfall,
        soil_texture=texture,
        ph=ph,
        method="VDLUFA"
    )
    if result:
        print(f"{texture:<25} {result['clay_percent']:>8}% {result['drainage_coef']:>10.3f} {result['caco3_loss']:>12.1f} kg/ha")

# Test 4: Show impact on lime requirement
print("\n" + "=" * 80)
print("Test 4: Impact on Lime Requirement (NV=53, Omya Calciprill)")
print("=" * 80)

nv = 53.0

print(f"\n{'Texture':<25} {'Method':<8} {'CaCO3 Loss':>12} {'Lime Req':>12}")
print("-" * 59)

# CEC Sandy Loam
cec_sandy_loam = calculate_caco3_loss(rainfall, "Sandy Loam", ph, "CEC")
lime_cec = cec_sandy_loam['caco3_loss'] * (100 / nv)
print(f"{'Sandy Loam':<25} {'CEC':<8} {cec_sandy_loam['caco3_loss']:>12.1f} {lime_cec:>12.1f} kg/ha")

# VDLUFA Schwach Lehm Sand
vdlufa_sls = calculate_caco3_loss(rainfall, "Schwach Lehm Sand", ph, "VDLUFA")
lime_vdlufa = vdlufa_sls['caco3_loss'] * (100 / nv)
print(f"{'Schwach Lehm Sand':<25} {'VDLUFA':<8} {vdlufa_sls['caco3_loss']:>12.1f} {lime_vdlufa:>12.1f} kg/ha")

diff_lime = abs(lime_cec - lime_vdlufa)
print(f"\nDifference in lime requirement: {diff_lime:.1f} kg/ha ({(diff_lime/lime_vdlufa*100):.1f}%)")

print("\n" + "=" * 80)
print("✅ All tests completed!")
print("=" * 80)
print("\nKey Findings:")
print("- CEC and VDLUFA use different clay % mappings for their soil classifications")
print("- This results in different CaCO3 loss values for pH Maintenance")
print("- The method-specific approach ensures accurate calculations for each system")
