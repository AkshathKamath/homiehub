from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import List, Optional
from datetime import datetime, date
import re

class UserCreate(BaseModel):
    # Required fields with validation
    name: str = Field(
        ..., 
        min_length=2, 
        max_length=100,
        description="User's full name"
    )
    email: EmailStr = Field(..., description="Valid email address")
    contact_number: str = Field(
        ..., 
        min_length=10, 
        max_length=15,
        description="Contact phone number"
    )
    age: int = Field(..., ge=18, le=100, description="Age must be between 18 and 100")
    gender: str = Field(..., description="User's gender")
    move_in_date: date = Field(..., description="Desired move-in date")
    
    # Optional fields with defaults and validation
    gender_preference: Optional[str] = Field(
        default="Any",
        description="Preferred roommate gender"
    )
    preferred_locations: Optional[List[str]] = Field(
        default=["Boston"],
        min_length=1,
        max_length=10,
        description="List of preferred locations"
    )
    budget_max: Optional[int] = Field(
        default=1500,
        ge=300,
        le=10000,
        description="Maximum monthly budget in USD"
    )
    lease_duration_months: Optional[int] = Field(
        default=12,
        ge=1,
        le=24,
        description="Desired lease duration in months"
    )
    room_type_preference: Optional[str] = Field(
        default="Shared",
        description="Preferred room type"
    )
    attached_bathroom: Optional[str] = Field(
        default="No",
        description="Attached bathroom preference"
    )
    lifestyle_food: Optional[str] = Field(
        default="Everything",
        description="Food lifestyle preference"
    )
    lifestyle_alcohol: Optional[str] = Field(
        default="Occasionally",
        description="Alcohol consumption preference"
    )
    lifestyle_smoke: Optional[str] = Field(
        default="No",
        description="Smoking preference"
    )
    utilities_preference: Optional[List[str]] = Field(
        default_factory=list,
        max_length=10,
        description="Preferred utilities to be included"
    )
    
    # Profile fields
    occupation: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Current occupation"
    )
    university: Optional[str] = Field(
        default=None,
        max_length=100,
        description="University name"
    )
    bio: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Short bio"
    )
    interests: Optional[List[str]] = Field(
        default_factory=list,
        max_length=20,
        description="List of interests"
    )
    
    # Validators
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name contains only letters, spaces, hyphens, apostrophes"""
        if not v or not v.strip():
            raise ValueError("Name cannot be empty")
        # Allow letters, spaces, hyphens, apostrophes, periods
        if not re.match(r"^[a-zA-Z\s\-'\.]+$", v):
            raise ValueError("Name can only contain letters, spaces, hyphens, apostrophes, and periods")
        return v.strip()
    
    @field_validator('contact_number')
    @classmethod
    def validate_contact_number(cls, v: str) -> str:
        """Validate phone number format"""
        # Remove common separators
        cleaned = re.sub(r'[\s\-\(\)\+]', '', v)
        if not cleaned.isdigit():
            raise ValueError("Contact number must contain only digits and standard separators")
        if len(cleaned) < 10 or len(cleaned) > 15:
            raise ValueError("Contact number must be between 10 and 15 digits")
        return v
    
    @field_validator('gender')
    @classmethod
    def validate_gender(cls, v: str) -> str:
        """Validate gender is from allowed values"""
        valid_genders = ['Male', 'Female', 'Non-binary', 'Prefer not to say']
        if v not in valid_genders:
            raise ValueError(f"Gender must be one of: {', '.join(valid_genders)}")
        return v
    
    @field_validator('gender_preference')
    @classmethod
    def validate_gender_preference(cls, v: Optional[str]) -> Optional[str]:
        """Validate gender preference"""
        if v is None:
            return "Any"
        valid_preferences = ['Male', 'Female', 'Non-binary', 'Mixed', 'Any']
        if v not in valid_preferences:
            raise ValueError(f"Gender preference must be one of: {', '.join(valid_preferences)}")
        return v
    
    @field_validator('preferred_locations')
    @classmethod
    def validate_preferred_locations(cls, v: Optional[List[str]]) -> List[str]:
        """Validate and clean location names"""
        if not v:
            return ["Boston"]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_locs = []
        for loc in v:
            loc_clean = loc.strip()
            if loc_clean and loc_clean not in seen:
                seen.add(loc_clean)
                unique_locs.append(loc_clean)
        
        if not unique_locs:
            return ["Boston"]
        
        return unique_locs[:10]  # Limit to 10 locations
    
    @field_validator('room_type_preference')
    @classmethod
    def validate_room_type(cls, v: Optional[str]) -> str:
        """Validate room type preference"""
        if v is None:
            return "Shared"
        valid_types = ['Shared', 'Private', 'Studio', 'Any']
        if v not in valid_types:
            raise ValueError(f"Room type must be one of: {', '.join(valid_types)}")
        return v
    
    @field_validator('attached_bathroom')
    @classmethod
    def validate_attached_bathroom(cls, v: Optional[str]) -> str:
        """Validate bathroom preference"""
        if v is None:
            return "No"
        valid_options = ['Yes', 'No', 'Any']
        if v not in valid_options:
            raise ValueError(f"Attached bathroom must be one of: {', '.join(valid_options)}")
        return v
    
    @field_validator('lifestyle_food')
    @classmethod
    def validate_lifestyle_food(cls, v: Optional[str]) -> str:
        """Validate food preference"""
        if v is None:
            return "Everything"
        valid_options = ['Vegetarian', 'Vegan', 'Non-vegetarian', 'Everything', 'Halal', 'Kosher']
        if v not in valid_options:
            raise ValueError(f"Food preference must be one of: {', '.join(valid_options)}")
        return v
    
    @field_validator('lifestyle_alcohol')
    @classmethod
    def validate_lifestyle_alcohol(cls, v: Optional[str]) -> str:
        """Validate alcohol preference"""
        if v is None:
            return "Occasionally"
        valid_options = ['Never', 'Rarely', 'Occasionally', 'Regularly']
        if v not in valid_options:
            raise ValueError(f"Alcohol preference must be one of: {', '.join(valid_options)}")
        return v
    
    @field_validator('lifestyle_smoke')
    @classmethod
    def validate_lifestyle_smoke(cls, v: Optional[str]) -> str:
        """Validate smoking preference"""
        if v is None:
            return "No"
        valid_options = ['Yes', 'No', 'Occasionally', 'Outside only']
        if v not in valid_options:
            raise ValueError(f"Smoking preference must be one of: {', '.join(valid_options)}")
        return v
    
    @field_validator('utilities_preference')
    @classmethod
    def validate_utilities(cls, v: Optional[List[str]]) -> List[str]:
        """Validate utilities list"""
        if not v:
            return []
        
        valid_utilities = [
            'Heat', 'Water', 'Gas', 'Electricity', 
            'Internet', 'Trash', 'Sewer', 'Cable'
        ]
        
        cleaned = []
        for util in v:
            util_clean = util.strip()
            if util_clean in valid_utilities and util_clean not in cleaned:
                cleaned.append(util_clean)
        
        return cleaned[:10]  # Limit to 10 utilities
    
    @field_validator('move_in_date')
    @classmethod
    def validate_move_in_date(cls, v: date) -> date:
        """Validate move-in date is not in the past"""
        today = date.today()
        if v < today:
            raise ValueError("Move-in date cannot be in the past")
        # Allow up to 1 year in future
        max_date = date(today.year + 1, today.month, today.day)
        if v > max_date:
            raise ValueError("Move-in date cannot be more than 1 year in the future")
        return v
    
    @field_validator('bio')
    @classmethod
    def validate_bio(cls, v: Optional[str]) -> Optional[str]:
        """Validate and sanitize bio"""
        if not v:
            return None
        
        # Strip whitespace
        v = v.strip()
        
        # Check for minimum content
        if len(v) < 10:
            raise ValueError("Bio must be at least 10 characters")
        
        # Basic XSS prevention - remove HTML tags
        v = re.sub(r'<[^>]+>', '', v)
        
        return v[:500]  # Enforce max length
    
    @field_validator('interests')
    @classmethod
    def validate_interests(cls, v: Optional[List[str]]) -> List[str]:
        """Validate interests list"""
        if not v:
            return []
        
        cleaned = []
        for interest in v:
            interest_clean = interest.strip()
            if interest_clean and len(interest_clean) <= 50:  # Max 50 chars per interest
                # Basic sanitization
                interest_clean = re.sub(r'<[^>]+>', '', interest_clean)
                if interest_clean not in cleaned:
                    cleaned.append(interest_clean)
        
        return cleaned[:20]  # Limit to 20 interests

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@email.com",
                "contact_number": "+1-234-567-8900",
                "age": 25,
                "gender": "Male",
                "gender_preference": "Any",
                "preferred_locations": ["Cambridge", "Boston"],
                "budget_max": 1500,
                "lease_duration_months": 12,
                "room_type_preference": "Shared",
                "attached_bathroom": "No",
                "lifestyle_food": "Vegetarian",
                "lifestyle_alcohol": "Occasionally",
                "lifestyle_smoke": "No",
                "utilities_preference": ["Heat", "Water"],
                "move_in_date": "2024-12-01",
                "occupation": "Software Engineer",
                "university": "MIT",
                "bio": "Quiet grad student looking for a peaceful living environment",
                "interests": ["Reading", "Hiking", "Cooking"]
            }
        }