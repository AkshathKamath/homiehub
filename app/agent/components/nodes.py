import logging
import json
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_vertexai import ChatVertexAI

from app.agent.LLM.prompts import PromptManager
from app.agent.components.state import AgentState

logger = logging.getLogger(__name__)

class AgentNodes:
    """Contains all node functions for the agent graph"""

    def __init__(self, llm_with_tools: ChatVertexAI, prompt_manager: PromptManager):
        self.llm_with_tools = llm_with_tools
        self.prompt_manager = prompt_manager

    def call_model(self, state: AgentState) -> AgentState:
        """
        Call the LLM with tools enabled.
        Only used to decide tool calls OR provide a final non-tool response.
        """
        try:
            messages = state["messages"]
            user_id = state.get("user_id", "")

            system_prompt = self.prompt_manager.get_system_prompt(user_id)

            context_message = HumanMessage(content=system_prompt)
            full_messages = [context_message] + messages

            logger.info(f"Calling LLM for user {user_id}")
            response = self.llm_with_tools.invoke(full_messages)

            state["metadata"]["request_count"] = state["metadata"].get("request_count", 0) + 1
            return {"messages": [response]}

        except Exception as e:
            logger.error(f"Error in call_model: {str(e)}", exc_info=True)
            error_msg = AIMessage(content=f"I encountered an error: {str(e)}")
            return {"messages": [error_msg]}

    def process_tool_output(self, state: AgentState) -> AgentState:
        """
        Final node:
        - If tool ran, return EXACT tool JSON (not LLM formatted text).
        - If no tool ran, return the LLM final message content.
        """
        logger.info("=" * 60)
        logger.info("PROCESS_TOOL_OUTPUT NODE CALLED")
        logger.info("=" * 60)

        try:
            messages = state["messages"]

            # Find most recent tool output
            last_tool_msg = None
            for msg in reversed(messages):
                if getattr(msg, "type", None) == "tool":
                    last_tool_msg = msg
                    break

            if last_tool_msg is None:
                # No tool output: use last AI message
                last_message = messages[-1] if messages else None
                if isinstance(last_message, AIMessage):
                    state["response"] = last_message.content
                else:
                    state["response"] = {"error": "no_tool_output_and_no_ai_message"}
                return state

            tool_content = last_tool_msg.content

            # Depending on serialization, tool_content can be dict or JSON string
            if isinstance(tool_content, dict):
                state["response"] = tool_content
            else:
                try:
                    state["response"] = json.loads(tool_content)
                except Exception:
                    state["response"] = tool_content  # fallback

            return state

        except Exception as e:
            logger.error(f"Error in process_tool_output node: {str(e)}", exc_info=True)
            state["response"] = {"error": "process_tool_output_failed", "detail": str(e)}
            return state


def should_continue(state: AgentState) -> str:
    """
    Determine whether to continue to tools or finish.
    """
    messages = state["messages"]

    if not messages:
        logger.warning("should_continue: No messages in state")
        return "finish"

    last_message = messages[-1]
    has_tool_calls = hasattr(last_message, "tool_calls") and bool(last_message.tool_calls)

    if has_tool_calls:
        return "continue"
    return "finish"
