import re
import networkx as nx
from typing import Dict, Any, List
import random

# Dataset activities - can be used for validation
common_activities = [
    "Receive Customer Order", "Validate Customer Order", "Perform Credit Check",
    "Approve Order", "Reject Order", "Schedule Order Fulfillment",
    "Generate Pick List", "Pack Items", "Generate Shipping Label",
    "Ship Order", "Generate Invoice", "Apply Discount", "Process Return Request"
]

def parse_prompt_mock(prompt: str) -> Dict[str, Any]:
    """
    Mock LLM prompt parser that converts natural language to structured process modifications.
    In a real system, this would use an actual LLM API.
    
    Args:
        prompt: Natural language prompt describing process changes
    
    Returns:
        Dictionary with action type and modification details
    """
    def clean_activity_name(text: str) -> str:
        """Extract and clean activity name from captured text"""
        # Remove quotes (single or double)
        text = re.sub(r"^['\"]|['\"]$", '', text.strip())
        # Remove 'step' or 'activity' suffix
        text = re.sub(r'\s+(?:step|activity)$', '', text, flags=re.IGNORECASE)
        return text.strip()
    
    prompt_lower = prompt.lower().strip()
    
    # Pattern matching for different types of modifications
    
    # ADD ACTIVITY patterns - match quoted strings or unquoted activity names
    add_patterns = [
        (r"add\s+['\"]([^'\"]+)['\"]?\s+step\s+after\s+['\"]([^'\"]+)['\"]", "after"),
        (r"add\s+['\"]([^'\"]+)['\"]?\s+after\s+['\"]([^'\"]+)['\"]", "after"),
        (r"insert\s+['\"]([^'\"]+)['\"]?\s+after\s+['\"]([^'\"]+)['\"]", "after"),
        (r"add\s+['\"]([^'\"]+)['\"]?\s+(?:step\s+)?before\s+['\"]([^'\"]+)['\"]", "before"),
        # Fallback patterns without quotes
        (r"add\s+(.+?)\s+step\s+after\s+(.+?)$", "after"),
        (r"add\s+(.+?)\s+after\s+(.+?)$", "after"),
    ]
    
    for pattern, position_type in add_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            # Extract from ORIGINAL prompt to preserve case
            original_match = re.search(pattern, prompt, re.IGNORECASE)
            if original_match:
                new_activity = clean_activity_name(original_match.group(1))
                reference_activity = clean_activity_name(original_match.group(2))
                
                return {
                    "action": "add_step",
                    "new_activity": new_activity,
                    "position": {position_type: reference_activity}
                }
    
    # REMOVE ACTIVITY patterns - handle quoted strings
    remove_patterns = [
        r"remove\s+['\"]([^'\"]+)['\"]",
        r"remove\s+(?:the\s+)?['\"]?([^'\"]+?)['\"]?(?:\s+step)?$",
        r"delete\s+['\"]?([^'\"]+?)['\"]?(?:\s+step)?$",
        r"eliminate\s+['\"]?([^'\"]+?)['\"]?(?:\s+step)?$",
    ]
    
    for pattern in remove_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            # Extract from ORIGINAL prompt to preserve case
            original_match = re.search(pattern, prompt, re.IGNORECASE)
            if original_match:
                activity_to_remove = clean_activity_name(original_match.group(1))
                return {
                    "action": "remove_step",
                    "activity": activity_to_remove
                }
    
    # MODIFY TIME/COST patterns
    time_patterns = [
        r"(?:increase|set|make)\s+([^.]+?)\s+time\s+to\s+(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|minutes?|mins?|days?)?",
        r"(?:decrease|reduce)\s+([^.]+?)\s+time\s+(?:by\s+)?(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|minutes?|mins?|days?)?",
        r"([^.]+?)\s+should\s+take\s+(\d+(?:\.\d+)?)\s*(?:hours?|hrs?|minutes?|mins?|days?)?"
    ]
    
    for pattern in time_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            activity = match.group(1).strip().title()
            time_value = float(match.group(2))
            
            # Convert to hours if other units specified
            if "minute" in prompt_lower or "min" in prompt_lower:
                time_value = time_value / 60
            elif "day" in prompt_lower:
                time_value = time_value * 24
            
            return {
                "action": "modify_kpi",
                "activity": activity,
                "modifications": {
                    "avg_time": time_value
                }
            }
    
    # COST modification patterns
    cost_patterns = [
        r"(?:increase|set|make)\s+([^.]+?)\s+cost\s+to\s+\$?(\d+(?:\.\d+)?)",
        r"(?:decrease|reduce)\s+([^.]+?)\s+cost\s+(?:by\s+)?\$?(\d+(?:\.\d+)?)",
        r"([^.]+?)\s+should\s+cost\s+\$?(\d+(?:\.\d+)?)"
    ]
    
    for pattern in cost_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            activity = match.group(1).strip().title()
            cost_value = float(match.group(2))
            
            return {
                "action": "modify_kpi",
                "activity": activity,
                "modifications": {
                    "cost": cost_value
                }
            }
    
    # PARALLEL/SEQUENTIAL flow patterns
    if "parallel" in prompt_lower or "simultaneously" in prompt_lower:
        parallel_match = re.search(r"make\s+([^.]+?)\s+and\s+([^.]+?)\s+(?:parallel|simultaneous)", prompt_lower)
        if parallel_match:
            activity1 = parallel_match.group(1).strip().title()
            activity2 = parallel_match.group(2).strip().title()
            return {
                "action": "make_parallel",
                "activities": [activity1, activity2]
            }
    
    # REORDER patterns
    reorder_patterns = [
        r"move\s+([^.]+?)\s+(?:before|prior to)\s+([^.]+)",
        r"put\s+([^.]+?)\s+(?:before|prior to)\s+([^.]+)",
        r"reorder\s+([^.]+?)\s+(?:before|prior to)\s+([^.]+)"
    ]
    
    for pattern in reorder_patterns:
        match = re.search(pattern, prompt_lower)
        if match:
            activity_to_move = match.group(1).strip().title()
            reference_activity = match.group(2).strip().title()
            return {
                "action": "reorder",
                "activity": activity_to_move,
                "position": {"before": reference_activity}
            }
    
    # If no specific patterns matched, try to extract activity names and guess intent
    # Using real O2C activity names from the dataset (defined at module level)
    mentioned_activities = []
    for activity in common_activities:
        if activity.lower() in prompt_lower:
            mentioned_activities.append(activity)
    
    # Default response for unrecognized prompts
    if mentioned_activities:
        # If activities are mentioned, assume it's an add request
        return {
            "action": "add_step",
            "new_activity": mentioned_activities[0],
            "position": {"after": "Receive Customer Order"}  # Default position - first activity in real O2C process
        }
    else:
        # Generic response for unclear prompts
        return {
            "action": "clarification_needed",
            "message": f"I'm not sure how to interpret '{prompt}'. Could you be more specific about what process change you'd like to make?",
            "suggestions": [
                "Add [activity] after [existing activity]",
                "Remove [activity] step", 
                "Increase [activity] time to [number] hours",
                "Make [activity1] and [activity2] parallel"
            ]
        }

def graph_to_networkx(process_graph) -> nx.DiGraph:
    """
    Convert a ProcessGraph pydantic model to a NetworkX DiGraph.
    
    Args:
        process_graph: ProcessGraph model with activities, edges, and kpis
    
    Returns:
        NetworkX DiGraph representation
    """
    graph = nx.DiGraph()
    
    # Add nodes with KPI attributes
    for activity in process_graph.activities:
        kpi_data = process_graph.kpis.get(activity, {})
        graph.add_node(activity, **kpi_data)
    
    # Add edges
    for edge in process_graph.edges:
        source = edge.get("from") or edge.get("source")
        target = edge.get("to") or edge.get("target")
        if source and target:
            graph.add_edge(source, target)
    
    return graph

def networkx_to_process_graph(graph: nx.DiGraph) -> Dict[str, Any]:
    """
    Convert a NetworkX DiGraph back to ProcessGraph format.
    
    Args:
        graph: NetworkX DiGraph
    
    Returns:
        Dictionary in ProcessGraph format
    """
    activities = list(graph.nodes())
    edges = [{"from": source, "to": target} for source, target in graph.edges()]
    
    # Extract KPI data from node attributes
    kpis = {}
    for node in graph.nodes(data=True):
        activity_name = node[0]
        attributes = node[1]
        if attributes:
            kpis[activity_name] = attributes
    
    return {
        "activities": activities,
        "edges": edges,
        "kpis": kpis
    }

def calculate_process_metrics(graph: nx.DiGraph) -> Dict[str, float]:
    """
    Calculate various process metrics from a NetworkX graph.
    
    Args:
        graph: NetworkX DiGraph representing the process
    
    Returns:
        Dictionary of calculated metrics
    """
    metrics = {}
    
    # Basic graph metrics
    metrics["activity_count"] = graph.number_of_nodes()
    metrics["connection_count"] = graph.number_of_edges()
    metrics["density"] = nx.density(graph)
    
    # Process flow metrics
    if graph.number_of_nodes() > 0:
        metrics["avg_degree"] = sum(dict(graph.degree()).values()) / graph.number_of_nodes()
    else:
        metrics["avg_degree"] = 0
    
    # Complexity metrics
    try:
        if nx.is_directed_acyclic_graph(graph):
            metrics["longest_path_length"] = nx.dag_longest_path_length(graph)
            metrics["critical_path"] = len(nx.dag_longest_path(graph))
        else:
            metrics["longest_path_length"] = 0
            metrics["critical_path"] = 0
    except:
        metrics["longest_path_length"] = 0
        metrics["critical_path"] = 0
    
    # Bottleneck analysis (simplified)
    in_degrees = dict(graph.in_degree())
    out_degrees = dict(graph.out_degree())
    
    metrics["potential_bottlenecks"] = len([node for node, degree in in_degrees.items() if degree > 1])
    metrics["parallel_activities"] = len([node for node, degree in out_degrees.items() if degree > 1])
    
    return metrics

def suggest_process_improvements(graph: nx.DiGraph, event_log_stats: Dict[str, Any] = None) -> List[str]:
    """
    Generate suggestions for process improvements based on graph structure and event log statistics.
    
    Args:
        graph: NetworkX DiGraph representing the process
        event_log_stats: Optional statistics from event log analysis
    
    Returns:
        List of improvement suggestions
    """
    suggestions = []
    metrics = calculate_process_metrics(graph)
    
    # Complexity-based suggestions
    if metrics["activity_count"] > 8:
        suggestions.append("Consider consolidating activities to reduce process complexity")
    
    if metrics["density"] < 0.3:
        suggestions.append("Process has low connectivity - consider adding parallel flows to improve efficiency")
    
    if metrics["potential_bottlenecks"] > 2:
        suggestions.append("Multiple convergence points detected - consider load balancing or parallel processing")
    
    # Structure-based suggestions
    activities = list(graph.nodes())
    
    if "Approval" in " ".join(activities) and metrics["activity_count"] > 6:
        suggestions.append("Consider implementing risk-based approval routing to reduce cycle time")
    
    if "Validation" not in " ".join(activities) and "Payment" in " ".join(activities):
        suggestions.append("Consider adding payment validation step to reduce errors and disputes")
    
    if metrics["parallel_activities"] == 0 and metrics["activity_count"] > 4:
        suggestions.append("No parallel activities detected - look for opportunities to parallelize independent tasks")
    
    # Event log based suggestions (if provided)
    if event_log_stats:
        if event_log_stats.get("avg_cycle_time", 0) > 10:
            suggestions.append("High cycle time detected - focus on reducing wait times between activities")
        
        if event_log_stats.get("cost_variance", 0) > 0.5:
            suggestions.append("High cost variance - consider standardizing activity costs and resource allocation")
    
    return suggestions[:5]  # Return top 5 suggestions
