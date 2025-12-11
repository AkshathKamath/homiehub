from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import date

class UserFilter(BaseModel):
    user_id: Optional[str] = Field(
        None,
        min_length=1,
        max_length=128,
        description="Unique identifier for the user requesting recommendations",
        examples=["N7BHzi80hxrkDeQBAziZ"]
    )
    
    location: Optional[List[str]] = Field(
        None,
        min_length=1,
        max_length=10,
        description="Filter by locations in Greater Boston area (can be multiple)",
        examples=[["Boston", "Cambridge"], ["Somerville"]]
    )
    
    max_rent: Optional[int] = Field(
        None,
        ge=0,
        le=10000,
        description="Maximum monthly rent in USD",
        examples=[2000, 1500]
    )
    
    room_type: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Type of room (e.g., Shared, Private, Studio)",
        examples=["Shared", "Private", "Studio"]
    )
    
    flatmate_gender: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Preferred flatmate gender",
        examples=["Male", "Female", "Mixed", "Any"]
    )
    
    attached_bathroom: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Bathroom availability preference",
        examples=["Yes", "No", "Shared"]
    )
    
    lease_duration_months: Optional[int] = Field(
        None,
        ge=1,
        le=24,
        description="Preferred lease duration in months",
        examples=[6, 12, 18]
    )
    
    available_from: Optional[date] = Field(
        None,
        description="Earliest date the room should be available (ISO 8601 format: YYYY-MM-DD)",
        examples=["2025-01-01", "2025-06-15"]
    )

    lifestyle_smoke: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Smoking preference (e.g., No, Yes, Outside-only, Occasional)"
    )
    lifestyle_alcohol: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Alcohol preference (e.g., No, Yes, Occasional, Social)"
    )
    lifestyle_food: Optional[str] = Field(
        None,
        min_length=1,
        max_length=50,
        description="Food preference (e.g., Veg, Non-Veg, Vegan, Halal, Kosher, Any)"
    )

    limit: int = Field(
        10,
        ge=1,
        le=100,
        description="Maximum number of results to return"
    )

    # @field_validator('user_id')
    # @classmethod
    # def validate_user_id(cls, v: str) -> str:
    #     """Validate user_id."""
    #     if not v or not v.strip():
    #         raise ValueError("user_id cannot be empty")
    #     return v.strip()
    @field_validator('location')
    @classmethod
    def validate_location(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate location list"""
        if v is None:
            return None
        
        if not isinstance(v, list):
            # If single string passed, convert to list
            return [v.strip()]
        
        # Clean and deduplicate locations
        cleaned = []
        seen = set()
        for loc in v:
            loc_clean = loc.strip()
            if loc_clean and loc_clean not in seen:
                seen.add(loc_clean)
                cleaned.append(loc_clean)
        
        if not cleaned:
            return None
        
        return cleaned[:10]

    @field_validator('room_type', 'flatmate_gender', 'attached_bathroom')
    @classmethod
    def validate_string_fields(cls, v: Optional[str]) -> Optional[str]:
        """Validate string fields."""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Filter value cannot be empty")
        return v

    @field_validator('available_from')
    @classmethod
    def validate_available_from(cls, v: Optional[date]) -> Optional[date]:
        """Validate date."""
        if v is not None:
            today = date.today()
            min_date = today - timedelta(days=30)
            max_date = today + timedelta(days=365)
            
            if v < min_date:
                raise ValueError(f"Date too far in past. Min: {min_date.isoformat()}")
            if v > max_date:
                raise ValueError(f"Date too far in future. Max: {max_date.isoformat()}")
        return v

    def has_filters(self) -> bool:
        """Check if any filters are applied."""
        return any([
            self.location,
            self.max_rent is not None,
            self.room_type,
            self.flatmate_gender,
            self.attached_bathroom,
            self.lease_duration_months is not None,
            self.available_from is not None
        ])

class User(BaseModel):
    user_id: str