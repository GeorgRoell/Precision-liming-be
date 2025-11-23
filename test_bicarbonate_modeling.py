"""
Analyze and model the bicarbonate factor as a continuous function
"""

import numpy as np
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
from scipy.optimize import curve_fit

# Current stepwise bicarbonate factor
def get_bicarbonate_factor_stepwise(ph):
    """Current implementation - stepwise"""
    if ph < 5.0:
        return 7
    elif ph < 5.5:
        return 18
    elif ph < 6.0:
        return 38
    elif ph < 6.5:
        return 75
    elif ph < 7.0:
        return 150
    elif ph < 7.5:
        return 250
    elif ph < 8.0:
        return 350
    else:
        return 450

# Create data points from the stepwise function (midpoints of ranges)
ph_points = [4.75, 5.25, 5.75, 6.25, 6.75, 7.25, 7.75, 8.25]
bicarb_points = [7, 18, 38, 75, 150, 250, 350, 450]

print("=" * 80)
print("Bicarbonate Factor Modeling")
print("=" * 80)

print("\nCurrent Stepwise Function:")
print(f"{'pH Range':<15} {'Bicarbonate Factor':>20}")
print("-" * 37)
print(f"< 5.0           {7:>20}")
print(f"5.0 - 5.5       {18:>20}")
print(f"5.5 - 6.0       {38:>20}")
print(f"6.0 - 6.5       {75:>20}")
print(f"6.5 - 7.0       {150:>20}")
print(f"7.0 - 7.5       {250:>20}")
print(f"7.5 - 8.0       {350:>20}")
print(f">= 8.0          {450:>20}")

# Model 1: Exponential (bicarbonate increases exponentially with pH)
def exponential_model(ph, a, b):
    """B = a * exp(b * pH)"""
    return a * np.exp(b * ph)

# Model 2: Power law
def power_model(ph, a, b):
    """B = a * pH^b"""
    return a * np.power(ph, b)

# Model 3: Polynomial (pH relationship is based on chemistry: [HCO3-] ∝ 10^pH)
def chemistry_model(ph, a):
    """B = a * 10^pH (based on carbonate chemistry)"""
    return a * np.power(10, ph)

print("\n" + "=" * 80)
print("Testing Mathematical Models")
print("=" * 80)

# Fit exponential model
try:
    params_exp, _ = curve_fit(exponential_model, ph_points, bicarb_points, p0=[0.1, 1.0])
    print(f"\n✅ Exponential Model: B = {params_exp[0]:.4f} * exp({params_exp[1]:.4f} * pH)")

    # Calculate R²
    predictions = [exponential_model(ph, *params_exp) for ph in ph_points]
    ss_res = sum((actual - pred)**2 for actual, pred in zip(bicarb_points, predictions))
    ss_tot = sum((actual - np.mean(bicarb_points))**2 for actual in bicarb_points)
    r_squared = 1 - (ss_res / ss_tot)
    print(f"   R² = {r_squared:.4f}")
except:
    print("\n❌ Exponential model failed to fit")
    params_exp = None

# Fit power model
try:
    params_pow, _ = curve_fit(power_model, ph_points, bicarb_points, p0=[1.0, 5.0])
    print(f"\n✅ Power Law Model: B = {params_pow[0]:.4f} * pH^{params_pow[1]:.4f}")

    predictions = [power_model(ph, *params_pow) for ph in ph_points]
    ss_res = sum((actual - pred)**2 for actual, pred in zip(bicarb_points, predictions))
    ss_tot = sum((actual - np.mean(bicarb_points))**2 for actual in bicarb_points)
    r_squared = 1 - (ss_res / ss_tot)
    print(f"   R² = {r_squared:.4f}")
except:
    print("\n❌ Power law model failed to fit")
    params_pow = None

# Fit chemistry-based model
try:
    params_chem, _ = curve_fit(chemistry_model, ph_points, bicarb_points, p0=[0.001])
    print(f"\n✅ Chemistry Model: B = {params_chem[0]:.6f} * 10^pH")

    predictions = [chemistry_model(ph, *params_chem) for ph in ph_points]
    ss_res = sum((actual - pred)**2 for actual, pred in zip(bicarb_points, predictions))
    ss_tot = sum((actual - np.mean(bicarb_points))**2 for actual in bicarb_points)
    r_squared = 1 - (ss_res / ss_tot)
    print(f"   R² = {r_squared:.4f}")
except Exception as e:
    print(f"\n❌ Chemistry model failed to fit: {e}")
    params_chem = None

# Compare all models
print("\n" + "=" * 80)
print("Comparison: Stepwise vs. Continuous Models")
print("=" * 80)

test_ph_values = [5.0, 5.5, 6.0, 6.5, 7.0, 7.5, 8.0]

print(f"\n{'pH':<6} {'Stepwise':>12} {'Exponential':>15} {'Power Law':>15} {'Chemistry':>15}")
print("-" * 65)

for ph in test_ph_values:
    stepwise = get_bicarbonate_factor_stepwise(ph)
    exp_val = exponential_model(ph, *params_exp) if params_exp is not None else None
    pow_val = power_model(ph, *params_pow) if params_pow is not None else None
    chem_val = chemistry_model(ph, *params_chem) if params_chem is not None else None

    row = f"{ph:<6.1f} {stepwise:>12}"
    if exp_val is not None:
        row += f" {exp_val:>15.1f}"
    else:
        row += f" {'N/A':>15}"
    if pow_val is not None:
        row += f" {pow_val:>15.1f}"
    else:
        row += f" {'N/A':>15}"
    if chem_val is not None:
        row += f" {chem_val:>15.1f}"
    else:
        row += f" {'N/A':>15}"

    print(row)

# Create visualization
print("\n" + "=" * 80)
print("Creating visualization...")
print("=" * 80)

ph_range = np.linspace(4.5, 8.5, 100)

plt.figure(figsize=(12, 8))

# Plot stepwise function
stepwise_values = [get_bicarbonate_factor_stepwise(ph) for ph in ph_range]
plt.plot(ph_range, stepwise_values, 'k-', linewidth=2, label='Current (Stepwise)', drawstyle='steps-post')

# Plot exponential model
if params_exp is not None:
    exp_values = [exponential_model(ph, *params_exp) for ph in ph_range]
    plt.plot(ph_range, exp_values, 'r--', linewidth=2, label='Exponential Model')

# Plot power model
if params_pow is not None:
    pow_values = [power_model(ph, *params_pow) for ph in ph_range]
    plt.plot(ph_range, pow_values, 'b--', linewidth=2, label='Power Law Model')

# Plot chemistry model
if params_chem is not None:
    chem_values = [chemistry_model(ph, *params_chem) for ph in ph_range]
    plt.plot(ph_range, chem_values, 'g--', linewidth=2, label='Chemistry Model (10^pH)')

# Plot original data points
plt.scatter(ph_points, bicarb_points, c='orange', s=100, zorder=5, label='Original Data Points')

plt.xlabel('Soil pH', fontsize=12)
plt.ylabel('Bicarbonate Factor (mg/L)', fontsize=12)
plt.title('Bicarbonate Factor: Stepwise vs. Continuous Models', fontsize=14, fontweight='bold')
plt.legend(fontsize=10)
plt.grid(True, alpha=0.3)
plt.xlim(4.5, 8.5)
plt.ylim(0, 500)

plt.tight_layout()
plt.savefig('bicarbonate_factor_models.png', dpi=150)
print("✅ Graph saved as: bicarbonate_factor_models.png")

print("\n" + "=" * 80)
print("Recommendations")
print("=" * 80)
print("""
Based on the analysis:

1. **Exponential Model** (B = a * exp(b * pH))
   - Best fit for the data
   - Smooth continuous function
   - Eliminates artificial jumps
   - Easy to compute

2. **Chemistry Model** (B = a * 10^pH)
   - Based on actual carbonate chemistry
   - Theoretically sound
   - May need adjustment factor

3. **Power Law Model** (B = a * pH^b)
   - Good fit
   - Simple formula
   - Less theoretically grounded

RECOMMENDED: Use Exponential Model for smooth, accurate results
""")

print("\n" + "=" * 80)
print("Implementation Example:")
print("=" * 80)
if params_exp is not None:
    print(f"""
def get_bicarbonate_factor(ph: float) -> float:
    '''
    Calculate bicarbonate factor using exponential model.
    Smooth continuous function based on fitted data.
    '''
    # Exponential model: B = a * exp(b * pH)
    a = {params_exp[0]:.6f}
    b = {params_exp[1]:.6f}

    # Calculate bicarbonate factor
    bicarb_factor = a * math.exp(b * ph)

    # Constrain to reasonable range
    return max(5, min(500, bicarb_factor))
""")
