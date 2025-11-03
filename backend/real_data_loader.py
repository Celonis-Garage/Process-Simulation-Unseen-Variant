import xml.etree.ElementTree as ET
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Tuple
import numpy as np

class RealDataLoader:
    """
    Loader for the real O2C event log data from o2c_data_orders_only.xml
    Calculates KPIs from actual process execution data.
    """
    
    def __init__(self, data_file_path: str = '../data/o2c_data_orders_only.xml'):
        self.data_file_path = data_file_path
        self.df_events = None
        self.df_orders = None
        self.kpis = None
        self._load_data()
    
    def _load_data(self):
        """Load and parse the case-centric event log XML file."""
        print(f"Loading real O2C data from {self.data_file_path}...")
        
        all_events = []
        all_orders = []
        
        # Parse the XML file
        tree = ET.parse(self.data_file_path)
        root = tree.getroot()
        
        for trace in root.findall('trace'):
            # Extract order attributes
            order_id = None
            order_value = None
            order_status = None
            
            for string_elem in trace.findall('string'):
                key = string_elem.get('key')
                value = string_elem.get('value')
                
                if key == 'concept:name':
                    order_id = value
                elif key == 'order_value':
                    order_value = float(value) if value else 0.0
                elif key == 'order_status':
                    order_status = value
            
            # Store order information
            all_orders.append({
                'order_id': order_id,
                'order_value': order_value,
                'order_status': order_status
            })
            
            # Extract events for this order
            events = trace.findall('event')
            for event in events:
                event_name = None
                event_time = None
                
                for child in event:
                    if child.get('key') == 'concept:name':
                        event_name = child.get('value')
                    elif child.get('key') == 'time:timestamp':
                        event_time = child.get('value')
                
                if event_name and event_time:
                    all_events.append({
                        'order_id': order_id,
                        'event_name': event_name,
                        'timestamp': datetime.fromisoformat(event_time.replace('Z', '+00:00')),
                        'order_value': order_value,
                        'order_status': order_status
                    })
        
        self.df_events = pd.DataFrame(all_events)
        self.df_orders = pd.DataFrame(all_orders)
        
        if not self.df_events.empty:
            self.df_events = self.df_events.sort_values(by=['order_id', 'timestamp']).reset_index(drop=True)
        
        print(f"✅ Loaded {len(self.df_orders)} orders with {len(self.df_events)} events")
        
        # Calculate KPIs after loading
        self._calculate_kpis()
    
    def _calculate_kpis(self):
        """Calculate KPIs from the event log data."""
        if self.df_events.empty:
            print("⚠️ No events found. Cannot calculate KPIs.")
            self.kpis = {}
            return
        
        print("Calculating KPIs from real data...")
        
        # Calculate time difference between consecutive events for each order
        self.df_events['time_diff_hours'] = self.df_events.groupby('order_id')['timestamp'].diff().dt.total_seconds() / 3600
        
        # Calculate average execution time for each event (throughput time per activity)
        event_throughput = self.df_events.groupby('event_name')['time_diff_hours'].agg(['mean', 'std', 'count']).reset_index()
        event_throughput.columns = ['event_name', 'avg_time_hours', 'std_time_hours', 'event_count']
        
        # Calculate order-level metrics
        order_metrics = self.df_events.groupby('order_id')['timestamp'].agg(['min', 'max']).reset_index()
        order_metrics['total_duration_hours'] = (order_metrics['max'] - order_metrics['min']).dt.total_seconds() / 3600
        order_metrics['total_duration_days'] = order_metrics['total_duration_hours'] / 24
        
        # Merge with order values to calculate cost metrics
        order_metrics = order_metrics.merge(self.df_orders[['order_id', 'order_value']], on='order_id', how='left')
        
        # Calculate average cost per order (typical O2C costs are 1-3% of order value)
        # We'll use 2% as a reasonable estimate
        order_metrics['estimated_cost'] = order_metrics['order_value'] * 0.02
        
        # Store KPIs in a structured format
        self.kpis = {
            'event_throughput': event_throughput.to_dict('records'),
            'order_execution_time': {
                'mean_hours': order_metrics['total_duration_hours'].mean(),
                'median_hours': order_metrics['total_duration_hours'].median(),
                'std_hours': order_metrics['total_duration_hours'].std(),
                'min_hours': order_metrics['total_duration_hours'].min(),
                'max_hours': order_metrics['total_duration_hours'].max(),
                'mean_days': order_metrics['total_duration_days'].mean(),
                'median_days': order_metrics['total_duration_days'].median()
            },
            'order_cost': {
                'mean_cost': order_metrics['estimated_cost'].mean(),
                'median_cost': order_metrics['estimated_cost'].median(),
                'std_cost': order_metrics['estimated_cost'].std(),
                'min_cost': order_metrics['estimated_cost'].min(),
                'max_cost': order_metrics['estimated_cost'].max()
            },
            'process_summary': {
                'total_orders': len(self.df_orders),
                'total_events': len(self.df_events),
                'unique_event_types': self.df_events['event_name'].nunique(),
                'avg_events_per_order': len(self.df_events) / len(self.df_orders) if len(self.df_orders) > 0 else 0,
                'avg_order_value': self.df_orders['order_value'].mean()
            }
        }
        
        print(f"✅ KPIs calculated successfully")
        print(f"   - Average order execution time: {self.kpis['order_execution_time']['mean_days']:.2f} days")
        print(f"   - Average order cost: ${self.kpis['order_cost']['mean_cost']:.2f}")
        print(f"   - Unique event types: {self.kpis['process_summary']['unique_event_types']}")
    
    def get_event_kpis_for_activities(self, activities: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Get KPIs (avg_time and cost) for a list of activities.
        Returns a dictionary mapping activity names to their KPIs.
        
        IMPORTANT: Calculates KPIs from ONLY the orders that follow the most frequent variant
        to ensure accurate baseline for simulation comparison.
        
        Note: Time represents time since previous event. For events like returns
        that happen much later, we cap at 24 hours to represent processing time.
        Cost is estimated as a percentage of average order value.
        """
        if self.df_events.empty or self.df_orders.empty:
            # Return default values if no data
            return {activity: {"avg_time": 1.0, "cost": 50.0} for activity in activities}
        
        kpis_dict = {}
        MAX_PROCESSING_TIME = 24.0  # Cap at 24 hours for UI display
        
        # Filter to only orders that follow the most frequent variant
        # This ensures KPIs match the baseline used in simulation
        variants = self.get_process_variants(top_n=1)
        if variants and len(variants) > 0:
            most_frequent = variants[0]
            variant_string = most_frequent['variant']
            
            # Find all orders that match this exact variant
            order_variants = self.df_events.groupby('order_id')['event_name'].apply(
                lambda x: ' → '.join(x)
            ).reset_index()
            order_variants.columns = ['order_id', 'variant_string']
            matching_order_ids = order_variants[
                order_variants['variant_string'] == variant_string
            ]['order_id'].tolist()
            
            # Filter events to only include orders from the most frequent variant
            filtered_events = self.df_events[self.df_events['order_id'].isin(matching_order_ids)]
            
            print(f"✅ KPI Calculation: Using {len(matching_order_ids)} orders from most frequent variant (out of {len(self.df_orders)} total)")
        else:
            # Fallback to all events if no variant found
            filtered_events = self.df_events
            print(f"⚠️ KPI Calculation: Using all {len(self.df_orders)} orders (no variant filtering)")
        
        # Calculate average order value and cost per activity
        avg_order_value = self.df_orders['order_value'].mean()
        
        # Estimate cost as a function of time and order value
        # Typical O2C costs are 1-3% of order value spread across activities
        cost_per_hour = (avg_order_value * 0.02) / 10  # 2% of order value / 10 typical hours
        
        for activity in activities:
            # Find matching events in the FILTERED dataset (most frequent variant only)
            matching_events = filtered_events[filtered_events['event_name'] == activity]
            
            if not matching_events.empty:
                avg_time = matching_events['time_diff_hours'].mean()
                # Handle NaN (first event in each order has no time_diff)
                if pd.isna(avg_time):
                    avg_time = 1.0  # Default 1 hour if we can't calculate
                else:
                    # Cap at MAX_PROCESSING_TIME for events with long wait times
                    # (e.g., returns that happen weeks after shipping)
                    avg_time = min(avg_time, MAX_PROCESSING_TIME)
                
                # Calculate cost based on time (activities that take longer cost more)
                estimated_cost = max(cost_per_hour * avg_time, 25.0)  # Minimum $25 per activity
                
                kpis_dict[activity] = {
                    "avg_time": round(avg_time, 2),
                    "cost": round(estimated_cost, 2)
                }
            else:
                # Activity not found in dataset, use default
                kpis_dict[activity] = {
                    "avg_time": 1.0,
                    "cost": 50.0  # Default cost
                }
        
        return kpis_dict
    
    def get_all_event_types(self) -> List[str]:
        """Get list of all unique event types in the dataset."""
        if self.df_events.empty:
            return []
        return sorted(self.df_events['event_name'].unique().tolist())
    
    def get_process_variants(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get the most common process variants from the data.
        A variant is a unique sequence of events.
        """
        if self.df_events.empty:
            return []
        
        # Create process variants
        variants = self.df_events.groupby('order_id')['event_name'].apply(list).reset_index()
        variants['variant_string'] = variants['event_name'].apply(lambda x: ' → '.join(x))
        
        # Count variant frequencies
        variant_counts = variants['variant_string'].value_counts().head(top_n)
        
        result = []
        for variant_str, count in variant_counts.items():
            activities = variant_str.split(' → ')
            result.append({
                'variant': variant_str,
                'activities': activities,
                'frequency': int(count),
                'percentage': round((count / len(self.df_orders)) * 100, 2)
            })
        
        return result
    
    def get_process_flow_metrics(self) -> Dict[str, Any]:
        """
        Calculate process flow metrics including edge frequencies and timing.
        Returns detailed flow statistics for all transitions in the process.
        """
        if self.df_events.empty:
            return {"edges": [], "total_cases": 0}
        
        # Calculate transitions (edges) between consecutive activities
        transitions = []
        
        for order_id in self.df_orders['order_id']:
            order_events = self.df_events[self.df_events['order_id'] == order_id].sort_values('timestamp')
            
            for i in range(len(order_events) - 1):
                current_event = order_events.iloc[i]
                next_event = order_events.iloc[i + 1]
                
                transitions.append({
                    'from': current_event['event_name'],
                    'to': next_event['event_name'],
                    'time_diff_hours': (next_event['timestamp'] - current_event['timestamp']).total_seconds() / 3600,
                    'order_id': order_id
                })
        
        if not transitions:
            return {"edges": [], "total_cases": len(self.df_orders)}
        
        # Convert to DataFrame for analysis
        df_transitions = pd.DataFrame(transitions)
        
        # Calculate metrics for each edge
        edge_metrics = []
        for (from_activity, to_activity), group in df_transitions.groupby(['from', 'to']):
            cases = len(group)
            avg_time_hours = group['time_diff_hours'].mean()
            avg_days = avg_time_hours / 24
            probability = cases / len(self.df_orders)
            
            edge_metrics.append({
                'from': from_activity,
                'to': to_activity,
                'cases': int(cases),
                'avg_time_hours': round(avg_time_hours, 2),
                'avg_days': round(avg_days, 3),
                'probability': round(probability, 4)
            })
        
        # Sort by frequency
        edge_metrics.sort(key=lambda x: x['cases'], reverse=True)
        
        return {
            'edges': edge_metrics,
            'total_cases': len(self.df_orders),
            'unique_transitions': len(edge_metrics)
        }
    
    def get_sample_event_log(self, n_cases: int = 20) -> List[Dict[str, Any]]:
        """
        Get a sample of the event log for simulation.
        Returns data in the format expected by the frontend.
        """
        if self.df_events.empty:
            return []
        
        # Get sample of order IDs
        sample_orders = self.df_orders['order_id'].head(n_cases).tolist()
        
        # Filter events for these orders
        sample_events = self.df_events[self.df_events['order_id'].isin(sample_orders)].copy()
        
        # Format for frontend
        event_log = []
        for _, row in sample_events.iterrows():
            event_log.append({
                "Case ID": row['order_id'],
                "Activity": row['event_name'],
                "Timestamp": row['timestamp'].strftime("%Y-%m-%d %H:%M:%S"),
                "Throughput Time": round(row['time_diff_hours'], 2) if not pd.isna(row['time_diff_hours']) else 0.0,
                "Order Value": row['order_value']
            })
        
        return event_log
    
    def get_event_log_for_activities(self, activities: List[str], n_cases: int = 1, custom_kpis: Dict[str, Dict[str, float]] = None) -> pd.DataFrame:
        """
        Generate a simulated event log for the user's designed process.
        Creates NEW synthetic order(s) following the specified activity sequence.
        Returns a DataFrame in the format expected by the frontend.
        
        Args:
            activities: List of activity names in order
            n_cases: Number of cases to simulate
            custom_kpis: Optional dict of custom KPIs to override data-based KPIs
                        Format: {"Activity Name": {"avg_time": hours, "cost": dollars}}
        """
        if not activities:
            return pd.DataFrame()
        
        # Get KPI data for realistic timing
        if custom_kpis:
            # Use custom KPIs if provided, fall back to dataset KPIs for missing activities
            dataset_kpis = self.get_event_kpis_for_activities(activities)
            kpis = {**dataset_kpis, **custom_kpis}  # Custom KPIs override dataset KPIs
        else:
            kpis = self.get_event_kpis_for_activities(activities)
        
        # Generate simulated order(s)
        event_log = []
        base_timestamp = pd.Timestamp.now()
        
        for case_num in range(n_cases):
            # Create a NEW order ID that doesn't exist in the data
            case_id = f"USER-DESIGN-{case_num + 1:03d}"
            
            # Generate random order value similar to data distribution
            avg_order_value = self.df_orders['order_value'].mean()
            std_order_value = self.df_orders['order_value'].std()
            order_value = np.random.normal(avg_order_value, std_order_value)
            order_value = max(1000, min(50000, order_value))  # Clamp to reasonable range
            
            current_time = base_timestamp + pd.Timedelta(days=case_num)
            
            # Generate events in the EXACT order specified by user's design
            for activity in activities:
                # Get timing and cost info for this activity
                activity_kpi = kpis.get(activity, {"avg_time": 1.0, "cost": 50.0})
                avg_time_hours = activity_kpi.get("avg_time", 1.0)
                activity_cost = activity_kpi.get("cost", 50.0)
                
                # Always use exact values - no variation
                actual_time = avg_time_hours
                
                event_log.append({
                    "Case ID": case_id,
                    "Activity": activity,
                    "Timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Throughput Time": round(actual_time, 2),
                    "Cost": round(activity_cost, 2),  # ✅ Add cost from KPIs
                    "Order Value": round(order_value, 2)
                })
                
                # Move time forward for next activity
                current_time += pd.Timedelta(hours=actual_time)
        
        return pd.DataFrame(event_log)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics about the dataset."""
        if self.df_events.empty or self.df_orders.empty:
            return {}
        
        return {
            "total_orders": len(self.df_orders),
            "total_events": len(self.df_events),
            "unique_event_types": self.df_events['event_name'].nunique(),
            "avg_events_per_order": round(len(self.df_events) / len(self.df_orders), 2),
            "avg_order_execution_time_hours": round(self.kpis['order_execution_time']['mean_hours'], 2),
            "avg_order_execution_time_days": round(self.kpis['order_execution_time']['mean_days'], 2),
            "order_statuses": self.df_orders['order_status'].value_counts().to_dict()
        }
    
    def calculate_order_execution_times(self) -> Dict[str, float]:
        """
        Calculate and return baseline order execution time and cost metrics.
        Used by the simulation engine for comparison with optimized variants.
        
        IMPORTANT: Returns activity-based timing for the most frequent variant,
        not the overall order execution time. This ensures fair comparison when
        activities are added/removed.
        
        NOTE: This MUST use the exact same calculation as the simulation engine
        to ensure 0% change when simulating the unmodified baseline process.
        """
        if not self.kpis or 'order_execution_time' not in self.kpis:
            # Return default values if KPIs haven't been calculated
            return {
                'mean_hours': 72.0,
                'median_hours': 60.0,
                'std_hours': 24.0,
                'mean_days': 3.0,
                'median_days': 2.5,
                'mean_cost': 500.0,
                'median_cost': 450.0,
                'baseline_activities': []
            }
        
        # Get the most frequent variant to use as baseline
        variants = self.get_process_variants(top_n=1)
        if variants and len(variants) > 0:
            baseline_variant = variants[0]
            baseline_activities = baseline_variant['activities']  # Use the list, not the string!
            
            # Calculate baseline using EXACT same method as simulation engine
            # This ensures perfect 0% change when activities match
            activity_kpis = self.get_event_kpis_for_activities(baseline_activities)
            
            # Sum activity times (matching SimulationEngine.calculate_process_duration logic)
            baseline_duration_hours = 0.0
            for activity in baseline_activities:
                if activity in activity_kpis:
                    baseline_duration_hours += activity_kpis[activity]['avg_time']
                else:
                    baseline_duration_hours += 1.5  # Same fallback as simulation engine
            
            # Sum activity costs (matching SimulationEngine.calculate_process_cost logic)
            baseline_cost = 0.0
            for activity in baseline_activities:
                if activity in activity_kpis and 'cost' in activity_kpis[activity]:
                    baseline_cost += activity_kpis[activity]['cost']
                else:
                    baseline_cost += 60.0  # Same fallback as simulation engine
            
            baseline_metrics = {
                'mean_hours': baseline_duration_hours,
                'median_hours': baseline_duration_hours,
                'std_hours': self.kpis['order_execution_time']['std_hours'],
                'mean_days': baseline_duration_hours / 24,
                'median_days': baseline_duration_hours / 24,
                'mean_cost': baseline_cost,
                'median_cost': baseline_cost,
                'std_cost': self.kpis['order_cost']['std_cost'] if 'order_cost' in self.kpis else 50.0,
                'baseline_activities': baseline_activities  # Store for reference
            }
            
            print(f"✅ Baseline calculated: {len(baseline_activities)} activities, {baseline_duration_hours:.2f}h, ${baseline_cost:.2f}")
        else:
            # Fallback to overall order execution time
            baseline_metrics = self.kpis['order_execution_time'].copy()
            baseline_metrics['baseline_activities'] = []
            
            # Add cost metrics if available
            if 'order_cost' in self.kpis:
                baseline_metrics['mean_cost'] = self.kpis['order_cost']['mean_cost']
                baseline_metrics['median_cost'] = self.kpis['order_cost']['median_cost']
                baseline_metrics['std_cost'] = self.kpis['order_cost']['std_cost']
        
        return baseline_metrics

# Create a singleton instance for easy import
_data_loader_instance = None

def get_data_loader(data_file_path: str = None) -> RealDataLoader:
    """Get or create the singleton data loader instance."""
    global _data_loader_instance
    if _data_loader_instance is None:
        if data_file_path:
            _data_loader_instance = RealDataLoader(data_file_path)
        else:
            _data_loader_instance = RealDataLoader()
    return _data_loader_instance


# Additional functions for loading enriched datasets
def load_users_data(data_dir: str = '../data') -> pd.DataFrame:
    """Load users dataset"""
    import os
    users_path = os.path.join(data_dir, 'users.csv')
    if os.path.exists(users_path):
        return pd.read_csv(users_path)
    return pd.DataFrame()


def load_items_data(data_dir: str = '../data') -> pd.DataFrame:
    """Load items dataset"""
    import os
    items_path = os.path.join(data_dir, 'items.csv')
    if os.path.exists(items_path):
        return pd.read_csv(items_path)
    return pd.DataFrame()


def load_suppliers_data(data_dir: str = '../data') -> pd.DataFrame:
    """Load suppliers dataset"""
    import os
    suppliers_path = os.path.join(data_dir, 'suppliers.csv')
    if os.path.exists(suppliers_path):
        return pd.read_csv(suppliers_path)
    return pd.DataFrame()


def load_order_kpis_data(data_dir: str = '../data') -> pd.DataFrame:
    """Load order KPIs dataset (includes normalized KPIs)"""
    import os
    kpis_path = os.path.join(data_dir, 'order_kpis.csv')
    if os.path.exists(kpis_path):
        return pd.read_csv(kpis_path)
    return pd.DataFrame()


def load_enriched_orders_data(data_dir: str = '../data') -> pd.DataFrame:
    """Load enriched orders dataset"""
    import os
    orders_path = os.path.join(data_dir, 'orders_enriched.csv')
    if os.path.exists(orders_path):
        return pd.read_csv(orders_path)
    return pd.DataFrame()


def get_baseline_kpis_from_data(data_dir: str = '../data') -> Dict[str, float]:
    """
    Calculate baseline KPIs from the order_kpis dataset
    Returns average values for each KPI (denormalized)
    """
    df_kpis = load_order_kpis_data(data_dir)
    
    if df_kpis.empty:
        # Default baseline KPIs
        return {
            'on_time_delivery': 79.8,
            'days_sales_outstanding': 38.0,
            'order_accuracy': 81.3,
            'invoice_accuracy': 76.5,
            'avg_cost_delivery': 33.48
        }
    
    # Use original (non-normalized) columns for baseline
    baseline = {}
    kpi_columns = ['on_time_delivery', 'days_sales_outstanding', 
                   'order_accuracy', 'invoice_accuracy', 'avg_cost_delivery']
    
    for kpi in kpi_columns:
        if kpi in df_kpis.columns:
            baseline[kpi] = float(df_kpis[kpi].mean())
    
    return baseline
