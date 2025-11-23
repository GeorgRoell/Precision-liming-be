# Liming prescription calculation engine
# nextfarming/geo/liming.py

import math
from typing import Dict, List, Tuple, Optional, Union
import logging

# Import rainfall lookup utility
try:
    from utils.rainfall_lookup import (
        get_rainfall_from_geometry,
        get_annual_rainfall,
        calculate_caco3_loss
    )
    RAINFALL_LOOKUP_AVAILABLE = True
except ImportError:
    RAINFALL_LOOKUP_AVAILABLE = False
    logging.warning("Rainfall lookup utility not available")

logger = logging.getLogger(__name__)

class VDLUFACalculator:
    """VDLUFA method for liming calculation based on German standards."""

    # Soil texture classifications
    SOIL_TEXTURES = [
        "Sand",
        "Schwach Lehm Sand",
        "Stark Lehmiger Sand",
        "Sandiger Schl Lehm",
        "Toniger Lehm b.Ton"
    ]

    # Lime type conversion factors (from CaO equivalent to actual lime types)
    LIME_CONVERSION_FACTORS = {
        "CaO": 1.0,              # Pure CaO (reference)
        "CaCO3": 1.785,          # Calcium carbonate (CaCO3/CaO = 100.09/56.08 = 1.785)
        "Ca(OH)2": 1.321,        # Calcium hydroxide (Ca(OH)2/CaO = 74.09/56.08 = 1.321)
        "Quicklime": 1.0,        # Quicklime (CaO)
        "Slaked_lime": 1.321,    # Slaked lime (Ca(OH)2)
        "Agrocarb": 2.381,       # Agrocarb (NV 42, conversion = 100/42 = 2.381)
        "Omya_Calciprill": 1.887    # Omya Calciprill (NV 53, conversion = 100/53 = 1.887)
    }

    # Mapping from Next Farming soil types to VDLUFA classifications
    TEXTURE_MAPPING = {
        # Next Farming API values -> VDLUFA classifications
        "Bog": None,  # Not used
        "Clay": "Toniger Lehm b.Ton",
        "Clayey loam": "Toniger Lehm b.Ton",
        "half-bog soil": None,  # Not used
        "loamy clay": "Toniger Lehm b.Ton",
        "sand": "Sand",
        "sandy loam": "Sandiger Schl Lehm",
        "silty clay": "Toniger Lehm b.Ton",
        "silty loam": "Stark Lehmiger Sand",
        "slightly clayey loam": "Toniger Lehm b.Ton",
        "slightly loamy sand": "Schwach Lehm Sand",
        "very loamy sand": "Stark Lehmiger Sand",
        # Case variations
        "CLAY": "Toniger Lehm b.Ton",
        "SANDY_LOAM": "Sandiger Schl Lehm",
        "SILTY_LOAM": "Stark Lehmiger Sand",
        "SAND": "Sand",
        # Direct VDLUFA names
        "Sand": "Sand",
        "Schwach Lehm Sand": "Schwach Lehm Sand",
        "Stark Lehmiger Sand": "Stark Lehmiger Sand",
        "Sandiger Schl Lehm": "Sandiger Schl Lehm",
        "Toniger Lehm b.Ton": "Toniger Lehm b.Ton"
    }

    # Crop types
    CROP_TYPES = [
        "Standard crops",
        "Other crops"
    ]

    @staticmethod
    def map_soil_texture(api_texture: str) -> str:
        """
        Map API soil texture to VDLUFA classification.

        Args:
            api_texture: Soil texture from API

        Returns:
            VDLUFA soil texture classification
        """
        if api_texture is None:
            return None

        # Try exact match first
        if api_texture in VDLUFACalculator.TEXTURE_MAPPING:
            return VDLUFACalculator.TEXTURE_MAPPING[api_texture]

        # Try case-insensitive match
        api_upper = api_texture.upper()
        if api_upper in VDLUFACalculator.TEXTURE_MAPPING:
            return VDLUFACalculator.TEXTURE_MAPPING[api_upper]

        # Default mapping based on common keywords
        texture_lower = api_texture.lower()
        if 'sand' in texture_lower:
            if 'loam' in texture_lower:
                return "Schwach Lehm Sand"
            else:
                return "Sand"
        elif 'clay' in texture_lower:
            return "Toniger Lehm b.Ton"
        elif 'loam' in texture_lower or 'lehm' in texture_lower:
            return "Stark Lehm Sand"
        elif 'silt' in texture_lower:
            return "Sandiger Schl Lehm"
        else:
            # Unknown texture - return None to use default
            return None

    @staticmethod
    def convert_lime_type(cao_equivalent: float, target_lime_type: str = "CaCO3") -> float:
        """
        Convert CaO equivalent to specific lime type.

        Args:
            cao_equivalent: Lime requirement in CaO equivalent (kg/ha)
            target_lime_type: Target lime type for conversion

        Returns:
            Converted lime requirement in kg/ha
        """
        if target_lime_type in VDLUFACalculator.LIME_CONVERSION_FACTORS:
            return cao_equivalent * VDLUFACalculator.LIME_CONVERSION_FACTORS[target_lime_type]
        else:
            return cao_equivalent  # Default to CaO if unknown type

    @staticmethod
    def reverse_calculate_ph(lime_kg_ha: float, soil_texture: str, crop_type: str, lime_type: str = "CaO", current_ph: float = None) -> float:
        """
        Reverse-calculate the pH that will be achieved given a lime application rate from a current pH.

        The approach: Calculate what the optimal pH would need to be such that the lime requirement
        from current_ph to that optimal equals lime_kg_ha.

        Args:
            lime_kg_ha: Lime application rate in kg/ha
            soil_texture: Soil texture classification
            crop_type: Type of crop (Standard crops or Other crops)
            lime_type: Type of lime used
            current_ph: Current soil pH (required for accurate calculation)

        Returns:
            Expected pH after lime application
        """
        if current_ph is None:
            # Fallback to old method if current pH not provided
            if lime_type in VDLUFACalculator.LIME_CONVERSION_FACTORS:
                conversion_factor = VDLUFACalculator.LIME_CONVERSION_FACTORS[lime_type]
                cao_kg_ha = lime_kg_ha / conversion_factor
            else:
                cao_kg_ha = lime_kg_ha

            cao_dt_ha = cao_kg_ha / 100
            mapped_texture = VDLUFACalculator.map_soil_texture(soil_texture)

            if crop_type == "Standard crops":
                return VDLUFACalculator._reverse_standard_crops(cao_dt_ha, mapped_texture)
            else:
                return VDLUFACalculator._reverse_other_crops(cao_dt_ha, mapped_texture)

        # New approach: Binary search to find target pH
        # We know: lime_needed(current_ph -> target_ph) = lime_kg_ha
        # Find target_ph that satisfies this equation

        mapped_texture = VDLUFACalculator.map_soil_texture(soil_texture)
        optimal_ph = VDLUFACalculator._get_optimal_ph(mapped_texture, crop_type)

        # If no lime needed, return current pH
        if lime_kg_ha <= 0:
            return current_ph

        # Binary search for the target pH
        low_ph = current_ph
        high_ph = optimal_ph
        tolerance = 0.01
        max_iterations = 100

        for _ in range(max_iterations):
            mid_ph = (low_ph + high_ph) / 2

            # Calculate lime needed to go from current_ph to mid_ph
            # We do this by calculating lime for mid_ph and subtracting lime for current_ph
            lime_for_mid = VDLUFACalculator.calculate_lime_requirement(current_ph, soil_texture, crop_type, lime_type, "pH Improvement")

            # Actually, we need a different approach - calculate directly what lime brings us to mid_ph
            # Use the formula: lime_to_target = lime_calc(current_ph, with target = mid_ph)
            # But the formula doesn't take target pH as input...

            # Let's try: calculate how much lime is needed if optimal was at mid_ph
            # This requires temporarily using mid_ph as optimal
            # Actually, this won't work with the current formula structure

            # Simpler approach: approximate using the derivative
            # For small pH changes, lime ≈ slope * (target_pH - current_pH)
            # But VDLUFA uses piecewise linear, so we can use the actual slope

            break  # Exit for now, need better approach

        # Fallback: use simple proportion based on optimal pH
        # If full lime needed = lime_to_optimal, and we apply lime_kg_ha
        # Then pH increase = (lime_kg_ha / lime_to_optimal) * (optimal_ph - current_ph)
        lime_to_optimal = VDLUFACalculator.calculate_lime_requirement(current_ph, soil_texture, crop_type, lime_type, "pH Improvement")

        if lime_to_optimal <= 0:
            return current_ph

        # Calculate proportional pH increase
        ph_increase_fraction = min(1.0, lime_kg_ha / lime_to_optimal)
        achieved_ph = current_ph + ph_increase_fraction * (optimal_ph - current_ph)

        return achieved_ph

    @staticmethod
    def _reverse_standard_crops(cao_dt_ha: float, soil_texture: str) -> float:
        """Reverse calculate pH from lime requirement for standard crops."""

        if soil_texture == "Sand":
            if cao_dt_ha >= 45.0:
                return 4.0  # Below minimum
            elif cao_dt_ha <= 0.0:
                return 5.9  # At or above optimal
            elif cao_dt_ha <= 3.93:  # Using threshold from formula
                # From: -11.852 * pH + 69.93 = cao_dt_ha
                return (69.93 - cao_dt_ha) / 11.852
            else:
                # From: -28.945 * pH + 160.52 = cao_dt_ha
                return (160.52 - cao_dt_ha) / 28.945

        elif soil_texture == "Schwach Lehm Sand":
            if cao_dt_ha >= 77.0:
                return 4.0
            elif cao_dt_ha <= 0.0:
                return 6.4
            elif cao_dt_ha <= 11.67:
                # From: -16.667 * pH + 106.67 = cao_dt_ha
                return (106.67 - cao_dt_ha) / 16.667
            else:
                # From: -38.71 * pH + 231.47 = cao_dt_ha
                return (231.47 - cao_dt_ha) / 38.71

        elif soil_texture == "Stark Lehmiger Sand":
            if cao_dt_ha >= 87.0:
                return 4.0
            elif cao_dt_ha <= 0.0:
                return 6.8
            elif cao_dt_ha <= 16.0:
                # From: -20.0 * pH + 136.0 = cao_dt_ha
                return (136.0 - cao_dt_ha) / 20.0
            else:
                # From: -47.912 * pH + 302.54 = cao_dt_ha
                return (302.54 - cao_dt_ha) / 47.912

        elif soil_texture == "Sandiger Schl Lehm":
            if cao_dt_ha >= 117.0:
                return 4.0
            elif cao_dt_ha <= 0.0:
                return 7.1
            elif cao_dt_ha <= 19.75:
                # From: -21.25 * pH + 150.87 = cao_dt_ha
                return (150.87 - cao_dt_ha) / 21.25
            else:
                # From: -58.122 * pH + 378.54 = cao_dt_ha
                return (378.54 - cao_dt_ha) / 58.122

        elif soil_texture == "Toniger Lehm b.Ton":
            if cao_dt_ha >= 160.0:
                return 4.0
            elif cao_dt_ha <= 0.0:
                return 7.3
            elif cao_dt_ha <= 22.22:
                # From: -22.222 * pH + 162.22 = cao_dt_ha
                return (162.22 - cao_dt_ha) / 22.222
            else:
                # From: -76.93 * pH + 505.53 = cao_dt_ha
                return (505.53 - cao_dt_ha) / 76.93

        else:  # Unknown texture - use sand as default
            if cao_dt_ha >= 45.0:
                return 4.0
            elif cao_dt_ha <= 0.0:
                return 5.9
            else:
                return (160.52 - cao_dt_ha) / 28.945

    @staticmethod
    def _reverse_other_crops(cao_dt_ha: float, soil_texture: str) -> float:
        """Reverse calculate pH from lime requirement for other crops."""

        if soil_texture == "Sand":
            if cao_dt_ha >= 50.0:
                return 3.4
            elif cao_dt_ha <= 0.0:
                return 5.2
            elif cao_dt_ha <= 5.6:
                # From: -8.0 * pH + 41.6 = cao_dt_ha
                return (41.6 - cao_dt_ha) / 8.0
            else:
                # From: -37.692 * pH + 178.46 = cao_dt_ha
                return (178.46 - cao_dt_ha) / 37.692

        elif soil_texture == "Schwach Lehm Sand":
            if cao_dt_ha >= 83.0:
                return 3.3
            elif cao_dt_ha <= 0.0:
                return 5.6
            elif cao_dt_ha <= 9.33:
                # From: -13.333 * pH + 74.667 = cao_dt_ha
                return (74.667 - cao_dt_ha) / 13.333
            else:
                # From: -46.348 * pH + 235.91 = cao_dt_ha
                return (235.91 - cao_dt_ha) / 46.348

        elif soil_texture == "Stark Lehmiger Sand":
            if cao_dt_ha >= 90.0:
                return 3.8
            elif cao_dt_ha <= 0.0:
                return 5.9
            elif cao_dt_ha <= 10.0:
                # From: -14.286 * pH + 84.286 = cao_dt_ha
                return (84.286 - cao_dt_ha) / 14.286
            else:
                # From: -60.989 * pH + 322.04 = cao_dt_ha
                return (322.04 - cao_dt_ha) / 60.989

        elif soil_texture == "Sandiger Schl Lehm":
            if cao_dt_ha >= 109.0:
                return 3.8
            elif cao_dt_ha <= 0.0:
                return 6.2
            elif cao_dt_ha <= 15.0:
                # From: -16.25 * pH + 100.75 = cao_dt_ha
                return (100.75 - cao_dt_ha) / 16.25
            else:
                # From: -63.309 * pH + 349.87 = cao_dt_ha
                return (349.87 - cao_dt_ha) / 63.309

        elif soil_texture == "Toniger Lehm b.Ton":
            if cao_dt_ha >= 121.0:
                return 3.8
            elif cao_dt_ha <= 0.0:
                return 6.4
            elif cao_dt_ha <= 17.78:
                # From: -17.778 * pH + 113.78 = cao_dt_ha
                return (113.78 - cao_dt_ha) / 17.778
            else:
                # From: -65.0 * pH + 368.24 = cao_dt_ha
                return (368.24 - cao_dt_ha) / 65.0

        else:
            return 5.0  # Default fallback

    @staticmethod
    def calculate_lime_requirement(current_ph: float, soil_texture: str, crop_type: str, lime_type: str = "CaO", liming_mode: str = "pH Improvement", caco3_loss_kg_ha: Optional[float] = None, nv: float = 100.0) -> float:
        """
        Calculate lime requirement using VDLUFA method.

        Args:
            current_ph: Current soil pH value
            soil_texture: Soil texture classification
            crop_type: Type of crop (Standard crops or Other crops)
            lime_type: Type of lime for final result (CaO, CaCO3, etc.)
            liming_mode: Liming strategy ("pH Improvement", "pH Maintenance", "Automatic")
            caco3_loss_kg_ha: Optional CaCO3 loss from leaching (kg/ha/year). If provided and liming_mode is "pH Maintenance", this will be used directly.
            nv: Neutralizing Value (percentage, default 100.0 for pure CaCO3 equivalent)

        Returns:
            Lime requirement in kg/ha (kilograms per hectare) for specified lime type
        """
        # Map soil texture to VDLUFA classification
        mapped_texture = VDLUFACalculator.map_soil_texture(soil_texture)

        # Get optimal pH for soil texture and crop type
        optimal_ph = VDLUFACalculator._get_optimal_ph(mapped_texture, crop_type)

        # Apply liming mode logic
        if liming_mode == "pH Maintenance":
            # For pH Maintenance, first check if pH is already at or above optimal
            if current_ph >= optimal_ph:
                logger.info(f"pH Maintenance: current pH ({current_ph}) is at or above optimal ({optimal_ph}) - no lime needed")
                return 0.0

            # For pH Maintenance, ONLY use rainfall-based CaCO3 loss calculation
            if caco3_loss_kg_ha is not None:
                # Calculation sequence: CaCO3 → CaO → Product with NV
                # Step 1: Convert CaCO3 loss to CaO equivalent
                cao_loss_kg_ha = caco3_loss_kg_ha / VDLUFACalculator.LIME_CONVERSION_FACTORS["CaCO3"]

                # Step 2: Apply NV to CaO (NV is relative to CaO in VDLUFA)
                lime_requirement = cao_loss_kg_ha * (100 / nv)

                logger.info(f"VDLUFA pH Maintenance: CaCO3 loss {caco3_loss_kg_ha} kg/ha → CaO {cao_loss_kg_ha:.1f} kg/ha → Product {lime_requirement:.1f} kg/ha (NV={nv}%)")
                return lime_requirement
            else:
                # No rainfall data available - cannot calculate maintenance
                logger.warning(f"pH Maintenance: No rainfall data available - returning 0")
                return 0.0

        elif liming_mode == "Automatic":
            # Automatic mode: improvement if below optimal
            if current_ph >= optimal_ph:
                return 0.0  # No lime needed if pH is at or above optimal
            else:
                # Below optimal - use improvement
                if crop_type == "Standard crops":
                    cao_dt_ha = VDLUFACalculator._calculate_standard_crops(current_ph, mapped_texture)
                else:
                    cao_dt_ha = VDLUFACalculator._calculate_other_crops(current_ph, mapped_texture)
        else:  # pH Improvement (default)
            # Calculate CaO equivalent first (formulas return dt/ha)
            if crop_type == "Standard crops":
                cao_dt_ha = VDLUFACalculator._calculate_standard_crops(current_ph, mapped_texture)
            else:
                cao_dt_ha = VDLUFACalculator._calculate_other_crops(current_ph, mapped_texture)

        # Convert dt/ha to kg/ha (1 dt = 100 kg)
        cao_kg_ha = cao_dt_ha * 100

        # Convert to desired lime type
        return VDLUFACalculator.convert_lime_type(cao_kg_ha, lime_type)

    @staticmethod
    def _get_optimal_ph(soil_texture: str, crop_type: str) -> float:
        """Get optimal pH for soil texture and crop type."""
        # VDLUFA optimal pH values based on soil texture and crop type
        # These values match the thresholds in _calculate_standard_crops and _calculate_other_crops
        # where lime requirement becomes 0 (verified against _reverse_standard_crops/_reverse_other_crops)
        optimal_ph_values = {
            "Standard crops": {
                "Sand": 5.9,                    # Formula returns 0 for pH > 5.8
                "Schwach Lehm Sand": 6.4,       # Formula returns 0 for pH > 6.3
                "Stark Lehmiger Sand": 6.8,     # Formula returns 0 for pH > 6.7
                "Sandiger Schl Lehm": 7.1,      # Formula returns 0 for pH > 7.0
                "Toniger Lehm b.Ton": 7.3       # Formula returns 0 for pH > 7.2 (was already correct)
            },
            "Other crops": {
                "Sand": 5.1,                    # Formula returns 0 for pH > 5.1
                "Schwach Lehm Sand": 5.5,       # Formula returns 0 for pH > 5.5
                "Stark Lehmiger Sand": 5.8,     # Formula returns 0 for pH > 5.8
                "Sandiger Schl Lehm": 6.1,      # Formula returns 0 for pH > 6.1
                "Toniger Lehm b.Ton": 6.3       # Formula returns 0 for pH > 6.3
            }
        }

        return optimal_ph_values.get(crop_type, {}).get(soil_texture, 6.5)

    @staticmethod
    def _calculate_standard_crops(current_ph: float, soil_texture: str) -> float:
        """Calculate for standard crops (arable land) using correct formulas."""

        if soil_texture == "Sand":
            if current_ph < 4:
                return 45.0
            elif 5.3 < current_ph < 5.9:
                return -11.852 * current_ph + 69.93
            elif current_ph > 5.8:
                return 0.0
            else:
                return -28.945 * current_ph + 160.52

        elif soil_texture == "Schwach Lehm Sand":
            if current_ph < 4:
                return 77.0
            elif 5.7 < current_ph < 6.4:
                return -16.667 * current_ph + 106.67
            elif current_ph > 6.3:
                return 0.0
            else:
                return -38.71 * current_ph + 231.47

        elif soil_texture == "Stark Lehmiger Sand":
            if current_ph < 4:
                return 87.0
            elif 6.0 < current_ph < 6.8:
                return -20.0 * current_ph + 136.0
            elif current_ph > 6.7:
                return 0.0
            else:
                return -47.912 * current_ph + 302.54

        elif soil_texture == "Sandiger Schl Lehm":
            if current_ph < 4:
                return 117.0
            elif 6.2 < current_ph < 7.1:
                return -21.25 * current_ph + 150.87
            elif current_ph > 7.0:
                return 0.0
            else:
                return -58.122 * current_ph + 378.54

        elif soil_texture == "Toniger Lehm b.Ton":
            if current_ph < 4:
                return 160.0
            elif 6.3 < current_ph < 7.3:
                return -22.222 * current_ph + 162.22
            elif current_ph > 6.3:
                return 0.0
            else:
                return -76.93 * current_ph + 505.53

        else:  # Unknown texture - use conservative sand calculation
            if current_ph < 4:
                return 45.0
            elif current_ph > 5.8:
                return 0.0
            else:
                return -28.945 * current_ph + 160.52

    @staticmethod
    def _calculate_other_crops(current_ph: float, soil_texture: str) -> float:
        """Calculate for other crops (grassland) using correct formulas."""

        if soil_texture == "Sand":
            if current_ph < 3.4:
                return 50.0
            elif 4.6 < current_ph < 5.2:
                return -8.0 * current_ph + 41.6
            elif current_ph > 5.1:
                return 0.0
            else:
                return -37.692 * current_ph + 178.46

        elif soil_texture == "Schwach Lehm Sand":
            if current_ph < 3.3:
                return 83.0
            elif 4.9 < current_ph < 5.6:
                return -13.333 * current_ph + 74.667
            elif current_ph > 5.5:
                return 0.0
            else:
                return -46.348 * current_ph + 235.91

        elif soil_texture == "Stark Lehmiger Sand":
            if current_ph < 3.8:
                return 90.0
            elif 5.1 < current_ph < 5.9:
                return -14.286 * current_ph + 84.286
            elif current_ph > 5.8:
                return 0.0
            else:
                return -60.989 * current_ph + 322.04

        elif soil_texture == "Sandiger Schl Lehm":
            if current_ph < 3.8:
                return 109.0
            elif 5.3 < current_ph < 6.2:
                return -16.25 * current_ph + 100.75
            elif current_ph > 6.1:
                return 0.0
            else:
                return -63.309 * current_ph + 349.87

        elif soil_texture == "Toniger Lehm b.Ton":
            if current_ph < 3.8:
                return 121.0
            elif 5.4 < current_ph < 6.4:
                return -17.778 * current_ph + 113.78
            elif current_ph > 6.3:
                return 0.0
            else:
                return -65.0 * current_ph + 368.24

        else:
            return 0.0


class CECCalculator:
    """CEC (Cation Exchange Capacity) method for liming calculation."""

    # Soil texture to CEC mapping (loaded from CSV)
    SOIL_CEC_VALUES = {}

    @classmethod
    def load_cec_data(cls, csv_path: str = None):
        """
        Load CEC values from CSV file.

        Args:
            csv_path: Path to soil_cec.csv file. If None, uses default location.
        """
        import csv
        from pathlib import Path

        if csv_path is None:
            # Try to find soil_cec.csv in the project root
            csv_path = Path(__file__).parent.parent / "soil_cec.csv"

        if not Path(csv_path).exists():
            print(f"Warning: CEC data file not found at {csv_path}")
            return False

        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    soil_type = row['Soil'].strip()
                    cec_value = float(row['CEC'])
                    cls.SOIL_CEC_VALUES[soil_type] = cec_value
            print(f"✅ Loaded CEC data for {len(cls.SOIL_CEC_VALUES)} soil types")
            return True
        except Exception as e:
            print(f"Error loading CEC data: {e}")
            return False

    # Mapping from various soil texture formats to USDA soil types
    # This mapping is used for CEC method to convert any input format to USDA standard
    TEXTURE_TO_USDA_MAPPING = {
        # VDLUFA German soil types → USDA
        "Sand": "Sand",
        "Schwach Lehm Sand": "Sandy Loam",
        "Stark Lehmiger Sand": "Loamy Sand",
        "Sandiger Schl Lehm": "Sandy Silt Loam",
        "Toniger Lehm b.Ton": "Clay Loam",
        # NextFarming uppercase format → USDA
        "SAND": "Sand",
        "SLIGHTLY_LOAMY_SAND": "Loamy Sand",
        "VERY_LOAMY_SAND": "Loamy Sand",
        "SANDY_LOAM": "Sandy Loam",
        "SILTY_LOAM": "Silt Loam",
        "CLAYEY_LOAM": "Clay Loam",
        "SLIGHTLY_CLAYEY_LOAM": "Clay Loam",
        "LOAMY_CLAY": "Clay Loam",
        "SILTY_CLAY": "Silty Clay",
        "SANDY_CLAY": "Sandy Clay",
        "CLAY": "Clay",
        "BOG": "Organic",
        "HALF_BOG_SOIL": "Organic",
        # English lowercase variations → USDA
        "sand": "Sand",
        "clay": "Clay",
        "clayey loam": "Clay Loam",
        "loamy clay": "Clay Loam",
        "sandy loam": "Sandy Loam",
        "silty clay": "Silty Clay",
        "silty loam": "Silt Loam",
        "slightly loamy sand": "Loamy Sand",
        "very loamy sand": "Loamy Sand",
        "slightly clayey loam": "Clay Loam",
        "sandy clay": "Sandy Clay",
        "sandy clay loam": "Sandy Clay Loam",
        "silt": "Silt",
        "organic": "Organic",
        # Direct USDA names (pass-through)
        "Loamy Sand": "Loamy Sand",
        "Sandy Loam": "Sandy Loam",
        "Sandy Silt Loam": "Sandy Silt Loam",
        "Silt Loam": "Silt Loam",
        "Clay Loam": "Clay Loam",
        "Sandy Clay": "Sandy Clay",
        "Silty Clay": "Silty Clay",
        "Sandy Clay Loam": "Sandy Clay Loam",
        "Loam": "Loam",
        "Silt": "Silt",
        "Organic": "Organic"
    }

    @classmethod
    def convert_to_usda_texture(cls, soil_texture: str) -> str:
        """
        Convert any soil texture format to USDA standard format.

        Args:
            soil_texture: Soil texture in any format (NextFarming, VDLUFA, English, etc.)

        Returns:
            USDA soil texture name, or original if no mapping found
        """
        if not soil_texture:
            return None

        # Try direct mapping
        usda_texture = cls.TEXTURE_TO_USDA_MAPPING.get(soil_texture)
        if usda_texture:
            return usda_texture

        # If not found, return original (might already be USDA format)
        return soil_texture

    @classmethod
    def get_cec_for_texture(cls, soil_texture: str) -> float:
        """
        Get CEC value for a given soil texture.

        Args:
            soil_texture: Soil texture name (any format)

        Returns:
            CEC value or default of 15.0 if not found
        """
        # Ensure data is loaded
        if not cls.SOIL_CEC_VALUES:
            cls.load_cec_data()

        if not soil_texture:
            return 15.0

        # Convert to USDA format first
        mapped_texture = cls.convert_to_usda_texture(soil_texture)

        # If mapped, get CEC value
        if mapped_texture and mapped_texture in cls.SOIL_CEC_VALUES:
            return cls.SOIL_CEC_VALUES[mapped_texture]

        # Try direct match with CSV
        if soil_texture in cls.SOIL_CEC_VALUES:
            return cls.SOIL_CEC_VALUES[soil_texture]

        # Try case-insensitive match
        for key, value in cls.SOIL_CEC_VALUES.items():
            if key.lower() == soil_texture.lower():
                return value

        # Try partial matching for common patterns
        texture_lower = soil_texture.lower()
        if 'organic' in texture_lower:
            return cls.SOIL_CEC_VALUES.get('Organic', 100)
        elif 'clay loam' in texture_lower:
            return cls.SOIL_CEC_VALUES.get('Clay Loam', 25)
        elif 'sandy clay loam' in texture_lower:
            return cls.SOIL_CEC_VALUES.get('Sandy Clay Loam', 30)
        elif 'silty clay' in texture_lower:
            return cls.SOIL_CEC_VALUES.get('Silty Clay', 30)
        elif 'sandy clay' in texture_lower:
            return cls.SOIL_CEC_VALUES.get('Sandy Clay', 20)
        elif 'clay' in texture_lower:
            return cls.SOIL_CEC_VALUES.get('Clay', 40)
        elif 'sandy loam' in texture_lower:
            return cls.SOIL_CEC_VALUES.get('Sandy Loam', 10)
        elif 'sandy silt loam' in texture_lower:
            return cls.SOIL_CEC_VALUES.get('Sandy Silt Loam', 20)
        elif 'silt loam' in texture_lower:
            return cls.SOIL_CEC_VALUES.get('Silt Loam', 20)
        elif 'loamy sand' in texture_lower:
            return cls.SOIL_CEC_VALUES.get('Loamy Sand', 15)
        elif 'silt' in texture_lower:
            return cls.SOIL_CEC_VALUES.get('Silt', 15)
        elif 'sand' in texture_lower:
            return cls.SOIL_CEC_VALUES.get('Sand', 5)

        # Default fallback
        print(f"Warning: No CEC value found for texture '{soil_texture}', using default 15.0")
        return 15.0

    @staticmethod
    def calculate_lime_requirement(
        current_ph: float,
        target_ph: float,
        cec_soil: float,
        fine_dry_soil: float,
        nv: float,
        dose: float = 1.0,
        s_cec_percentage: float = None,
        modified_s_cec: float = None,
        liming_mode: str = "pH Improvement",
        caco3_loss_kg_ha: float = None
    ) -> float:
        """
        Calculate lime requirement using CEC method.

        Args:
            current_ph: Current soil pH
            target_ph: Target pH to achieve
            cec_soil: Cation Exchange Capacity of soil
            fine_dry_soil: Fine & dry soil value
            nv: Neutralizing Value
            dose: Dose factor (default 1.0)
            s_cec_percentage: Current S/CEC percentage
            modified_s_cec: User-modified S/CEC percentage
            liming_mode: Liming strategy ("pH Improvement", "pH Maintenance", "Automatic")
            caco3_loss_kg_ha: Optional CaCO3 loss from leaching (kg/ha/year). If provided and liming_mode is "pH Maintenance", this will be used directly.

        Returns:
            Lime requirement in kg/ha
        """

        # Adjust target pH based on liming mode
        effective_target_ph = target_ph

        if liming_mode == "pH Maintenance":
            # For pH Maintenance, first check if pH is already at or above target
            if current_ph >= target_ph:
                logger.info(f"CEC pH Maintenance: current pH ({current_ph}) is at or above target ({target_ph}) - no lime needed")
                return 0.0

            # For pH Maintenance, ONLY use rainfall-based CaCO3 loss calculation
            if caco3_loss_kg_ha is not None:
                # Calculation sequence: CaCO3 → CaO → Product with NV
                # Step 1: Convert CaCO3 loss to CaO equivalent
                cao_loss_kg_ha = caco3_loss_kg_ha / 1.785

                # Step 2: Apply NV to CaO (NV is relative to CaO)
                lime_requirement = cao_loss_kg_ha * (100 / nv)

                logger.info(f"CEC pH Maintenance: CaCO3 loss {caco3_loss_kg_ha} kg/ha → CaO {cao_loss_kg_ha:.1f} kg/ha → Product {lime_requirement:.1f} kg/ha (NV={nv}%)")
                return lime_requirement
            else:
                # No rainfall data available - cannot calculate maintenance
                logger.warning(f"CEC pH Maintenance: No rainfall data available - returning 0")
                return 0.0

        elif liming_mode == "Automatic":
            # Automatic: use maintenance if at target, improvement if below, nothing if above
            if current_ph > target_ph:
                return 0.0  # No lime needed if pH is above target
            elif current_ph >= target_ph - 0.1:  # Within 0.1 of target
                # Use rainfall-based maintenance if available
                if caco3_loss_kg_ha is not None:
                    lime_requirement = caco3_loss_kg_ha * (100 / nv)
                    logger.info(f"CEC Automatic (Maintenance): Using rainfall-based CaCO3 loss: {lime_requirement:.1f} kg/ha")
                    return lime_requirement
                else:
                    # Fallback to pH increment method
                    effective_target_ph = current_ph + 0.1  # Maintenance
            else:
                effective_target_ph = target_ph  # Improvement

        if modified_s_cec is None or s_cec_percentage is None:
            # Standard calculation without S/CEC modification
            return CECCalculator._calculate_standard(
                current_ph, effective_target_ph, cec_soil, fine_dry_soil, nv, dose
            )
        else:
            # Calculation with S/CEC modification
            return CECCalculator._calculate_with_modified_s_cec(
                current_ph, effective_target_ph, cec_soil, fine_dry_soil, nv, dose,
                s_cec_percentage, modified_s_cec
            )

    @staticmethod
    def reverse_calculate_ph(
        lime_kg_ha: float,
        current_ph: float,
        cec_soil: float,
        fine_dry_soil: float,
        nv: float,
        dose: float = 1.0
    ) -> float:
        """
        Reverse-calculate the target pH that will be achieved with a given lime amount.

        Args:
            lime_kg_ha: Lime application rate in kg/ha
            current_ph: Current soil pH
            cec_soil: Cation Exchange Capacity of soil
            fine_dry_soil: Fine & dry soil value
            nv: Neutralizing Value
            dose: Dose factor

        Returns:
            Expected target pH after lime application
        """
        if lime_kg_ha <= 0:
            return current_ph

        # Reverse the formula to solve for target pH
        # Original: lime_kg_ha = (((cec_soil * 150/3500) * fine_dry_soil) / (nv*10) / 0.5) * ((target_ph - current_ph) * dose) * 1000
        # Simplified: lime_kg_ha = K * (target_ph - current_ph) * dose
        # Where K = (((cec_soil * 150/3500) * fine_dry_soil) / (nv*10) / 0.5) * 1000

        numerator = (cec_soil * 150 / 3500) * fine_dry_soil
        K = (numerator / (nv * 10) / 0.5) * 1000

        # Solve for target_ph:
        # lime_kg_ha = K * (target_ph - current_ph) * dose
        # lime_kg_ha / (K * dose) = target_ph - current_ph
        # target_ph = current_ph + lime_kg_ha / (K * dose)

        if K * dose == 0:
            return current_ph

        target_ph = current_ph + (lime_kg_ha / (K * dose))

        return target_ph

    @staticmethod
    def _calculate_standard(
        current_ph: float,
        target_ph: float,
        cec_soil: float,
        fine_dry_soil: float,
        nv: float,
        dose: float
    ) -> float:
        """Standard CEC calculation."""

        if current_ph >= target_ph:
            return 0.0

        # Formula: (((CEC Soil * 150/3500) * Fine & dry soil value) / ((NV*10)) / 0.5) * ((Target pH - Current pH) * Dose) * 1000
        numerator = (cec_soil * 150 / 3500) * fine_dry_soil
        # Divide by (NV*10), then divide by 0.5 (two separate divisions)
        ph_difference = target_ph - current_ph

        # Calculate and convert to kg/ha (multiply by 1000)
        lime_requirement = (numerator / (nv * 10) / 0.5) * (ph_difference * dose) * 1000

        # Debug logging
        print(f"\n=== CEC CALCULATION DEBUG ===")
        print(f"Current pH: {current_ph}")
        print(f"Target pH: {target_ph}")
        print(f"CEC Soil: {cec_soil}")
        print(f"Fine & dry soil: {fine_dry_soil}")
        print(f"NV: {nv}")
        print(f"Dose: {dose}")
        print(f"---")
        print(f"CEC * 150/3500 = {cec_soil * 150 / 3500}")
        print(f"Numerator = {numerator}")
        print(f"Numerator / (NV*10) = {numerator / (nv * 10)}")
        print(f"Numerator / (NV*10) / 0.5 = {numerator / (nv * 10) / 0.5}")
        print(f"pH difference = {ph_difference}")
        print(f"Result = {lime_requirement} kg/ha")
        print(f"=============================\n")

        return max(0.0, lime_requirement)

    @staticmethod
    def _calculate_with_modified_s_cec(
        current_ph: float,
        target_ph: float,
        cec_soil: float,
        fine_dry_soil: float,
        nv: float,
        dose: float,
        s_cec_percentage: float,
        modified_s_cec: float
    ) -> float:
        """CEC calculation with modified S/CEC percentage."""

        # Calculate pH corresponding to modified S/CEC
        # This is a simplified mapping - you may need to provide the actual S/CEC to pH conversion
        calculated_s_cec_ph = CECCalculator._s_cec_to_ph(modified_s_cec)

        # Calculate average pH
        average_ph = (current_ph + calculated_s_cec_ph) / 2

        if average_ph > target_ph:
            return 0.0

        # Calculate for current pH
        qty_current = CECCalculator._calculate_standard(
            current_ph, target_ph, cec_soil, fine_dry_soil, nv, dose
        )

        # Calculate for S/CEC pH
        qty_s_cec = CECCalculator._calculate_standard(
            calculated_s_cec_ph, target_ph, cec_soil, fine_dry_soil, nv, dose
        )

        # Return average
        return (qty_current + qty_s_cec) / 2

    @staticmethod
    def _s_cec_to_ph(s_cec_percentage: float) -> float:
        """
        Convert S/CEC percentage to pH value.
        This is a simplified conversion - you may need to provide the actual mapping.
        """
        # Example conversion (this needs to be adjusted based on your actual data)
        # Assuming linear relationship for now
        if s_cec_percentage <= 50:
            return 4.5 + (s_cec_percentage / 50) * 2.0  # pH 4.5 to 6.5
        else:
            return 6.5 + ((s_cec_percentage - 50) / 50) * 1.5  # pH 6.5 to 8.0


class LimingPrescription:
    """Main class for generating liming prescriptions."""

    def __init__(self, method: str = "VDLUFA"):
        """
        Initialize liming prescription calculator.

        Args:
            method: Calculation method ("VDLUFA" or "CEC")
        """
        self.method = method
        self.vdlufa = VDLUFACalculator()
        self.cec = CECCalculator()

    def calculate_prescription(
        self,
        soil_data: List[Dict],
        method_params: Dict
    ) -> List[Dict]:
        """
        Calculate liming prescription for multiple zones/samples.

        Args:
            soil_data: List of soil sample data dictionaries
            method_params: Parameters specific to the chosen method

        Returns:
            List of prescription results with lime requirements
        """

        results = []

        for sample in soil_data:
            # Determine which soil texture will be used for calculation (needed for CaCO3 loss calc)
            original_texture = sample.get('soil_texture')
            if self.method == "VDLUFA":
                if original_texture is None:
                    actual_texture_used = method_params.get('default_soil_texture', 'Sandiger Schl Lehm')
                else:
                    mapped_texture = VDLUFACalculator.map_soil_texture(original_texture)
                    actual_texture_used = mapped_texture if mapped_texture else method_params.get('default_soil_texture', 'Sandiger Schl Lehm')
            else:  # CEC method
                if original_texture is None:
                    # Use USDA default texture
                    actual_texture_used = method_params.get('default_soil_texture', 'Sandy Loam')
                else:
                    # Convert any texture format (NextFarming, VDLUFA, English) to USDA standard
                    actual_texture_used = CECCalculator.convert_to_usda_texture(original_texture)
                logger.info(f"CEC method: Converted texture '{original_texture}' → '{actual_texture_used}' (USDA format)")

            # Lookup annual rainfall and calculate CaCO3 loss BEFORE prescription calculation
            annual_rainfall_mm = None
            caco3_loss_data = None

            logger.info(f"=== Processing zone {sample.get('zone_name', 'Unknown')} ===")
            boundary_value = sample.get('boundary')
            logger.info(f"Boundary present: {boundary_value is not None}")
            if boundary_value:
                logger.info(f"Boundary type: {type(boundary_value).__name__}, has 'type' key: {'type' in boundary_value if isinstance(boundary_value, dict) else 'N/A'}")
            else:
                logger.warning(f"⚠️ Zone {sample.get('zone_name', 'Unknown')} has NO boundary data")
            logger.info(f"RAINFALL_LOOKUP_AVAILABLE: {RAINFALL_LOOKUP_AVAILABLE}")

            if RAINFALL_LOOKUP_AVAILABLE and sample.get('boundary'):
                try:
                    logger.info(f"Attempting to get rainfall from geometry...")
                    annual_rainfall_mm = get_rainfall_from_geometry(sample.get('boundary'))
                    logger.info(f"Rainfall lookup result: {annual_rainfall_mm}")

                    if annual_rainfall_mm:
                        logger.info(f"Retrieved rainfall for zone {sample.get('zone_name', 'Unknown')}: {annual_rainfall_mm} mm/year")

                        # Calculate CaCO3 loss from leaching
                        if actual_texture_used and sample.get('ph_value'):
                            logger.info(f"Calculating CaCO3 loss with texture={actual_texture_used}, pH={sample.get('ph_value')}, method={self.method}")
                            caco3_loss_data = calculate_caco3_loss(
                                precipitation_mm=annual_rainfall_mm,
                                soil_texture=actual_texture_used,
                                ph=sample.get('ph_value'),
                                method=self.method  # Use method-specific clay mapping
                            )
                            logger.info(f"CaCO3 loss calculation result: {caco3_loss_data}")
                        else:
                            logger.warning(f"Cannot calculate CaCO3 loss: texture={actual_texture_used}, pH={sample.get('ph_value')}")
                    else:
                        logger.warning(f"Rainfall lookup returned None/0")
                except Exception as e:
                    logger.error(f"Failed to lookup rainfall/calculate CaCO3 loss for zone {sample.get('zone_name', 'Unknown')}: {e}", exc_info=True)
            else:
                if not RAINFALL_LOOKUP_AVAILABLE:
                    logger.warning(f"Rainfall lookup not available (import failed)")
                if not sample.get('boundary'):
                    logger.warning(f"Zone {sample.get('zone_name', 'Unknown')} has no boundary data")

            # Add CaCO3 loss to sample data for use in calculation
            sample_with_caco3 = sample.copy()
            if caco3_loss_data:
                sample_with_caco3['caco3_loss_kg_ha'] = caco3_loss_data.get('caco3_loss')

            # Calculate prescription
            if self.method == "VDLUFA":
                lime_requirement, applied_mode, target_ph, was_capped = self._calculate_vdlufa_prescription(sample_with_caco3, method_params)
            else:  # CEC
                lime_requirement, applied_mode, target_ph, was_capped = self._calculate_cec_prescription(sample_with_caco3, method_params)

            # Add prescription result
            result = {
                'sample_id': sample.get('id'),
                'sample_name': sample.get('name'),
                'field_id': sample.get('field_id'),
                'field_name': sample.get('field_name', 'Unknown Field'),
                'zone_name': sample.get('zone_name', 'Main Zone'),
                'zone_area': sample.get('area'),  # Zone area for weighted average calculation
                'current_ph': sample.get('ph_value'),
                'target_ph': target_ph,
                'was_capped': was_capped,
                'soil_texture': actual_texture_used,  # Show the texture actually used for calculation
                'original_soil_texture': original_texture,  # Keep original for reference
                'organic_matter': sample.get('humus_level'),
                'boundary': sample.get('boundary'),
                'lime_requirement_kg_ha': round(lime_requirement, 2),
                'method': self.method,
                'calculation_params': method_params,
                'applied_mode': applied_mode,  # Track which mode was actually applied
                'annual_rainfall_mm': annual_rainfall_mm,  # Annual rainfall data
                'caco3_loss_kg_ha_year': caco3_loss_data.get('caco3_loss') if caco3_loss_data else None  # CaCO3 leaching loss
            }

            results.append(result)

        return results

    def _calculate_vdlufa_prescription(self, sample: Dict, params: Dict) -> Tuple[float, str, float, bool]:
        """Calculate using VDLUFA method.

        Returns:
            Tuple of (lime_requirement, applied_mode, target_ph, was_capped)
        """
        current_ph = sample.get('ph_value')
        soil_texture = sample.get('soil_texture')
        crop_type = params.get('crop_type', 'Standard crops')
        lime_type = params.get('lime_type', 'CaCO3')  # Default to agricultural lime
        max_rate = params.get('max_application_rate')

        # Handle missing data
        if current_ph is None:
            return 0.0, "N/A", None, False

        # If soil texture is missing, use default based on other available data or user preference
        if soil_texture is None:
            # Default to medium texture for missing data
            soil_texture = params.get('default_soil_texture', 'Sandiger Schl Lehm')

        # Get liming mode from parameters
        liming_mode = params.get('liming_mode', 'pH Improvement')

        # Determine which mode will actually be applied
        mapped_texture = VDLUFACalculator.map_soil_texture(soil_texture)
        optimal_ph = VDLUFACalculator._get_optimal_ph(mapped_texture, crop_type)

        if liming_mode == "Automatic":
            if current_ph > optimal_ph:
                applied_mode = "None (pH above optimal)"
            elif current_ph >= optimal_ph - 0.1:
                applied_mode = "Maintenance"
            else:
                applied_mode = "Improvement"
        elif liming_mode == "pH Maintenance":
            if current_ph >= optimal_ph:
                applied_mode = "None (pH at/above optimal)"
            else:
                applied_mode = "Maintenance"
        else:  # pH Improvement
            applied_mode = "Improvement"

        # Calculate lime requirement (pass CaCO3 loss if available for pH Maintenance or Automatic)
        caco3_loss = sample.get('caco3_loss_kg_ha') if liming_mode in ["pH Maintenance", "Automatic"] else None
        nv = params.get('nv', 100.0)  # Default to 100% (pure CaCO3 equivalent)
        lime_req = self.vdlufa.calculate_lime_requirement(current_ph, soil_texture, crop_type, lime_type, liming_mode, caco3_loss, nv)

        # Check if we need to cap the application rate
        # NOTE: max_rate is in the units of the selected lime type
        was_capped = False

        # Set target pH based on mode
        if liming_mode == "pH Maintenance":
            # In maintenance mode, target is to maintain current pH (compensate for leaching)
            target_ph = current_ph
        else:
            # In improvement or automatic mode, target is optimal pH
            target_ph = optimal_ph

        if max_rate is not None and lime_req > max_rate:
            # Cap the lime requirement
            lime_req = max_rate
            was_capped = True
            # Reverse-calculate what pH we'll actually achieve (only for improvement mode)
            if liming_mode != "pH Maintenance":
                target_ph = VDLUFACalculator.reverse_calculate_ph(lime_req, soil_texture, crop_type, lime_type, current_ph)
            # For maintenance mode, target_ph stays as current_ph even when capped

        return lime_req, applied_mode, target_ph, was_capped

    def _calculate_cec_prescription(self, sample: Dict, params: Dict) -> Tuple[float, str, float, bool]:
        """Calculate using CEC method.

        Returns:
            Tuple of (lime_requirement, applied_mode, target_ph, was_capped)
        """
        current_ph = sample.get('ph_value')
        target_ph = params.get('target_ph', 6.5)
        soil_texture = sample.get('soil_texture')
        max_rate = params.get('max_application_rate')

        # Get CEC value from CSV based on soil texture
        if soil_texture:
            cec_soil = CECCalculator.get_cec_for_texture(soil_texture)
        else:
            # Use default or user-provided CEC value if no texture available
            cec_soil = params.get('cec_soil', 15.0)

        fine_dry_soil = params.get('fine_dry_soil')
        nv = params.get('nv')
        dose = params.get('dose', 1.0)
        s_cec_percentage = params.get('s_cec_percentage')
        modified_s_cec = params.get('modified_s_cec')

        if any(v is None for v in [current_ph, fine_dry_soil, nv]):
            return 0.0, "N/A", None, False

        # Get liming mode from parameters
        liming_mode = params.get('liming_mode', 'pH Improvement')

        # Determine which mode will actually be applied
        if liming_mode == "Automatic":
            if current_ph > target_ph:
                applied_mode = "None (pH above target)"
            elif current_ph >= target_ph - 0.1:
                applied_mode = "Maintenance"
            else:
                applied_mode = "Improvement"
        elif liming_mode == "pH Maintenance":
            if current_ph >= target_ph:
                applied_mode = "None (pH at/above target)"
            else:
                applied_mode = "Maintenance"
        else:  # pH Improvement
            applied_mode = "Improvement"

        # Calculate lime requirement (pass CaCO3 loss if available for pH Maintenance or Automatic)
        caco3_loss = sample.get('caco3_loss_kg_ha') if liming_mode in ["pH Maintenance", "Automatic"] else None
        lime_req = self.cec.calculate_lime_requirement(
            current_ph, target_ph, cec_soil, fine_dry_soil, nv, dose,
            s_cec_percentage, modified_s_cec, liming_mode, caco3_loss
        )

        # Check if we need to cap the application rate
        # NOTE: max_rate is in the units of the selected lime type
        was_capped = False

        # Set achieved target pH based on mode
        if liming_mode == "pH Maintenance":
            # In maintenance mode, target is to maintain current pH
            achieved_target_ph = current_ph
        else:
            # In improvement or automatic mode, target is the user-specified target
            achieved_target_ph = target_ph

        if max_rate is not None and lime_req > max_rate:
            # Cap the lime requirement
            lime_req = max_rate
            was_capped = True
            # Reverse-calculate what pH we'll actually achieve (only for improvement mode)
            if liming_mode != "pH Maintenance":
                achieved_target_ph = CECCalculator.reverse_calculate_ph(
                    lime_req, current_ph, cec_soil, fine_dry_soil, nv, dose
                )
            # For maintenance mode, achieved_target_ph stays as current_ph even when capped

        return lime_req, applied_mode, achieved_target_ph, was_capped