from fastapi import APIRouter, HTTPException, status, Depends
import logging
from pydantic import BaseModel

from app.services.recommendation_service import RecommendationService, get_recommendation_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recommendation", tags=["recommendations"])

class RecommendationRequest(BaseModel):
    user_id: str
    limit: int = 10

@router.post("")
async def get_matched_rooms(
    request: RecommendationRequest,
    rec_service_obj: RecommendationService = Depends(get_recommendation_service)
):
    try:
        return await rec_service_obj.find_best_match(user_id=request.user_id)
    except Exception as e:
        logger.error(f"Error in create_room endpoint: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get matches"
        )