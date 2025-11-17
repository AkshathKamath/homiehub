from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_google_vertexai import ChatVertexAI
import logging
from typing import Optional

from app.agent.components.state import AgentState
from app.agent.components.nodes import AgentNodes, should_continue
from app.agent.LLM.prompts import PromptManager
from app.services.tool_regsitry import ToolRegistry

logger = logging.getLogger(__name__)

class AgentGraphBuilder:
    """Builds the agent workflow graph"""
    def __init__(
        self,
        llm_client: ChatVertexAI,
        tool_registry: ToolRegistry,
        prompt_manager: PromptManager
    ):
        """
        Initialize graph builder
        
        Args:
            llm_client: LLM client instance
            tool_registry: Tool registry instance
            prompt_manager: Prompt manager instance
        """
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.prompt_manager = prompt_manager
        self._compiled_graph: Optional[StateGraph] = None

    def build(self) -> StateGraph:
        """
        Build and compile the agent graph
        
        Returns:
            Compiled StateGraph
        """
        if self._compiled_graph is not None:
            logger.debug("Returning cached compiled graph")
            return self._compiled_graph
        
        logger.info("Building agent graph...")
        
        # Get tools in LangChain format
        tools = self.tool_registry.get_langchain_tools()
        
        # Bind tools to LLM
        llm_with_tools = self.llm_client.bind_tools(tools)
        
        # Create nodes
        agent_nodes = AgentNodes(llm_with_tools, self.prompt_manager)
        
        # Create workflow
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("agent", agent_nodes.call_model)
        workflow.add_node("tools", ToolNode(tools))
        workflow.add_node("process_output", agent_nodes.process_tool_output)

        # Set entry point
        workflow.set_entry_point("agent")

        # Add conditional edges from agent
        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "continue": "tools",      # If agent wants to use tools
                "finish": "process_output" # If agent has final answer
            }
        )

        # After tools execute, go back to agent to process results
        workflow.add_edge("tools", "agent")

        # # Add edge from agent to tools
        # workflow.add_edge("agent", "process_output")

        # Add edge from process_output to END
        workflow.add_edge("process_output", END)

        self._compiled_graph = workflow.compile()

        logger.info("✓ Agent graph compiled successfully")
        return self._compiled_graph
    
    def get_graph(self) -> StateGraph:
        """
        Get the compiled graph (builds if not already built)
        
        Returns:
            Compiled StateGraph
        """
        if self._compiled_graph is None:
            return self.build()
        return self._compiled_graph

def create_agent_graph(
    llm_client: ChatVertexAI,
    tool_registry: ToolRegistry,
    prompt_manager: PromptManager
) -> StateGraph:
    """
    Convenience function to create agent graph
    
    Args:
        llm_client: LLM client instance
        tool_registry: Tool registry instance
        prompt_manager: Prompt manager instance
        
    Returns:
        Compiled StateGraph
    """
    builder = AgentGraphBuilder(llm_client, tool_registry, prompt_manager)
    return builder.build()