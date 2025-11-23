"""
Test to verify what "Sandy Loam" actually maps to and calculates
"""

from calculators.liming import VDLUFACalculator
from utils.rainfall_lookup import calculate_caco3_loss

# User's conditions
rainfall = 800  # mm/year
ph = 6.4
nv = 53

print("=" * 80)
print("TEXTURE MAPPING TEST")
print("=" * 80)

# Test the mapping
mapped_texture = VDLUFACalculator.map_soil_texture("Sandy Loam")
print(f"\nInput: 'Sandy Loam'")
print(f"VDLUFA maps to: '{mapped_texture}'")
print()

# Calculate with the mapped texture
print("=" * 80)
print(f"CaCO3 Loss Calculation for: {mapped_texture}")
print("=" * 80)

result = calculate_caco3_loss(
    precipitation_mm=rainfall,
    soil_texture=mapped_texture,
    ph=ph,
    method="VDLUFA"
)

if result:
    caco3 = result['caco3_loss']
    clay = result['clay_percent']
    drainage = result['drainage_coef']
    bicarb = result['bicarbonate_factor']

    cao = caco3 / 1.785
    product = cao * (100 / nv)

    print(f"\nTexture: {mapped_texture}")
    print(f"Clay %: {clay}%")
    print(f"Drainage: {drainage:.3f}")
    print(f"Bicarbonate: {bicarb:.1f} mg/L")
    print(f"CaCO3 loss: {caco3:.1f} kg/ha/year")
    print(f"CaO loss: {cao:.2f} kg/ha")
    print(f"Product (NV={nv}%): {product:.2f} kg/ha")
    print()
    print(f"User reported VDLUFA: 193.22 kgCaO")
    print(f"We calculated: {cao:.2f} kgCaO")
    print(f"Difference: {abs(cao - 193.22):.2f} kgCaO")
else:
    print(f"\n❌ Calculation returned None!")

# Also test CEC
print()
print("=" * 80)
print("CaCO3 Loss Calculation for: Sandy Loam (CEC)")
print("=" * 80)

result_cec = calculate_caco3_loss(
    precipitation_mm=rainfall,
    soil_texture="Sandy Loam",
    ph=ph,
    method="CEC"
)

if result_cec:
    caco3 = result_cec['caco3_loss']
    clay = result_cec['clay_percent']

    cao = caco3 / 1.785
    product = cao * (100 / nv)

    print(f"\nTexture: Sandy Loam")
    print(f"Clay %: {clay}%")
    print(f"CaCO3 loss: {caco3:.1f} kg/ha/year")
    print(f"CaO loss: {cao:.2f} kg/ha")
    print(f"Product (NV={nv}%): {product:.2f} kg/ha")
    print()
    print(f"User reported CEC: 113.08 kgCaO")
    print(f"We calculated: {cao:.2f} kgCaO")
    print(f"Difference: {abs(cao - 113.08):.2f} kgCaO")

print()
print("=" * 80)
print("HYPOTHESIS")
print("=" * 80)
print()
print("If both values are WAY OFF from what user sees:")
print("→ User might be using different rainfall or pH values")
print("→ Or there's local calculation happening in the GUI")
print()
print("Let's calculate backwards from user's values:")
print()

# Reverse calculate what rainfall would give user's CEC value
user_cec_cao = 113.08
user_cec_caco3 = user_cec_cao * 1.785  # = 201.85 kg/ha

print(f"User's CEC CaO: {user_cec_cao} kg/ha")
print(f"Implies CaCO3: {user_cec_caco3:.2f} kg/ha")
print()

# For CEC Sandy Loam at pH 6.4:
# CaCO3 = rainfall × drainage × bicarb × 0.82 / 100
# 201.85 = rainfall × 0.55 × 107.7 × 0.82 / 100
# rainfall = 201.85 × 100 / (0.55 × 107.7 × 0.82)
# rainfall = 20185 / 48.5097 = 416.1 mm

implied_rainfall_cec = user_cec_caco3 * 100 / (0.55 * 107.7 * 0.82)
print(f"Implied rainfall from CEC calculation: {implied_rainfall_cec:.1f} mm/year")
print(f"(If user used {implied_rainfall_cec:.0f} mm rainfall, they'd get {user_cec_cao} kgCaO)")
print()
