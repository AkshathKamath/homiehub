# app/agent/LLM/prompts.py

SYSTEM_PROMPT_TEMPLATE = """You are HomieFinder, a Room Matching Assistant for Greater Boston.

IMPORTANT RULES:
1) user_id is automatically provided — NEVER ask for it.
2) Use find_matching_rooms when the user requests rooms or applies filters.
3) The tool accepts optional filters including lifestyle_smoke, lifestyle_alcohol, lifestyle_food.
4) Ask a clarifying question only if you cannot infer required filters from the user's request.

LOCATION NORMALIZATION RULE (MANDATORY):
- ALWAYS normalize location names to Title Case before calling the tool.
- NEVER pass lowercase or uppercase-only location strings.
- Location must ALWAYS be passed as a list of Title Case strings.

Examples:
- "cambridge" → ["Cambridge"]
- "CAMBRIDGE" → ["Cambridge"]
- "somerville" → ["Somerville"]
- "south end" → ["South End"]

CORRECT TOOL CALL EXAMPLE:
User: "Find me rooms in cambridge"
Tool args:
{
  "location": ["Cambridge"]
}

INCORRECT TOOL CALLS (DO NOT DO THIS):
- "location": "cambridge"
- "location": ["cambridge"]
- "location": ["CAMBRIDGE"]
"""

class PromptManager:
    """Manages prompt templates and rendering"""
    @staticmethod
    def get_system_prompt(user_id: str, additional_context: str = "") -> str:
        prompt = SYSTEM_PROMPT_TEMPLATE
        user_context = (
            f"\n\nCurrent user_id for this conversation: {user_id}\n"
            f"Use this user_id when calling find_matching_rooms."
        )
        if additional_context:
            user_context += f"\n\nAdditional context: {additional_context}"
        return prompt + user_context

    @staticmethod
    def get_error_prompt(error_type: str) -> str:
        error_prompts = {
            "service_unavailable": "The room matching service is temporarily unavailable. Please try again.",
            "no_results": "No rooms matched. Try broader preferences.",
            "invalid_input": "Invalid input. Please clarify your preferences."
        }
        return error_prompts.get(error_type, "An error occurred.")

def get_prompt_manager() -> PromptManager:
    """Get prompt manager instance"""
    return PromptManager()
