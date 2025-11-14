from google.cloud.firestore import AsyncClient, SERVER_TIMESTAMP
from google.cloud.firestore_v1.vector import Vector
import logging

from app.db.firestore import get_firestore
from app.models.user import UserCreate
from app.core.vectorize_user import vectorize_user

logger = logging.getLogger(__name__)

class UserService:
    def __init__(
          self  
    ):
        self._firestore: AsyncClient = get_firestore()
    
    async def add_user(
            self,
            user: UserCreate
    ):
        try:
            user_data = user.model_dump()
            user_data['move_in_date'] = user_data['move_in_date'].isoformat()
            user_data['created_at'] = SERVER_TIMESTAMP
            # user_vector = vectorize_user(user_data=user_data)
            # user_data['user_vector'] = Vector(user_vector)
            doc_ref = self._firestore.collection('users').document()
            await doc_ref.set(user_data)
            logger.info(f"User created with ID: {doc_ref.id}")
            return {
            "id": doc_ref.id,
            "message": "User created successfully"
            }
        
        except Exception as e:
            logger.error(f"Failed to create user: {str(e)}", exc_info=True)
            raise


def get_user_service() -> UserService:
    """Create new instance per request"""
    return UserService()

        