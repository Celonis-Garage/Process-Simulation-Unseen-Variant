import pandas as pd
import networkx as nx
from datetime import datetime, timedelta
import random
from typing import List, Dict, Any
import numpy as np

def generate_dummy_o2c_log(activities: List[str] = None, kpis: Dict[str, Dict[str, float]] = None, n_cases: int = 20) -> pd.DataFrame:
    """
    Generate synthetic Order-to-Cash event log data.
    
    Args:
        activities: List of activity names in the process
        kpis: Dictionary mapping activity names to their KPI values (avg_time, cost)
        n_cases: Number of cases to generate
    
    Returns:
        pandas.DataFrame with columns: Case ID, Activity, Timestamp, Throughput Time, Cost
    """
    
    # Default O2C activities if none provided
    if activities is None:
        activities = [
            "Order Received", 
            "Order Approved", 
            "Invoice Created", 
            "Payment Validation", 
            "Payment Received"
        ]
    
    # Default KPIs if none provided
    if kpis is None:
        kpis = {
            "Order Received": {"avg_time": 1.0, "cost": 5.0},
            "Order Approved": {"avg_time": 0.5, "cost": 3.0},
            "Invoice Created": {"avg_time": 1.0, "cost": 2.0},
            "Payment Validation": {"avg_time": 0.5, "cost": 4.0},
            "Payment Received": {"avg_time": 0.3, "cost": 1.0}
        }
    
    rows = []
    base_date = datetime(2025, 10, 1, 9, 0)  # Start from Oct 1, 2025
    
    for case_id in range(1, n_cases + 1):
        case_start_time = base_date + timedelta(days=random.randint(0, 30))
        current_time = case_start_time
        
        for activity in activities:
            # Get KPIs for this activity or use defaults
            activity_kpis = kpis.get(activity, {"avg_time": 1.0, "cost": 5.0})
            
            # Add some realistic variance to timing and costs
            base_time = activity_kpis.get("avg_time", 1.0)
            base_cost = activity_kpis.get("cost", 5.0)
            
            # Generate realistic variations (log-normal distribution for positive values)
            time_variance = np.random.lognormal(0, 0.3)  # 30% coefficient of variation
            cost_variance = np.random.lognormal(0, 0.2)  # 20% coefficient of variation
            
            throughput_time = round(base_time * time_variance, 2)
            cost = round(base_cost * cost_variance, 2)
            
            # Add some business logic variations
            if activity == "Order Approved":
                # Some orders might need extra approval time
                if random.random() < 0.2:  # 20% chance
                    throughput_time *= 3
                    cost *= 1.5
            
            elif activity == "Payment Validation":
                # Payment validation might fail and need retry
                if random.random() < 0.1:  # 10% chance
                    throughput_time *= 2
                    cost *= 1.8
            
            elif activity == "Payment Received":
                # Payment might come early or late
                time_factor = random.choice([0.5, 1.0, 1.0, 1.0, 2.0])  # Mostly normal, some early/late
                throughput_time *= time_factor
            
            rows.append({
                "Case ID": f"CASE_{case_id:03d}",
                "Activity": activity,
                "Timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "Throughput Time": throughput_time,
                "Cost": cost
            })
            
            # Move to next activity start time
            current_time += timedelta(hours=throughput_time)
    
    df = pd.DataFrame(rows)
    
    # Add some derived columns for analysis
    df['Day of Week'] = pd.to_datetime(df['Timestamp']).dt.day_name()
    df['Hour'] = pd.to_datetime(df['Timestamp']).dt.hour
    
    return df

def create_process_graph(activities: List[str]) -> nx.DiGraph:
    """
    Create a NetworkX directed graph from a list of activities.
    Assumes sequential flow for simplicity.
    
    Args:
        activities: List of activity names in order
    
    Returns:
        NetworkX DiGraph representing the process
    """
    graph = nx.DiGraph()
    
    # Add nodes
    for activity in activities:
        graph.add_node(activity)
    
    # Add edges (sequential flow)
    for i in range(len(activities) - 1):
        graph.add_edge(activities[i], activities[i + 1])
    
    return graph

def create_complex_process_graph(activities: List[str], parallel_activities: List[tuple] = None) -> nx.DiGraph:
    """
    Create a more complex process graph with potential parallel flows.
    
    Args:
        activities: List of all activity names
        parallel_activities: List of tuples indicating parallel activities [(start, end, [parallel_acts])]
    
    Returns:
        NetworkX DiGraph with parallel flows
    """
    graph = nx.DiGraph()
    
    # Add all nodes
    for activity in activities:
        graph.add_node(activity)
    
    # Create basic sequential flow
    for i in range(len(activities) - 1):
        graph.add_edge(activities[i], activities[i + 1])
    
    # Add parallel flows if specified
    if parallel_activities:
        for start_act, end_act, parallel_acts in parallel_activities:
            # Remove direct edge between start and end
            if graph.has_edge(start_act, end_act):
                graph.remove_edge(start_act, end_act)
            
            # Add parallel paths
            for parallel_act in parallel_acts:
                graph.add_edge(start_act, parallel_act)
                graph.add_edge(parallel_act, end_act)
    
    return graph

def generate_variant_comparison_data() -> Dict[str, Any]:
    """
    Generate comparison data for different O2C process variants.
    Used for similarity analysis in simulation.
    """
    variants = {
        "standard_o2c": {
            "activities": ["Order Received", "Order Approved", "Invoice Created", "Payment Received"],
            "description": "Standard Order-to-Cash process",
            "typical_cycle_time": 5.2,
            "typical_cost": 85.0,
            "sample_log": None
        },
        "validated_o2c": {
            "activities": ["Order Received", "Order Approved", "Invoice Created", "Payment Validation", "Payment Received"],
            "description": "O2C with payment validation step",
            "typical_cycle_time": 6.8,
            "typical_cost": 105.0,
            "sample_log": None
        },
        "express_o2c": {
            "activities": ["Order Received", "Invoice Created", "Payment Received"],
            "description": "Express O2C for trusted customers",
            "typical_cycle_time": 2.1,
            "typical_cost": 45.0,
            "sample_log": None
        }
    }
    
    # Generate sample logs for each variant
    for variant_name, variant_data in variants.items():
        variant_data["sample_log"] = generate_dummy_o2c_log(
            activities=variant_data["activities"],
            n_cases=10
        ).to_dict('records')
    
    return variants

def add_realistic_delays_and_bottlenecks(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add realistic delays and bottlenecks to the event log data.
    Simulates real-world process variations.
    """
    df_modified = df.copy()
    
    # Add Friday delays (people leaving early)
    friday_mask = df_modified['Day of Week'] == 'Friday'
    friday_afternoon_mask = friday_mask & (df_modified['Hour'] >= 15)
    df_modified.loc[friday_afternoon_mask, 'Throughput Time'] *= 1.5
    
    # Add Monday bottlenecks (catching up from weekend)
    monday_mask = df_modified['Day of Week'] == 'Monday'
    monday_morning_mask = monday_mask & (df_modified['Hour'] <= 11)
    df_modified.loc[monday_morning_mask, 'Throughput Time'] *= 1.3
    
    # Add end-of-month rush (more validation needed)
    timestamps = pd.to_datetime(df_modified['Timestamp'])
    end_of_month_mask = timestamps.dt.day >= 25
    validation_mask = df_modified['Activity'].str.contains('Validation|Approval')
    df_modified.loc[end_of_month_mask & validation_mask, 'Throughput Time'] *= 1.8
    df_modified.loc[end_of_month_mask & validation_mask, 'Cost'] *= 1.4
    
    return df_modified
