from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class UserCreate(BaseModel):
    name: str
    email: str
    preferred_locations: List[str]
    gender: str
    gender_preference: str
    room_type_preference: str
    budget_max: int
    attached_bathroom: str
    lifestyle_food: str
    lifestyle_alcohol: str
    lifestyle_smoke: str
    utilities_preference: List[str]
    contact: str
    description: str