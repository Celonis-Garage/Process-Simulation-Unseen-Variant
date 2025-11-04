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

# Location coordinates for the warehouse layout (in 3D space)
LOCATIONS = {
    'Receive Customer Order': {'x': -10, 'y': 0, 'z': 0, 'label': 'Sales Desk'},
    'Validate Customer Order': {'x': -8, 'y': 0, 'z': 2, 'label': 'Validation'},
    'Perform Credit Check': {'x': -6, 'y': 0, 'z': 3, 'label': 'Finance'},
    'Approve Order': {'x': -4, 'y': 0, 'z': 2, 'label': 'Approval Desk'},
    'Reject Order': {'x': -4, 'y': 0, 'z': -3, 'label': 'Rejection'},
    'Apply Discount': {'x': -2, 'y': 0, 'z': 3, 'label': 'Discount Desk'},
    'Schedule Order Fulfillment': {'x': 0, 'y': 0, 'z': 0, 'label': 'Scheduler'},
    'Generate Pick List': {'x': 2, 'y': 0, 'z': -2, 'label': 'Warehouse A'},
    'Pack Items': {'x': 4, 'y': 0, 'z': -3, 'label': 'Packing Station'},
    'Generate Shipping Label': {'x': 6, 'y': 0, 'z': -2, 'label': 'Labeling'},
    'Ship Order': {'x': 8, 'y': 0, 'z': 0, 'label': 'Shipping Dock'},
    'Process Return Request': {'x': 6, 'y': 0, 'z': 3, 'label': 'Returns'},
    'Generate Invoice': {'x': 10, 'y': 0, 'z': 1, 'label': 'Billing'},
}

# Supplier location coordinates (arranged around the perimeter)
SUPPLIER_LOCATIONS = {
    'S001': {'x': -18, 'y': 0, 'z': -8, 'label': 'Global Office Solutions', 'country': 'USA'},
    'S002': {'x': -18, 'y': 0, 'z': -6, 'label': 'TechSource Electronics', 'country': 'USA'},
    'S003': {'x': -18, 'y': 0, 'z': -4, 'label': 'Premier Furniture Co.', 'country': 'USA'},
    'S004': {'x': -20, 'y': 0, 'z': -2, 'label': 'Pacific Supplies Ltd.', 'country': 'China'},
    'S005': {'x': -20, 'y': 0, 'z': 0, 'label': 'EuroTech GmbH', 'country': 'Germany'},
    'S006': {'x': -20, 'y': 0, 'z': 2, 'label': 'National Print Supply', 'country': 'USA'},
    'S007': {'x': -18, 'y': 0, 'z': 4, 'label': 'Asian Trade Partners', 'country': 'Singapore'},
    'S008': {'x': -18, 'y': 0, 'z': 6, 'label': 'Metro Storage Systems', 'country': 'USA'},
    'S009': {'x': -16, 'y': 0, 'z': 8, 'label': 'Nordic Furniture AB', 'country': 'Sweden'},
    'S010': {'x': -14, 'y': 0, 'z': 9, 'label': 'Quantum Computing Supplies', 'country': 'USA'},
    'S011': {'x': -12, 'y': 0, 'z': 9, 'label': 'MicroParts Inc.', 'country': 'Taiwan'},
    'S012': {'x': -10, 'y': 0, 'z': 9, 'label': 'Southern Office Depot', 'country': 'USA'},
    'S013': {'x': -8, 'y': 0, 'z': 9, 'label': 'Global Supplies Network', 'country': 'UAE'},
    'S014': {'x': -6, 'y': 0, 'z': 9, 'label': 'Eco-Friendly Products Co.', 'country': 'Canada'},
    'S015': {'x': -4, 'y': 0, 'z': 9, 'label': 'Premium Electronics Ltd.', 'country': 'Japan'},
    'S016': {'x': -2, 'y': 0, 'z': 9, 'label': 'FastShip Supplies', 'country': 'Mexico'},
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
    items_df: pd.DataFrame
) -> List[Dict[str, Any]]:
    """
    Generate animation paths for items from suppliers to warehouse
    
    Args:
        items: List of item dictionaries
        item_supplier_map: Mapping of item_id to supplier_id
        keyframes: Order event keyframes
        items_df: DataFrame with item information (for category lookup)
        
    Returns:
        List of item path dictionaries with animation data
    """
    item_paths = []
    
    # Find warehouse arrival time (Generate Pick List event)
    warehouse_time = 180.0  # Default
    pack_time = 240.0  # Default
    
    for kf in keyframes:
        if kf['event'] == 'Generate Pick List':
            warehouse_time = kf['time']
        elif kf['event'] == 'Pack Items':
            pack_time = kf['time']
    
    warehouse_loc = LOCATIONS.get('Generate Pick List', {'x': 2, 'y': 0, 'z': -2})
    pack_loc = LOCATIONS.get('Pack Items', {'x': 4, 'y': 0, 'z': -3})
    
    for item in items:
        item_id = item.get('item_id', '')
        supplier_id = item_supplier_map.get(item_id, 'S001')
        
        # Get supplier location
        supplier_loc = SUPPLIER_LOCATIONS.get(supplier_id, {'x': -18, 'y': 0, 'z': 0})
        
        # Get item category for color
        item_row = items_df[items_df['item_id'] == item_id]
        category = item_row['category'].iloc[0] if len(item_row) > 0 else 'Others'
        color = CATEGORY_COLORS.get(category, CATEGORY_COLORS['Others'])
        
        # Calculate transit time based on distance (longer for international suppliers)
        transit_duration = 60.0  # Default 60 seconds
        if supplier_loc.get('country') not in ['USA', 'Canada', 'Mexico']:
            transit_duration = 120.0  # 2 minutes for international
        
        departure_time = max(0, warehouse_time - transit_duration - 30)  # Leave supplier early
        
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
                    'time': warehouse_time - 10,
                    'position': [warehouse_loc['x'], 0, warehouse_loc['z']],
                    'label': 'Arrived at Warehouse',
                    'status': 'arrived'
                },
                {
                    'time': pack_time - 5,
                    'position': [warehouse_loc['x'], 0, warehouse_loc['z']],
                    'label': 'Moving to Packing',
                    'status': 'ready'
                },
                {
                    'time': pack_time,
                    'position': [pack_loc['x'], 0, pack_loc['z']],
                    'label': 'Being Packed',
                    'status': 'packing'
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
        
        # Parse events and create animation keyframes
        keyframes = []
        min_time = None
        max_time = None
        
        for i, event in enumerate(events):
            event_name = event.get('event_name', event.get('Activity', ''))
            timestamp = event.get('timestamp', event.get('Timestamp', None))
            
            if not event_name or event_name not in LOCATIONS:
                continue
                
            # Parse timestamp
            if isinstance(timestamp, str):
                try:
                    dt = pd.to_datetime(timestamp)
                except:
                    dt = datetime.now()
            else:
                dt = timestamp if timestamp else datetime.now()
            
            if min_time is None:
                min_time = dt
                
            max_time = dt
            
            # Calculate time offset in seconds from start
            time_offset = (dt - min_time).total_seconds()
            
            # Get location for this event
            loc = LOCATIONS[event_name]
            
            keyframes.append({
                'time': time_offset,
                'position': [loc['x'], loc['y'], loc['z']],
                'event': event_name,
                'label': loc['label'],
                'timestamp': dt.isoformat()
            })
        
        # Calculate total duration
        total_duration = (max_time - min_time).total_seconds() if max_time and min_time else 0
        
        # Load items dataframe and get item-supplier mapping
        data_dir = export_dir.parent.parent / 'data'
        items_csv_path = data_dir / 'items.csv'
        items_df = pd.read_csv(items_csv_path) if items_csv_path.exists() else pd.DataFrame()
        
        item_supplier_map = get_item_supplier_mapping(case_id, data_dir)
        
        # Generate item animation paths
        item_paths = generate_item_paths(items, item_supplier_map, keyframes, items_df)
        
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
                    'position': [loc['x'], loc['y'], loc['z']],
                }
                for event_name, loc in LOCATIONS.items()
            ],
            'item_paths': item_paths,
            'supplier_locations': [
                {
                    'supplier_id': supplier_id,
                    'label': loc['label'],
                    'country': loc['country'],
                    'position': [loc['x'], loc['y'], loc['z']],
                }
                for supplier_id, loc in SUPPLIER_LOCATIONS.items()
                if supplier_id in item_supplier_map.values()
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

