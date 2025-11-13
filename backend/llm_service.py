"""
LLM service for parsing natural language prompts using Groq API.
"""

import os
import json
from pathlib import Path
from groq import Groq
from typing import Dict, Any, Optional, List
from action_schemas import ProcessAction, ActionType
from llm_prompts import SYSTEM_PROMPT, VARIANT_SELECTION_PROMPT, get_user_prompt, FALLBACK_SUGGESTIONS
import logging

logger = logging.getLogger(__name__)


class GroqLLMService:
    """Service for parsing process modification prompts using Groq LLM."""
    
    def __init__(self, api_key: Optional[str] = None, data_loader=None):
        """
        Initialize Groq LLM service.
        
        Args:
            api_key: Groq API key. If not provided, reads from GROQ_API_KEY env var.
            data_loader: RealDataLoader instance for fetching KPIs from data.
        """
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found. Please provide API key or set environment variable.")
        self.data_loader = data_loader
        
        self.client = Groq(api_key=self.api_key)
        # Use current Groq models: llama-3.3-70b-versatile (best), llama-3.1-8b-instant (fast), mixtral-8x7b-32768
        self.model = "llama-3.3-70b-versatile"
        
        # Load variant contexts for initial process selection
        self.variant_contexts = self._load_variant_contexts()
        variant_count = len(self.variant_contexts.get('variants', []))
        logger.info(f"Loaded {variant_count} process variant contexts")
        if variant_count > 0:
            logger.info(f"Variant IDs: {[v['variant_id'] for v in self.variant_contexts.get('variants', [])]}")
    
    def _load_variant_contexts(self) -> Dict[str, Any]:
        """Load pre-generated variant contexts from data file."""
        try:
            data_dir = Path(__file__).parent.parent / 'data'
            contexts_path = data_dir / 'variant_contexts.json'
            
            if not contexts_path.exists():
                logger.warning(f"Variant contexts file not found: {contexts_path}")
                return {"variants": []}
            
            with open(contexts_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading variant contexts: {e}")
            return {"variants": []}
        
    def parse_prompt(
        self, 
        user_prompt: str, 
        current_process: Optional[Dict[str, Any]] = None,
        conversation_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Parse user prompt using Groq LLM and return structured action.
        Handles both initial variant selection and process modifications.
        
        Args:
            user_prompt: User's natural language request
            current_process: Current process graph state (activities, edges, kpis)
            conversation_history: Optional previous messages for context
            
        Returns:
            Dictionary with action details (compatible with existing frontend)
        """
        if current_process is None:
            current_process = {"activities": [], "edges": [], "kpis": {}}
        
        # Check if this is an initial variant selection (empty process)
        is_initial_selection = len(current_process.get('activities', [])) == 0
        
        if is_initial_selection:
            logger.info(f"Initial variant selection requested: {user_prompt}")
            return self._select_initial_variant(user_prompt)
        
        # Otherwise, handle as a process modification
        logger.info(f"Process modification requested: {user_prompt}")
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
    
    def generate_event_narration(self, event_data: Dict[str, Any]) -> str:
        """
        Generate natural language narration for a simulation event.
        
        Args:
            event_data: Dictionary containing event details (event_name, timestamp, case_id, 
                       order_value, order_status, users, items, suppliers, etc.)
        
        Returns:
            Natural language narration string
        """
        try:
            # Extract item names from items list (only if relevant to this event)
            item_names = [item.get('name', 'Item') for item in event_data.get('items', [])]
            items_str = ', '.join(item_names) if item_names else None  # Show all items
            
            # Extract supplier names (only if relevant to this event)
            suppliers = event_data.get('suppliers', [])
            suppliers_str = ', '.join(suppliers) if suppliers else None  # Show all suppliers
            
            # Get the specific user for this event
            user = event_data.get('user', 'System')
            
            # Build ACTION-FOCUSED prompt - only show what's relevant to THIS specific event
            narration_prompt = f"""Generate 2-3 CRISP bullets focused on the ACTION happening RIGHT NOW. Only mention attributes DIRECTLY involved in this step.

Event: {event_data.get('event_name', 'Unknown Event')}
User: {user}"""

            # Add items ONLY if they exist and are relevant
            if items_str:
                narration_prompt += f"\nItems: {items_str}"
            
            # Add suppliers ONLY if they exist and are relevant
            if suppliers_str:
                narration_prompt += f"\nSuppliers: {suppliers_str}"

            narration_prompt += f"""

FOCUS ON: What action is being performed RIGHT NOW? What specific data is being processed?

FORMAT (2-3 bullets, action-focused):
• Action: [verb phrase describing what's happening]
• By: [user name only]
• Data: [only IF relevant to this specific action]

EXAMPLES:
For "Validate Customer Order":
• Action: Validating order accuracy
• By: Bob Smith

For "Pack Items":
• Action: Packing items for shipment
• By: Diana Lopez
• Items: Laptop, Mouse

For "Approve Order":
• Action: Performing credit approval
• By: Charlie Davis

YOUR OUTPUT (2-3 bullets, action-focused, NO extra words):"""

            # Call Groq API
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",  # Use faster model for real-time narration
                messages=[
                    {"role": "system", "content": "Output ONLY crisp bullet points focused on the CURRENT ACTION. Max 3 bullets. Show only attributes directly involved in THIS step."},
                    {"role": "user", "content": narration_prompt}
                ],
                temperature=0.2,  # Very low for consistency
                max_tokens=60  # Even more concise
            )
            
            narration = response.choices[0].message.content.strip()
            
            # Remove quotes if LLM wrapped the text
            if narration.startswith('"') and narration.endswith('"'):
                narration = narration[1:-1]
            
            logger.info(f"Generated narration for {event_data.get('event_name')}: {narration[:50]}...")
            return narration
            
        except Exception as e:
            logger.error(f"Error generating narration: {e}")
            # Fallback narration in bullet format (action-focused)
            event_name = event_data.get('event_name', 'Unknown Event')
            user = event_data.get('user', 'System')
            
            return f"• Action: {event_name}\n• By: {user}"
    
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
            
            # ✅ DUPLICATES ALLOWED: Users can add same activity multiple times (loops/rework)
            # The LLM prompts have been updated to handle this correctly
            if action.new_activity in current_activities:
                logger.info(f"✓ Allowing duplicate activity '{action.new_activity}' - creates loop/rework scenario")
            
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
            # Position validation happens later - allow duplicates here
        
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
    
    def _select_initial_variant(self, user_prompt: str) -> Dict[str, Any]:
        """
        Select an initial process variant based on user's description.
        Uses LLM to match user intent with pre-analyzed variant contexts.
        
        Args:
            user_prompt: User's description of desired process (e.g., "standard order", "rejected order")
            
        Returns:
            Dictionary with select_variant action and suggested next steps
        """
        try:
            # Build variant context summary for LLM
            variants_summary = []
            for v in self.variant_contexts.get('variants', []):
                variants_summary.append({
                    'variant_id': v['variant_id'],
                    'activities': v['event_sequence'],
                    'frequency': f"{v['frequency_percentage']}%",
                    'keywords': v.get('keywords', []),
                    'context': v['context']
                })
            
            # Create prompt for variant selection
            from llm_prompts import get_variant_selection_prompt
            prompt = get_variant_selection_prompt(user_prompt, variants_summary)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": VARIANT_SELECTION_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=600,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            logger.info(f"Variant selection LLM response: {response_text[:200]}...")
            
            result = json.loads(response_text)
            logger.info(f"Parsed JSON result: {json.dumps(result, indent=2)}")
            
            # Validate and enrich response
            selected_id = result.get('selected_variant_id')
            logger.info(f"Selected variant ID: {selected_id}")
            
            if selected_id:
                # Find the full variant data
                selected_variant = next(
                    (v for v in self.variant_contexts.get('variants', []) if v['variant_id'] == selected_id),
                    None
                )
                
                if selected_variant:
                    logger.info(f"Found variant {selected_id} with {len(selected_variant['event_sequence'])} activities")
                    
                    # Fetch real KPIs from data for this variant
                    activities = selected_variant['event_sequence']
                    kpis_data = {}
                    
                    if self.data_loader:
                        try:
                            # Get real KPIs from data
                            raw_kpis = self.data_loader.get_event_kpis_for_activities(activities)
                            logger.info(f"Fetched KPIs from data for {len(activities)} activities")
                            
                            # Format KPIs for frontend
                            for activity, vals in raw_kpis.items():
                                avg_time = vals.get('avg_time', 1.0)
                                cost = vals.get('cost', 50.0)
                                
                                # Format time string
                                if avg_time < 1:
                                    time_str = f"{round(avg_time * 60)}m"
                                elif avg_time < 24:
                                    time_str = f"{round(avg_time, 1)}h"
                                else:
                                    time_str = f"{round(avg_time / 24, 1)}d"
                                
                                kpis_data[activity] = {
                                    'avgTime': time_str,
                                    'avgCost': f"${cost:.2f}"
                                }
                            
                            logger.info(f"Formatted KPIs: {json.dumps(kpis_data, indent=2)}")
                        except Exception as e:
                            logger.error(f"Failed to fetch KPIs from data: {e}")
                            # Will use empty dict, frontend will use defaults
                    
                    response_data = {
                        'action': 'select_variant',
                        'variant_id': selected_id,
                        'activities': activities,
                        'kpis': kpis_data,  # Include real KPIs from data
                        'explanation': result.get('explanation', ''),
                        'confidence': result.get('confidence', 0.8),
                        'suggested_prompts': result.get('suggested_prompts', [
                            "Add a quality check step after packing",
                            "Change the invoice generation time to 1 hour",
                            "Remove the credit check step"
                        ])
                    }
                    logger.info(f"Returning variant selection with KPIs: {json.dumps(response_data, indent=2)}")
                    return response_data
                else:
                    logger.warning(f"Variant {selected_id} not found in variant_contexts")
            
            # Fallback if no valid variant selected
            return self._fallback_action(
                user_prompt,
                "Could not match your request to a process variant. Please describe the type of order scenario you want (e.g., 'standard fulfillment', 'rejected order', 'order with discount')."
            )
            
        except Exception as e:
            logger.error(f"Error selecting variant: {e}")
            return self._fallback_action(user_prompt, f"Error selecting process variant: {str(e)}")
    
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

