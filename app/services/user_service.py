from google.cloud.firestore import Client,SERVER_TIMESTAMP
import logging

from app.db.firestore import get_firestore
from app.models.user import UserCreate

logger = logging.getLogger(__name__)

class UserService:
    def __init__(
          self  
    ):
        self._firestore: Client = get_firestore()
    
    def add_user(
            self,
            user: UserCreate
    ):
        try:
            user_data = user.model_dump()
            user_data['created_at'] = SERVER_TIMESTAMP
            doc_ref = self._firestore.collection('users').document()
            doc_ref.set(user_data)
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

        