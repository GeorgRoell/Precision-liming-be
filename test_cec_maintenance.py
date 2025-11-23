"""
Test CEC method with rainfall-based pH Maintenance
"""

from calculators.liming import CECCalculator

# Test parameters
current_ph = 5.8
target_ph = 6.5
cec_soil = 10.0  # Sandy Loam
fine_dry_soil = 1500.0
nv = 53.0  # Omya Calciprill
dose = 1.0

# Simulated CaCO3 loss from rainfall (e.g., 800mm rainfall)
# From VDLUFA example: ~130 kg/ha CaCO3 loss
caco3_loss_kg_ha = 130.0

print("=" * 70)
print("CEC Method - Rainfall-Based pH Maintenance Test")
print("=" * 70)

print("\n📊 Test Parameters:")
print(f"  Current pH: {current_ph}")
print(f"  Target pH: {target_ph}")
print(f"  CEC: {cec_soil} meq/100g (Sandy Loam)")
print(f"  Fine & dry soil: {fine_dry_soil}")
print(f"  NV: {nv}% (Omya Calciprill)")
print(f"  Dose: {dose}")
print(f"  CaCO3 Loss: {caco3_loss_kg_ha} kg/ha/year")

# Test 1: pH Improvement Mode (should NOT use rainfall)
print("\n" + "=" * 70)
print("Test 1: pH Improvement Mode")
print("=" * 70)

lime_improvement = CECCalculator.calculate_lime_requirement(
    current_ph=current_ph,
    target_ph=target_ph,
    cec_soil=cec_soil,
    fine_dry_soil=fine_dry_soil,
    nv=nv,
    dose=dose,
    liming_mode="pH Improvement",
    caco3_loss_kg_ha=caco3_loss_kg_ha  # Should be ignored in this mode
)

print(f"✅ Result: {lime_improvement:.1f} kg/ha")
print(f"   Expected: Should calculate based on pH change (5.8 → 6.5)")

# Test 2: pH Maintenance Mode (should USE rainfall)
print("\n" + "=" * 70)
print("Test 2: pH Maintenance Mode WITH Rainfall Data")
print("=" * 70)

lime_maintenance = CECCalculator.calculate_lime_requirement(
    current_ph=current_ph,
    target_ph=target_ph,
    cec_soil=cec_soil,
    fine_dry_soil=fine_dry_soil,
    nv=nv,
    dose=dose,
    liming_mode="pH Maintenance",
    caco3_loss_kg_ha=caco3_loss_kg_ha
)

print(f"✅ Result: {lime_maintenance:.1f} kg/ha")
print(f"   Formula: CaCO3_loss × (100 / NV) = {caco3_loss_kg_ha} × (100 / {nv})")
print(f"   Expected: {caco3_loss_kg_ha * (100 / nv):.1f} kg/ha")

# Test 3: pH Maintenance Mode WITHOUT Rainfall Data
print("\n" + "=" * 70)
print("Test 3: pH Maintenance Mode WITHOUT Rainfall Data")
print("=" * 70)

lime_maintenance_no_rainfall = CECCalculator.calculate_lime_requirement(
    current_ph=current_ph,
    target_ph=target_ph,
    cec_soil=cec_soil,
    fine_dry_soil=fine_dry_soil,
    nv=nv,
    dose=dose,
    liming_mode="pH Maintenance",
    caco3_loss_kg_ha=None  # No rainfall data
)

print(f"✅ Result: {lime_maintenance_no_rainfall:.1f} kg/ha")
print(f"   Expected: 0.0 kg/ha (no rainfall data available)")

# Test 4: pH Maintenance with pH ABOVE target
print("\n" + "=" * 70)
print("Test 4: pH Maintenance with pH Above Target")
print("=" * 70)

lime_above_target = CECCalculator.calculate_lime_requirement(
    current_ph=6.8,  # Above target
    target_ph=target_ph,
    cec_soil=cec_soil,
    fine_dry_soil=fine_dry_soil,
    nv=nv,
    dose=dose,
    liming_mode="pH Maintenance",
    caco3_loss_kg_ha=caco3_loss_kg_ha
)

print(f"✅ Result: {lime_above_target:.1f} kg/ha")
print(f"   Expected: 0.0 kg/ha (pH already above target)")

# Test 5: Automatic Mode with pH near target
print("\n" + "=" * 70)
print("Test 5: Automatic Mode (pH within 0.1 of target)")
print("=" * 70)

lime_automatic = CECCalculator.calculate_lime_requirement(
    current_ph=6.45,  # Within 0.1 of target (6.5)
    target_ph=target_ph,
    cec_soil=cec_soil,
    fine_dry_soil=fine_dry_soil,
    nv=nv,
    dose=dose,
    liming_mode="Automatic",
    caco3_loss_kg_ha=caco3_loss_kg_ha
)

print(f"✅ Result: {lime_automatic:.1f} kg/ha")
print(f"   Expected: {caco3_loss_kg_ha * (100 / nv):.1f} kg/ha (uses maintenance mode)")

# Summary
print("\n" + "=" * 70)
print("📝 Summary")
print("=" * 70)
print(f"pH Improvement:             {lime_improvement:.1f} kg/ha")
print(f"pH Maintenance (w/ rainfall): {lime_maintenance:.1f} kg/ha")
print(f"pH Maintenance (no rainfall): {lime_maintenance_no_rainfall:.1f} kg/ha")
print(f"pH above target:             {lime_above_target:.1f} kg/ha")
print(f"Automatic (near target):     {lime_automatic:.1f} kg/ha")

print("\n" + "=" * 70)
print("✅ All tests completed!")
print("=" * 70)
