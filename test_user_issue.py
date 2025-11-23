"""
Diagnostic test for user-reported 71% discrepancy
User reported: Sandy Loam pH 6.4
- CEC: 113.08 kgCaO
- VDLUFA: 193.22 kgCaO
"""

from utils.rainfall_lookup import calculate_caco3_loss, CEC_TEXTURE_TO_CLAY, VDLUFA_TEXTURE_TO_CLAY

# User's exact conditions
rainfall = 800  # mm/year (typical Central Germany)
ph = 6.4
nv = 53  # Calciprill

print("=" * 80)
print("DIAGNOSTIC TEST - User Reported Issue")
print("=" * 80)
print(f"\nConditions:")
print(f"  Soil Texture: Sandy Loam")
print(f"  pH: {ph}")
print(f"  Rainfall: {rainfall} mm/year")
print(f"  Product NV: {nv}%")
print()

# Test 1: CEC Method with "Sandy Loam"
print("=" * 80)
print("TEST 1: CEC Method with 'Sandy Loam'")
print("=" * 80)

# Check if texture exists in CEC
if "Sandy Loam" in CEC_TEXTURE_TO_CLAY:
    print(f"✅ 'Sandy Loam' found in CEC texture mapping")
    print(f"   Clay %: {CEC_TEXTURE_TO_CLAY['Sandy Loam']}%")
else:
    print(f"❌ 'Sandy Loam' NOT found in CEC texture mapping")

result_cec = calculate_caco3_loss(
    precipitation_mm=rainfall,
    soil_texture="Sandy Loam",
    ph=ph,
    method="CEC"
)

if result_cec:
    caco3_loss = result_cec['caco3_loss']
    clay_pct = result_cec['clay_percent']
    drainage = result_cec['drainage_coef']
    bicarb = result_cec['bicarbonate_factor']

    print(f"\nCalculation breakdown:")
    print(f"  Clay %: {clay_pct}%")
    print(f"  Drainage coefficient: {drainage:.3f}")
    print(f"  Bicarbonate factor: {bicarb:.1f} mg/L")
    print(f"  CaCO3 loss: {caco3_loss:.1f} kg/ha/year")

    # Apply conversion
    cao_loss = caco3_loss / 1.785
    product = cao_loss * (100 / nv)

    print(f"\nConversion to product:")
    print(f"  CaO loss: {cao_loss:.2f} kg/ha")
    print(f"  Product needed (NV={nv}%): {product:.2f} kg/ha")
    print(f"\n  💡 User reported: 113.08 kgCaO")
    print(f"  💡 We calculated: {cao_loss:.2f} kgCaO")
    if abs(cao_loss - 113.08) < 1:
        print(f"  ✅ MATCH!")
    else:
        print(f"  ❌ MISMATCH - Difference: {abs(cao_loss - 113.08):.2f} kgCaO")

print()

# Test 2: VDLUFA Method with "Sandy Loam"
print("=" * 80)
print("TEST 2: VDLUFA Method with 'Sandy Loam'")
print("=" * 80)

# Check if texture exists in VDLUFA
if "Sandy Loam" in VDLUFA_TEXTURE_TO_CLAY:
    print(f"✅ 'Sandy Loam' found in VDLUFA texture mapping")
    print(f"   Clay %: {VDLUFA_TEXTURE_TO_CLAY['Sandy Loam']}%")
else:
    print(f"❌ 'Sandy Loam' NOT found in VDLUFA texture mapping")
    print(f"   Available VDLUFA textures: {list(VDLUFA_TEXTURE_TO_CLAY.keys())}")

result_vdlufa = calculate_caco3_loss(
    precipitation_mm=rainfall,
    soil_texture="Sandy Loam",
    ph=ph,
    method="VDLUFA"
)

if result_vdlufa:
    caco3_loss = result_vdlufa['caco3_loss']
    clay_pct = result_vdlufa['clay_percent']
    drainage = result_vdlufa['drainage_coef']
    bicarb = result_vdlufa['bicarbonate_factor']

    print(f"\nCalculation breakdown:")
    print(f"  Clay %: {clay_pct}%")
    print(f"  Drainage coefficient: {drainage:.3f}")
    print(f"  Bicarbonate factor: {bicarb:.1f} mg/L")
    print(f"  CaCO3 loss: {caco3_loss:.1f} kg/ha/year")

    # Apply conversion
    cao_loss = caco3_loss / 1.785
    product = cao_loss * (100 / nv)

    print(f"\nConversion to product:")
    print(f"  CaO loss: {cao_loss:.2f} kg/ha")
    print(f"  Product needed (NV={nv}%): {product:.2f} kg/ha")
    print(f"\n  💡 User reported: 193.22 kgCaO")
    print(f"  💡 We calculated: {cao_loss:.2f} kgCaO")
    if abs(cao_loss - 193.22) < 1:
        print(f"  ✅ MATCH!")
    else:
        print(f"  ❌ MISMATCH - Difference: {abs(cao_loss - 193.22):.2f} kgCaO")
else:
    print(f"\n❌ VDLUFA calculation returned None!")
    print(f"   This likely means 'Sandy Loam' is not a valid VDLUFA texture")

print()

# Test 3: Try common German textures for comparison
print("=" * 80)
print("TEST 3: VDLUFA German Textures (for comparison)")
print("=" * 80)

german_textures = ["Sand", "Schwach Lehm Sand", "Lehm"]

for texture in german_textures:
    result = calculate_caco3_loss(
        precipitation_mm=rainfall,
        soil_texture=texture,
        ph=ph,
        method="VDLUFA"
    )

    if result:
        caco3 = result['caco3_loss']
        cao = caco3 / 1.785
        product = cao * (100 / nv)
        print(f"\n{texture}:")
        print(f"  Clay: {result['clay_percent']}%, CaCO3: {caco3:.1f} kg/ha, CaO: {cao:.2f} kg/ha")

        if abs(cao - 193.22) < 5:
            print(f"  ⚠️  CLOSE TO USER'S VALUE (193.22 kgCaO)")

print()
print("=" * 80)
print("DIAGNOSIS")
print("=" * 80)
print()
print("If VDLUFA doesn't recognize 'Sandy Loam', it might:")
print("1. Return None (calculation fails)")
print("2. Use a default/fallback texture")
print("3. Be handled differently in the GUI vs backend")
print()
print("Check where the user is seeing these values:")
print("- In the GUI directly?")
print("- From backend API response?")
print("- From a calculation log?")
print()
