from google.cloud.firestore import AsyncClient, SERVER_TIMESTAMP
from google.cloud.firestore_v1.vector import Vector
import logging

from app.db.firestore import get_firestore
from app.models.room import RoomCreate
from app.core.vectorize_room import vectorize_room

logger = logging.getLogger(__name__)

class RoomService:
    def __init__(self):
        self._firestore: AsyncClient = get_firestore()
    
    async def add_room(
            self,
            room: RoomCreate
    ):
        try:
            room_data = room.model_dump()
            
            # Convert date to string for Firestore
            room_data['available_from'] = room_data['available_from'].isoformat()
            
            room_data['created_at'] = SERVER_TIMESTAMP
            # room_vector = vectorize_room(room_data=room_data)
            # room_data['room_vector'] = Vector(room_vector)
            doc_ref = self._firestore.collection('rooms').document()
            await doc_ref.set(room_data)
            logger.info(f"Room created with ID: {doc_ref.id}")
            return {
                "id": doc_ref.id,
                "message": "Room created successfully"
            }
        except Exception as e:
            logger.error(f"Failed to create room: {str(e)}", exc_info=True)
            raise


def get_room_service() -> RoomService:
    """Create new instance per request"""
    return RoomService()