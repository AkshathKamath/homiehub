from google.cloud.firestore import AsyncClient, SERVER_TIMESTAMP
from google.cloud.firestore_v1.vector import Vector
import logging

from app.db.firestore import get_firestore
from app.models.user import UserCreate, UserLogin
from app.core.security import hash_password, verify_password, create_access_token
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
            if_exist = await self._firestore.collection('users').where("email", "==", user_data['email']).limit(1).get()
            if len(if_exist) > 0:
                logger.warning(f"User with email {user_data['email']} already exists.")
                return {
                    "message": "User with this email already exists."
                }
            user_data['password'] = hash_password(user_data['password'])
            user_data['move_in_date'] = user_data['move_in_date'].isoformat()
            user_data['created_at'] = SERVER_TIMESTAMP
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
    
    async def authenticate_user(
            self,
            user: UserLogin
    ):
        try:
            query = self._firestore.collection('users').where("email", "==", user.email).limit(1)
            docs = await query.get()
            if len(docs) == 0:
                logger.warning(f"Authentication failed for email: {user.email}")
                return {
                    "message": "Invalid email or password"
                }
            user_doc = docs[0]
            user_data = user_doc.to_dict()
            if not verify_password(user.password, user_data['password']):
                logger.warning(f"Authentication failed for email: {user.email}")
                return {
                    "message": "Invalid email or password"
                }
            token_data = {
                "user_id": user_doc.id
            }
            access_token = create_access_token(token_data)
            logger.info(f"User authenticated: {user.email}")
            return {
                "access_token": access_token,
                "token_type": "bearer"
            }
        
        except Exception as e:
            logger.error(f"Authentication error for email {user.email}: {str(e)}", exc_info=True)
            raise

def get_user_service() -> UserService:
    """Create new instance per request"""
    return UserService()

        