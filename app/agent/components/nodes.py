import logging
from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_vertexai import ChatVertexAI

from app.agent.LLM.prompts import PromptManager
from app.agent.components.state import AgentState

logger = logging.getLogger(__name__)

class AgentNodes:
    """Contains all node functions for the agent graph"""
    
    def __init__(self, llm_with_tools: ChatVertexAI, prompt_manager: PromptManager):
        """
        Initialize agent nodes
        
        Args:
            llm_with_tools: LLM client with tools bound
            prompt_manager: Prompt manager instance
        """
        self.llm_with_tools = llm_with_tools
        self.prompt_manager = prompt_manager
    
    def call_model(self, state: AgentState) -> AgentState:
        """
        Call the LLM with tools
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with LLM response
        """
        try:
            messages = state["messages"]
            user_id = state.get("user_id", "")
            
            # Get system prompt
            system_prompt = self.prompt_manager.get_system_prompt(user_id)
            
            # Check if we're processing tool results
            has_tool_results = False
            for msg in messages:
                if hasattr(msg, 'type') and msg.type == 'tool':
                    has_tool_results = True
                    break
            
            # If we have tool results, add instruction to show them
            if has_tool_results:
                system_prompt += "\n\nIMPORTANT: Tool results are below. Present them COMPLETELY to the user. Do not summarize."
            
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
        Process the final response after tool execution
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with final response
        """
        logger.info("=" * 60)
        logger.info("PROCESS_TOOL_OUTPUT NODE CALLED")
        logger.info("=" * 60)
        try:
            messages = state["messages"]
            logger.info(f"process_tool_output: State keys: {state.keys()}")
            logger.info(f"process_tool_output: Current response field: '{state.get('response', 'NOT SET')}'")
            logger.info(f"process_tool_output: Processing {len(messages)} messages")
            last_message = messages[-1]
            
            # Extract final response
            if isinstance(last_message, AIMessage):
                state["response"] = last_message.content
            else:
                state["response"] = "I'm sorry, I couldn't generate a proper response."
            
            logger.info("Processed tool output successfully")
            return state
            
        except Exception as e:
            logger.error(f"Error in process_tool_output node: {str(e)}", exc_info=True)
            state["response"] = "An error occurred while processing the response."
            return state

def should_continue(state: AgentState) -> str:
    """
    Determine whether to continue to tools or finish
    
    Args:
        state: Current agent state
        
    Returns:
        "continue" to call tools, "finish" to end
    """
    messages = state["messages"]
    
    if not messages:
        logger.warning("should_continue: No messages in state")
        return "finish"
    
    last_message = messages[-1]
    
    # Check if there are tool calls
    has_tool_calls = hasattr(last_message, 'tool_calls') and bool(last_message.tool_calls)
    
    logger.info(f"should_continue: Checking last message")
    logger.info(f"  Message type: {type(last_message).__name__}")
    logger.info(f"  Has tool_calls: {has_tool_calls}")
    
    if has_tool_calls:
        logger.info(f"  Tool calls: {last_message.tool_calls}")
        logger.info("  Decision: continue to tools")
        return "continue"
    else:
        logger.info("  Decision: finish (go to process_output)")
        return "finish"