"""
LLM service for parsing natural language prompts using Groq API.
"""

import os
import json
from groq import Groq
from typing import Dict, Any, Optional, List
from action_schemas import ProcessAction, ActionType
from llm_prompts import SYSTEM_PROMPT, get_user_prompt, FALLBACK_SUGGESTIONS
import logging

logger = logging.getLogger(__name__)


class GroqLLMService:
    """Service for parsing process modification prompts using Groq LLM."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Groq LLM service.
        
        Args:
            api_key: Groq API key. If not provided, reads from GROQ_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found. Please provide API key or set environment variable.")
        
        self.client = Groq(api_key=self.api_key)
        # Use current Groq models: llama-3.3-70b-versatile (best), llama-3.1-8b-instant (fast), mixtral-8x7b-32768
        self.model = "llama-3.3-70b-versatile"
        
    def parse_prompt(
        self, 
        user_prompt: str, 
        current_process: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Parse user prompt using Groq LLM and return structured action.
        
        Args:
            user_prompt: User's natural language request
            current_process: Current process graph state (activities, edges, kpis)
            conversation_history: Optional previous messages for context
            
        Returns:
            Dictionary with action details (compatible with existing frontend)
        """
        if current_process is None:
            # Default to empty process (in production, this should come from frontend/session)
            current_process = {"activities": [], "edges": [], "kpis": {}}
        
        # 🔴 DEBUG: Log what activities are in the current process
        logger.info(f"Current process activities: {current_process.get('activities', [])}")
        
        try:
            # Build messages
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT}
            ]
            
            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)
            
            # Add current user request with context
            user_message = get_user_prompt(user_prompt, current_process)
            messages.append({"role": "user", "content": user_message})
            
            logger.info(f"Sending prompt to Groq: {user_prompt}")
            
            # Call Groq API with JSON mode
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.1,  # Low temperature for consistency
                max_tokens=500,
                response_format={"type": "json_object"}  # Force JSON output
            )
            
            # Parse response
            response_text = response.choices[0].message.content
            logger.info(f"Groq response: {response_text}")
            
            # Parse JSON
            action_dict = json.loads(response_text)
            
            # Validate using Pydantic
            action = ProcessAction(**action_dict)
            
            # Convert to legacy format for backward compatibility (pass current_process for validation)
            result = self._to_legacy_format(action, current_process)
            
            logger.info(f"Parsed action: {result.get('action')} with confidence {action.confidence}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from LLM: {e}")
            logger.error(f"Response was: {response_text if 'response_text' in locals() else 'N/A'}")
            return self._fallback_action(user_prompt, "Could not parse response. Please rephrase your request.")
            
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return self._fallback_action(user_prompt, f"Error processing request: {str(e)}")
    
    def _to_legacy_format(self, action: ProcessAction, current_process: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert ProcessAction to format expected by existing frontend/backend.
        Maintains backward compatibility and validates action integrity.
        
        Args:
            action: The parsed action from LLM
            current_process: Current process state for validation
        """
        current_activities = current_process.get("activities", [])
        
        # VALIDATION: For add_step, ensure new_activity is provided and makes sense
        if action.action == "add_step":
            if not action.new_activity:
                return {
                    "action": "clarification_needed",
                    "message": "I need a clear activity name to add. What should the new step be called?",
                    "suggestions": FALLBACK_SUGGESTIONS
                }
            
            # 🔴 CRITICAL: Check if activity already exists in current process
            # If user says "change/set X time" and LLM wrongly returns add_step, catch it here
            logger.info(f"Checking if '{action.new_activity}' exists in current activities: {current_activities}")
            
            if action.new_activity in current_activities:
                logger.warning(f"⚠️ LLM returned add_step for existing activity '{action.new_activity}'! Blocking and returning clarification.")
                return {
                    "action": "clarification_needed",
                    "message": f"⚠️ '{action.new_activity}' already exists in the current process. Did you mean to MODIFY its time/cost instead of adding it?\n\n• To change time: 'Set {action.new_activity} time to X hours'\n• To change cost: 'Set {action.new_activity} cost to $X'\n• To add a different activity: Specify the new activity name",
                    "suggestions": [
                        f"Set {action.new_activity} time to [X] hours",
                        f"Set {action.new_activity} cost to $[X]",
                        "Add [new activity name] after [existing activity]"
                    ]
                }
            
            # ✅ STRICT VALIDATION: Reject activities not in dataset
            # Check if the new_activity is in the common activities list (dataset activities)
            from utils import common_activities
            if action.new_activity not in common_activities:
                return {
                    "action": "clarification_needed",
                    "message": f"'{action.new_activity}' is not in the current dataset activities list. For now, you can only add activities that exist in the dataset. Available activities: {', '.join(common_activities)}",
                    "suggestions": [
                        f"Add one of the existing activities: {', '.join(common_activities[:5])}...",
                        "Or specify which existing activity you want to work with"
                    ]
                }
            # Ensure we're not adding an activity that's supposed to be referenced
            if action.position:
                ref_activity = action.position.get("after") or action.position.get("before")
                if ref_activity and action.new_activity.lower() == ref_activity.lower():
                    return {
                        "action": "clarification_needed",
                        "message": f"It seems you want to add '{action.new_activity}', but that activity already exists in the process. Did you mean to add a different activity?",
                        "suggestions": FALLBACK_SUGGESTIONS
                    }
        
        result = {
            "action": action.action,
        }
        
        # Add fields that exist
        if action.activity:
            result["activity"] = action.activity
        if action.new_activity:
            result["new_activity"] = action.new_activity
        if action.activities:
            result["activities"] = action.activities
        if action.position:
            result["position"] = action.position
        if action.modifications:
            result["modifications"] = action.modifications
            
        # Handle time/cost modifications if using new format
        if action.time_value is not None and not action.modifications:
            result["modifications"] = {"avg_time": action.time_value}
        if action.cost_value is not None and not action.modifications:
            result["modifications"] = {"cost": action.cost_value}
            
        # Meta fields
        if action.message or action.clarification_message:
            result["message"] = action.message or action.clarification_message
        if action.suggestions:
            result["suggestions"] = action.suggestions
        if action.explanation:
            result["explanation"] = action.explanation
            
        return result
    
    def _fallback_action(self, prompt: str, error: str) -> Dict[str, Any]:
        """Return clarification action when parsing fails."""
        return {
            "action": "clarification_needed",
            "message": f"I couldn't understand that request. {error}",
            "suggestions": FALLBACK_SUGGESTIONS
        }
    
    def validate_action(
        self, 
        action_dict: Dict[str, Any], 
        current_process: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate if action can be executed on current process.
        
        Args:
            action_dict: Action dictionary
            current_process: Current process state
            
        Returns:
            (is_valid, error_message)
        """
        action_type = action_dict.get("action")
        activities = current_process.get("activities", [])
        
        # Validate activity exists for operations that require it
        if action_type in ["remove_step", "rename_activity", "modify_kpi", "reorder"]:
            activity = action_dict.get("activity")
            if activity and activity not in activities:
                # Try case-insensitive match
                activities_lower = {a.lower(): a for a in activities}
                if activity.lower() in activities_lower:
                    # Auto-correct case
                    action_dict["activity"] = activities_lower[activity.lower()]
                else:
                    return False, f"Activity '{activity}' not found in process. Available: {', '.join(activities)}"
        
        # Validate reference activity exists
        position = action_dict.get("position")
        if position:
            ref_activity = position.get("after") or position.get("before")
            if ref_activity and ref_activity not in activities:
                # Try case-insensitive match
                activities_lower = {a.lower(): a for a in activities}
                if ref_activity.lower() in activities_lower:
                    # Auto-correct case
                    if "after" in position:
                        position["after"] = activities_lower[ref_activity.lower()]
                    else:
                        position["before"] = activities_lower[ref_activity.lower()]
                else:
                    return False, f"Reference activity '{ref_activity}' not found. Available: {', '.join(activities)}"
        
        # Validate parallel activities exist
        if action_type == "make_parallel":
            parallel_activities = action_dict.get("activities", [])
            missing = [a for a in parallel_activities if a not in activities]
            if missing:
                return False, f"Activities not found: {', '.join(missing)}"
        
        # Validate numeric values
        modifications = action_dict.get("modifications", {})
        if "avg_time" in modifications and modifications["avg_time"] <= 0:
            return False, "Time value must be positive"
        if "cost" in modifications and modifications["cost"] < 0:
            return False, "Cost value cannot be negative"
        
        return True, None


# Global instance (can be initialized once)
_llm_service = None


def get_llm_service(api_key: Optional[str] = None) -> GroqLLMService:
    """
    Get or create LLM service singleton.
    
    Args:
        api_key: Optional API key override
        
    Returns:
        GroqLLMService instance
    """
    global _llm_service
    if _llm_service is None or api_key:
        _llm_service = GroqLLMService(api_key=api_key)
    return _llm_service

