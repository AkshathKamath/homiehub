from fastapi import APIRouter, HTTPException, status, Depends
import logging

from app.services.user_service import UserService, get_user_service
from app.core.dependencies import get_current_user
from app.models.user import UserCreate, UserLogin, UserUpdate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    user_service_obj: UserService = Depends(get_user_service)
):
    """Create a new user"""
    try:
        return await user_service_obj.add_user(user=user)
    except Exception as e:
        logger.error(f"Error in create_user endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.post("/login", status_code=status.HTTP_200_OK)
async def login_user(
    user: UserLogin,
    user_service_obj: UserService = Depends(get_user_service)
):
    """Authenticate a user and return a JWT token"""
    try:
        return await user_service_obj.authenticate_user(user=user)
    except Exception as e:
        logger.error(f"Error in login_user endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate user"
        )

@router.patch("/me", status_code=status.HTTP_200_OK)
async def update_current_user(
    user_update: UserUpdate,
    current_user: dict = Depends(get_current_user),
    user_service_obj: UserService = Depends(get_user_service)
):
    """
    Update the authenticated user's profile and preferences
    
    Only updates fields that are provided in the request.
    Automatically re-vectorizes user if matching preferences change.
    
    Example request body:
    {
        "budget_max": 1800,
        "preferred_locations": ["Cambridge", "Somerville"],
        "lifestyle_food": "Vegetarian",
        "bio": "Updated bio text"
    }
    """
    try:
        user_id = current_user['user_id']
        logger.info(f"Update request for user: {user_id}")
        
        result = await user_service_obj.update_user(user_id, user_update)
        
        return result
        
    except ValueError as e:
        logger.error(f"User not found: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user profile"
        )