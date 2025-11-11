"""
Script to regenerate order_kpis.csv with realistic KPIs based on process outcomes.

This fixes the training data by assigning appropriate KPIs based on business logic:
- Rejected orders: Terrible KPIs (business failure)
- Orders with returns: Poor KPIs (customer dissatisfaction)
- Successful orders: Good KPIs (normal business)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
DATA_DIR = Path(__file__).parent.parent / 'data'

# KPI ranges based on process outcomes
KPI_RANGES = {
    'rejected': {
        'on_time_delivery': (0, 30),  # Very low - order never delivered
        'days_sales_outstanding': (60, 90),  # Very high - no payment received
        'order_accuracy': (0, 40),  # Very low - order never fulfilled
        'invoice_accuracy': (0, 40),  # Very low - no proper invoicing
        'avg_cost_delivery': (35, 55)  # High - wasted resources
    },
    'return': {
        'on_time_delivery': (40, 60),  # Low - return delays
        'days_sales_outstanding': (45, 65),  # High - payment complications
        'order_accuracy': (50, 70),  # Low - incorrect items
        'invoice_accuracy': (55, 75),  # Low - billing issues
        'avg_cost_delivery': (30, 45)  # High - return costs
    },
    'successful': {
        'on_time_delivery': (80, 95),  # High - normal delivery
        'days_sales_outstanding': (28, 40),  # Normal payment terms
        'order_accuracy': (85, 98),  # High - correct items
        'invoice_accuracy': (80, 95),  # High - accurate billing
        'avg_cost_delivery': (18, 30)  # Normal delivery costs
    },
    'with_discount': {
        'on_time_delivery': (75, 90),  # Slightly lower - promotional orders
        'days_sales_outstanding': (30, 42),  # Slightly higher - discount processing
        'order_accuracy': (80, 95),  # Good but not perfect
        'invoice_accuracy': (75, 92),  # Good - discount adjustments
        'avg_cost_delivery': (20, 32)  # Slightly higher - special handling
    }
}


def load_event_log():
    """Load the O2C event log"""
    from lxml import etree as ET
    
    xml_path = DATA_DIR / 'o2c_data_orders_only.xml'
    
    events = []
    tree = ET.parse(str(xml_path))
    root = tree.getroot()
    
    for trace in root.findall('trace'):
        # Get order ID
        order_id_elem = trace.find('.//string[@key="concept:name"]')
        if order_id_elem is None:
            continue
        order_id = order_id_elem.get('value')
        
        # Get events
        for event in trace.findall('event'):
            event_name_elem = event.find('.//string[@key="concept:name"]')
            timestamp_elem = event.find('.//date[@key="time:timestamp"]')
            
            if event_name_elem is not None and timestamp_elem is not None:
                events.append({
                    'order_id': order_id,
                    'event_name': event_name_elem.get('value'),
                    'timestamp': pd.to_datetime(timestamp_elem.get('value'))
                })
    
    df = pd.DataFrame(events)
    logger.info(f"Loaded {len(df)} events for {df['order_id'].nunique()} orders")
    return df


def classify_order(event_sequence):
    """Classify order type based on event sequence"""
    events_set = set(event_sequence)
    
    # Priority: Check for negative outcomes first
    if 'Reject Order' in events_set:
        return 'rejected'
    elif 'Process Return Request' in events_set:
        return 'return'
    elif 'Apply Discount' in events_set:
        return 'with_discount'
    elif 'Generate Invoice' in events_set:
        return 'successful'
    else:
        # Incomplete order (shouldn't happen but handle it)
        return 'rejected'  # Treat as failure


def generate_realistic_kpis(order_type, seed=None):
    """Generate realistic KPIs based on order type"""
    if seed is not None:
        np.random.seed(seed)
    
    ranges = KPI_RANGES[order_type]
    
    kpis = {
        'on_time_delivery': np.random.uniform(*ranges['on_time_delivery']),
        'days_sales_outstanding': np.random.uniform(*ranges['days_sales_outstanding']),
        'order_accuracy': np.random.uniform(*ranges['order_accuracy']),
        'invoice_accuracy': np.random.uniform(*ranges['invoice_accuracy']),
        'avg_cost_delivery': np.random.uniform(*ranges['avg_cost_delivery'])
    }
    
    return kpis


def normalize_kpi(value, kpi_name):
    """Normalize KPI to 0-1 range based on domain knowledge"""
    # Define normalization ranges (min, max for each KPI)
    normalization_ranges = {
        'on_time_delivery': (0, 100),  # Percentage
        'days_sales_outstanding': (0, 90),  # Days
        'order_accuracy': (0, 100),  # Percentage
        'invoice_accuracy': (0, 100),  # Percentage
        'avg_cost_delivery': (0, 100)  # Dollars
    }
    
    min_val, max_val = normalization_ranges[kpi_name]
    normalized = (value - min_val) / (max_val - min_val)
    return np.clip(normalized, 0, 1)


def regenerate_kpis():
    """Main function to regenerate all KPIs with realistic business logic"""
    logger.info("="*80)
    logger.info("REGENERATING ORDER KPIs WITH REALISTIC BUSINESS LOGIC")
    logger.info("="*80)
    
    # Load event log
    df_events = load_event_log()
    
    # Group by order to get event sequences
    order_sequences = df_events.groupby('order_id')['event_name'].apply(list).to_dict()
    
    # Generate KPIs for each order
    kpi_records = []
    order_type_counts = {'rejected': 0, 'return': 0, 'successful': 0, 'with_discount': 0}
    
    for i, (order_id, event_sequence) in enumerate(order_sequences.items()):
        # Classify order type
        order_type = classify_order(event_sequence)
        order_type_counts[order_type] += 1
        
        # Generate KPIs with deterministic seed for reproducibility
        seed = hash(order_id) % (2**31)
        kpis = generate_realistic_kpis(order_type, seed=seed)
        
        # Create record with both raw and normalized values
        record = {'order_id': order_id}
        for kpi_name, kpi_value in kpis.items():
            record[kpi_name] = kpi_value
            record[f'{kpi_name}_normalized'] = normalize_kpi(kpi_value, kpi_name)
        
        kpi_records.append(record)
        
        if (i + 1) % 200 == 0:
            logger.info(f"  Processed {i + 1}/{len(order_sequences)} orders...")
    
    # Create DataFrame
    df_kpis = pd.DataFrame(kpi_records)
    
    # Log statistics
    logger.info("\n" + "="*80)
    logger.info("KPI GENERATION SUMMARY")
    logger.info("="*80)
    logger.info(f"Total orders: {len(df_kpis)}")
    logger.info("\nOrder type distribution:")
    for order_type, count in order_type_counts.items():
        percentage = (count / len(df_kpis)) * 100
        logger.info(f"  {order_type.capitalize()}: {count} ({percentage:.1f}%)")
    
    logger.info("\nKPI Statistics by Type:")
    for order_type in ['rejected', 'return', 'successful', 'with_discount']:
        # Get orders of this type
        order_ids = [oid for oid, seq in order_sequences.items() if classify_order(seq) == order_type]
        if not order_ids:
            continue
        
        type_kpis = df_kpis[df_kpis['order_id'].isin(order_ids)]
        logger.info(f"\n  {order_type.upper()}:")
        logger.info(f"    On-Time Delivery: {type_kpis['on_time_delivery'].mean():.2f}%")
        logger.info(f"    Days Sales Outstanding: {type_kpis['days_sales_outstanding'].mean():.2f} days")
        logger.info(f"    Order Accuracy: {type_kpis['order_accuracy'].mean():.2f}%")
        logger.info(f"    Invoice Accuracy: {type_kpis['invoice_accuracy'].mean():.2f}%")
        logger.info(f"    Avg Cost of Delivery: ${type_kpis['avg_cost_delivery'].mean():.2f}")
    
    # Save to CSV
    output_path = DATA_DIR / 'order_kpis.csv'
    df_kpis.to_csv(output_path, index=False)
    logger.info(f"\n✅ Saved regenerated KPIs to: {output_path}")
    logger.info("="*80)
    
    return df_kpis


if __name__ == '__main__':
    regenerate_kpis()

