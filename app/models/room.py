from pydantic import BaseModel
from typing import List
from datetime import date

class RoomCreate(BaseModel):
    location: str
    address: str
    flatmate_gender: str
    room_type: str
    rent: int
    attached_bathroom: str
    lifestyle_food: str
    lifestyle_alcohol: str
    lifestyle_smoke: str
    num_bedrooms: int
    num_bathrooms: int
    utilities_included: List[str]
    contact: str
    description: str
    amenities: List[str]
    lease_duration: str
    available_from: date
    photos: List[str]