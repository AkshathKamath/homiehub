from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.responses import JSONResponse
import logging
from langgraph.graph import StateGraph
from langchain_core.messages import HumanMessage
from langchain_google_vertexai import ChatVertexAI
import time

from app.models.agent import AgentRequest, AgentResponse
from app.core.dependencies import (
    get_agent_graph,
    get_state_manager_dependency,
    get_llm_client_dependency
)
from app.agent.components.state import StateManager
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["llm-agent"])

@router.post("", response_model=AgentResponse, status_code=status.HTTP_200_OK)
async def chat_with_agent(
    request: AgentRequest,
    agent_graph: StateGraph = Depends(get_agent_graph),
    state_manager: StateManager = Depends(get_state_manager_dependency)
):
    """
    Main chat endpoint for conversational room matching
    
    This endpoint:
    1. Creates fresh state for the request
    2. Executes the agent graph
    3. Returns formatted response
    
    The agent graph and tools are shared across requests,
    but each request gets its own isolated state.
    """
    start_time = time.time()
    request_id = f"req_{int(time.time() * 1000)}"
    try:
        logger.info(f"[{request_id}] Processing chat request from user {request.user_id}")
        if not request.user_id or not request.user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="user_id is required and cannot be empty"
            )
        if not request.message or not request.message.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="message is required and cannot be empty"
            )
        # Create fresh state for this request
        initial_message = HumanMessage(content=request.message)
        initial_state = state_manager.create_initial_state(
            user_id=request.user_id,
            initial_message=initial_message,
            metadata={
                "request_id": request_id,
                "timestamp": time.time()
            }
        )
        # Execute agent graph
        logger.info(f"[{request_id}] Executing agent graph")
        result = agent_graph.invoke(initial_state)
        # Extract tool usage
        tools_used = []
        seen_tool_calls = set()  # Track unique tool calls
        
        for msg in result["messages"]:
            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                for tool_call in msg.tool_calls:
                    # Create unique identifier for this tool call
                    tool_id = tool_call.get('id')
                    
                    # Only add if we haven't seen this exact tool call before
                    if tool_id and tool_id not in seen_tool_calls:
                        seen_tool_calls.add(tool_id)
                        tools_used.append({
                            "tool": tool_call.get('name', 'unknown'),
                            "args": tool_call.get('args', {})
                        })
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        logger.info(
            f"[{request_id}] Request completed in {duration_ms}ms, "
            f"tools_used: {len(tools_used)}"
        )
        # Build response
        return AgentResponse(
            response=result["response"],
            state={
                "message_count": len(result["messages"]),
                "original_message": request.message,
                "user_id": request.user_id,
                "agent_type": "room_matching_assistant",
                "model": settings.gemini_model,
                "request_id": request_id,
                "duration_ms": duration_ms
            },
            tools_used=tools_used if tools_used else None
        )
    except HTTPException:
        raise
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            f"[{request_id}] Error processing request after {duration_ms}ms: {str(e)}",
            exc_info=True
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing request: {str(e)}"
        )

@router.post("/debug-llm")
async def test_llm(
    request: AgentRequest,
    llm_client: ChatVertexAI = Depends(get_llm_client_dependency)
):
    """Debug endpoint to test LLM directly"""
    try:
        response = llm_client.invoke([HumanMessage(content=request.message)])
        return {
            "success": True,
            "response": response.content,
            "type": type(response).__name__
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@router.post("/debug/test-graph")
async def test_graph(
    request: AgentRequest,
    agent_graph: StateGraph = Depends(get_agent_graph),
    state_manager: StateManager = Depends(get_state_manager_dependency)
):
    """Debug endpoint to test full graph execution with detailed logging"""
    try:
        logger.info(f"DEBUG: Starting graph test for user {request.user_id}")
        logger.info(f"DEBUG: Message: {request.message}")
        
        # Create initial state
        initial_message = HumanMessage(content=request.message)
        initial_state = state_manager.create_initial_state(
            user_id=request.user_id,
            initial_message=initial_message,
            metadata={"debug": True}
        )
        
        logger.info(f"DEBUG: Initial state created")
        logger.info(f"DEBUG: Initial state keys: {initial_state.keys()}")
        logger.info(f"DEBUG: Initial messages count: {len(initial_state['messages'])}")
        
        # Execute graph
        result = agent_graph.invoke(initial_state)
        
        logger.info(f"DEBUG: Graph execution complete")
        logger.info(f"DEBUG: Result keys: {result.keys()}")
        logger.info(f"DEBUG: Final messages count: {len(result.get('messages', []))}")
        logger.info(f"DEBUG: Response field: '{result.get('response', 'EMPTY')}'")
        
        # Log each message
        for i, msg in enumerate(result.get("messages", [])):
            msg_type = type(msg).__name__
            msg_content = msg.content if hasattr(msg, 'content') else 'NO CONTENT'
            has_tool_calls = hasattr(msg, 'tool_calls') and bool(msg.tool_calls)
            
            logger.info(f"DEBUG: Message {i}:")
            logger.info(f"  Type: {msg_type}")
            logger.info(f"  Content: {msg_content[:200] if msg_content else 'NONE'}")
            logger.info(f"  Has tool calls: {has_tool_calls}")
            
            if has_tool_calls:
                logger.info(f"  Tool calls: {msg.tool_calls}")
        
        return {
            "success": True,
            "response": result.get("response", ""),
            "message_count": len(result.get("messages", [])),
            "messages_summary": [
                {
                    "index": i,
                    "type": type(msg).__name__,
                    "has_content": bool(msg.content) if hasattr(msg, 'content') else False,
                    "content_preview": msg.content[:100] if hasattr(msg, 'content') and msg.content else None,
                    "has_tool_calls": hasattr(msg, 'tool_calls') and bool(msg.tool_calls)
                }
                for i, msg in enumerate(result.get("messages", []))
            ],
            "final_response": result.get("response", "NO RESPONSE")
        }
        
    except Exception as e:
        logger.error(f"DEBUG: Error in test_graph: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }