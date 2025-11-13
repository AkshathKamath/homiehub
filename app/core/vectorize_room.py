import numpy as np
from typing import Dict, List

from app.config import LOCATION_COORDS, WEIGHTS, LAT_MAX, LAT_MIN, LON_MAX, LON_MIN, GENDER_MAP, BUDGET_MAX, BUDGET_MIN, LEASE_MIN, LEASE_MAX, FOOD_MAP, ALCOHOL_MAP, SMOKE_MAP

def vectorize_room(room_data: Dict) -> np.ndarray:
    """
    Vectorize room preferences for similarity matching.
    All inputs are pre-validated by Pydantic model.
    """
    # Location handling (already validated and cleaned)
    location = room_data.get('location', 'Boston')
    lat, lon = LOCATION_COORDS.get(location, (42.3601, -71.0589))

    # Safe normalization with bounds checking
    lat_normalized = max(0.0, min(1.0, (lat - LAT_MIN) / (LAT_MAX - LAT_MIN)))
    lon_normalized = max(0.0, min(1.0, (lon - LON_MIN) / (LON_MAX - LON_MIN)))

    # Gender preference (validated, with safe default)
    gender = GENDER_MAP.get(room_data.get('flatmate_gender', 'Mixed'), 0.5)

    # Rent (validated to be within range)
    rent = room_data.get('rent', 1500)
    rent_normalized = max(0.0, min(1.0, (rent - BUDGET_MIN) / (BUDGET_MAX - BUDGET_MIN)))

    # Lease duration (validated to be 1-24 months)
    lease_duration = room_data.get('lease_duration_months', 12)
    lease_normalized = max(0.0, min(1.0, (lease_duration - LEASE_MIN) / (LEASE_MAX - LEASE_MIN)))

    # Room type (validated enum)
    room_type_val = room_data.get('room_type', 'Shared')
    room_type = 0.0 if room_type_val == 'Shared' else (1.0 if room_type_val == 'Private' else 0.5)

    # Bathroom (validated enum)
    bathroom_val = room_data.get('attached_bathroom', 'No')
    bathroom = 0.0 if bathroom_val == 'No' else 1.0

    # Lifestyle preferences (all validated enums with safe defaults)
    food = FOOD_MAP.get(room_data.get('lifestyle_food', 'Everything'), 1.0)
    alcohol = ALCOHOL_MAP.get(room_data.get('lifestyle_alcohol', 'Occasionally'), 0.5)
    smoke = SMOKE_MAP.get(room_data.get('lifestyle_smoke', 'No'), 0.0)

    # Utilities (validated list)
    utilities = min(1.0, len(room_data.get('utilities_included', [])) / 4.0)

    # Build normalized vector
    normalized_vector = np.array([
        lat_normalized, lon_normalized, gender, rent_normalized, lease_normalized,
        room_type, bathroom, food, alcohol, smoke, utilities
    ], dtype=np.float32)

    # Apply weights
    weighted_vector = normalized_vector * WEIGHTS
    
    # Validate output vector
    if np.any(np.isnan(weighted_vector)) or np.any(np.isinf(weighted_vector)):
        raise ValueError("Invalid vector computed - contains NaN or Inf values")
    
    return weighted_vector