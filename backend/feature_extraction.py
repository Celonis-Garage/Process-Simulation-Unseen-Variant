"""
Feature Extraction for Process Scenarios
Converts process graphs into 409-dimensional feature vectors for ML model input
"""

import numpy as np
import pandas as pd
import logging
from typing import Dict, List, Tuple, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# All unique events from O2C dataset (13 events)
ALL_EVENTS = [
    'Receive Customer Order',
    'Validate Customer Order',
    'Perform Credit Check',
    'Approve Order',
    'Schedule Order Fulfillment',
    'Generate Pick List',
    'Pack Items',
    'Generate Shipping Label',
    'Ship Order',
    'Generate Invoice',
    'Receive Payment',
    'Close Order',
    'Cancel Order'
]

# Feature dimensions
FREQ_MATRIX_DIM = 13 * 13  # 169
DURATION_MATRIX_DIM = 13 * 13  # 169
USER_VECTOR_DIM = 7  # 7
ITEMS_MATRIX_DIM = 24 * 2  # 48 (quantity + line total)
SUPPLIER_VECTOR_DIM = 16  # 16
TOTAL_FEATURE_DIM = FREQ_MATRIX_DIM + DURATION_MATRIX_DIM + USER_VECTOR_DIM + ITEMS_MATRIX_DIM + SUPPLIER_VECTOR_DIM  # 409


def build_transition_matrix_frequency(
    activities: List[str],
    edges: List[Dict]
) -> np.ndarray:
    """
    Build 13x13 transition matrix with arc frequencies
    
    Args:
        activities: List of activity names in the process
        edges: List of edges with 'from', 'to' keys
    
    Returns:
        Flattened 169-dim array
    """
    matrix = np.zeros((13, 13))
    
    # Map activity names to indices
    event_to_idx = {event: idx for idx, event in enumerate(ALL_EVENTS)}
    
    # Count transitions
    for edge in edges:
        from_activity = edge.get('from', '')
        to_activity = edge.get('to', '')
        
        if from_activity in event_to_idx and to_activity in event_to_idx:
            from_idx = event_to_idx[from_activity]
            to_idx = event_to_idx[to_activity]
            matrix[from_idx, to_idx] += 1
    
    return matrix.flatten()


def build_transition_matrix_duration(
    activities: List[str],
    edges: List[Dict]
) -> np.ndarray:
    """
    Build 13x13 transition matrix with arc durations (in minutes)
    
    Args:
        activities: List of activity names in the process
        edges: List of edges with 'from', 'to', 'duration_hours' or 'avgDays' keys
    
    Returns:
        Flattened 169-dim array
    """
    matrix = np.zeros((13, 13))
    
    # Map activity names to indices
    event_to_idx = {event: idx for idx, event in enumerate(ALL_EVENTS)}
    
    # Set durations (convert to minutes)
    for edge in edges:
        from_activity = edge.get('from', '')
        to_activity = edge.get('to', '')
        
        if from_activity in event_to_idx and to_activity in event_to_idx:
            from_idx = event_to_idx[from_activity]
            to_idx = event_to_idx[to_activity]
            
            # Try different duration keys
            duration_hours = edge.get('duration_hours', 0) or edge.get('avgDays', 0) * 24 or 0
            duration_minutes = duration_hours * 60
            
            matrix[from_idx, to_idx] = duration_minutes
    
    return matrix.flatten()


def build_user_vector(
    user_ids: List[str],
    num_users: int = 7
) -> np.ndarray:
    """
    Build 7x1 binary user vector
    
    Args:
        user_ids: List of formatted user IDs (e.g., 'U001', 'U002')
        num_users: Total number of users (default: 7)
    
    Returns:
        7-dim binary array
    """
    vector = np.zeros(num_users)
    for user_id in user_ids:
        # Extract numeric part from 'U001' format
        if isinstance(user_id, str) and user_id.startswith('U'):
            user_num = int(user_id[1:])
        else:
            user_num = int(user_id) if isinstance(user_id, (int, float)) else 0
        
        if 1 <= user_num <= num_users:
            vector[user_num - 1] = 1
    return vector


def build_items_matrix(
    items_data: List[Dict],
    num_items: int = 24
) -> np.ndarray:
    """
    Build 24x2 items matrix (quantity + line total)
    
    Args:
        items_data: List of dicts with 'item_id' (formatted like 'I001'), 'quantity', 'line_total'
        num_items: Total number of items (default: 24)
    
    Returns:
        Flattened 48-dim array (24 items × 2 columns)
    """
    matrix = np.zeros((num_items, 2))
    
    for item in items_data:
        item_id = item.get('item_id', 0)
        
        # Extract numeric part from 'I001' format
        if isinstance(item_id, str) and item_id.startswith('I'):
            item_num = int(item_id[1:])
        else:
            item_num = int(item_id) if isinstance(item_id, (int, float)) else 0
        
        if 1 <= item_num <= num_items:
            idx = item_num - 1
            matrix[idx, 0] = item.get('quantity', 0)
            matrix[idx, 1] = item.get('line_total', 0)
    
    return matrix.flatten()


def build_supplier_vector(
    supplier_ids: List[str],
    num_suppliers: int = 16
) -> np.ndarray:
    """
    Build 16x1 binary supplier vector
    
    Args:
        supplier_ids: List of formatted supplier IDs (e.g., 'S001', 'S002')
        num_suppliers: Total number of suppliers (default: 16)
    
    Returns:
        16-dim binary array
    """
    vector = np.zeros(num_suppliers)
    for supplier_id in supplier_ids:
        # Extract numeric part from 'S001' format
        if isinstance(supplier_id, str) and supplier_id.startswith('S'):
            supplier_num = int(supplier_id[1:])
        else:
            supplier_num = int(supplier_id) if isinstance(supplier_id, (int, float)) else 0
        
        if 1 <= supplier_num <= num_suppliers:
            vector[supplier_num - 1] = 1
    return vector


def extract_features_from_scenario(
    activities: List[str],
    edges: List[Dict],
    users_involved: List[str],
    items_involved: List[Dict],
    suppliers_involved: List[str],
    scalers: Optional[Dict] = None
) -> np.ndarray:
    """
    Extract complete 409-dimensional feature vector from a process scenario
    
    Args:
        activities: List of activity names
        edges: List of edges with 'from', 'to', and duration info
        users_involved: List of formatted user IDs (e.g., 'U001', 'U002')
        items_involved: List of item dicts with 'item_id', 'quantity', 'line_total'
        suppliers_involved: List of formatted supplier IDs (e.g., 'S001', 'S002')
        scalers: Optional dict of fitted scalers for normalization
    
    Returns:
        409-dimensional feature vector (scaled if scalers provided)
    """
    # Build individual feature components
    freq_matrix = build_transition_matrix_frequency(activities, edges)
    duration_matrix = build_transition_matrix_duration(activities, edges)
    user_vector = build_user_vector(users_involved)
    items_matrix = build_items_matrix(items_involved)
    supplier_vector = build_supplier_vector(suppliers_involved)
    
    # Split items matrix into quantity and line total
    items_qty = items_matrix[::2]  # Every other element (quantity)
    items_amt = items_matrix[1::2]  # Every other element (line total)
    
    # Apply scaling if scalers provided
    if scalers:
        freq_matrix_scaled = scalers['freq'].transform(freq_matrix.reshape(1, -1)).flatten()
        duration_matrix_scaled = scalers['duration'].transform(duration_matrix.reshape(1, -1)).flatten()
        user_vector_scaled = scalers['users'].transform(user_vector.reshape(1, -1)).flatten()
        items_qty_scaled = scalers['items_qty'].transform(items_qty.reshape(1, -1)).flatten()
        items_amt_scaled = scalers['items_amt'].transform(items_amt.reshape(1, -1)).flatten()
        supplier_vector_scaled = scalers['suppliers'].transform(supplier_vector.reshape(1, -1)).flatten()
        
        # Interleave items quantity and line total back together
        items_matrix_scaled = np.empty(48)
        items_matrix_scaled[::2] = items_qty_scaled
        items_matrix_scaled[1::2] = items_amt_scaled
        
        # Concatenate all scaled features
        feature_vector = np.concatenate([
            freq_matrix_scaled,
            duration_matrix_scaled,
            user_vector_scaled,
            items_matrix_scaled,
            supplier_vector_scaled
        ])
    else:
        # No scaling - just concatenate raw features
        feature_vector = np.concatenate([
            freq_matrix,
            duration_matrix,
            user_vector,
            items_matrix,
            supplier_vector
        ])
    
    assert feature_vector.shape[0] == TOTAL_FEATURE_DIM, \
        f"Feature vector dimension mismatch: {feature_vector.shape[0]} != {TOTAL_FEATURE_DIM}"
    
    return feature_vector


def extract_features_from_process_graph(
    process_graph: Dict,
    users_involved: List[int],
    items_involved: List[Dict],
    suppliers_involved: List[int],
    scalers: Optional[Dict] = None
) -> np.ndarray:
    """
    Convenience function to extract features from a process graph dict
    
    Args:
        process_graph: Dict with 'activities', 'edges' keys
        users_involved: List of user IDs
        items_involved: List of item dicts
        suppliers_involved: List of supplier IDs
        scalers: Optional dict of fitted scalers
    
    Returns:
        409-dimensional feature vector
    """
    activities = process_graph.get('activities', [])
    edges = process_graph.get('edges', [])
    
    return extract_features_from_scenario(
        activities,
        edges,
        users_involved,
        items_involved,
        suppliers_involved,
        scalers
    )


def parse_activity_duration(time_str: str) -> float:
    """
    Parse activity duration string to hours
    
    Args:
        time_str: Time string like "2h", "1.5d", "30m"
    
    Returns:
        Duration in hours
    """
    time_str = time_str.strip().lower()
    
    if 'h' in time_str:
        return float(time_str.replace('h', ''))
    elif 'd' in time_str:
        return float(time_str.replace('d', '')) * 24
    elif 'm' in time_str:
        return float(time_str.replace('m', '')) / 60
    else:
        # Try to parse as number (assume hours)
        try:
            return float(time_str)
        except ValueError:
            return 1.0  # Default


def enrich_edges_with_durations(
    activities: List[str],
    edges: List[Dict],
    activity_kpis: Dict[str, Dict]
) -> List[Dict]:
    """
    Add duration information to edges based on activity KPIs
    
    Args:
        activities: List of activity names
        edges: List of edges (may be missing duration info)
        activity_kpis: Dict mapping activity names to {'avg_time': hours, 'cost': dollars}
    
    Returns:
        List of edges enriched with duration_hours
    """
    enriched_edges = []
    
    for edge in edges:
        enriched_edge = edge.copy()
        
        # If duration not already set, use the 'to' activity's avg_time
        if 'duration_hours' not in enriched_edge and 'avgDays' not in enriched_edge:
            to_activity = edge.get('to', '')
            if to_activity in activity_kpis:
                enriched_edge['duration_hours'] = activity_kpis[to_activity].get('avg_time', 1.0)
            else:
                enriched_edge['duration_hours'] = 1.0
        
        enriched_edges.append(enriched_edge)
    
    return enriched_edges


def log_feature_summary(feature_vector: np.ndarray):
    """
    Log summary of extracted features for debugging
    
    Args:
        feature_vector: 409-dimensional feature vector
    """
    logger.info(f"Feature vector extracted: {feature_vector.shape}")
    logger.info(f"  Frequency matrix (169): [{feature_vector[0:3].round(3)}...{feature_vector[166:169].round(3)}]")
    logger.info(f"  Duration matrix (169): [{feature_vector[169:172].round(3)}...{feature_vector[335:338].round(3)}]")
    logger.info(f"  User vector (7): {feature_vector[338:345].round(3)}")
    logger.info(f"  Items matrix (48): [{feature_vector[345:348].round(3)}...{feature_vector[390:393].round(3)}]")
    logger.info(f"  Supplier vector (16): {feature_vector[393:409].round(3)}")

