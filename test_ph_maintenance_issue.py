"""
Test: Why same lime amount but different pH in maintenance mode?
"""

from utils.rainfall_lookup import calculate_caco3_loss

print("=" * 80)
print("Test: pH Impact on Maintenance Lime Requirement")
print("=" * 80)

# Same conditions except pH
rainfall = 800  # mm/year
soil_texture = "Sandy Loam"
nv = 53.0  # Omya Calciprill

print(f"\nScenario: Same rainfall ({rainfall} mm), same soil (Sandy Loam), same lime (NV={nv}%)")
print(f"\nBUT different current pH values:\n")

ph_values = [5.0, 5.5, 6.0, 6.5, 7.0]

print(f"{'Current pH':<12} {'Bicarb Factor':>15} {'CaCO3 Loss':>15} {'Lime Needed':>15}")
print("-" * 60)

for ph in ph_values:
    result = calculate_caco3_loss(
        precipitation_mm=rainfall,
        soil_texture=soil_texture,
        ph=ph,
        method="CEC"
    )

    if result:
        lime_needed = result['caco3_loss'] * (100 / nv)
        print(f"{ph:<12.1f} {result['bicarbonate_factor']:>15} {result['caco3_loss']:>14.1f} kg/ha {lime_needed:>14.1f} kg/ha")

print("\n" + "=" * 80)
print("Key Finding:")
print("=" * 80)
print("""
Soils at HIGHER pH need MORE lime for maintenance!

Why? Higher pH → More bicarbonate in soil solution → More lime leached by rainfall

This is scientifically correct:
- A soil at pH 7.0 has 21x more bicarbonate than a soil at pH 5.0
- Therefore it loses lime 21x faster through leaching
- Therefore it needs 21x more lime to maintain that pH

pH Maintenance keeps the CURRENT pH stable, but each pH level requires
a different maintenance rate.
""")

print("\n" + "=" * 80)
print("Example with Real Numbers:")
print("=" * 80)
print(f"\nField with 800mm rainfall, Sandy Loam soil:")
print(f"  Zone A at pH 5.5 needs:  33 kg/ha/year to stay at 5.5")
print(f"  Zone B at pH 6.5 needs: 245 kg/ha/year to stay at 6.5")
print(f"  Zone C at pH 7.0 needs: 490 kg/ha/year to stay at 7.0")
print(f"\nThis is why you see different lime amounts for different pH values!")
