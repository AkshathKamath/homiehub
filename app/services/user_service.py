from google.cloud.firestore import AsyncClient, SERVER_TIMESTAMP, DELETE_FIELD
from google.cloud.firestore_v1.vector import Vector
import logging

from app.db.firestore import get_firestore
from app.models.user import UserCreate, UserLogin, UserUpdate
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
    
    async def update_user(
    self,
    user_id: str,
    user_update: UserUpdate
) -> dict:
        """
        Update user profile and preferences
        
        Args:
            user_id: The user's document ID in Firestore
            user_update: UserUpdate model with fields to update
            
        Returns:
            Dictionary with success message and updated user data
            
        Raises:
            Exception: If user not found or update fails
        """
        try:
            # Get user document reference
            user_ref = self._firestore.collection('users').document(user_id)
            user_doc = await user_ref.get()
            
            # Check if user exists
            if not user_doc.exists:
                logger.warning(f"User not found: {user_id}")
                raise ValueError(f"User with ID {user_id} not found")
            
            # Convert update model to dict, excluding None values
            update_data = user_update.model_dump(exclude_none=True)
            
            # Convert date to ISO string if present
            if 'move_in_date' in update_data:
                update_data['move_in_date'] = update_data['move_in_date'].isoformat()
            
            # Add updated timestamp
            update_data['updated_at'] = SERVER_TIMESTAMP
            update_data['user_vector'] = DELETE_FIELD
        
            logger.info(f"Updating user {user_id} and removing vector for re-generation")
            
            # Log what's being updated
            logger.info(f"Updating user {user_id} with fields: {list(update_data.keys())}")
            
            # Update the document
            await user_ref.update(update_data)
            
            # Get updated user data
            updated_doc = await user_ref.get()
            
            logger.info(f"User {user_id} updated successfully")
            
            return {
                "user_id": user_id,
                "message": "User updated successfully",
            }
            
        except ValueError as e:
            # User not found
            logger.error(f"Validation error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {str(e)}", exc_info=True)
            raise
    
    async def get_user_by_id(
    self,
    user_id: str
) -> dict:
        """
        Get user profile by ID
        
        Args:
            user_id: The user's document ID
            
        Returns:
            User data without sensitive fields
        """
        try:
            user_ref = self._firestore.collection('users').document(user_id)
            user_doc = await user_ref.get()
            
            if not user_doc.exists:
                raise ValueError(f"User with ID {user_id} not found")
            
            user_data = user_doc.to_dict()
            
            # Remove sensitive fields
            user_data.pop('password', None)
            user_data.pop('user_vector', None)
            
            logger.info(f"Retrieved user profile: {user_id}")
            
            return user_data
            
        except ValueError as e:
            logger.error(f"User not found: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {str(e)}", exc_info=True)
            raise

def get_user_service() -> UserService:
    """Create new instance per request"""
    return UserService()

        