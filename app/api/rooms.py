from fastapi import APIRouter, HTTPException, status, Depends
import logging

from app.services.room_service import RoomService, get_room_service
from app.core.dependencies import get_current_user
from app.models.room import RoomCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_room(
    room: RoomCreate,
    current_user: dict = Depends(get_current_user),
    room_service_obj: RoomService = Depends(get_room_service)
):
    """Create a new room"""
    try:
        user_id = current_user['user_id']
        return await room_service_obj.add_room(user_id=user_id, room=room)
    except Exception as e:
        logger.error(f"Error in create_room endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create room"
        )

@router.get("/me", status_code=status.HTTP_200_OK)
async def get_room(
    current_user: dict = Depends(get_current_user),
    room_service_obj: RoomService = Depends(get_room_service)
):
    """
    Get all rooms created by the authenticated user
    
    Returns only active rooms by default.
    """
    try:
        user_id = current_user['user_id']
        logger.info(f"Fetching rooms for user: {user_id}")
        
        rooms = await room_service_obj.get_room(user_id=user_id)
        return rooms
        
    except Exception as e:
        logger.error(f"Error fetching user rooms: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch user rooms"
        )

@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_room(
    current_user: dict = Depends(get_current_user),
    room_service_obj: RoomService = Depends(get_room_service)
):
    """
    Delete the authenticated user's room.
    """
    try:
        user_id = current_user['user_id']
        logger.info(f"Deleting room for user: {user_id}")

        return await room_service_obj.delete_room(user_id=user_id)

    except Exception:
        logger.error("Error deleting room", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete room"
        )