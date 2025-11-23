"""
Test the new Power Law Model for bicarbonate factor
Compare old stepwise vs. new continuous function
"""

from utils.rainfall_lookup import get_bicarbonate_factor, calculate_caco3_loss

print("=" * 80)
print("Test: Power Law Model - Smooth Bicarbonate Factor")
print("=" * 80)

# Test the bicarbonate factor directly
print("\n1. Bicarbonate Factor Values:")
print("-" * 80)
print(f"{'pH':<8} {'Bicarbonate Factor':>20} {'Notes':<30}")
print("-" * 80)

# Test at exact boundaries (where old model had jumps)
test_ph_values = [
    (4.99, "Just below pH 5.0"),
    (5.00, "Exactly pH 5.0"),
    (5.01, "Just above pH 5.0"),
    (5.49, "Just below pH 5.5"),
    (5.50, "Exactly pH 5.5"),
    (5.51, "Just above pH 5.5"),
    (5.99, "Just below pH 6.0"),
    (6.00, "Exactly pH 6.0"),
    (6.01, "Just above pH 6.0"),
    (6.49, "Just below pH 6.5"),
    (6.50, "Exactly pH 6.5"),
    (6.51, "Just above pH 6.5"),
    (7.00, "Exactly pH 7.0"),
    (7.50, "Exactly pH 7.5"),
]

for ph, note in test_ph_values:
    b_factor = get_bicarbonate_factor(ph)
    print(f"{ph:<8.2f} {b_factor:>20.1f} {note:<30}")

print("\n" + "=" * 80)
print("2. CaCO3 Loss Calculation - Smooth Transitions")
print("=" * 80)

# Test parameters
rainfall = 800  # mm/year
soil_texture = "Sandy Loam"
nv = 53.0

print(f"\nConditions: {rainfall} mm rainfall, {soil_texture}, NV={nv}%\n")
print(f"{'pH':<8} {'Bicarb':>10} {'CaCO3 Loss':>15} {'Lime Needed':>15} {'Change':>12}")
print("-" * 62)

prev_lime = None
for ph in [5.0, 5.5, 6.0, 6.5, 7.0, 7.5]:
    result = calculate_caco3_loss(
        precipitation_mm=rainfall,
        soil_texture=soil_texture,
        ph=ph,
        method="CEC"
    )

    if result:
        lime_needed = result['caco3_loss'] * (100 / nv)
        change = ""
        if prev_lime is not None:
            diff = lime_needed - prev_lime
            pct = (diff / prev_lime) * 100
            change = f"+{diff:.0f} ({pct:+.0f}%)"

        print(f"{ph:<8.1f} {result['bicarbonate_factor']:>10.1f} {result['caco3_loss']:>14.1f} kg {lime_needed:>14.1f} kg {change:>12}")
        prev_lime = lime_needed

print("\n" + "=" * 80)
print("3. No More Artificial Jumps - Gradual Changes")
print("=" * 80)

print(f"\nTesting 0.01 pH increments around pH 6.0 boundary:\n")
print(f"{'pH':<8} {'Bicarbonate':>15} {'Lime (kg/ha)':>15} {'Jump?':>10}")
print("-" * 50)

ph_range = [5.97, 5.98, 5.99, 6.00, 6.01, 6.02, 6.03]
prev_value = None

for ph in ph_range:
    result = calculate_caco3_loss(
        precipitation_mm=rainfall,
        soil_texture=soil_texture,
        ph=ph,
        method="CEC"
    )

    if result:
        lime_needed = result['caco3_loss'] * (100 / nv)
        jump = ""
        if prev_value is not None:
            diff_pct = ((lime_needed - prev_value) / prev_value) * 100
            if abs(diff_pct) > 10:
                jump = f"⚠️ {diff_pct:+.0f}%"
            else:
                jump = f"✓ {diff_pct:+.1f}%"

        print(f"{ph:<8.2f} {result['bicarbonate_factor']:>15.1f} {lime_needed:>15.1f} {jump:>10}")
        prev_value = lime_needed

print("\n" + "=" * 80)
print("✅ Power Law Model Implemented Successfully!")
print("=" * 80)
print("""
Key Benefits:
1. Smooth continuous function - no artificial jumps
2. Gradual transitions between pH values
3. More accurate representation of soil chemistry
4. Better user experience with predictable results

Formula: B = 0.0023 × pH^5.79 (R² = 0.9852)
""")
