"""Test rainfall lookup functionality."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from utils.rainfall_lookup import get_annual_rainfall, get_rainfall_from_geometry

print("=" * 70)
print("RAINFALL LOOKUP TEST")
print("=" * 70)
print()

# Test 1: Direct coordinate lookup
print("Test 1: Direct Coordinate Lookup")
print("-" * 70)

test_locations = [
    ("Regensburg, Germany", 12.1, 49.0),
    ("Central Germany", 10.0, 51.0),
    ("Berlin, Germany", 13.4, 52.5),
    ("Munich, Germany", 11.6, 48.1),
]

for name, lon, lat in test_locations:
    rainfall = get_annual_rainfall(lon, lat)
    if rainfall:
        print(f"{name:<25} ({lon:6.2f}°E, {lat:5.2f}°N): {rainfall:6.0f} mm/year")
    else:
        print(f"{name:<25} ({lon:6.2f}°E, {lat:5.2f}°N): No data")

print()

# Test 2: Geometry-based lookup
print("Test 2: Geometry-based Lookup (Polygon)")
print("-" * 70)

# Example polygon (small area near Regensburg)
test_geometry = {
    "type": "Polygon",
    "coordinates": [[
        [12.0, 49.0],
        [12.2, 49.0],
        [12.2, 49.1],
        [12.0, 49.1],
        [12.0, 49.0]
    ]]
}

rainfall = get_rainfall_from_geometry(test_geometry)
if rainfall:
    print(f"Polygon near Regensburg:  {rainfall:6.0f} mm/year")
else:
    print("Polygon near Regensburg:  No data")

print()

# Test 3: Point geometry
print("Test 3: Point Geometry Lookup")
print("-" * 70)

point_geometry = {
    "type": "Point",
    "coordinates": [12.1, 49.0]
}

rainfall = get_rainfall_from_geometry(point_geometry)
if rainfall:
    print(f"Point (Regensburg):       {rainfall:6.0f} mm/year")
else:
    print("Point (Regensburg):       No data")

print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)
