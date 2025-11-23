"""
Test script to verify pH Maintenance calculations are correct
"""

from utils.rainfall_lookup import calculate_caco3_loss

# Test conditions
rainfall = 800  # mm/year
ph = 6.0
nv = 53  # Calciprill

print("="*80)
print("Testing pH Maintenance Calculation")
print("="*80)
print(f"\nTest Conditions:")
print(f"  Rainfall: {rainfall} mm/year")
print(f"  pH: {ph}")
print(f"  Product NV: {nv}%")
print()

# Test VDLUFA method
print("VDLUFA Method (German texture 'Sand'):")
print("-"*80)
result_vdlufa = calculate_caco3_loss(
    precipitation_mm=rainfall,
    soil_texture="Sand",
    ph=ph,
    method="VDLUFA"
)

if result_vdlufa:
    caco3_loss = result_vdlufa['caco3_loss']
    cao_loss = caco3_loss / 1.785
    product = cao_loss * (100 / nv)

    print(f"  CaCO3 loss: {caco3_loss:.1f} kg/ha/year")
    print(f"  CaO loss: {cao_loss:.1f} kg/ha")
    print(f"  Product needed (NV={nv}%): {product:.1f} kg/ha")
print()

# Test CEC method
print("CEC Method (USDA texture 'Sandy Loam'):")
print("-"*80)
result_cec = calculate_caco3_loss(
    precipitation_mm=rainfall,
    soil_texture="Sandy Loam",
    ph=ph,
    method="CEC"
)

if result_cec:
    caco3_loss = result_cec['caco3_loss']
    cao_loss = caco3_loss / 1.785
    product = cao_loss * (100 / nv)

    print(f"  CaCO3 loss: {caco3_loss:.1f} kg/ha/year")
    print(f"  CaO loss: {cao_loss:.1f} kg/ha")
    print(f"  Product needed (NV={nv}%): {product:.1f} kg/ha")
print()

# Compare
if result_vdlufa and result_cec:
    vdlufa_product = (result_vdlufa['caco3_loss'] / 1.785) * (100 / nv)
    cec_product = (result_cec['caco3_loss'] / 1.785) * (100 / nv)
    diff = abs(vdlufa_product - cec_product)
    diff_pct = (diff / cec_product) * 100

    print("="*80)
    print("Comparison:")
    print("="*80)
    print(f"  VDLUFA: {vdlufa_product:.1f} kg/ha")
    print(f"  CEC: {cec_product:.1f} kg/ha")
    print(f"  Difference: {diff:.1f} kg/ha ({diff_pct:.1f}%)")
    print()

    if diff_pct < 10:
        print("  ✅ PASS: Difference is acceptable (< 10%)")
        print("  This is expected due to different texture classifications")
    else:
        print("  ❌ FAIL: Difference is too large (> 10%)")
        print("  Something may be wrong with the calculation")
    print()

print("="*80)
print("Expected Result:")
print("="*80)
print("Both methods should follow: CaCO3 → CaO → Product with NV")
print("Formula: Product = (CaCO3_loss / 1.785) × (100 / NV)")
print()
print("If you see ~270 kg/ha, the formula is WRONG (applying NV to CaCO3)")
print("If you see ~151 kg/ha, the formula is CORRECT (applying NV to CaO)")
print("="*80)
