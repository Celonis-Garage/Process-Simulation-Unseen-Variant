"""
Action schemas for process simulation modifications.
Defines all possible actions that can be performed on a process model.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from enum import Enum


class ActionType(str, Enum):
    """All supported process modification actions."""
    # Structure actions
    ADD_STEP = "add_step"
    REMOVE_STEP = "remove_step"
    RENAME_ACTIVITY = "rename_activity"
    REORDER = "reorder"
    DUPLICATE_ACTIVITY = "duplicate_activity"
    MERGE_ACTIVITIES = "merge_activities"
    SPLIT_ACTIVITY = "split_activity"
    
    # Flow control
    ADD_GATEWAY = "add_gateway"
    MAKE_PARALLEL = "make_parallel"
    MAKE_SEQUENTIAL = "make_sequential"
    ADD_CONDITIONAL = "add_conditional"
    ADD_LOOP = "add_loop"
    
    # KPI modifications
    MODIFY_KPI = "modify_kpi"
    MODIFY_TIME = "modify_time"
    MODIFY_COST = "modify_cost"
    MODIFY_PROBABILITY = "modify_probability"
    SET_SLA = "set_sla"
    
    # Resources
    ASSIGN_RESOURCE = "assign_resource"
    SET_RESOURCE_CAPACITY = "set_resource_capacity"
    
    # Simulation config
    SET_ARRIVAL_RATE = "set_arrival_rate"
    SET_WORKING_HOURS = "set_working_hours"
    
    # Meta actions
    CREATE_VARIANT = "create_variant"
    WHAT_IF_ANALYSIS = "what_if_analysis"
    CLARIFICATION_NEEDED = "clarification_needed"


class GatewayType(str, Enum):
    """Types of process gateways."""
    XOR = "xor"  # Exclusive OR (decision)
    AND = "and"  # Parallel gateway
    OR = "or"    # Inclusive OR


class ProcessAction(BaseModel):
    """
    Structured representation of a process modification action.
    Compatible with existing frontend expectations while extensible.
    """
    action: str  # Use string instead of ActionType for backward compatibility
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)
    
    # Activity-related fields (existing fields)
    activity: Optional[str] = None
    new_activity: Optional[str] = None
    activities: Optional[List[str]] = None
    position: Optional[Dict[str, str]] = None  # {"before": "X"} or {"after": "Y"}
    modifications: Optional[Dict[str, Any]] = None  # For KPI changes
    
    # Gateway fields (new)
    gateway_type: Optional[str] = None
    condition: Optional[str] = None
    
    # KPI modifications (new, more structured)
    time_value: Optional[float] = None
    time_unit: Optional[str] = None  # hours, minutes, days
    cost_value: Optional[float] = None
    probability: Optional[float] = None
    
    # Resource fields (new)
    resource_name: Optional[str] = None
    resource_capacity: Optional[int] = None
    
    # Meta fields
    explanation: Optional[str] = None
    message: Optional[str] = None  # For clarification_needed
    clarification_message: Optional[str] = None
    suggestions: Optional[List[str]] = None
    
    class Config:
        use_enum_values = True


# Backward compatibility helper
def to_legacy_format(action: ProcessAction) -> Dict[str, Any]:
    """
    Convert ProcessAction to legacy format expected by current frontend.
    """
    result = {
        "action": action.action,
    }
    
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
    if action.message or action.clarification_message:
        result["message"] = action.message or action.clarification_message
    if action.suggestions:
        result["suggestions"] = action.suggestions
    
    return result

