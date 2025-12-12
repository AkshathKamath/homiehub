from fastapi import APIRouter, HTTPException, status, Depends
import logging

from app.core.dependencies import get_current_user
from app.services.recommendation_service import RecommendationService, get_recommendation_service
from app.models.user import UserFilter, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendation", tags=["recommendations"])

@router.post("")
async def get_matched_rooms(
    user: UserFilter,
    current_user: dict = Depends(get_current_user),
    rec_service_obj: RecommendationService = Depends(get_recommendation_service)
):
    try:
        user_id = current_user['user_id']
        return await rec_service_obj.find_best_match(user_id=user_id, user=user)
    except Exception as e:
        logger.error(f"Error in create_room endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get matches"
        )

@router.post("/agent")
async def get_matched_rooms_agent(
    user: UserFilter,
    rec_service_obj: RecommendationService = Depends(get_recommendation_service)
):
    try:
        return await rec_service_obj.find_best_match(user_id=user.user_id, user=user)
    except Exception as e:
        logger.error(f"Error in create_room endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get matches"
        )

@router.post("/time", status_code=status.HTTP_200_OK)
async def get_rooms_by_availability(
    user: UserFilter,
    current_user: dict = Depends(get_current_user),
    rec_service_obj: RecommendationService = Depends(get_recommendation_service)
):
    """
    Get rooms sorted by availability date (soonest first)
    
    Returns rooms sorted by available_from in ascending order.
    Filters are applied but NO vector similarity matching.
    
    Use this when you want to find rooms available soonest.
    """
    try:
        user_id = current_user['user_id']
        return await rec_service_obj.find_rooms_by_availability(user_id=user_id, user=user)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error in get_rooms_by_availability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get rooms by availability"
        )

