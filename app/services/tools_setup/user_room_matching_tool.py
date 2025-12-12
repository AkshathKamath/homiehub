"""
Function-based room search tool
Returns RAW JSON from matching service (no formatting)
"""
from langchain_core.tools import tool
import httpx
from typing import Optional, Dict, Any, List
import logging
from app.config import settings

logger = logging.getLogger(__name__)

_http_client: Optional[httpx.Client] = None

def get_http_client() -> httpx.Client:
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
    location: Optional[List[str]] = None,
    max_rent: Optional[int] = None,
    room_type: Optional[str] = None,
    flatmate_gender: Optional[str] = None,
    attached_bathroom: Optional[str] = None,
    lease_duration_months: Optional[int] = None,
    available_from: Optional[str] = None,
    lifestyle_smoke: Optional[str] = None,    # ✅ NEW
    lifestyle_alcohol: Optional[str] = None,  # ✅ NEW
    lifestyle_food: Optional[str] = None,     # ✅ NEW
    limit: int = 10
) -> Dict[str, Any]:
    """
    Finds rooms matching user preferences using vector similarity search.
    Returns raw JSON from the matching service.
    """
    try:
        payload: Dict[str, Any] = {"user_id": user_id, "limit": limit}

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

        # ✅ lifestyle filters
        if lifestyle_smoke:
            payload["lifestyle_smoke"] = lifestyle_smoke
        if lifestyle_alcohol:
            payload["lifestyle_alcohol"] = lifestyle_alcohol
        if lifestyle_food:
            payload["lifestyle_food"] = lifestyle_food

        logger.info(f"Calling matching service with payload: {payload}")

        client = get_http_client()
        response = client.post(
            f"{settings.matching_service_url}/recommendation/agent",
            json=payload
        )

        if response.status_code == 404:
            return {"error": "user_not_found", "detail": f"User '{user_id}' not found"}
        if response.status_code == 400:
            return {"error": "invalid_request", "detail": response.json().get("detail", "Invalid request")}
        if response.status_code != 200:
            return {"error": "matching_service_error", "status_code": response.status_code}

        return response.json()

    except httpx.ConnectError:
        return {"error": "connect_error", "detail": "Unable to connect to matching service"}
    except httpx.TimeoutException:
        return {"error": "timeout", "detail": "Request timed out"}
    except Exception as e:
        logger.error(f"Error in find_matching_rooms: {str(e)}", exc_info=True)
        return {"error": "exception", "detail": str(e)}
