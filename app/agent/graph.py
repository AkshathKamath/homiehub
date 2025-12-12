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
        self.llm_client = llm_client
        self.tool_registry = tool_registry
        self.prompt_manager = prompt_manager
        self._compiled_graph: Optional[StateGraph] = None

    def build(self) -> StateGraph:
        if self._compiled_graph is not None:
            return self._compiled_graph

        tools = self.tool_registry.get_langchain_tools()
        llm_with_tools = self.llm_client.bind_tools(tools)
        agent_nodes = AgentNodes(llm_with_tools, self.prompt_manager)

        workflow = StateGraph(AgentState)

        workflow.add_node("agent", agent_nodes.call_model)
        workflow.add_node("tools", ToolNode(tools))
        workflow.add_node("process_output", agent_nodes.process_tool_output)

        workflow.set_entry_point("agent")

        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "continue": "tools",
                "finish": "process_output"
            }
        )

        # ✅ IMPORTANT: after tools, DO NOT go back to agent
        workflow.add_edge("tools", "process_output")
        workflow.add_edge("process_output", END)

        self._compiled_graph = workflow.compile()
        return self._compiled_graph

    def get_graph(self) -> StateGraph:
        if self._compiled_graph is None:
            return self.build()
        return self._compiled_graph
