from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import numpy as np

load_dotenv()

class Settings(BaseSettings):
    app_name: str = "User Service"
    debug: bool = True

    gcloud_json: str

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'

settings = Settings()

## Map of location to coordinates
LOCATION_COORDS = {
    # Core Boston neighborhoods
    "Boston": (42.3601, -71.0589),
    "Downtown Boston": (42.3551, -71.0603),
    "Back Bay": (42.3505, -71.0763),
    "South End": (42.3414, -71.0742),
    "North End": (42.3647, -71.0542),
    "Beacon Hill": (42.3588, -71.0707),
    "Fenway": (42.3467, -71.0972),
    "South Boston": (42.3334, -71.0495),
    "East Boston": (42.3713, -71.0395),
    "Charlestown": (42.3782, -71.0602),
    "Roxbury": (42.3318, -71.0828),
    "Jamaica Plain": (42.3099, -71.1206),
    "Mission Hill": (42.3331, -71.1008),
    
    # Cambridge (nearby areas)
    "Cambridge": (42.3736, -71.1097),
    "Central Square": (42.3657, -71.1040),
    "Kendall Square": (42.3656, -71.0857),
    "Harvard Square": (42.3736, -71.1190),
    
    # Somerville (nearby areas)
    "Somerville": (42.3876, -71.0995),
    "Union Square": (42.3793, -71.0936),
    "Davis Square": (42.3967, -71.1226),
    
    # Brookline
    "Brookline": (42.3318, -71.1212),
    "Coolidge Corner": (42.3421, -71.1211),
    
    # Allston/Brighton
    "Allston": (42.3543, -71.1312),
    "Brighton": (42.3481, -71.1509),
}

## Vector weights
WEIGHTS = np.array([
    3.0,  # index 0: latitude (location - high priority)
    3.0,  # index 1: longitude (location - high priority)
    4.0,  # index 2: gender (STRICT - highest priority)
    3.0,  # index 3: budget (high priority)
    4.0,  # index 4: lease_duration (STRICT - highest priority)
    2.0,  # index 5: room_type (medium priority)
    1.0,  # index 6: bathroom (low priority)
    1.0,  # index 7: food (low priority)
    1.0,  # index 8: alcohol (low priority)
    1.0,  # index 9: smoke (low priority)
    2.0   # index 10: utilities (medium priority)
], dtype=np.float32)

GENDER_MAP = {"Male": 0.0, "Female": 1.0, "Mixed": 0.5}

FOOD_MAP = {"Vegan": 0.0, "Vegetarian": 0.5, "Everything": 1.0}

ALCOHOL_MAP = {
    "Never": 0.0,
    "Rarely": 0.25,
    "Occasionally": 0.5,
    "Regularly": 0.75,
    "Frequently": 1.0
}
SMOKE_MAP = {"No": 0.0, "Outside Only": 0.5, "Yes": 1.0}

LAT_MIN, LAT_MAX = 42.25, 42.45
LON_MIN, LON_MAX = -71.20, -71.00
BUDGET_MIN, BUDGET_MAX = 500, 3000
LEASE_MIN, LEASE_MAX = 1, 24