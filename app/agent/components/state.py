from typing import TypedDict, Annotated, List, Dict, Any
import operator
from datetime import datetime
import json

from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    State structure for the agent workflow
    
    This state is created fresh for each request and contains
    all the context needed for the agent to process a conversation.
    """
    messages: Annotated[List[BaseMessage], operator.add]  # Message history
    response: str  # Final response to user
    user_id: str  # User identifier
    metadata: Dict[str, Any]  # Additional metadata

class StateManager:
    """Utilities for managing agent state"""
    
    @staticmethod
    def create_initial_state(
        user_id: str,
        initial_message: BaseMessage,
        metadata: Dict[str, Any] = None
    ) -> AgentState:
        """
        Create initial state for a new conversation
        
        Args:
            user_id: User identifier
            initial_message: First message in conversation
            metadata: Optional metadata
            
        Returns:
            Initial AgentState
        """
        return AgentState(
            messages=[initial_message],
            response="",
            user_id=user_id,
            metadata=metadata or {
                "created_at": datetime.utcnow().isoformat(),
                "request_count": 0
            }
        )

    @staticmethod
    def cleanup_state(state: AgentState, max_messages: int = 20) -> AgentState:
        """
        Cleanup state by truncating old messages
        
        Args:
            state: AgentState to cleanup
            max_messages: Maximum number of messages to keep
            
        Returns:
            Cleaned up AgentState
        """
        if len(state["messages"]) > max_messages:
            # Keep first message (context) and most recent messages
            state["messages"] = (
                [state["messages"][0]] + 
                state["messages"][-(max_messages-1):]
            )
        return state

def get_state_manager() -> StateManager:
    """Get state manager instance"""
    return StateManager()