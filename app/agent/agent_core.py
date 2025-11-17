from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langchain_google_vertexai import ChatVertexAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.prebuilt import ToolNode
import logging
import operator

from app.config import settings
from app.services.tools import get_available_tools

logger = logging.getLogger(__name__)

class AgentState(TypedDict):
    """State structure for the agent workflow"""
    messages: Annotated[list, operator.add]
    response: str
    user_id: str

SYSTEM_PROMPT = """You are HomieFinder, an intelligent and friendly Room Matching Assistant that helps users find their perfect room in the Greater Boston area.

Your primary capability:
- Finding rooms using advanced vector similarity search that matches user preferences with available rooms
- The search considers location, budget, room type, lifestyle preferences, and many other factors

IMPORTANT: The user_id is automatically provided with each request. You do NOT need to ask for it or mention it. When the user asks to find rooms, you can immediately call the find_matching_rooms tool using the user_id that's already available.

Available Tool:
find_matching_rooms - Searches for personalized room recommendations
   Required Parameter:
   - user_id: User's unique identifier (AUTOMATICALLY PROVIDED - use it directly)
   
   Optional Filters:
   - location: Boston area cities (Boston, Cambridge, Somerville, Allston, Brighton, Brookline, etc.)
   - max_rent: Maximum monthly rent in USD
   - room_type: "Shared", "Private", or "Studio"
   - flatmate_gender: "Male", "Female", "Mixed", or "Any"
   - attached_bathroom: "Yes", "No", or "Shared"
   - lease_duration_months: Preferred lease duration (1-24 months)
   - available_from: Date in YYYY-MM-DD format (e.g., "2025-01-01", "2025-06-15")
   - limit: Number of results (1-100, default 10)

How to interact with users:
1. Be friendly and conversational - you're helping people find their home!
2. Understand what the user is looking for through their message
3. When you understand their preferences, immediately call find_matching_rooms (user_id is already available)
4. The tool returns detailed room information - present it conversationally
5. Highlight key features that match what the user is looking for
6. Help users understand why certain rooms are good matches
7. Encourage them to contact the room owners directly
8. If the user wants to refine their search, ask clarifying questions and search again

Important Guidelines:
- NEVER ask for user_id - it's automatically provided
- Only use filters that the user explicitly mentions or clearly implies
- For locations, stick to Greater Boston area cities
- Be conversational - don't just dump data, explain what you're showing
- Help users refine their search if they're not satisfied with results
- The tool returns ALL room details including contact info, so present it clearly
- Point out lifestyle matches (vegetarian household, quiet study environment, etc.)
- Mention practical details like proximity to transit, utilities included, etc.
- If the user's query is vague, ask clarifying questions before searching

Remember: You're not just returning data - you're helping someone find their next home. Be warm, helpful, and personal!
"""

class AgentService:
    """Service for managing the AI agent workflow"""
    def __init__(self):
        """Initialize the agent service"""
        
        try:
            self.llm = ChatVertexAI(
                model_name=settings.gemini_model,
                project=settings.google_cloud_project,  # Fixed: was gcloud_project
                location=settings.vertex_ai_location,
                temperature=0.7,
                convert_system_message_to_human=True
            )
            logger.info(f"LLM Agent initialized with model: {settings.gemini_model}")
            self.tools = get_available_tools()
            self.llm_with_tools = self.llm.bind_tools(self.tools)
            self.agent = self._create_agent_graph()
            logger.info("Agent service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {str(e)}")
            raise

    def _should_continue(self, state: AgentState) -> str:
        """Determine whether to continue to tools or end"""
        messages = state["messages"]
        last_message = messages[-1]
        
        if not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
            return "end"
        else:
            return "continue"
    
    def _call_model(self, state: AgentState) -> AgentState:
        """Call the LLM with tools"""
        messages = state["messages"]
        user_id = state.get("user_id", "")
        
        # For Gemini, include system prompt and user_id context as human message
        context_content = f"{SYSTEM_PROMPT}\n\nCurrent user_id for this conversation: {user_id}\nUse this user_id when calling find_matching_rooms."
        context_message = HumanMessage(content=context_content)
        full_messages = [context_message] + messages
        
        # Get LLM response
        response = self.llm_with_tools.invoke(full_messages)
        
        return {"messages": [response]}
    
    def _process_tool_output(self, state: AgentState) -> AgentState:
        """Process the final response after tool execution"""
        messages = state["messages"]
        last_message = messages[-1]
        
        if isinstance(last_message, AIMessage):
            state["response"] = last_message.content
        
        return state

    def _create_agent_graph(self):
        """Creates a LangGraph with tool-calling capabilities"""
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("agent", self._call_model)
        workflow.add_node("tools", ToolNode(self.tools))
        workflow.add_node("process_output", self._process_tool_output)
        
        # Set entry point
        workflow.set_entry_point("agent")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "agent",
            self._should_continue,
            {
                "continue": "tools",
                "end": "process_output"
            }
        )
        
        # Add edge from tools back to agent
        workflow.add_edge("tools", "agent")
        workflow.add_edge("process_output", END)
        
        # Compile the graph
        return workflow.compile()

    def process_message(self, message: str, user_id: str) -> dict:
        """
        Process a user message through the agent
        
        Args:
            message: User's message
            user_id: User's unique identifier
        
        Returns:
            Dictionary containing the agent's response and metadata
        """
        try:
            logger.info(f"Processing message for user {user_id}: {message}")
            
            # Create initial state
            initial_state = {
                "messages": [HumanMessage(content=message)],
                "response": "",
                "user_id": user_id
            }
            
            # Run the agent
            result = self.agent.invoke(initial_state)
            
            logger.info(f"Agent response generated successfully for user {user_id}")
            
            # Extract tool usage information
            tools_used = []
            for msg in result["messages"]:
                if hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tools_used.append({
                            "tool": tool_call.get('name', 'unknown'),
                            "args": tool_call.get('args', {})
                        })
            
            return {
                "response": result["response"],
                "state": {
                    "message_count": len(result["messages"]),
                    "original_message": message,
                    "user_id": user_id,
                    "agent_type": "room_matching_assistant",
                    "model": settings.gemini_model
                },
                "tools_used": tools_used if tools_used else None
            }
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}", exc_info=True)
            raise

_agent_service = None

def get_agent_service() -> AgentService:
    """Get or create the agent service singleton"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service