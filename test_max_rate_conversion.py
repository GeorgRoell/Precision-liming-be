"""Test max application rate conversion from CaCO3 to different lime types."""

# Test the conversion logic
LIME_CONVERSION_FACTORS = {
    "CaO": 1.0,              # Pure CaO (reference)
    "CaCO3": 1.785,          # Calcium carbonate
    "Ca(OH)2": 1.321,        # Calcium hydroxide
    "Quicklime": 1.0,        # Quicklime (CaO)
    "Slaked_lime": 1.321,    # Slaked lime (Ca(OH)2)
    "Agrocarb": 2.381,       # Agrocarb (NV 42)
    "Omya_Calciprill": 1.887 # Omya Calciprill (NV 53)
}

max_rate_caco3 = 3000  # kg/ha in CaCO3 equivalents

print("=" * 70)
print("MAX APPLICATION RATE CONVERSION TEST")
print("=" * 70)
print(f"\nInput: Max rate = {max_rate_caco3} kg/ha CaCO3 equivalent\n")
print(f"{'Lime Type':<20} {'Conversion':<15} {'Max Rate (kg/ha)':<20}")
print("-" * 70)

caco3_factor = LIME_CONVERSION_FACTORS["CaCO3"]

for lime_type, conversion_factor in LIME_CONVERSION_FACTORS.items():
    # Convert from CaCO3 to lime type
    max_rate_in_lime_type = max_rate_caco3 * (conversion_factor / caco3_factor)

    print(f"{lime_type:<20} {conversion_factor:<15.3f} {max_rate_in_lime_type:<20.1f}")

print("\n" + "=" * 70)
print("EXAMPLE: If VDLUFA calculates 5000 kg/ha CaO needed:")
print("=" * 70)

calculated_cao = 5000
print(f"\nCalculated requirement: {calculated_cao} kg/ha CaO")
print(f"Max rate limit (CaCO3): {max_rate_caco3} kg/ha")

# Convert max rate to CaO
max_rate_cao = max_rate_caco3 * (LIME_CONVERSION_FACTORS["CaO"] / caco3_factor)
print(f"Max rate in CaO:        {max_rate_cao:.1f} kg/ha")

if calculated_cao > max_rate_cao:
    print(f"\n✓ CAPPED: {calculated_cao} > {max_rate_cao:.1f}")
    print(f"  Applied: {max_rate_cao:.1f} kg/ha CaO")
    print(f"  Which equals: {max_rate_caco3} kg/ha CaCO3 ✓")
else:
    print(f"\n✗ NOT CAPPED: {calculated_cao} <= {max_rate_cao:.1f}")
    print(f"  Applied: {calculated_cao} kg/ha CaO")
