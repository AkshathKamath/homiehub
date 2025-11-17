from fastapi import Depends, HTTPException, status
from typing import Optional
import logging
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import StateGraph

from app.agent.LLM.gemini import get_llm_client
from app.services.tool_regsitry import get_tool_registry
from app.agent.LLM.prompts import get_prompt_manager
from app.agent.graph import AgentGraphBuilder, create_agent_graph
from app.agent.components.state import StateManager

logger = logging.getLogger(__name__)

_graph_builder: Optional[AgentGraphBuilder] = None

def get_llm_client_dependency() -> ChatVertexAI:
    """
    Dependency for getting LLM client
    
    Returns:
        ChatVertexAI instance
        
    Raises:
        HTTPException: If LLM client not available
    """
    try:
        return get_llm_client()
    except Exception as e:
        logger.error(f"Failed to get LLM client: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable"
        )
    
def get_tool_registry_dependency():
    """
    Dependency for getting tool registry
    
    Returns:
        ToolRegistry instance
        
    Raises:
        HTTPException: If tool registry not available
    """
    try:
        return get_tool_registry()
    except Exception as e:
        logger.error(f"Failed to get tool registry: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tool service temporarily unavailable"
        )


def get_prompt_manager_dependency():
    """
    Dependency for getting prompt manager
    
    Returns:
        PromptManager instance
    """
    return get_prompt_manager()


def get_state_manager_dependency():
    """
    Dependency for getting state manager
    
    Returns:
        StateManager instance
    """
    return StateManager()

def get_agent_graph_builder(
    llm_client: ChatVertexAI = Depends(get_llm_client_dependency),
    tool_registry = Depends(get_tool_registry_dependency),
    prompt_manager = Depends(get_prompt_manager_dependency)
) -> AgentGraphBuilder:
    """
    Dependency for getting agent graph builder
    
    This is cached at application level to avoid recompiling the graph
    on every request.
    
    Args:
        llm_client: LLM client from dependency
        tool_registry: Tool registry from dependency
        prompt_manager: Prompt manager from dependency
        
    Returns:
        AgentGraphBuilder instance
    """
    global _graph_builder
    
    if _graph_builder is None:
        logger.info("Creating agent graph builder (first time)")
        _graph_builder = AgentGraphBuilder(
            llm_client=llm_client,
            tool_registry=tool_registry,
            prompt_manager=prompt_manager
        )
        # Build graph once
        _graph_builder.build()
    
    return _graph_builder

def get_agent_graph(
    graph_builder: AgentGraphBuilder = Depends(get_agent_graph_builder)
) -> StateGraph:
    """
    Dependency for getting compiled agent graph
    
    The graph itself is stateless and can be reused across requests.
    
    Args:
        graph_builder: Graph builder from dependency
        
    Returns:
        Compiled StateGraph
    """
    return graph_builder.get_graph()
