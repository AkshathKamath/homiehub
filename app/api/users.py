from fastapi import APIRouter, HTTPException, status, Depends
import logging

from app.services.user_service import UserService, get_user_service
from app.models.user import UserCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users", tags=["users"])

@router.post("", status_code=status.HTTP_201_CREATED)
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