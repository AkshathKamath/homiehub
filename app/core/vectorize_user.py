import numpy as np
from typing import Dict, List

from app.config import LOCATION_COORDS, WEIGHTS, LAT_MAX, LAT_MIN, LON_MAX, LON_MIN, GENDER_MAP, BUDGET_MAX, BUDGET_MIN, LEASE_MIN, LEASE_MAX, FOOD_MAP, ALCOHOL_MAP, SMOKE_MAP

def vectorize_user(user_data: Dict) -> np.ndarray:
    """
    Vectorize user preferences for similarity matching.
    All inputs are pre-validated by Pydantic model.
    """
    # Location handling (already validated and cleaned)
    preferred_locations = user_data.get('preferred_locations', ['Boston'])
    lats, lons = [], []
    for loc in preferred_locations:
        if loc in LOCATION_COORDS:
            lat, lon = LOCATION_COORDS[loc]
            lats.append(lat)
            lons.append(lon)
    
    # Default to Boston if no valid locations found
    if not lats:
        lats, lons = [42.3601], [-71.0589]
    
    avg_lat = sum(lats) / len(lats)
    avg_lon = sum(lons) / len(lons)
    
    # Safe normalization with bounds checking
    lat_normalized = max(0.0, min(1.0, (avg_lat - LAT_MIN) / (LAT_MAX - LAT_MIN)))
    lon_normalized = max(0.0, min(1.0, (avg_lon - LON_MIN) / (LON_MAX - LON_MIN)))

    # Gender preference (validated, with safe default)
    gender = GENDER_MAP.get(user_data.get('gender_preference', 'Any'), 0.5)

    # Budget (validated to be within range)
    budget = user_data.get('budget_max', 1500)
    budget_normalized = max(0.0, min(1.0, (budget - BUDGET_MIN) / (BUDGET_MAX - BUDGET_MIN)))

    # Lease duration (validated to be 1-24 months)
    lease_duration = user_data.get('lease_duration_months', 12)
    lease_normalized = max(0.0, min(1.0, (lease_duration - LEASE_MIN) / (LEASE_MAX - LEASE_MIN)))

    # Room type (validated enum)
    room_type_pref = user_data.get('room_type_preference', 'Shared')
    room_type = 0.0 if room_type_pref == 'Shared' else (1.0 if room_type_pref == 'Private' else 0.5)

    # Bathroom (validated enum)
    bathroom_pref = user_data.get('attached_bathroom', 'No')
    bathroom = 0.0 if bathroom_pref == 'No' else (1.0 if bathroom_pref == 'Yes' else 0.5)

    # Lifestyle preferences (all validated enums)
    food = FOOD_MAP.get(user_data.get('lifestyle_food', 'Everything'), 1.0)
    alcohol = ALCOHOL_MAP.get(user_data.get('lifestyle_alcohol', 'Occasionally'), 0.5)
    smoke = SMOKE_MAP.get(user_data.get('lifestyle_smoke', 'No'), 0.0)

    # Utilities (validated list)
    utilities = min(1.0, len(user_data.get('utilities_preference', [])) / 4.0)

    # Build normalized vector
    normalized_vector = np.array([
        lat_normalized, lon_normalized, gender, budget_normalized, lease_normalized,
        room_type, bathroom, food, alcohol, smoke, utilities
    ], dtype=np.float32)

    # Apply weights
    weighted_vector = normalized_vector * WEIGHTS
    
    # Validate output vector
    if np.any(np.isnan(weighted_vector)) or np.any(np.isinf(weighted_vector)):
        raise ValueError("Invalid vector computed - contains NaN or Inf values")
    
    return weighted_vector