"""
USD Builder for O2C Process Visualization
Converts O2C event sequences into USD/GLTF 3D animations
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Tuple
from datetime import datetime
import logging


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types"""
    def default(self, obj):
        if isinstance(obj, (np.integer, np.int64)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)

logger = logging.getLogger(__name__)

def generate_dynamic_supplier_positions(supplier_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Dynamically generate positions for suppliers based on how many there are.
    Distributes them evenly along top (z=10) and bottom (z=-10) rows.
    
    Args:
        supplier_ids: List of supplier IDs to position
        
    Returns:
        Dictionary mapping supplier_id to position dict with x, y, z, label, country
    """
    positions = {}
    count = len(supplier_ids)
    
    # Distribute evenly between top and bottom
    top_count = (count + 1) // 2
    bottom_count = count - top_count
    
    # Calculate spacing to fit all suppliers (doubled from 32 to 64 for wider layout)
    x_range = 64  # From -32 to 32
    x_spacing = x_range / max(top_count, bottom_count) if count > 0 else 8
    x_start = -32
    
    # Load supplier data for labels and countries
    data_dir = Path(__file__).parent.parent / 'data'
    df_suppliers = pd.read_csv(data_dir / 'suppliers.csv')
    
    # Position top row
    for i, sid in enumerate(supplier_ids[:top_count]):
        supplier_info = df_suppliers[df_suppliers['supplier_id'] == sid]
        label = supplier_info['name'].iloc[0].split()[0] if len(supplier_info) > 0 else sid
        country = supplier_info['country'].iloc[0] if len(supplier_info) > 0 else 'USA'
        
        positions[sid] = {
            'x': x_start + i * x_spacing,
            'y': 0,
            'z': 10,  # Moved from 8 to 10 for wider scene
            'label': label[:15],  # Truncate long names
            'country': country
        }
    
    # Position bottom row
    for i, sid in enumerate(supplier_ids[top_count:]):
        supplier_info = df_suppliers[df_suppliers['supplier_id'] == sid]
        label = supplier_info['name'].iloc[0].split()[0] if len(supplier_info) > 0 else sid
        country = supplier_info['country'].iloc[0] if len(supplier_info) > 0 else 'USA'
        
        positions[sid] = {
            'x': x_start + i * x_spacing,
            'y': 0,
            'z': -10,  # Moved from -8 to -10 for wider scene
            'label': label[:15],
            'country': country
        }
    
    return positions

def generate_dynamic_activity_positions(activities: List[str], most_frequent_variant: List[str]) -> Dict[str, Dict[str, Any]]:
    """
    Dynamically generate positions for activities.
    Main flow activities go horizontally at z=0 in sequence order.
    True deviations (Reject, Discount, Returns) are positioned with rectangular box flow.
    
    Args:
        activities: All unique activities in this case (in order they appear)
        most_frequent_variant: Activities in the most frequent variant (reference)
        
    Returns:
        Dictionary mapping activity name to position dict with x, y, z, label, type
    """
    positions = {}
    
    # Position main flow horizontally (doubled spacing from 4 to 8)
    x_start = -36
    x_spacing = 8
    
    # Shorten common labels
    label_map = {
        'Receive Customer Order': 'Receive Order',
        'Validate Customer Order': 'Validate',
        'Perform Credit Check': 'Credit Check',
        'Approve Order': 'Approve',
        'Schedule Order Fulfillment': 'Schedule',
        'Generate Pick List': 'Pick List',
        'Pack Items': 'Pack',
        'Generate Shipping Label': 'Ship Label',
        'Ship Order': 'Ship',
        'Generate Invoice': 'Invoice',
        'Reject Order': 'Reject',
        'Apply Discount': 'Discount',
        'Process Return Request': 'Returns',
    }
    
    # Known deviation activities that should have rectangular box flow
    known_deviations = {'Reject Order', 'Apply Discount', 'Process Return Request'}
    
    # Separate main flow from true deviations
    main_flow_activities = [a for a in activities if a not in known_deviations]
    deviation_activities = [a for a in activities if a in known_deviations]
    
    # Position main flow activities in order
    for i, activity in enumerate(main_flow_activities):
        positions[activity] = {
            'x': x_start + i * x_spacing,
            'y': 0,
            'z': 0,
            'label': label_map.get(activity, activity[:12]),
            'type': 'main'
        }
    
    # Position deviations using rectangular box flow pattern
    # Place them BETWEEN relevant main events
    for dev_activity in deviation_activities:
        if dev_activity == 'Reject Order':
            # Between Approve and Schedule
            if 'Approve Order' in positions and 'Schedule Order Fulfillment' in positions:
                x_between = (positions['Approve Order']['x'] + positions['Schedule Order Fulfillment']['x']) / 2
                z_offset = -6  # Below main line (increased from -4 to -6 for wider layout)
            else:
                # Fallback if those events don't exist
                x_between = x_start + 2 * x_spacing
                z_offset = -6
                
        elif dev_activity == 'Apply Discount':
            # Between Schedule and Pick List
            if 'Schedule Order Fulfillment' in positions and 'Generate Pick List' in positions:
                x_between = (positions['Schedule Order Fulfillment']['x'] + positions['Generate Pick List']['x']) / 2
                z_offset = 6  # Above main line (increased from 4 to 6 for wider layout)
            else:
                x_between = x_start + 4 * x_spacing
                z_offset = 6
                
        elif dev_activity == 'Process Return Request':
            # Between Ship and Invoice
            if 'Ship Order' in positions and 'Generate Invoice' in positions:
                x_between = (positions['Ship Order']['x'] + positions['Generate Invoice']['x']) / 2
                z_offset = 6  # Above main line (increased from 4 to 6 for wider layout)
            else:
                x_between = x_start + 8 * x_spacing
                z_offset = 6
        else:
            # Unknown deviation - place at end
            x_between = x_start + len(main_flow_activities) * x_spacing
            z_offset = 6
        
        positions[dev_activity] = {
            'x': x_between,
            'y': 0,
            'z': z_offset,
            'label': label_map.get(dev_activity, dev_activity[:12]),
            'type': 'deviation'
        }
    
    return positions

# Location coordinates for the warehouse layout (in 3D space)
# Most frequent variant (10 activities) in a straight horizontal line at z=0
# Deviations positioned BETWEEN main events, creating rectangular box flow
# Spacing increased to 8 units between stations (was 4) for better visibility with 3x larger stations
LOCATIONS = {
    # Main flow - horizontal line (most frequent variant) - 8 unit spacing
    'Receive Customer Order': {'x': -36, 'y': 0, 'z': 0, 'label': 'Receive Order', 'type': 'main'},
    'Validate Customer Order': {'x': -28, 'y': 0, 'z': 0, 'label': 'Validate', 'type': 'main'},
    'Perform Credit Check': {'x': -20, 'y': 0, 'z': 0, 'label': 'Credit Check', 'type': 'main'},
    'Approve Order': {'x': -12, 'y': 0, 'z': 0, 'label': 'Approve', 'type': 'main'},
    'Schedule Order Fulfillment': {'x': -4, 'y': 0, 'z': 0, 'label': 'Schedule', 'type': 'main'},
    'Generate Pick List': {'x': 4, 'y': 0, 'z': 0, 'label': 'Pick List', 'type': 'main'},
    'Pack Items': {'x': 12, 'y': 0, 'z': 0, 'label': 'Pack', 'type': 'main'},
    'Generate Shipping Label': {'x': 20, 'y': 0, 'z': 0, 'label': 'Ship Label', 'type': 'main'},
    'Ship Order': {'x': 28, 'y': 0, 'z': 0, 'label': 'Ship', 'type': 'main'},
    'Generate Invoice': {'x': 36, 'y': 0, 'z': 0, 'label': 'Invoice', 'type': 'main'},
    
    # Deviations - positioned BETWEEN main events for rectangular box flow
    # Reject Order: Between Approve and Schedule (x=-8, between -12 and -4)
    'Reject Order': {'x': -8, 'y': 0, 'z': -6, 'label': 'Reject', 'type': 'deviation'},
    
    # Apply Discount: Between Schedule and Pick List (x=0, between -4 and 4)
    'Apply Discount': {'x': 0, 'y': 0, 'z': 6, 'label': 'Discount', 'type': 'deviation'},
    
    # Process Return Request: Between Ship and Invoice (x=32, between 28 and 36)
    'Process Return Request': {'x': 32, 'y': 0, 'z': 6, 'label': 'Returns', 'type': 'deviation'},
}

# Supplier location coordinates (arranged along top and bottom edges)
# Spacing adjusted to match wider layout (doubled from 4 to 8 units)
SUPPLIER_LOCATIONS = {
    # Top row (z = 10, moved further out for wider scene)
    'S001': {'x': -32, 'y': 0, 'z': 10, 'label': 'Global Office', 'country': 'USA'},
    'S002': {'x': -24, 'y': 0, 'z': 10, 'label': 'TechSource', 'country': 'USA'},
    'S003': {'x': -16, 'y': 0, 'z': 10, 'label': 'Premier Furn', 'country': 'USA'},
    'S004': {'x': -8, 'y': 0, 'z': 10, 'label': 'Pacific', 'country': 'China'},
    'S005': {'x': 0, 'y': 0, 'z': 10, 'label': 'EuroTech', 'country': 'Germany'},
    'S006': {'x': 8, 'y': 0, 'z': 10, 'label': 'Natl Print', 'country': 'USA'},
    'S007': {'x': 16, 'y': 0, 'z': 10, 'label': 'Asian Trade', 'country': 'Singapore'},
    'S008': {'x': 24, 'y': 0, 'z': 10, 'label': 'Metro Storage', 'country': 'USA'},
    # Bottom row (z = -10, moved further out for wider scene)
    'S009': {'x': -32, 'y': 0, 'z': -10, 'label': 'Nordic Furn', 'country': 'Sweden'},
    'S010': {'x': -24, 'y': 0, 'z': -10, 'label': 'Quantum', 'country': 'USA'},
    'S011': {'x': -16, 'y': 0, 'z': -10, 'label': 'MicroParts', 'country': 'Taiwan'},
    'S012': {'x': -8, 'y': 0, 'z': -10, 'label': 'Southern', 'country': 'USA'},
    'S013': {'x': 0, 'y': 0, 'z': -10, 'label': 'Global Net', 'country': 'UAE'},
    'S014': {'x': 8, 'y': 0, 'z': -10, 'label': 'Eco-Friendly', 'country': 'Canada'},
    'S015': {'x': 16, 'y': 0, 'z': -10, 'label': 'Premium Elec', 'country': 'Japan'},
    'S016': {'x': 24, 'y': 0, 'z': -10, 'label': 'FastShip', 'country': 'Mexico'},
}

# Category to color mapping for items
CATEGORY_COLORS = {
    'Electronics': '#3b82f6',      # Blue
    'Office Supplies': '#10b981',  # Green
    'Furniture': '#f59e0b',        # Amber
    'Printing': '#8b5cf6',         # Purple
    'Storage': '#ec4899',          # Pink
    'Accessories': '#06b6d4',      # Cyan
    'Others': '#6b7280',           # Gray
}


def get_item_supplier_mapping(case_id: str, data_dir: Path) -> Dict[str, str]:
    """
    Get mapping of items to suppliers for a specific order
    
    Args:
        case_id: Order ID
        data_dir: Path to data directory
        
    Returns:
        Dict mapping item_id to supplier_id
    """
    order_suppliers_path = data_dir / 'order_suppliers.csv'
    if not order_suppliers_path.exists():
        return {}
    
    df_order_suppliers = pd.read_csv(order_suppliers_path)
    order_suppliers = df_order_suppliers[df_order_suppliers['order_id'] == case_id]
    
    # Create item_id -> supplier_id mapping
    item_supplier_map = {}
    for _, row in order_suppliers.iterrows():
        item_supplier_map[row['item_id']] = row['supplier_id']
    
    return item_supplier_map


def generate_item_paths(
    items: List[Dict[str, Any]],
    item_supplier_map: Dict[str, str],
    keyframes: List[Dict[str, Any]],
    items_df: pd.DataFrame,
    activity_positions: Dict[str, Dict[str, Any]],
    supplier_positions: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Generate animation paths for items from suppliers to order sphere.
    Items converge at warehouse if it exists, otherwise at order approval point.
    
    Args:
        items: List of item dictionaries
        item_supplier_map: Mapping of item_id to supplier_id
        keyframes: Order event keyframes
        items_df: DataFrame with item information (for category lookup)
        activity_positions: Dynamic positions for activities
        supplier_positions: Dynamic positions for suppliers
        
    Returns:
        List of item path dictionaries with animation data
    """
    item_paths = []
    
    # Check if warehouse and pack events exist in this order
    has_warehouse = 'Generate Pick List' in activity_positions
    has_pack = 'Pack Items' in activity_positions
    has_approve = 'Approve Order' in activity_positions
    
    # Determine convergence point based on which events exist
    if has_warehouse:
        # Items converge at warehouse when order reaches there
        convergence_event = 'Generate Pick List'
        merge_event = 'Pack Items' if has_pack else 'Generate Pick List'
    elif has_approve:
        # Items converge after order approval if no warehouse
        convergence_event = 'Approve Order'
        merge_event = 'Approve Order'
    else:
        # Fallback to first event
        convergence_event = keyframes[0]['event'] if keyframes else None
        merge_event = convergence_event
    
    # Find convergence and merge times from keyframes
    convergence_time = 180.0  # Default
    merge_time = 240.0  # Default
    
    for kf in keyframes:
        if kf['event'] == convergence_event:
            convergence_time = kf['time']
        if kf['event'] == merge_event:
            merge_time = kf['time']
    
    # Get convergence and merge locations (where order sphere will be)
    convergence_loc = activity_positions.get(convergence_event, {'x': 0, 'y': 0, 'z': 0})
    merge_loc = activity_positions.get(merge_event, convergence_loc)
    
    for item in items:
        item_id = item.get('item_id', '')
        supplier_id = item_supplier_map.get(item_id, 'S001')
        
        # Get supplier location
        supplier_loc = supplier_positions.get(supplier_id, {'x': -18, 'y': 0, 'z': 0, 'label': supplier_id, 'country': 'USA'})
        
        # Get item category for color
        item_row = items_df[items_df['item_id'] == item_id]
        category = item_row['category'].iloc[0] if len(item_row) > 0 else 'Others'
        color = CATEGORY_COLORS.get(category, CATEGORY_COLORS['Others'])
        
        # Fixed transit time for all suppliers (so timing is consistent)
        transit_duration = 40.0  # 40 seconds transit time for all
        
        # Stagger departure times - 15 seconds between each item for clear separation
        item_offset = items.index(item) * 15  # 15 seconds between items
        departure_time = max(0, convergence_time - transit_duration - 60 + item_offset)
        arrival_time = departure_time + transit_duration
        
        # Label based on convergence type
        convergence_label = 'Warehouse' if has_warehouse else 'Order Approval'
        
        # Create item animation path
        item_path = {
            'item_id': item_id,
            'name': item.get('name', ''),
            'quantity': int(item.get('quantity', 1)),
            'category': category,
            'supplier_id': supplier_id,
            'supplier_name': supplier_loc.get('label', ''),
            'color': color,
            'keyframes': [
                {
                    'time': 0.0,
                    'position': [supplier_loc['x'], 0, supplier_loc['z']],
                    'label': f"At {supplier_loc.get('label', 'Supplier')}",
                    'status': 'waiting'
                },
                {
                    'time': departure_time,
                    'position': [supplier_loc['x'], 0, supplier_loc['z']],
                    'label': f"Departing from {supplier_loc.get('label', 'Supplier')}",
                    'status': 'in_transit'
                },
                {
                    'time': arrival_time,
                    'position': [convergence_loc['x'], 0, convergence_loc['z']],
                    'label': f'Arrived at {convergence_label}',
                    'status': 'arrived'
                },
                {
                    'time': merge_time - 2,
                    'position': [convergence_loc['x'], 0, convergence_loc['z']],
                    'label': 'Moving to Order',
                    'status': 'ready'
                },
                {
                    'time': merge_time,
                    'position': [merge_loc['x'], 0, merge_loc['z']],
                    'label': 'Merged with Order',
                    'status': 'merged'
                }
            ]
        }
        
        item_paths.append(item_path)
    
    return item_paths


def generate_gltf_for_case(
    case_id: str,
    events: List[Dict[str, Any]],
    order_info: Dict[str, Any],
    users: List[str],
    items: List[Dict[str, Any]],
    suppliers: List[str],
    kpis: Dict[str, float],
    export_dir: Path
) -> Tuple[str, Dict[str, Any]]:
    """
    Generate a GLTF-compatible JSON file for a single O2C case.
    
    Since USD Python libraries (pxr) may not be installed, we'll create a
    simplified JSON format that can be consumed by the Three.js frontend.
    
    Args:
        case_id: Order ID
        events: List of event dictionaries with 'event_name' and 'timestamp'
        order_info: Order metadata (value, status, etc.)
        users: List of user IDs involved
        items: List of item dictionaries
        suppliers: List of supplier IDs
        kpis: KPI values for this order
        export_dir: Directory to save the export
        
    Returns:
        Tuple of (file_path, metadata)
    """
    try:
        # Ensure export directory exists
        export_dir.mkdir(parents=True, exist_ok=True)
        
        # Get unique activities from this case
        unique_activities = []
        for event in events:
            event_name = event.get('event_name', event.get('Activity', ''))
            if event_name and event_name not in unique_activities:
                unique_activities.append(event_name)
        
        # Define most frequent variant (baseline O2C process)
        most_frequent_variant = [
            'Receive Customer Order',
            'Validate Customer Order',
            'Perform Credit Check',
            'Approve Order',
            'Schedule Order Fulfillment',
            'Generate Pick List',
            'Pack Items',
            'Generate Shipping Label',
            'Ship Order',
            'Generate Invoice'
        ]
        
        # Filter to only activities that actually exist in this case
        main_flow = [a for a in most_frequent_variant if a in unique_activities]
        
        # Generate dynamic activity positions
        activity_positions = generate_dynamic_activity_positions(unique_activities, main_flow)
        
        # Get unique suppliers and generate dynamic positions
        unique_suppliers = list(set(suppliers))
        supplier_positions = generate_dynamic_supplier_positions(unique_suppliers)
        
        # Parse events and create animation keyframes
        # First pass: collect all timestamps to find true min/max
        parsed_events = []
        for event in events:
            event_name = event.get('event_name', event.get('Activity', ''))
            timestamp = event.get('timestamp', event.get('Timestamp', None))
            
            if not event_name or event_name not in activity_positions:
                continue
                
            # Parse timestamp
            if isinstance(timestamp, str):
                try:
                    dt = pd.to_datetime(timestamp)
                except:
                    dt = datetime.now()
            else:
                dt = timestamp if timestamp else datetime.now()
            
            parsed_events.append({
                'name': event_name,
                'dt': dt,
                'loc': activity_positions[event_name]
            })
        
        # Find true min and max times
        if parsed_events:
            min_time = min(pe['dt'] for pe in parsed_events)
            max_time = max(pe['dt'] for pe in parsed_events)
        else:
            min_time = datetime.now()
            max_time = datetime.now()
        
        # Second pass: create keyframes with correct time offsets
        keyframes = []
        for pe in parsed_events:
            time_offset = (pe['dt'] - min_time).total_seconds()
            
            keyframes.append({
                'time': time_offset,
                'position': [pe['loc']['x'], pe['loc']['y'], pe['loc']['z']],
                'event': pe['name'],
                'label': pe['loc']['label'],
                'timestamp': pe['dt'].isoformat()
            })
        
        # Sort keyframes by time to ensure chronological order
        keyframes.sort(key=lambda kf: kf['time'])
        
        # Calculate total duration
        total_duration = (max_time - min_time).total_seconds() if max_time and min_time else 0
        
        # Load items dataframe and get item-supplier mapping
        data_dir = export_dir.parent.parent / 'data'
        items_csv_path = data_dir / 'items.csv'
        items_df = pd.read_csv(items_csv_path) if items_csv_path.exists() else pd.DataFrame()
        
        item_supplier_map = get_item_supplier_mapping(case_id, data_dir)
        
        # Generate item animation paths
        item_paths = generate_item_paths(items, item_supplier_map, keyframes, items_df, activity_positions, supplier_positions)
        
        # Build complete scene data (convert numpy types to native Python types)
        scene_data = {
            'case_id': case_id,
            'order_info': {
                'order_value': float(order_info.get('order_value', 0)),
                'order_status': str(order_info.get('order_status', 'Unknown')),
                'num_items': int(order_info.get('num_items', 0)),
                'total_quantity': int(order_info.get('total_quantity', 0)),
            },
            'kpis': {
                'on_time_delivery': round(kpis.get('on_time_delivery', 0), 2),
                'days_sales_outstanding': round(kpis.get('days_sales_outstanding', 0), 2),
                'order_accuracy': round(kpis.get('order_accuracy', 0), 2),
                'invoice_accuracy': round(kpis.get('invoice_accuracy', 0), 2),
                'avg_cost_delivery': round(kpis.get('avg_cost_delivery', 0), 2),
            },
            'entities': {
                'users': users,
                'items': [
                    {
                        'id': str(item.get('item_id', '')),
                        'name': str(item.get('name', '')),
                        'quantity': int(item.get('quantity', 0)),
                        'line_total': float(item.get('line_total', 0)),
                    }
                    for item in items
                ],
                'suppliers': suppliers,
            },
            'animation': {
                'duration': total_duration,
                'keyframes': keyframes,
            },
            'locations': [
                {
                    'name': event_name,
                    'label': loc['label'],
                    'type': loc.get('type', 'main'),
                    'position': [loc['x'], loc['y'], loc['z']],
                }
                for event_name, loc in activity_positions.items()
            ],
            'item_paths': item_paths,
            'supplier_locations': [
                {
                    'supplier_id': supplier_id,
                    'label': loc['label'],
                    'country': loc['country'],
                    'position': [loc['x'], loc['y'], loc['z']],
                }
                for supplier_id, loc in supplier_positions.items()
            ],
        }
        
        # Save to JSON file using custom encoder for numpy types
        output_file = export_dir / f'{case_id}_scene.json'
        with open(output_file, 'w') as f:
            json.dump(scene_data, f, indent=2, cls=NumpyEncoder)
        
        logger.info(f"Generated scene file: {output_file}")
        
        metadata = {
            'case_id': case_id,
            'duration': total_duration,
            'num_events': len(keyframes),
            'start_time': min_time.isoformat() if min_time else None,
            'end_time': max_time.isoformat() if max_time else None,
        }
        
        return str(output_file), metadata
        
    except Exception as e:
        logger.error(f"Error generating GLTF for case {case_id}: {e}")
        raise


def get_sample_case_data(
    data_loader,
    case_id: str = None,
    seed: int = 42
) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any], List[str], List[Dict], List[str], Dict]:
    """
    Fetch all data for a single sample case from the backend.
    
    Args:
        data_loader: RealDataLoader instance
        case_id: Specific case ID, or None to pick the first one
        seed: Random seed for consistent entity selection
        
    Returns:
        Tuple of (case_id, events, order_info, users, items, suppliers, kpis)
    """
    import random
    import numpy as np
    
    # Load enriched data
    data_dir = Path(__file__).parent.parent / 'data'
    
    df_orders = pd.read_csv(data_dir / 'orders_enriched.csv')
    df_order_users = pd.read_csv(data_dir / 'order_users.csv')
    df_order_items = pd.read_csv(data_dir / 'order_items.csv')
    df_order_suppliers = pd.read_csv(data_dir / 'order_suppliers.csv')
    df_kpis = pd.read_csv(data_dir / 'order_kpis.csv')
    df_items = pd.read_csv(data_dir / 'items.csv')
    
    # Select case
    if case_id is None:
        # Use seed to consistently pick the same sample
        random.seed(seed)
        np.random.seed(seed)
        case_id = df_orders['order_id'].iloc[seed % len(df_orders)]
    
    logger.info(f"Fetching data for case: {case_id}")
    
    # Get events from data loader
    events_df = data_loader.df_events[data_loader.df_events['order_id'] == case_id].copy()
    events_df = events_df.sort_values('timestamp')
    
    events = []
    for _, row in events_df.iterrows():
        events.append({
            'event_name': row['event_name'],
            'timestamp': row['timestamp'],
        })
    
    # Get order info
    order_row = df_orders[df_orders['order_id'] == case_id].iloc[0]
    order_info = {
        'order_value': order_row['order_value'],
        'order_status': order_row['order_status'],
        'num_items': order_row['num_items'],
        'total_quantity': order_row['total_quantity'],
    }
    
    # Get users
    users_df = df_order_users[df_order_users['order_id'] == case_id]
    users = users_df['user_id'].tolist()
    
    # Get items
    items_df = df_order_items[df_order_items['order_id'] == case_id]
    items_df = items_df.merge(df_items[['item_id', 'name', 'category']], on='item_id', how='left')
    items = []
    for _, row in items_df.iterrows():
        items.append({
            'item_id': row['item_id'],
            'name': row['name'],
            'quantity': row['quantity'],
            'line_total': row['line_total'],
        })
    
    # Get suppliers
    suppliers_df = df_order_suppliers[df_order_suppliers['order_id'] == case_id]
    suppliers = suppliers_df['supplier_id'].tolist()
    
    # Get KPIs (denormalized)
    kpi_row = df_kpis[df_kpis['order_id'] == case_id].iloc[0]
    kpis = {
        'on_time_delivery': kpi_row['on_time_delivery'],
        'days_sales_outstanding': kpi_row['days_sales_outstanding'],
        'order_accuracy': kpi_row['order_accuracy'],
        'invoice_accuracy': kpi_row['invoice_accuracy'],
        'avg_cost_delivery': kpi_row['avg_cost_delivery'],
    }
    
    return case_id, events, order_info, users, items, suppliers, kpis

