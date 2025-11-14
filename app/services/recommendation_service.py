from google.cloud.firestore import AsyncClient
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
import logging

from app.db.firestore import get_firestore

logger = logging.getLogger(__name__)

class RecommendationService:
    def __init__(
            self
    ):
        self._firestore: AsyncClient = get_firestore()
    
    async def find_best_match(
            self,
            user_id: str,
            limit: int = 10
    ):
        try:
            user_ref = self._firestore.collection('users').document(user_id)
            user_doc = await user_ref.get()
            user_data = user_doc.to_dict()
            query_vector = user_data['user_vector']
            vector_query = self._firestore.collection('rooms').find_nearest(
                vector_field='room_vector',
                query_vector=query_vector,
                distance_measure=DistanceMeasure.EUCLIDEAN,
                limit=limit
            )
            results = []
            async for doc in vector_query.stream():
                room_data = doc.to_dict()
                results.append({
                    'room_id': doc.id,
                    'room_data': room_data,
                    # Distance is automatically included by Firestore
                })
            return {
                'user_id': user_id,
                'matches': results,
                'total_results': len(results)
            }


        except Exception as e:
            logger.error(f"Failed to get matched rooms: {str(e)}", exc_info=True)
            raise

def get_recommendation_service() -> RecommendationService:
    """Create new instance per request"""
    return RecommendationService()