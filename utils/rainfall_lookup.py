"""
Rainfall Lookup Utility
- Primary: Local shapefile lookup (fast, reliable)
- Fallback: USDA ArcGIS ImageServer (if shapefile fails)
"""

import requests
from typing import Optional, Tuple
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)

# Shapefile configuration
SHAPEFILE_PATH = Path(__file__).parent.parent / "data" / "rainfall" / "rainfall_Europe.shp"
RAINFALL_ATTRIBUTE = "mean_rain"  # Attribute containing rainfall in mm/year

# USDA Global Annual Rainfall ImageServer (fallback)
RAINFALL_SERVICE_URL = "https://geo.fas.usda.gov/arcgis2/rest/services/G_Climatology/Annual_Rainfall/ImageServer/identify"

# Shapefile cache
_shapefile_data = None
_spatial_index = None


def _load_shapefile():
    """Load shapefile and create spatial index (cached)."""
    global _shapefile_data, _spatial_index

    if _shapefile_data is not None:
        return _shapefile_data, _spatial_index

    try:
        import fiona
        from shapely.geometry import shape, Point
        from rtree import index

        if not SHAPEFILE_PATH.exists():
            logger.warning(f"Shapefile not found: {SHAPEFILE_PATH}")
            return None, None

        logger.info(f"Loading rainfall shapefile: {SHAPEFILE_PATH}")

        # Load all features
        features = []
        idx = index.Index()

        with fiona.open(SHAPEFILE_PATH) as src:
            for i, feature in enumerate(src):
                geom = shape(feature['geometry'])
                rainfall = feature['properties'].get(RAINFALL_ATTRIBUTE)

                if rainfall is not None:
                    features.append({
                        'geometry': geom,
                        'rainfall': float(rainfall),
                        'bounds': geom.bounds
                    })
                    # Add to spatial index
                    idx.insert(i, geom.bounds)

        _shapefile_data = features
        _spatial_index = idx

        logger.info(f"✅ Loaded {len(features)} rainfall polygons from shapefile")
        return _shapefile_data, _spatial_index

    except ImportError as e:
        logger.error(f"Missing dependencies for shapefile lookup: {e}")
        logger.error("Install with: pip install fiona shapely rtree")
        return None, None
    except Exception as e:
        logger.error(f"Failed to load shapefile: {e}", exc_info=True)
        return None, None


@lru_cache(maxsize=1000)
def get_rainfall_from_shapefile(longitude: float, latitude: float) -> Optional[float]:
    """
    Get rainfall from local shapefile (FAST method).

    Args:
        longitude: Longitude in decimal degrees (WGS84)
        latitude: Latitude in decimal degrees (WGS84)

    Returns:
        Annual rainfall in mm/year, or None if not found
    """
    try:
        from shapely.geometry import Point

        features, spatial_idx = _load_shapefile()

        if features is None or spatial_idx is None:
            return None

        point = Point(longitude, latitude)

        # Use spatial index to find candidate polygons
        candidates = list(spatial_idx.intersection((longitude, latitude, longitude, latitude)))

        # Check which polygon actually contains the point
        for idx in candidates:
            if idx < len(features):
                feature = features[idx]
                if feature['geometry'].contains(point):
                    rainfall = feature['rainfall']
                    logger.info(f"✅ Shapefile lookup: ({longitude:.2f}, {latitude:.2f}) = {rainfall} mm/year")
                    return rainfall

        logger.warning(f"Point ({longitude:.2f}, {latitude:.2f}) not found in shapefile")
        return None

    except Exception as e:
        logger.error(f"Shapefile lookup failed: {e}")
        return None


@lru_cache(maxsize=1000)
def get_annual_rainfall(longitude: float, latitude: float) -> Optional[float]:
    """
    Get annual rainfall in mm for a given location.

    Strategy:
    1. Try shapefile lookup first (FAST, ~10ms)
    2. Fall back to USDA API if shapefile fails (SLOW, ~500-2000ms)

    Args:
        longitude: Longitude in decimal degrees (WGS84)
        latitude: Latitude in decimal degrees (WGS84)

    Returns:
        Annual rainfall in mm, or None if lookup fails

    Example:
        >>> rainfall = get_annual_rainfall(12.1, 49.0)  # Regensburg, Germany
        >>> print(f"Annual rainfall: {rainfall} mm")
        Annual rainfall: 658 mm
    """
    # Try shapefile first (fast, local)
    rainfall = get_rainfall_from_shapefile(longitude, latitude)
    if rainfall is not None:
        return rainfall

    # Fall back to USDA API (slow, online)
    logger.info(f"Shapefile lookup failed, trying USDA API for ({longitude:.2f}, {latitude:.2f})")

    try:
        # Construct geometry parameter with spatial reference
        geometry = {
            "x": longitude,
            "y": latitude,
            "spatialReference": {"wkid": 4326}  # WGS84
        }

        params = {
            "geometry": str(geometry).replace("'", '"'),  # Convert to JSON format
            "geometryType": "esriGeometryPoint",
            "returnGeometry": "false",
            "returnCatalogItems": "false",
            "f": "json"
        }

        response = requests.get(RAINFALL_SERVICE_URL, params=params, timeout=5)
        response.raise_for_status()

        data = response.json()

        # Extract pixel value (rainfall in mm)
        pixel_value = data.get("value")

        if pixel_value == "NoData" or pixel_value is None:
            logger.warning(f"No rainfall data available for coordinates: ({longitude}, {latitude})")
            return None

        rainfall_mm = float(pixel_value)
        logger.info(f"📡 USDA API lookup: ({longitude:.2f}, {latitude:.2f}) = {rainfall_mm} mm/year")

        return rainfall_mm

    except requests.RequestException as e:
        logger.error(f"Failed to query rainfall service: {e}")
        return None
    except (KeyError, ValueError, TypeError) as e:
        logger.error(f"Failed to parse rainfall response: {e}")
        return None


def get_rainfall_from_geometry(geometry: dict) -> Optional[float]:
    """
    Extract centroid from GeoJSON geometry and get rainfall.

    Args:
        geometry: GeoJSON geometry object (Point, Polygon, MultiPolygon, etc.)

    Returns:
        Annual rainfall in mm, or None if lookup fails

    Example:
        >>> geometry = {
        ...     "type": "Polygon",
        ...     "coordinates": [[[12.0, 49.0], [12.2, 49.0], [12.2, 49.1], [12.0, 49.1], [12.0, 49.0]]]
        ... }
        >>> rainfall = get_rainfall_from_geometry(geometry)
    """
    try:
        centroid = get_geometry_centroid(geometry)
        if centroid is None:
            return None

        longitude, latitude = centroid
        # Round to 2 decimal places (~1km precision) to ensure all zones in same field get identical rainfall
        # This is appropriate since rainfall data has coarse spatial resolution anyway
        longitude = round(longitude, 2)
        latitude = round(latitude, 2)
        return get_annual_rainfall(longitude, latitude)

    except Exception as e:
        logger.error(f"Failed to get rainfall from geometry: {e}")
        return None


def get_geometry_centroid(geometry: dict) -> Optional[Tuple[float, float]]:
    """
    Calculate centroid of a GeoJSON geometry.

    Args:
        geometry: GeoJSON geometry object

    Returns:
        Tuple of (longitude, latitude), or None if calculation fails
    """
    try:
        geom_type = geometry.get("type")
        coordinates = geometry.get("coordinates")

        if not coordinates:
            return None

        if geom_type == "Point":
            return tuple(coordinates[:2])

        elif geom_type == "Polygon":
            # Use exterior ring (first ring)
            exterior_ring = coordinates[0]
            return calculate_polygon_centroid(exterior_ring)

        elif geom_type == "MultiPolygon":
            # Use first polygon's exterior ring
            first_polygon = coordinates[0]
            exterior_ring = first_polygon[0]
            return calculate_polygon_centroid(exterior_ring)

        else:
            logger.warning(f"Unsupported geometry type: {geom_type}")
            return None

    except Exception as e:
        logger.error(f"Failed to calculate centroid: {e}")
        return None


def calculate_polygon_centroid(ring: list) -> Tuple[float, float]:
    """
    Calculate centroid of a polygon ring using simple average.

    Args:
        ring: List of [lon, lat] coordinate pairs

    Returns:
        Tuple of (longitude, latitude)
    """
    # Simple centroid calculation (average of all points)
    # This is approximate but sufficient for rainfall lookup
    lons = [coord[0] for coord in ring]
    lats = [coord[1] for coord in ring]

    centroid_lon = sum(lons) / len(lons)
    centroid_lat = sum(lats) / len(lats)

    return (centroid_lon, centroid_lat)


# CaCO3 Loss Calculation from Natural Leaching
# ==============================================

# Texture class data - mapping from German VDLUFA names to clay percentages
VDLUFA_TEXTURE_TO_CLAY = {
    'Sand': 5,
    'Schwach Lehm Sand': 12,
    'Stark Lehmiger Sand': 12,
    'Sandiger Schl Lehm': 15,
    'Toniger Lehm b.Ton': 32,
    # Additional mappings for completeness
    'Lehm': 20,
    'Schluff': 10,
    'Ton': 60,
}

# CEC Method - USDA/International soil texture to clay percentages
# These follow standard USDA soil texture triangle classifications
CEC_TEXTURE_TO_CLAY = {
    'Sand': 5,                  # 0-10% clay
    'Loamy Sand': 8,            # 0-15% clay
    'Sandy Loam': 10,           # 0-20% clay
    'Loam': 18,                 # 7-27% clay
    'Silt Loam': 15,            # 0-27% clay
    'Silt': 6,                  # 0-12% clay
    'Sandy Clay Loam': 27,      # 20-35% clay
    'Clay Loam': 33,            # 27-40% clay
    'Sandy Clay': 42,           # 35-55% clay
    'Silty Clay': 47,           # 40-60% clay
    'Clay': 60,                 # 40-100% clay
    'Sandy Silt Loam': 17,      # Custom classification
    'Organic': 20,              # High organic matter soil
    # Case-insensitive variations
    'sand': 5,
    'loamy sand': 8,
    'sandy loam': 10,
    'loam': 18,
    'silt loam': 15,
    'silt': 6,
    'sandy clay loam': 27,
    'clay loam': 33,
    'sandy clay': 42,
    'silty clay': 47,
    'clay': 60,
    'organic': 20,
}


def get_bicarbonate_factor(ph: float) -> float:
    """
    Get bicarbonate factor based on soil pH using Power Law Model.

    This model provides smooth, continuous values instead of stepwise jumps.
    Formula: B = a * pH^b where a=0.0023, b=5.7923 (R²=0.9852)

    Args:
        ph: Soil pH value

    Returns:
        Bicarbonate factor (mg/L)
    """
    # Power Law Model coefficients (fitted from VDLUFA data)
    a = 0.002304  # Coefficient
    b = 5.792337  # Exponent

    # Calculate bicarbonate factor
    bicarb_factor = a * (ph ** b)

    # Constrain to reasonable range (5-500 mg/L)
    # These bounds prevent extreme values outside typical agricultural pH ranges
    return max(5.0, min(500.0, bicarb_factor))


def calculate_drainage_coefficient(clay_percent: float) -> float:
    """
    Calculate drainage coefficient from clay content.

    Args:
        clay_percent: Clay content percentage

    Returns:
        Drainage coefficient (D)
    """
    return 0.6 - (0.005 * clay_percent)


def calculate_caco3_loss(precipitation_mm: float, soil_texture: str, ph: float, method: str = "VDLUFA") -> Optional[dict]:
    """
    Calculate CaCO3 loss per hectare per year from natural leaching.

    Formula: CaCO3 Loss = P × (0.6 - 0.005 × Clay%) × B × 0.82 / 100

    Where:
    - P = Annual precipitation (mm)
    - Clay% = Clay content percentage (from soil texture)
    - B = Bicarbonate factor (from pH)
    - 0.82 = Conversion factor

    Args:
        precipitation_mm: Annual precipitation in mm
        soil_texture: Soil texture name (VDLUFA or CEC classification depending on method)
        ph: Soil pH value
        method: Calculation method ("VDLUFA" or "CEC") - determines which clay mapping to use

    Returns:
        Dictionary containing:
            - caco3_loss: CaCO3 loss in kg/ha/year
            - clay_percent: Clay content percentage
            - drainage_coef: Drainage coefficient
            - bicarbonate_factor: Bicarbonate factor used
        Or None if texture not found
    """
    try:
        # Get clay percentage from texture based on method
        if method == "CEC":
            clay_percent = CEC_TEXTURE_TO_CLAY.get(soil_texture)
        else:  # VDLUFA (default)
            clay_percent = VDLUFA_TEXTURE_TO_CLAY.get(soil_texture)

        if clay_percent is None:
            logger.warning(f"Unknown soil texture for CaCO3 loss calculation ({method} method): {soil_texture}")
            return None

        # Calculate drainage coefficient
        drainage_coef = calculate_drainage_coefficient(clay_percent)

        # Get bicarbonate factor from pH
        bicarbonate_factor = get_bicarbonate_factor(ph)

        # Calculate CaCO3 loss
        # Formula: P × D × B × 0.82 / 100
        caco3_loss = precipitation_mm * drainage_coef * bicarbonate_factor * 0.82 / 100

        logger.info(f"Calculated CaCO3 loss ({method}): {caco3_loss:.1f} kg/ha/year "
                   f"(P={precipitation_mm}mm, texture={soil_texture}, clay={clay_percent}%, pH={ph})")

        return {
            'caco3_loss': round(caco3_loss, 1),
            'clay_percent': clay_percent,
            'drainage_coef': round(drainage_coef, 3),
            'bicarbonate_factor': bicarbonate_factor
        }

    except Exception as e:
        logger.error(f"Failed to calculate CaCO3 loss: {e}")
        return None
