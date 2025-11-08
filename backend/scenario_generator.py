"""
Scenario Generator for Process Simulations
Randomly assigns users, items, and suppliers to process scenarios
"""

import numpy as np
import pandas as pd
import random
import logging
from typing import Dict, List, Tuple
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Item category to supplier mapping (based on notebook logic)
CATEGORY_SUPPLIER_MAP = {
    'Electronics': [1, 2, 3, 4],  # Suppliers 1-4 for Electronics
    'Office Supplies': [5, 6, 7, 8],  # Suppliers 5-8 for Office Supplies
    'Furniture': [9, 10, 11, 12],  # Suppliers 9-12 for Furniture
    'Others': [13, 14, 15, 16]  # Suppliers 13-16 for Others
}


class ScenarioGenerator:
    """
    Generates random entity assignments for process scenarios
    """
    
    def __init__(self, data_dir: Path):
        """
        Initialize scenario generator with data
        
        Args:
            data_dir: Path to data directory
        """
        self.data_dir = data_dir
        self.users_df: pd.DataFrame = None
        self.items_df: pd.DataFrame = None
        self.suppliers_df: pd.DataFrame = None
        self._load_data()
    
    def _load_data(self):
        """Load user, item, and supplier data"""
        try:
            self.users_df = pd.read_csv(self.data_dir / 'users.csv')
            self.items_df = pd.read_csv(self.data_dir / 'items.csv')
            self.suppliers_df = pd.read_csv(self.data_dir / 'suppliers.csv')
            
            logger.info(f"✓ Loaded {len(self.users_df)} users")
            logger.info(f"✓ Loaded {len(self.items_df)} items")
            logger.info(f"✓ Loaded {len(self.suppliers_df)} suppliers")
        except Exception as e:
            logger.error(f"Failed to load entity data: {e}")
            # Create minimal defaults
            self.users_df = pd.DataFrame({
                'user_id': range(1, 8),
                'name': [f'User {i}' for i in range(1, 8)],
                'role': ['Admin', 'Sales', 'Finance', 'Warehouse', 'Shipping', 'Quality', 'Support']
            })
            self.items_df = pd.DataFrame({
                'item_id': range(1, 25),
                'name': [f'Item {i}' for i in range(1, 25)],
                'category': ['Electronics'] * 6 + ['Office Supplies'] * 6 + ['Furniture'] * 6 + ['Others'] * 6,
                'unit_price': [random.uniform(10, 500) for _ in range(24)]
            })
            self.suppliers_df = pd.DataFrame({
                'supplier_id': range(1, 17),
                'name': [f'Supplier {i}' for i in range(1, 17)]
            })
            logger.warning("Using default entity data")
    
    def generate_scenario_entities(
        self,
        activities: List[str],
        num_users: int = None,
        num_items: int = None,
        session_seed: int = None
    ) -> Tuple[List[str], List[Dict], List[str], float]:
        """
        Generate deterministic entity assignments for a scenario.
        
        Args:
            activities: List of activity names in the process
            num_users: Number of users to assign (default: deterministic 3)
            num_items: Number of items to assign (default: deterministic 5)
            session_seed: Fixed seed for the session (if None, uses hash of activities)
        
        Returns:
            Tuple of (user_ids, items_data, supplier_ids, order_value)
        """
        # Use session seed if provided, otherwise hash of activities
        if session_seed is not None:
            seed = session_seed
            logger.debug(f"Using session seed: {seed}")
        else:
            # Fallback to activity-based seed (backward compatibility)
            activities_str = '|'.join(sorted(activities))
            seed = hash(activities_str) % (2**31)
            logger.debug(f"Using activity-based seed: {seed}")
        
        random.seed(seed)
        np.random.seed(seed)
        
        # 1. Assign users (deterministic count based on seed)
        if num_users is None:
            num_users = 3  # Fixed at 3 for consistency
        # Generate formatted user IDs like 'U001', 'U002', etc.
        user_nums = random.sample(range(1, 8), min(num_users, 7))
        user_ids = [f'U{num:03d}' for num in user_nums]
        
        # 2. Assign items (deterministic count)
        if num_items is None:
            num_items = 5  # Fixed at 5 for consistency
        
        # Generate formatted item IDs like 'I001', 'I002', etc.
        item_nums = random.sample(range(1, 25), min(num_items, 24))
        selected_item_ids = [f'I{num:03d}' for num in item_nums]
        items_data = []
        order_value = 0.0
        
        for item_id in selected_item_ids:
            # Get item info
            item_row = self.items_df[self.items_df['item_id'] == item_id].iloc[0]
            
            # Deterministic quantity (3-5, seeded by item_id)
            quantity = 3 + (hash(item_id) % 3)  # Always 3, 4, or 5
            unit_price = item_row['unit_price']
            line_total = quantity * unit_price
            order_value += line_total
            
            items_data.append({
                'item_id': item_id,
                'name': item_row['name'],
                'category': item_row['category'],
                'quantity': quantity,
                'unit_price': unit_price,
                'line_total': line_total
            })
        
        # 3. Assign suppliers based on item categories (deterministic)
        supplier_nums = set()
        for item in items_data:
            category = item['category']
            # Get possible suppliers for this category
            possible_suppliers = CATEGORY_SUPPLIER_MAP.get(category, [13, 14, 15, 16])
            # Deterministically select 1 supplier per item based on category
            supplier_idx = hash(item['item_id'] + category) % len(possible_suppliers)
            selected_supplier = possible_suppliers[supplier_idx]
            supplier_nums.add(selected_supplier)
        
        # Generate formatted supplier IDs like 'S001', 'S002', etc.
        supplier_ids = sorted([f'S{num:03d}' for num in supplier_nums])
        
        logger.debug(f"Generated scenario: {len(user_ids)} users, {len(items_data)} items, {len(supplier_ids)} suppliers")
        
        return user_ids, items_data, supplier_ids, order_value
    
    def get_entity_details(
        self,
        user_ids: List[str],
        items_data: List[Dict],
        supplier_ids: List[str]
    ) -> Dict:
        """
        Get detailed information about entities for summary
        
        Args:
            user_ids: List of user IDs
            items_data: List of item dicts
            supplier_ids: List of supplier IDs
        
        Returns:
            Dict with detailed entity information
        """
        # Get user details
        users_info = []
        for user_id in user_ids:
            user_row = self.users_df[self.users_df['user_id'] == user_id]
            if not user_row.empty:
                user = user_row.iloc[0]
                users_info.append({
                    'id': user_id,  # Keep as formatted string like 'U001'
                    'name': user['name'],
                    'role': user.get('role', 'Unknown')
                })
        
        # Items info is already detailed
        items_info = items_data
        
        # Get supplier details
        suppliers_info = []
        for supplier_id in supplier_ids:
            supplier_row = self.suppliers_df[self.suppliers_df['supplier_id'] == supplier_id]
            if not supplier_row.empty:
                supplier = supplier_row.iloc[0]
                suppliers_info.append({
                    'id': supplier_id,  # Keep as formatted string like 'S001'
                    'name': supplier['name'],
                    'specialization': supplier.get('specialization', 'General')
                })
        
        return {
            'users': users_info,
            'items': items_info,
            'suppliers': suppliers_info
        }
    
    def generate_scenario_summary(
        self,
        user_ids: List[str],
        items_data: List[Dict],
        supplier_ids: List[str],
        kpi_predictions: Dict[str, float]
    ) -> str:
        """
        Generate a human-readable summary of the scenario
        
        Args:
            user_ids: List of user IDs
            items_data: List of item dicts
            supplier_ids: List of supplier IDs
            kpi_predictions: Dict of predicted KPI values
        
        Returns:
            Summary string
        """
        # Get detailed entity info
        entity_details = self.get_entity_details(user_ids, items_data, supplier_ids)
        
        # Build summary
        summary_parts = []
        
        # Users summary
        users_str = ', '.join([f"{u['name']} ({u['role']})" for u in entity_details['users']])
        summary_parts.append(f"Team members: {users_str}.")
        
        # Items summary
        total_items = sum([item['quantity'] for item in items_data])
        total_value = sum([item['line_total'] for item in items_data])
        items_str = ', '.join([f"{item['quantity']}× {item['name']}" for item in items_data[:3]])
        if len(items_data) > 3:
            items_str += f", and {len(items_data) - 3} more items"
        summary_parts.append(f"Order contains {total_items} items ({items_str}) worth ${total_value:.2f}.")
        
        # Suppliers summary
        suppliers_str = ', '.join([s['name'] for s in entity_details['suppliers'][:3]])
        if len(entity_details['suppliers']) > 3:
            suppliers_str += f" and {len(entity_details['suppliers']) - 3} others"
        summary_parts.append(f"Sourced from suppliers: {suppliers_str}.")
        
        # KPI predictions summary
        otd = kpi_predictions.get('on_time_delivery', 0)
        dso = kpi_predictions.get('days_sales_outstanding', 0)
        summary_parts.append(
            f"Predicted performance: {otd:.1f}% on-time delivery, "
            f"{dso:.0f} days sales outstanding."
        )
        
        return ' '.join(summary_parts)
    
    def get_user_names(self, user_ids: List[str]) -> List[str]:
        """Get user names by formatted IDs (e.g., 'U001')"""
        names = []
        for user_id in user_ids:
            user_row = self.users_df[self.users_df['user_id'] == user_id]
            if not user_row.empty:
                names.append(user_row.iloc[0]['name'])
        return names
    
    def get_item_names(self, item_ids: List[str]) -> List[str]:
        """Get item names by formatted IDs (e.g., 'I001')"""
        names = []
        for item_id in item_ids:
            item_row = self.items_df[self.items_df['item_id'] == item_id]
            if not item_row.empty:
                names.append(item_row.iloc[0]['name'])
        return names
    
    def get_supplier_names(self, supplier_ids: List[str]) -> List[str]:
        """Get supplier names by formatted IDs (e.g., 'S001')"""
        names = []
        for supplier_id in supplier_ids:
            supplier_row = self.suppliers_df[self.suppliers_df['supplier_id'] == supplier_id]
            if not supplier_row.empty:
                names.append(supplier_row.iloc[0]['name'])
        return names

