from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
import logging
import json
from typing import List

from app.services.room_service import RoomService, get_room_service
from app.core.dependencies import get_current_user
from app.models.room import RoomCreate, RoomDeleteRequest
from app.core.storage import upload_room_photos

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rooms", tags=["rooms"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_room(
    room_data: str = Form(...),
    photos: List[UploadFile] = File(None),
    current_user: dict = Depends(get_current_user),
    room_service_obj: RoomService = Depends(get_room_service)
):
    """Create a new room"""
    try:
        user_id = current_user['user_id']
        
        # Parse room data
        room_dict = json.loads(room_data)
        room = RoomCreate(**room_dict)
        
        # Generate room ID first for photo uploads
        doc_ref = room_service_obj._firestore.collection('rooms').document()
        room_id = doc_ref.id
        
        # Upload photos if provided
        photo_urls = []
        if photos:
            photo_urls = await upload_room_photos(room_id, photos)
            # Combine existing photos from JSON with uploaded photo URLs
            room.photos.extend(photo_urls)
        
        # Create the room with the generated ID
        result = await room_service_obj.add_room_with_id(user_id=user_id, room=room, room_id=room_id)
        return result
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
    room: RoomDeleteRequest,
    current_user: dict = Depends(get_current_user),
    room_service_obj: RoomService = Depends(get_room_service)
):
    """
    Delete the authenticated user's room.
    """
    try:
        user_id = current_user['user_id']
        logger.info(f"Deleting room for user: {user_id}")

        return await room_service_obj.delete_room_by_id(user_id=user_id, room_id=room.room_id)

    except Exception:
        logger.error("Error deleting room", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete room"
        )