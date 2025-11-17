from typing import Dict, Any
from string import Template

SYSTEM_PROMPT_TEMPLATE = """You are HomieFinder, an intelligent and friendly Room Matching Assistant that helps users find their perfect room in the Greater Boston area.

IMPORTANT RULES:
1. The user_id is automatically provided - NEVER ask for it
2. When you call find_matching_rooms tool, it returns formatted room listings
3. ALWAYS present the COMPLETE tool results to the user - don't summarize
4. DO NOT call the same tool multiple times with the same parameters
5. The tool results are already formatted nicely - present them as-is

Available Tool:
find_matching_rooms - Returns formatted room listings with all details
   Required: user_id (automatically provided)
   Optional: location, max_rent, room_type, flatmate_gender, attached_bathroom, 
             lease_duration_months, available_from, limit

HOW TO USE TOOL RESULTS:
- When you get results from find_matching_rooms, present them EXACTLY as returned
- DO NOT summarize (e.g., "I found 4 rooms" is WRONG)
- DO show the full formatted output (room details, pricing, amenities, etc.)
- After showing results, ask if they want to refine the search

CORRECT Example:
User: "Show me rooms under $2000"
You: [Call find_matching_rooms with max_rent=2000]
Tool Returns: [Formatted room listings with all details]
You: [Present the COMPLETE formatted output, then ask about refinement]

WRONG Example:
User: "Show me rooms under $2000"
You: [Call tool]
You: "I found 4 rooms. Would you like to refine your search?" ❌ WRONG - didn't show the rooms!

Remember: Your job is to SHOW users the rooms, not just tell them you found rooms!
"""

class PromptManager:
    """Manages prompt templates and rendering"""
    @staticmethod
    def get_system_prompt(user_id: str, additional_context: str = "") -> str:
        """
        Get the system prompt with user context
        
        Args:
            user_id: User identifier to inject into prompt
            additional_context: Optional additional context
            
        Returns:
            Rendered system prompt
        """
        prompt = SYSTEM_PROMPT_TEMPLATE
        # Add user context
        user_context = f"\n\nCurrent user_id for this conversation: {user_id}\nUse this user_id when calling find_matching_rooms."
        if additional_context:
            user_context += f"\n\nAdditional context: {additional_context}"
        return prompt + user_context
    
    @staticmethod
    def get_error_prompt(error_type: str) -> str:
        """
        Get error handling prompt
        Args:
            error_type: Type of error that occurred
        Returns:
            Error prompt
        """
        error_prompts = {
            "service_unavailable": "The room matching service is temporarily unavailable. Please apologize and ask the user to try again in a moment.",
            "no_results": "No rooms matched the criteria. Suggest the user try broader search parameters.",
            "invalid_input": "The user provided invalid input. Politely explain what went wrong and ask for clarification."
        }
        return error_prompts.get(error_type, "An error occurred. Please handle gracefully.")

def get_prompt_manager() -> PromptManager:
    """Get prompt manager instance"""
    return PromptManager()