from typing import TypedDict, Annotated, List, Dict, Any
import operator
from datetime import datetime

from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    State structure for the agent workflow
    """
    messages: Annotated[List[BaseMessage], operator.add]
    response: Any  # ✅ allow dict JSON
    user_id: str
    metadata: Dict[str, Any]


class StateManager:
    """Utilities for managing agent state"""

    @staticmethod
    def create_initial_state(
        user_id: str,
        initial_message: BaseMessage,
        metadata: Dict[str, Any] = None
    ) -> AgentState:
        return AgentState(
            messages=[initial_message],
            response={},  # ✅ default to JSON
            user_id=user_id,
            metadata=metadata or {
                "created_at": datetime.utcnow().isoformat(),
                "request_count": 0
            }
        )

    @staticmethod
    def cleanup_state(state: AgentState, max_messages: int = 20) -> AgentState:
        if len(state["messages"]) > max_messages:
            state["messages"] = (
                [state["messages"][0]] +
                state["messages"][-(max_messages - 1):]
            )
        return state


def get_state_manager() -> StateManager:
    return StateManager()
