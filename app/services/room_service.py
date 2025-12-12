from google.cloud.firestore import AsyncClient, SERVER_TIMESTAMP, FieldFilter
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
            user_id: str,
            room: RoomCreate
    ):
        try:
            room_data = room.model_dump()
            
            # Convert date to string for Firestore
            room_data['available_from'] = room_data['available_from'].isoformat()
            
            room_data['created_at'] = SERVER_TIMESTAMP
            room_data['created_by_user'] = user_id

            doc_ref = self._firestore.collection('rooms').document()
            await doc_ref.set(room_data)
            logger.info(f"Room created with ID: {doc_ref.id}")
            return {
                "id": doc_ref.id,
                "message": "Room created successfully",
                "created_by_user": user_id
            }
        except Exception as e:
            logger.error(f"Failed to create room: {str(e)}", exc_info=True)
            raise
    
    async def get_room(
            self,
            user_id: str
    ) -> dict:
        """
        Get the room created by a specific user
        
        Assumes one user creates one room (primary room listing).
        If user has multiple rooms, returns the most recent one.
        
        Args:
            user_id: User's ID
            
        Returns:
            Room data dictionary
            
        Raises:
            ValueError: If no room found for this user
        """
        try:
            rooms_ref = self._firestore.collection('rooms')
            query = rooms_ref.where(
                filter=FieldFilter('created_by_user', '==', user_id)
            )
            
            docs = await query.get()
            
            if not docs:
                logger.warning(f"No room found for user: {user_id}")
                return {"message": "No room found for this user."}
            
            # Get the first (most recent) room
            room_doc = docs[0]
            room_data = room_doc.to_dict()
            
            # Remove internal fields
            room_data.pop('room_vector', None)
            
            # Add room ID
            room_data['id'] = room_doc.id
            
            logger.info(f"Retrieved room {room_doc.id} for user {user_id}")
            
            return room_data
            
        except ValueError as e:
            logger.error(f"Room not found: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to get room for user {user_id}: {str(e)}", exc_info=True)
            raise
    
    async def delete_room_by_id(self, user_id: str, room_id: str) -> dict:
        try:
            doc_ref = self._firestore.collection("rooms").document(room_id)
            snap = await doc_ref.get()

            if not snap.exists:
                logger.warning(f"Room {room_id} not found for deletion")
                return {"message": "Room not found."}

            room_data = snap.to_dict() or {}
            created_by = room_data.get("created_by_user")

            if created_by != user_id:
                # user is trying to delete someone else's room_id
                logger.warning(f"User {user_id} unauthorized to delete room {room_id}")
                return {"message": "Unauthorized to delete this room."}

            await doc_ref.delete()

            logger.info(f"Deleted room {room_id} for user {user_id}")
            return {"id": room_id, "message": "Room deleted successfully"}

        except Exception as e:
            logger.error(f"Failed to delete room {room_id} for user {user_id}: {str(e)}", exc_info=True)
            raise


def get_room_service() -> RoomService:
    """Create new instance per request"""
    return RoomService()