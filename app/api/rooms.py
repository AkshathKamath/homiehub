from fastapi import APIRouter, HTTPException, status, Depends
import logging

from app.services.room_service import RoomService, get_room_service
from app.models.room import RoomCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def create_room(
    room: RoomCreate,
    room_service_obj: RoomService = Depends(get_room_service)
):
    """Create a new room"""
    try:
        return await room_service_obj.add_room(room=room)
    except Exception as e:
        logger.error(f"Error in create_room endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create room"
        )