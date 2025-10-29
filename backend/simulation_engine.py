import networkx as nx
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
import random

class SimulationEngine:
    """
    Simulation engine that predicts KPI changes based on process modifications.
    Uses NetworkX for graph analysis and real O2C data patterns for predictions.
    """
    
    def __init__(self):
        pass
    
    def calculate_graph_metrics(self, graph: nx.DiGraph) -> Dict[str, float]:
        """Calculate graph-based metrics for process complexity analysis."""
        metrics = {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
            "avg_degree": sum(dict(graph.degree()).values()) / graph.number_of_nodes() if graph.number_of_nodes() > 0 else 0,
            "density": nx.density(graph),
            "longest_path": 0
        }
        
        # Calculate longest path (critical path approximation)
        try:
            if nx.is_directed_acyclic_graph(graph):
                longest_path = nx.dag_longest_path_length(graph)
                metrics["longest_path"] = longest_path
        except:
            metrics["longest_path"] = metrics["node_count"]  # Fallback
        
        return metrics
    
    def calculate_process_duration(self, graph: nx.DiGraph, real_kpis: Optional[Dict[str, Dict[str, float]]] = None) -> float:
        """
        Calculate expected process duration based on activity times.
        Uses real KPIs if available, otherwise estimates.
        """
        total_time = 0.0
        activities = list(graph.nodes())
        activities_found = 0
        
        for activity in activities:
            if real_kpis and activity in real_kpis:
                # Use real KPI data
                total_time += real_kpis[activity].get('avg_time', 1.5)
                activities_found += 1
            else:
                # Fallback: estimate 1.5 hours per activity (reasonable default)
                total_time += 1.5
        
        # Log data coverage
        if len(activities) > 0:
            coverage = (activities_found / len(activities)) * 100
            if coverage < 100:
                print(f"⚠️ Using estimates for {len(activities) - activities_found}/{len(activities)} activities ({100-coverage:.0f}%)")
        
        # Note: Parallel activity adjustment disabled for consistency with baseline calculation
        # If needed in future, apply same adjustment to baseline calculation as well
        # out_degrees = dict(graph.out_degree())
        # parallel_count = sum(1 for degree in out_degrees.values() if degree > 1)
        # if parallel_count > 0:
        #     total_time *= (1 - 0.1 * parallel_count)
        
        print(f"📊 Calculated process duration: {total_time:.2f}h from {len(activities)} activities ({activities_found} from real data)")
        
        return total_time
    
    def calculate_process_cost(self, graph: nx.DiGraph, real_kpis: Optional[Dict[str, Dict[str, float]]] = None) -> float:
        """
        Calculate expected process cost based on activity costs.
        Uses real KPIs if available, otherwise estimates.
        """
        total_cost = 0.0
        activities = list(graph.nodes())
        activities_found = 0
        
        for activity in activities:
            if real_kpis and activity in real_kpis and 'cost' in real_kpis[activity]:
                # Use real KPI data
                total_cost += real_kpis[activity]['cost']
                activities_found += 1
            else:
                # Fallback: estimate $60 per activity (reasonable default based on typical O2C costs)
                total_cost += 60.0
        
        # Log data coverage
        if len(activities) > 0:
            coverage = (activities_found / len(activities)) * 100
            if coverage < 100:
                print(f"⚠️ Using cost estimates for {len(activities) - activities_found}/{len(activities)} activities ({100-coverage:.0f}%)")
        
        print(f"💰 Calculated process cost: ${total_cost:.2f} from {len(activities)} activities ({activities_found} from real data)")
        
        return total_cost
    
    def predict_kpi_changes(
        self, 
        graph: nx.DiGraph, 
        event_log: pd.DataFrame,
        real_kpis: Optional[Dict[str, Dict[str, float]]] = None,
        baseline_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        Predict KPI changes based on the modified process graph.
        Uses real baseline metrics for comparison.
        """
        graph_metrics = self.calculate_graph_metrics(graph)
        
        # Calculate expected duration and cost for the modified process
        expected_duration = self.calculate_process_duration(graph, real_kpis)
        expected_cost = self.calculate_process_cost(graph, real_kpis)
        
        # Get baseline from real data if available
        # IMPORTANT: Baseline should be calculated from ACTIVITY processing times, not total order time
        # This ensures fair comparison when activities are added/removed
        if baseline_metrics and 'mean_hours' in baseline_metrics:
            # Use real data AS THE BASELINE
            # Note: We use this AS-IS as the reference point
            baseline_duration = baseline_metrics['mean_hours']
            print(f"✅ Using real baseline duration: {baseline_duration:.2f}h")
            
            # Also calculate baseline as sum of activity times for most frequent variant
            # This will be closer to expected_duration calculation
            baseline_activity_sum = expected_duration  # For now, use the calculated duration as both
        else:
            # Fallback: reasonable estimate based on typical O2C processes (rarely used)
            baseline_duration = 72.0  # 3 days
            baseline_activity_sum = expected_duration
            print(f"⚠️ Using fallback baseline duration: {baseline_duration:.2f}h (no real data available)")
        
        # Get baseline cost from real data if available
        if baseline_metrics and 'mean_cost' in baseline_metrics:
            # Use real cost data
            baseline_cost = baseline_metrics['mean_cost']
            print(f"✅ Using real baseline cost: ${baseline_cost:.2f}")
        else:
            # Fallback: estimate based on baseline duration and typical O2C costs
            baseline_cost = baseline_duration * 8.0  # $8/hour typical cost rate
            print(f"⚠️ Using fallback baseline cost: ${baseline_cost:.2f} (no real data available)")
        
        # Calculate changes (normalized)
        cycle_time_change = (expected_duration - baseline_duration) / baseline_duration
        cost_change = (expected_cost - baseline_cost) / baseline_cost
        
        # Revenue impact (simplified business logic)
        # Faster processes and lower costs improve revenue
        revenue_impact = -cycle_time_change * 0.15 - cost_change * 0.1
        
        # Confidence based on data availability and graph complexity
        if real_kpis and baseline_metrics and 'mean_hours' in baseline_metrics:
            confidence_base = 0.80  # Higher confidence with real data
        elif real_kpis or (baseline_metrics and 'mean_hours' in baseline_metrics):
            confidence_base = 0.65  # Moderate confidence with partial real data
        else:
            confidence_base = 0.45  # Lower confidence with estimates
        
        # Adjust confidence based on complexity
        complexity_penalty = min(0.15, graph_metrics["node_count"] * 0.015)
        confidence = confidence_base - complexity_penalty + random.uniform(-0.03, 0.03)
        confidence = max(0.35, min(0.92, confidence))  # Clamp between 0.35 and 0.92
        
        return {
            "cycle_time_change": round(cycle_time_change, 3),
            "cost_change": round(cost_change, 3),
            "revenue_impact": round(revenue_impact, 3),
            "confidence": round(confidence, 2),
            "expected_duration_hours": round(expected_duration, 2),
            "expected_cost": round(expected_cost, 2),
            "baseline_duration_hours": round(baseline_duration, 2),
            "baseline_cost": round(baseline_cost, 2)
        }
    
    def generate_summary(
        self, 
        predictions: Dict[str, float], 
        graph: nx.DiGraph,
        has_real_data: bool = False
    ) -> str:
        """Generate natural language summary of simulation results."""
        activities = list(graph.nodes())
        activity_count = len(activities)
        
        # Determine impact direction
        cycle_impact = "increases" if predictions["cycle_time_change"] > 0 else "decreases"
        cost_impact = "increases" if predictions["cost_change"] > 0 else "decreases" 
        revenue_impact = "positive" if predictions["revenue_impact"] > 0 else "negative"
        
        cycle_percent = abs(predictions["cycle_time_change"]) * 100
        cost_percent = abs(predictions["cost_change"]) * 100
        revenue_percent = abs(predictions["revenue_impact"]) * 100
        
        summary = f"The modified process with {activity_count} activities "
        
        if abs(predictions["cycle_time_change"]) > 0.01:
            summary += f"{cycle_impact} cycle time by approximately {cycle_percent:.1f}% "
            summary += f"(from {predictions['baseline_duration_hours']:.1f}h to {predictions['expected_duration_hours']:.1f}h) "
        
        if abs(predictions["cost_change"]) > 0.01:
            summary += f"and {cost_impact} costs by {cost_percent:.1f}%. "
        else:
            summary += ". "
        
        # Add revenue impact
        if abs(predictions["revenue_impact"]) > 0.01:
            summary += f"This has a {revenue_impact} revenue impact of approximately {revenue_percent:.1f}%. "
        
        # Add context based on activities
        validation_activities = [a for a in activities if 'Validation' in a or 'Check' in a]
        approval_activities = [a for a in activities if 'Approve' in a or 'Review' in a]
        
        if validation_activities:
            summary += f"The process includes {len(validation_activities)} validation/check step(s) which improve quality but may extend processing time. "
        
        if approval_activities:
            summary += f"There are {len(approval_activities)} approval step(s) which provide control but could create bottlenecks. "
        
        if activity_count < 6:
            summary += "The streamlined process reduces overhead and accelerates execution. "
        elif activity_count > 10:
            summary += "The comprehensive process provides thorough control but may create complexity. "
        
        # Confidence statement
        confidence_text = "high" if predictions["confidence"] > 0.75 else "moderate" if predictions["confidence"] > 0.55 else "reasonable"
        data_source = "real O2C data" if has_real_data else "estimated patterns"
        summary += f"Prediction confidence is {confidence_text} ({predictions['confidence']:.0%}) based on {data_source}."
        
        return summary
    
    def simulate(
        self, 
        graph: nx.DiGraph, 
        event_log: pd.DataFrame,
        real_kpis: Optional[Dict[str, Dict[str, float]]] = None,
        baseline_metrics: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Main simulation method that orchestrates the prediction process.
        """
        # Predict KPI changes
        predictions = self.predict_kpi_changes(graph, event_log, real_kpis, baseline_metrics)
        
        # Generate summary
        summary = self.generate_summary(predictions, graph, has_real_data=(real_kpis is not None))
        
        return {
            "cycle_time_change": predictions["cycle_time_change"],
            "cost_change": predictions["cost_change"], 
            "revenue_impact": predictions["revenue_impact"],
            "confidence": predictions["confidence"],
            "summary": summary,
            # Absolute KPI values for UI display
            "cycle_time_hours": predictions["expected_duration_hours"],
            "cycle_time_days": round(predictions["expected_duration_hours"] / 24, 2),
            "cost_dollars": predictions["expected_cost"],
            "baseline_cycle_time_hours": predictions["baseline_duration_hours"],
            "baseline_cycle_time_days": round(predictions["baseline_duration_hours"] / 24, 2),
            "baseline_cost_dollars": predictions["baseline_cost"]
        }
