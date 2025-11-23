from pydantic import BaseModel
from typing import List, Optional


# Authentication Models
class Token(BaseModel):
    access_token: str
    token_type: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(BaseModel):
    username: str
    email: Optional[str] = None
    disabled: bool = False


# Soil Sample Models
class SoilSample(BaseModel):
    """Soil sample data for liming calculation."""
    id: Optional[str] = None
    name: Optional[str] = None
    field_id: Optional[str] = None
    field_name: Optional[str] = None
    zone_name: Optional[str] = None
    area: Optional[float] = None
    ph_value: float
    soil_texture: Optional[str] = None
    humus_level: Optional[float] = None
    boundary: Optional[dict] = None


# VDLUFA Calculation Models
class VDLUFACalculationRequest(BaseModel):
    """Request model for VDLUFA calculation."""
    soil_data: List[SoilSample]
    crop_type: str = "Standard crops"
    lime_type: str = "CaCO3"
    liming_mode: str = "pH Improvement"
    default_soil_texture: str = "Sandiger Schl Lehm"
    max_application_rate: Optional[float] = None


# CEC Calculation Models
class CECCalculationRequest(BaseModel):
    """Request model for CEC calculation."""
    soil_data: List[SoilSample]
    target_ph: float = 6.5
    fine_dry_soil: float
    nv: float
    dose: float = 1.0
    cec_soil: Optional[float] = 15.0
    liming_mode: str = "pH Improvement"
    max_application_rate: Optional[float] = None
    s_cec_percentage: Optional[float] = None
    modified_s_cec: Optional[float] = None


# Response Models
class LimingResult(BaseModel):
    """Single liming prescription result."""
    sample_id: Optional[str]
    sample_name: Optional[str]
    field_id: Optional[str]
    field_name: str
    zone_name: str
    zone_area: Optional[float]
    current_ph: float
    target_ph: Optional[float]
    was_capped: bool
    soil_texture: Optional[str]
    original_soil_texture: Optional[str]
    lime_requirement_kg_ha: float
    method: str
    applied_mode: str


class CalculationSummary(BaseModel):
    """Summary statistics for liming calculation."""
    total_samples: int
    total_area: float
    average_lime_kg_ha: float
    method: str
    user: str


class CalculationResponse(BaseModel):
    """Complete calculation response with results and summary."""
    results: List[LimingResult]
    summary: CalculationSummary
