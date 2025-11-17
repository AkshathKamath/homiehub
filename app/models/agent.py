from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class AgentRequest(BaseModel):
    """Request model for agent chat endpoint"""
    message: str = Field(
        ...,
        min_length=1,
        description="The user's message or query",
        examples=["Find me rooms in Cambridge under $1500"]
    )
    user_id: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Unique identifier for the user",
        examples=["N7BHzi80hxrkDeOBAzi7"]
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Find me quiet rooms in Cambridge for studying",
                "user_id": "N7BHzi80hxrkDeOBAzi7"
            }
        }


class AgentResponse(BaseModel):
    """Response model for agent chat endpoint"""
    response: str = Field(
        ...,
        description="The agent's conversational response"
    )
    state: Dict[str, Any] = Field(
        ...,
        description="Metadata about the conversation state"
    )
    tools_used: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="List of tools that were called during this interaction"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "I found 4 great rooms in Cambridge...",
                "state": {
                    "message_count": 5,
                    "original_message": "Find me rooms in Cambridge",
                    "user_id": "N7BHzi80hxrkDeOBAzi7",
                    "agent_type": "room_matching_assistant",
                    "model": "gemini-1.5-flash"
                },
                "tools_used": [
                    {
                        "tool": "find_matching_rooms",
                        "args": {
                            "user_id": "N7BHzi80hxrkDeOBAzi7",
                            "location": "Cambridge"
                        }
                    }
                ]
            }
        }


class RoomMatch(BaseModel):
    """Model for a matched room"""
    room_id: str
    room_data: Dict[str, Any]


class MatchingResponse(BaseModel):
    """Model for matching service response"""
    user_id: str
    matches: List[RoomMatch]
    total_results: int