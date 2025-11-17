"""
Function-based room search tool
Simple, clean, and works perfectly with LangChain
"""
from langchain_core.tools import tool
import httpx
from typing import Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)

# Shared HTTP client (singleton pattern)
_http_client: Optional[httpx.Client] = None

def get_http_client() -> httpx.Client:
    """Get or create shared HTTP client"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(
            timeout=30.0,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
    return _http_client


@tool
def find_matching_rooms(
    user_id: str,
    location: Optional[str] = None,
    max_rent: Optional[int] = None,
    room_type: Optional[str] = None,
    flatmate_gender: Optional[str] = None,
    attached_bathroom: Optional[str] = None,
    lease_duration_months: Optional[int] = None,
    available_from: Optional[str] = None,
    limit: int = 10
) -> str:
    """
    Finds rooms matching user preferences using vector similarity search.
    
    Args:
        user_id: User's unique identifier (REQUIRED)
        location: Location in Greater Boston (e.g., "Cambridge", "Boston", "Somerville")
        max_rent: Maximum monthly rent in USD (e.g., 2000, 1500)
        room_type: Type of room - "Shared", "Private", or "Studio"
        flatmate_gender: Preferred flatmate gender - "Male", "Female", "Mixed", or "Any"
        attached_bathroom: Bathroom preference - "Yes", "No", or "Shared"
        lease_duration_months: Preferred lease duration in months (1-24)
        available_from: Earliest availability date in YYYY-MM-DD format (e.g., "2025-01-01")
        limit: Maximum number of results to return (1-100, default 10)
    
    Returns:
        Formatted string with matching room details
    """
    try:
        # Build payload
        payload = {"user_id": user_id, "limit": limit}
        
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
        
        # Call matching service
        client = get_http_client()
        response = client.post(
            f"{settings.matching_service_url}/recommendation",
            json=payload
        )
        
        if response.status_code == 404:
            return f"User with ID '{user_id}' not found. Please verify your user ID."
        
        if response.status_code == 400:
            error_detail = response.json().get('detail', 'Invalid request')
            return f"Invalid request: {error_detail}"
        
        if response.status_code != 200:
            logger.error(f"Matching service error: {response.status_code}")
            return f"Error from matching service: {response.status_code}"
        
        # Parse results
        result = response.json()
        matches = result.get('matches', [])
        total_results = result.get('total_results', 0)
        
        if not matches:
            return _format_no_results(payload)
        
        # Format and return results
        formatted_output = _format_results(matches, total_results, payload)
        
        logger.info(f"Returning {len(formatted_output)} characters of formatted results")
        logger.info(f"Preview: {formatted_output[:200]}")
        
        return formatted_output
        
    except httpx.ConnectError:
        logger.error("Unable to connect to matching service")
        return "Unable to connect to the matching service. Please try again later."
    except httpx.TimeoutException:
        logger.error("Request timed out")
        return "Request timed out. Please try again."
    except Exception as e:
        logger.error(f"Error in find_matching_rooms: {str(e)}", exc_info=True)
        return f"An error occurred while searching for rooms: {str(e)}"


def _format_no_results(payload: dict) -> str:
    """Format message when no results found"""
    filter_info = []
    if 'location' in payload:
        filter_info.append(f"location: {payload['location']}")
    if 'max_rent' in payload:
        filter_info.append(f"max rent: ${payload['max_rent']}")
    if 'room_type' in payload:
        filter_info.append(f"room type: {payload['room_type']}")
    
    filters_text = f" with filters ({', '.join(filter_info)})" if filter_info else ""
    return f"No matching rooms found{filters_text}. Try adjusting your preferences or removing some filters."


def _format_results(matches: list, total_results: int, payload: dict) -> str:
    """Format successful results - simple numbered list"""
    
    # Header
    output = f"\nFound {total_results} matching room{'s' if total_results != 1 else ''}.\n"
    
    # Show applied filters
    filters = []
    if 'location' in payload:
        filters.append(f"Location: {payload['location']}")
    if 'max_rent' in payload:
        filters.append(f"Max Rent: ${payload['max_rent']}")
    if 'room_type' in payload:
        filters.append(f"Room Type: {payload['room_type']}")
    
    if filters:
        output += f"Filters applied: {', '.join(filters)}\n"
    
    output += "\n"
    
    # Format each room
    for idx, match in enumerate(matches, 1):
        room_id = match.get('room_id', 'N/A')
        room_data = match.get('room_data', {})
        
        output += f"{idx}. Room ID: {room_id}\n"
        output += f"   Location: {room_data.get('location', 'N/A')}\n"
        output += f"   Monthly Rent: ${room_data.get('rent', 'N/A')}\n"
        output += f"   Room Type: {room_data.get('room_type', 'N/A')}\n"
        output += f"   Bedrooms: {room_data.get('num_bedrooms', 'N/A')}\n"
        output += f"   Bathrooms: {room_data.get('num_bathrooms', 'N/A')}\n"
        output += f"   Attached Bathroom: {room_data.get('attached_bathroom', 'N/A')}\n"
        output += f"   Available From: {room_data.get('available_from', 'N/A')}\n"
        output += f"   Lease Duration: {room_data.get('lease_duration_months', 'N/A')} months\n"
        output += f"   Flatmate Gender: {room_data.get('flatmate_gender', 'N/A')}\n"
        output += f"   Smoking: {room_data.get('lifestyle_smoke', 'N/A')}\n"
        output += f"   Alcohol: {room_data.get('lifestyle_alcohol', 'N/A')}\n"
        output += f"   Food Preference: {room_data.get('lifestyle_food', 'N/A')}\n"
        
        # Amenities
        if 'amenities' in room_data and room_data['amenities']:
            output += f"   Amenities: {', '.join(room_data['amenities'])}\n"
        
        # Utilities
        if 'utilities_included' in room_data and room_data['utilities_included']:
            output += f"   Utilities Included: {', '.join(room_data['utilities_included'])}\n"
        
        # Description
        if 'description' in room_data:
            output += f"   Description: {room_data['description']}\n"
        
        # Address
        if 'address' in room_data:
            output += f"   Address: {room_data['address']}\n"
        
        # Contact
        if 'contact' in room_data:
            output += f"   Contact: {room_data['contact']}\n"
        
        output += "\n"
    
    return output