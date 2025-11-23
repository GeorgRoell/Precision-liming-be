from fastapi import APIRouter, HTTPException, Depends
from typing import List

from calculators.liming import VDLUFACalculator, CECCalculator, LimingPrescription
from models.schemas import (
    VDLUFACalculationRequest,
    CECCalculationRequest,
    CalculationResponse,
    CalculationSummary,
)
from api.auth import get_current_user

router = APIRouter()


@router.post("/calculate/vdlufa", response_model=CalculationResponse)
async def calculate_vdlufa_prescription(
    request: VDLUFACalculationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate liming prescription using VDLUFA method.

    This endpoint contains your proprietary liming algorithm.
    Only authenticated users can access it.

    **Authentication Required**: Include JWT token in Authorization header.

    **Example Request**:
    ```json
    {
        "soil_data": [
            {
                "ph_value": 5.2,
                "soil_texture": "sandy loam",
                "area": 10.5,
                "field_name": "North Field",
                "zone_name": "Zone 1"
            }
        ],
        "crop_type": "Standard crops",
        "lime_type": "CaCO3",
        "liming_mode": "pH Improvement",
        "default_soil_texture": "Sandiger Schl Lehm",
        "max_application_rate": 5000
    }
    ```

    **Returns**:
    - `results`: List of liming prescriptions for each zone
    - `summary`: Aggregated statistics (total area, average lime, etc.)
    """
    try:
        # Convert Pydantic models to dicts
        soil_data = [sample.model_dump() for sample in request.soil_data]

        method_params = {
            'crop_type': request.crop_type,
            'lime_type': request.lime_type,
            'liming_mode': request.liming_mode,
            'default_soil_texture': request.default_soil_texture,
            'max_application_rate': request.max_application_rate
        }

        # Run calculation (your proprietary code - protected on server!)
        calculator = LimingPrescription(method="VDLUFA")
        results = calculator.calculate_prescription(soil_data, method_params)

        # Calculate summary statistics
        total_area = sum(r.get('zone_area', 0) or 0 for r in results)
        avg_lime = sum(r['lime_requirement_kg_ha'] for r in results) / len(results) if results else 0

        summary = CalculationSummary(
            total_samples=len(results),
            total_area=round(total_area, 2),
            average_lime_kg_ha=round(avg_lime, 2),
            method='VDLUFA',
            user=current_user['username']
        )

        return CalculationResponse(
            results=results,
            summary=summary
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Calculation failed: {str(e)}"
        )


@router.post("/calculate/cec", response_model=CalculationResponse)
async def calculate_cec_prescription(
    request: CECCalculationRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Calculate liming prescription using CEC method.

    This endpoint contains your proprietary CEC-based liming algorithm.
    Only authenticated users can access it.

    **Authentication Required**: Include JWT token in Authorization header.

    **Example Request**:
    ```json
    {
        "soil_data": [
            {
                "ph_value": 5.2,
                "soil_texture": "sandy loam",
                "area": 10.5,
                "field_name": "North Field"
            }
        ],
        "target_ph": 6.5,
        "fine_dry_soil": 1500.0,
        "nv": 53.0,
        "dose": 1.0,
        "liming_mode": "pH Improvement",
        "max_application_rate": 5000
    }
    ```

    **Returns**:
    - `results`: List of liming prescriptions for each zone
    - `summary`: Aggregated statistics
    """
    try:
        soil_data = [sample.model_dump() for sample in request.soil_data]

        method_params = {
            'target_ph': request.target_ph,
            'fine_dry_soil': request.fine_dry_soil,
            'nv': request.nv,
            'dose': request.dose,
            'cec_soil': request.cec_soil,
            'liming_mode': request.liming_mode,
            'max_application_rate': request.max_application_rate,
            's_cec_percentage': request.s_cec_percentage,
            'modified_s_cec': request.modified_s_cec
        }

        calculator = LimingPrescription(method="CEC")
        results = calculator.calculate_prescription(soil_data, method_params)

        total_area = sum(r.get('zone_area', 0) or 0 for r in results)
        avg_lime = sum(r['lime_requirement_kg_ha'] for r in results) / len(results) if results else 0

        summary = CalculationSummary(
            total_samples=len(results),
            total_area=round(total_area, 2),
            average_lime_kg_ha=round(avg_lime, 2),
            method='CEC',
            user=current_user['username']
        )

        return CalculationResponse(
            results=results,
            summary=summary
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Calculation failed: {str(e)}"
        )


@router.get("/methods")
async def list_calculation_methods():
    """
    List available calculation methods and their descriptions.

    **No authentication required** - informational endpoint.

    Returns available liming calculation methods.
    """
    return {
        "methods": [
            {
                "name": "VDLUFA",
                "description": "German VDLUFA standard method based on soil texture and crop type",
                "parameters": [
                    "crop_type",
                    "lime_type",
                    "liming_mode",
                    "soil_texture"
                ]
            },
            {
                "name": "CEC",
                "description": "Cation Exchange Capacity method for precise pH adjustment",
                "parameters": [
                    "target_ph",
                    "fine_dry_soil",
                    "nv",
                    "dose",
                    "cec_soil"
                ]
            }
        ]
    }


@router.get("/lime-types")
async def list_lime_types():
    """
    List available lime types and their conversion factors.

    **No authentication required** - informational endpoint.
    """
    return {
        "lime_types": {
            "CaO": {"name": "Pure Calcium Oxide", "factor": 1.0, "nv": 179},
            "CaCO3": {"name": "Calcium Carbonate", "factor": 1.785, "nv": 100},
            "Ca(OH)2": {"name": "Calcium Hydroxide", "factor": 1.321, "nv": 135},
            "Agrocarb": {"name": "Agrocarb", "factor": 2.381, "nv": 42},
            "Omya_Calciprill": {"name": "Omya Calciprill", "factor": 1.887, "nv": 53}
        }
    }
