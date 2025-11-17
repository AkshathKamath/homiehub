from langchain_google_vertexai import ChatVertexAI
from typing import Optional
import logging

from app.config import settings

logger = logging.getLogger(__name__)

class LLMClientManager:
    """Manages LLM client lifecycle and configuration"""
    
    _instance: Optional[ChatVertexAI] = None

    @classmethod
    def initialize(cls) -> None:
        """
        Initialize LLM client (should be called once at startup)
        
        Returns:
            Configured ChatVertexAI instance
        """
        if cls._instance is not None:
            logger.warning("LLM client already initialized, returning existing instance")
            return cls._instance
        try:
            logger.info(f"Initializing LLM client with model: {settings.gemini_model}")
            cls._instance = ChatVertexAI(
                model_name=settings.gemini_model,
                project=settings.google_cloud_project,  # Fixed: was gcloud_project
                location=settings.vertex_ai_location,
                temperature=0.7,
                max_retries=3
            )
            logger.info("✓ LLM client initialized successfully")
        except Exception as e:
            logger.error(f"✗ Failed to initialize LLM client: {str(e)}")
            raise
    
    @classmethod
    def get_client(cls) -> ChatVertexAI:
        """
        Get the initialized LLM client
        
        Returns:
            ChatVertexAI instance
            
        Raises:
            RuntimeError: If client not initialized
        """
        if cls._instance is None:
            raise RuntimeError(
                "LLM client not initialized. Call initialize() first."
            )
        return cls._instance

def get_llm_client() -> ChatVertexAI:
    """
    Convenience function to get LLM client

    Returns:
        ChatVertexAI instance
    """
    return LLMClientManager.get_client()