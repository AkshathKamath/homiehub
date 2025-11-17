from typing import Dict, List, Optional
import logging
import httpx
from langchain_core.tools import StructuredTool


logger = logging.getLogger(__name__)

class ToolRegistry:
    """Registry for managing agent tools"""
    
    def __init__(self):
        """Initialize tool registry"""
        self._http_client: Optional[httpx.Client] = None
    
    def initialize(self):
        """Initialize all tools (should be called at startup)"""
        logger.info("Initializing tool registry...")
        # Create shared HTTP client for all tools
        self._http_client = httpx.Client(
            timeout=30.0,
            limits=httpx.Limits(
                max_connections=100,
                max_keepalive_connections=20
            )
        )
        logger.info("✓ Tool registry initialized")

    def get_langchain_tools(self) -> List:
        """
        Get tools in LangChain format for binding to LLM
        
        Returns:
            List of tools for LangChain
        """
        from app.services.tools_setup.user_room_matching_tool import find_matching_rooms
        
        tools = [find_matching_rooms]
        
        logger.info(f"Returning {len(tools)} function-based tools")
        return tools

    def shutdown(self):
        """Cleanup resources"""
        logger.info("Shutting down tool registry...")
        if self._http_client:
            self._http_client.close()
        logger.info("✓ Tool registry shutdown complete")

_registry: Optional[ToolRegistry] = None

def get_tool_registry() -> ToolRegistry:
    """Get or create tool registry singleton"""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        _registry.initialize()
    return _registry