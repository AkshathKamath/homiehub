from langchain.tools import tool
import httpx
import logging
from typing import Dict, Any, Optional
from app.config import settings

logger = logging.getLogger(__name__)


def format_room_data(room_id: str, room_data: dict, rank: int) -> str:
    """
    Helper function to format room data into a readable string
    
    Args:
        room_id: Unique room identifier
        room_data: Dictionary containing room information
        rank: The ranking position of this room
    
    Returns:
        Formatted string with room details
    """
    output = f"\n{'='*60}\n"
    output += f"🏠 ROOM #{rank} - ID: {room_id}\n"
    output += f"{'='*60}\n\n"
    
    # Location and Rent (Most Important)
    output += "📍 LOCATION & PRICING:\n"
    output += f"   • Location: {room_data.get('location', 'N/A')}\n"
    output += f"   • Monthly Rent: ${room_data.get('rent', 'N/A')}\n"
    output += f"   • Address: {room_data.get('address', 'N/A')}\n"
    
    # Room Details
    output += "\n🏠 ROOM DETAILS:\n"
    output += f"   • Room Type: {room_data.get('room_type', 'N/A')}\n"
    output += f"   • Bedrooms: {room_data.get('num_bedrooms', 'N/A')}\n"
    output += f"   • Bathrooms: {room_data.get('num_bathrooms', 'N/A')}\n"
    output += f"   • Attached Bathroom: {room_data.get('attached_bathroom', 'N/A')}\n"
    
    # Availability
    output += "\n📅 AVAILABILITY:\n"
    output += f"   • Available From: {room_data.get('available_from', 'N/A')}\n"
    output += f"   • Lease Duration: {room_data.get('lease_duration_months', 'N/A')} months\n"
    
    # Flatmate Info
    output += "\n👥 FLATMATE INFORMATION:\n"
    output += f"   • Gender: {room_data.get('flatmate_gender', 'N/A')}\n"
    
    # Lifestyle
    output += "\n🎯 LIFESTYLE:\n"
    output += f"   • Smoking: {room_data.get('lifestyle_smoke', 'N/A')}\n"
    output += f"   • Alcohol: {room_data.get('lifestyle_alcohol', 'N/A')}\n"
    output += f"   • Food: {room_data.get('lifestyle_food', 'N/A')}\n"
    
    # Amenities
    if 'amenities' in room_data and room_data['amenities']:
        output += "\n✨ AMENITIES:\n"
        for amenity in room_data['amenities']:
            output += f"   • {amenity}\n"
    
    # Utilities
    if 'utilities_included' in room_data and room_data['utilities_included']:
        output += "\n💡 UTILITIES INCLUDED:\n"
        for utility in room_data['utilities_included']:
            output += f"   • {utility}\n"
    
    # Description
    if 'description' in room_data:
        output += f"\n📝 DESCRIPTION:\n{room_data['description']}\n"
    
    # Contact
    if 'contact' in room_data:
        output += f"\n📧 CONTACT: {room_data['contact']}\n"
    
    return output


@tool
def find_matching_rooms(
    user_id: str,
    location: str = None,
    max_rent: int = None,
    room_type: str = None,
    flatmate_gender: str = None,
    attached_bathroom: str = None,
    lease_duration_months: int = None,
    available_from: str = None,
    limit: int = 10
) -> str:
    """
    Finds rooms that match user preferences using the vector similarity matching service.
    This tool calls the recommendation API which returns detailed room information.
    
    Args:
        user_id: The user's unique identifier (REQUIRED)
        location: Filter by location in Greater Boston area (e.g., "Boston", "Cambridge", "Somerville")
        max_rent: Maximum monthly rent in USD (e.g., 2000, 1500)
        room_type: Type of room - "Shared", "Private", or "Studio"
        flatmate_gender: Preferred flatmate gender - "Male", "Female", "Mixed", or "Any"
        attached_bathroom: Bathroom preference - "Yes", "No", or "Shared"
        lease_duration_months: Preferred lease duration in months (1-24)
        available_from: Earliest availability date in YYYY-MM-DD format (e.g., "2025-01-01")
        limit: Maximum number of results to return (1-100, default 10)
    
    Returns:
        Formatted string containing detailed information about matching rooms
    """
    try:
        # Build request payload
        payload = {
            "user_id": user_id,
            "limit": limit
        }
        
        # Add optional filters
        if location:
            payload["location"] = location
        if max_rent is not None:
            payload["max_rent"] = max_rent
        if room_type:
            payload["room_type"] = room_type
        if flatmate_gender:
            payload["flatmate_gender"] = flatmate_gender
        if attached_bathroom:
            payload["attached_bathroom"] = attached_bathroom
        if lease_duration_months is not None:
            payload["lease_duration_months"] = lease_duration_months
        if available_from:
            payload["available_from"] = available_from
        
        logger.info(f"Calling matching service with payload: {payload}")
        
        # Call matching service API
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{settings.matching_service_url}/recommendation",
                json=payload
            )
        
        if response.status_code == 404:
            return f"User with ID '{user_id}' not found in the system. Please verify your user ID."
        
        if response.status_code == 400:
            error_detail = response.json().get('detail', 'Invalid request')
            return f"Invalid request: {error_detail}"
        
        if response.status_code != 200:
            return f"Error from matching service: {response.status_code} - {response.text}"
        
        result = response.json()
        matches = result.get('matches', [])
        total_results = result.get('total_results', 0)
        
        if not matches or len(matches) == 0:
            filter_info = []
            if location:
                filter_info.append(f"location: {location}")
            if max_rent:
                filter_info.append(f"max rent: ${max_rent}")
            if room_type:
                filter_info.append(f"room type: {room_type}")
            
            filters_text = f" with filters ({', '.join(filter_info)})" if filter_info else ""
            return f"No matching rooms found{filters_text}. Try adjusting your preferences or removing some filters."
        
        # Format header
        output = f"\n🎉 Found {total_results} matching room{'s' if total_results != 1 else ''} for you!\n"
        
        # Add filter summary if filters were applied
        applied_filters = []
        if location:
            applied_filters.append(f"Location: {location}")
        if max_rent:
            applied_filters.append(f"Max Rent: ${max_rent}")
        if room_type:
            applied_filters.append(f"Room Type: {room_type}")
        if flatmate_gender:
            applied_filters.append(f"Flatmate: {flatmate_gender}")
        if attached_bathroom:
            applied_filters.append(f"Bathroom: {attached_bathroom}")
        if lease_duration_months:
            applied_filters.append(f"Lease: {lease_duration_months} months")
        if available_from:
            applied_filters.append(f"Available from: {available_from}")
        
        if applied_filters:
            output += f"\n🔍 Filters applied: {', '.join(applied_filters)}\n"
        
        # Format each room
        for idx, match in enumerate(matches, 1):
            room_id = match.get('room_id', 'N/A')
            room_data = match.get('room_data', {})
            output += format_room_data(room_id, room_data, idx)
        
        # Add summary at the end
        output += f"\n{'='*60}\n"
        output += f"💡 TIP: Review each room's details and contact the owners directly!\n"
        output += f"{'='*60}\n"
        
        return output.strip()
        
    except httpx.ConnectError:
        logger.error("Unable to connect to matching service")
        return "Unable to connect to the matching service. Please make sure the service is running."
    except httpx.TimeoutException:
        logger.error("Request to matching service timed out")
        return "Request timed out. The matching service may be experiencing high load."
    except Exception as e:
        logger.error(f"Error finding matching rooms: {str(e)}", exc_info=True)
        return f"An error occurred while searching for rooms: {str(e)}"


def get_available_tools():
    """Returns list of available tools"""
    return [find_matching_rooms]