from pydantic import BaseModel, Field, field_validator, EmailStr
from typing import List, Optional
from datetime import date
import re

class RoomCreate(BaseModel):
    # Required fields with validation
    location: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="City or area name"
    )
    address: str = Field(
        ..., 
        min_length=5, 
        max_length=200,
        description="Full street address"
    )
    flatmate_gender: str = Field(
        ...,
        description="Gender preference for flatmates"
    )
    rent: int = Field(
        ..., 
        ge=300, 
        le=10000,
        description="Monthly rent in USD"
    )
    attached_bathroom: str = Field(
        ...,
        description="Attached bathroom availability"
    )
    lease_duration_months: int = Field(
        ..., 
        ge=1, 
        le=24,
        description="Lease duration in months"
    )
    room_type: str = Field(
        ...,
        description="Type of room"
    )
    utilities_included: List[str] = Field(
        default_factory=list,
        max_length=10,
        description="Utilities included in rent"
    )
    contact: EmailStr = Field(
        ...,
        description="Contact email for inquiries"
    )
    available_from: date = Field(
        ...,
        description="Date when room becomes available"
    )
    
    # Optional lifestyle preferences
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
    
    # Optional property details
    num_bedrooms: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Total bedrooms in unit"
    )
    num_bathrooms: Optional[int] = Field(
        default=None,
        ge=1,
        le=10,
        description="Total bathrooms in unit"
    )
    description: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="Room description"
    )
    amenities: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="Available amenities"
    )
    photos: List[str] = Field(
        default_factory=list,
        max_length=20,
        description="Photo URLs"
    )
    
    # Validators
    @field_validator('location')
    @classmethod
    def validate_location(cls, v: str) -> str:
        """Validate and clean location name"""
        if not v or not v.strip():
            raise ValueError("Location cannot be empty")
        return v.strip()
    
    @field_validator('address')
    @classmethod
    def validate_address(cls, v: str) -> str:
        """Validate address format"""
        if not v or not v.strip():
            raise ValueError("Address cannot be empty")
        v = v.strip()
        if len(v) < 5:
            raise ValueError("Address must be at least 5 characters")
        return v
    
    @field_validator('flatmate_gender')
    @classmethod
    def validate_flatmate_gender(cls, v: str) -> str:
        """Validate flatmate gender preference"""
        valid_options = ['Male', 'Female', 'Non-binary', 'Mixed', 'Any']
        if v not in valid_options:
            raise ValueError(f"Flatmate gender must be one of: {', '.join(valid_options)}")
        return v
    
    @field_validator('room_type')
    @classmethod
    def validate_room_type(cls, v: str) -> str:
        """Validate room type"""
        valid_types = ['Shared', 'Private', 'Studio']
        if v not in valid_types:
            raise ValueError(f"Room type must be one of: {', '.join(valid_types)}")
        return v
    
    @field_validator('attached_bathroom')
    @classmethod
    def validate_attached_bathroom(cls, v: str) -> str:
        """Validate bathroom option"""
        valid_options = ['Yes', 'No']
        if v not in valid_options:
            raise ValueError(f"Attached bathroom must be 'Yes' or 'No'")
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
    
    @field_validator('utilities_included')
    @classmethod
    def validate_utilities(cls, v: List[str]) -> List[str]:
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
    
    @field_validator('available_from')
    @classmethod
    def validate_available_from(cls, v: date) -> date:
        """Validate availability date is not too far in past"""
        today = date.today()
        # Allow up to 30 days in the past (for already available rooms)
        from datetime import timedelta
        min_date = today - timedelta(days=30)
        if v < min_date:
            raise ValueError("Available from date cannot be more than 30 days in the past")
        # Allow up to 1 year in future
        max_date = date(today.year + 1, today.month, today.day)
        if v > max_date:
            raise ValueError("Available from date cannot be more than 1 year in the future")
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        """Validate and sanitize description"""
        if not v:
            return None
        
        v = v.strip()
        
        if len(v) < 10:
            raise ValueError("Description must be at least 10 characters")
        
        # Basic XSS prevention - remove HTML tags
        v = re.sub(r'<[^>]+>', '', v)
        
        return v[:2000]  # Enforce max length
    
    @field_validator('amenities')
    @classmethod
    def validate_amenities(cls, v: List[str]) -> List[str]:
        """Validate amenities list"""
        if not v:
            return []
        
        valid_amenities = [
            'WiFi', 'Parking', 'Laundry in unit', 'Laundry in building',
            'Gym', 'Pool', 'Elevator', 'Doorman', 'Pet-friendly',
            'Air conditioning', 'Heating', 'Dishwasher', 'Microwave',
            'Furnished', 'Hardwood floors', 'Balcony', 'Patio',
            'Storage', 'Bike storage', 'Kitchen'
        ]
        
        cleaned = []
        for amenity in v:
            amenity_clean = amenity.strip()
            if amenity_clean and amenity_clean not in cleaned:
                # Allow custom amenities but sanitize
                amenity_clean = re.sub(r'<[^>]+>', '', amenity_clean)
                if len(amenity_clean) <= 50:
                    cleaned.append(amenity_clean)
        
        return cleaned[:20]  # Limit to 20 amenities
    
    @field_validator('photos')
    @classmethod
    def validate_photos(cls, v: List[str]) -> List[str]:
        """Validate photo URLs"""
        if not v:
            return []
        
        cleaned = []
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        for photo_url in v:
            photo_url = photo_url.strip()
            if url_pattern.match(photo_url) and photo_url not in cleaned:
                cleaned.append(photo_url)
        
        return cleaned[:20]  # Limit to 20 photos

    class Config:
        json_schema_extra = {
            "example": {
                "location": "Cambridge",
                "address": "123 Main Street, Cambridge, MA 02139",
                "flatmate_gender": "Mixed",
                "rent": 1100,
                "attached_bathroom": "No",
                "lease_duration_months": 12,
                "room_type": "Shared",
                "utilities_included": ["Heat", "Water", "Gas"],
                "lifestyle_food": "Vegetarian",
                "lifestyle_alcohol": "Rarely",
                "lifestyle_smoke": "No",
                "contact": "landlord@email.com",
                "available_from": "2025-01-01",
                "num_bedrooms": 3,
                "num_bathrooms": 2,
                "description": "Spacious 3BR apartment near MIT with 2 current roommates",
                "amenities": ["WiFi", "Laundry in building", "Bike storage"],
                "photos": ["https://example.com/photo1.jpg"]
            }
        }