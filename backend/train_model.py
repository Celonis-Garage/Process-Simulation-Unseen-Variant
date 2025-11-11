"""
Standalone Model Training Script
Trains the KPI prediction model from the enriched O2C dataset
"""

import numpy as np
import pandas as pd
import pickle
import json
from pathlib import Path
from datetime import datetime
import logging
from lxml import etree as ET
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler
import tensorflow as tf
from tensorflow import keras

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
BACKEND_DIR = Path(__file__).parent
DATA_DIR = BACKEND_DIR.parent / 'data'
MODELS_DIR = BACKEND_DIR / 'trained_models'

# Constants
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

def check_data_files():
    """Check if all required data files exist"""
    required_files = [
        'o2c_data_orders_only.xml',
        'users.csv',
        'items.csv',
        'suppliers.csv',
        'order_kpis.csv',
        'orders_enriched.csv',
        'order_users.csv',
        'order_items.csv',
        'order_suppliers.csv'
    ]
    
    missing = []
    for file in required_files:
        if not (DATA_DIR / file).exists():
            missing.append(file)
    
    if missing:
        logger.error(f"Missing required data files: {missing}")
        logger.error("Please run the Jupyter notebook (cells 41-45) to generate these files")
        return False
    
    logger.info("✓ All required data files found")
    return True


def load_event_log():
    """Load event log from XML"""
    logger.info("Loading event log from XML...")
    
    xml_path = DATA_DIR / 'o2c_data_orders_only.xml'
    tree = ET.parse(str(xml_path))
    root = tree.getroot()
    
    all_events = []
    for trace in root.findall('trace'):
        order_id = None
        for string_elem in trace.findall('string'):
            if string_elem.get('key') == 'concept:name':
                order_id = string_elem.get('value')
                break
        
        events = trace.findall('event')
        for i, event in enumerate(events):
            event_name = None
            event_time = None
            
            # Look for <string> element with key='concept:name'
            for string_elem in event.findall('string'):
                if string_elem.get('key') == 'concept:name':
                    event_name = string_elem.get('value')
                    break
            
            # Look for <date> element with key='time:timestamp'
            for date_elem in event.findall('date'):
                if date_elem.get('key') == 'time:timestamp':
                    event_time = date_elem.get('value')
                    break
            
            if event_name and event_time:
                all_events.append({
                    'order_id': order_id,
                    'event_name': event_name,
                    'timestamp': pd.to_datetime(event_time),
                    'event_sequence': i
                })
    
    df_events = pd.DataFrame(all_events)
    
    if df_events.empty:
        logger.error("No events were extracted from XML. Check XML file format.")
        raise ValueError("Failed to parse events from XML file")
    
    df_events = df_events.sort_values(['order_id', 'timestamp']).reset_index(drop=True)
    
    # Calculate duration to next event
    df_events['duration_minutes'] = 0.0
    for order_id in df_events['order_id'].unique():
        mask = df_events['order_id'] == order_id
        order_events = df_events[mask].copy()
        if len(order_events) > 1:
            durations = (order_events['timestamp'].shift(-1) - order_events['timestamp']).dt.total_seconds() / 60
            df_events.loc[mask, 'duration_minutes'] = durations.fillna(0).values
    
    logger.info(f"✓ Loaded {len(df_events)} events for {df_events['order_id'].nunique()} orders")
    return df_events


def extract_features_for_order(order_id, df_events, df_users, df_items, df_suppliers):
    """Extract 417-dimensional feature vector for one order"""
    
    # Get events for this order
    order_events = df_events[df_events['order_id'] == order_id].copy()
    activities = order_events['event_name'].tolist()
    
    # 1. Transition matrix (frequency) - 13x13 = 169
    freq_matrix = np.zeros((13, 13))
    event_to_idx = {event: idx for idx, event in enumerate(ALL_EVENTS)}
    
    for i in range(len(order_events) - 1):
        from_event = order_events.iloc[i]['event_name']
        to_event = order_events.iloc[i + 1]['event_name']
        if from_event in event_to_idx and to_event in event_to_idx:
            from_idx = event_to_idx[from_event]
            to_idx = event_to_idx[to_event]
            freq_matrix[from_idx, to_idx] += 1
    
    freq_features = freq_matrix.flatten()
    
    # 2. Transition matrix (duration in minutes) - 13x13 = 169
    duration_matrix = np.zeros((13, 13))
    for i in range(len(order_events) - 1):
        from_event = order_events.iloc[i]['event_name']
        to_event = order_events.iloc[i + 1]['event_name']
        duration = order_events.iloc[i]['duration_minutes']
        if from_event in event_to_idx and to_event in event_to_idx:
            from_idx = event_to_idx[from_event]
            to_idx = event_to_idx[to_event]
            duration_matrix[from_idx, to_idx] = duration
    
    duration_features = duration_matrix.flatten()
    
    # 3. User vector - 7
    user_vector = np.zeros(7)
    order_users = df_users[df_users['order_id'] == order_id]
    for user_id in order_users['user_id'].values:
        # Extract numeric part from 'U001' format
        user_id_num = int(user_id[1:]) if isinstance(user_id, str) and user_id.startswith('U') else int(user_id)
        if 1 <= user_id_num <= 7:
            user_vector[user_id_num - 1] = 1
    
    # 4. Items matrix - 24x2 = 48
    items_matrix = np.zeros((24, 2))
    order_items = df_items[df_items['order_id'] == order_id]
    for _, item in order_items.iterrows():
        # Extract numeric part from 'I001' format
        item_id_str = item['item_id']
        item_id_num = int(item_id_str[1:]) if isinstance(item_id_str, str) and item_id_str.startswith('I') else int(item_id_str)
        if 1 <= item_id_num <= 24:
            idx = item_id_num - 1
            items_matrix[idx, 0] = item['quantity']
            items_matrix[idx, 1] = item['line_total']
    
    items_features = items_matrix.flatten()
    
    # 5. Supplier vector - 16
    supplier_vector = np.zeros(16)
    order_suppliers = df_suppliers[df_suppliers['order_id'] == order_id]
    for supplier_id in order_suppliers['supplier_id'].values:
        # Extract numeric part from 'S001' format
        supplier_id_num = int(supplier_id[1:]) if isinstance(supplier_id, str) and supplier_id.startswith('S') else int(supplier_id)
        if 1 <= supplier_id_num <= 16:
            supplier_vector[supplier_id_num - 1] = 1
    
    # 6. Outcome features - 8 (NEW!)
    # These explicitly capture business logic for the model to learn
    activity_set = set(activities)
    
    # Baseline activities for completeness
    baseline_activities = [
        'Receive Customer Order', 'Validate Customer Order', 'Perform Credit Check',
        'Approve Order', 'Schedule Order Fulfillment', 'Generate Pick List',
        'Pack Items', 'Generate Shipping Label', 'Ship Order', 'Generate Invoice'
    ]
    
    has_rejection = 1.0 if 'Reject Order' in activity_set else 0.0
    has_return = 1.0 if 'Process Return Request' in activity_set else 0.0
    has_cancellation = 1.0 if 'Cancel Order' in activity_set else 0.0
    process_completed = 1.0 if 'Generate Invoice' in activity_set else 0.0
    completeness_ratio = min(len(activities) / len(baseline_activities), 2.0)
    
    if has_rejection and 'Reject Order' in activities:
        rejection_position = activities.index('Reject Order') / max(len(activities), 1)
    else:
        rejection_position = 0.0
    
    generates_revenue = 1.0 if ('Ship Order' in activity_set and 'Generate Invoice' in activity_set) else 0.0
    has_discount = 1.0 if 'Apply Discount' in activity_set else 0.0
    
    outcome_features = np.array([
        has_rejection,
        has_return,
        has_cancellation,
        process_completed,
        completeness_ratio,
        rejection_position,
        generates_revenue,
        has_discount
    ])
    
    # Concatenate all features (now 417 dimensions)
    feature_vector = np.concatenate([
        freq_features,
        duration_features,
        user_vector,
        items_features,
        supplier_vector,
        outcome_features  # NEW: 8 outcome features
    ])
    
    return feature_vector


def prepare_dataset():
    """Load and prepare the complete dataset"""
    logger.info("="*80)
    logger.info("PREPARING DATASET")
    logger.info("="*80)
    
    # Load all data
    df_events = load_event_log()
    df_kpis = pd.read_csv(DATA_DIR / 'order_kpis.csv')
    df_users = pd.read_csv(DATA_DIR / 'order_users.csv')
    df_items = pd.read_csv(DATA_DIR / 'order_items.csv')
    df_suppliers = pd.read_csv(DATA_DIR / 'order_suppliers.csv')
    
    logger.info(f"✓ Loaded KPIs for {len(df_kpis)} orders")
    
    # Get unique orders
    order_ids = df_kpis['order_id'].unique()
    logger.info(f"✓ Processing {len(order_ids)} orders")
    
    # Extract features for all orders
    logger.info("Extracting features (this may take a few minutes)...")
    X = []
    y = []
    
    for i, order_id in enumerate(order_ids):
        if (i + 1) % 100 == 0:
            logger.info(f"  Processed {i + 1}/{len(order_ids)} orders...")
        
        # Extract features
        features = extract_features_for_order(order_id, df_events, df_users, df_items, df_suppliers)
        X.append(features)
        
        # Extract target KPIs (use normalized columns)
        kpi_row = df_kpis[df_kpis['order_id'] == order_id].iloc[0]
        kpis = np.array([
            kpi_row['on_time_delivery_normalized'],
            kpi_row['days_sales_outstanding_normalized'],
            kpi_row['order_accuracy_normalized'],
            kpi_row['invoice_accuracy_normalized'],
            kpi_row['avg_cost_delivery_normalized']
        ])
        y.append(kpis)
    
    X = np.array(X)
    y = np.array(y)
    
    logger.info(f"✓ Feature extraction complete")
    logger.info(f"  Features shape: {X.shape}")
    logger.info(f"  Targets shape: {y.shape}")
    
    return X, y


def normalize_features(X_train, X_val, X_test):
    """Apply feature normalization with separate scalers"""
    logger.info("Applying feature normalization...")
    
    # Split features into groups (updated for 417 dimensions)
    freq_idx = slice(0, 169)
    duration_idx = slice(169, 338)
    users_idx = slice(338, 345)
    items_idx = slice(345, 393)
    suppliers_idx = slice(393, 409)
    outcome_idx = slice(409, 417)  # NEW: Outcome features
    
    # Extract feature groups
    X_freq_train = X_train[:, freq_idx]
    X_duration_train = X_train[:, duration_idx]
    X_users_train = X_train[:, users_idx]
    X_items_train = X_train[:, items_idx]
    X_suppliers_train = X_train[:, suppliers_idx]
    X_outcome_train = X_train[:, outcome_idx]  # NEW
    
    X_freq_val = X_val[:, freq_idx]
    X_duration_val = X_val[:, duration_idx]
    X_users_val = X_val[:, users_idx]
    X_items_val = X_val[:, items_idx]
    X_suppliers_val = X_val[:, suppliers_idx]
    X_outcome_val = X_val[:, outcome_idx]  # NEW
    
    X_freq_test = X_test[:, freq_idx]
    X_duration_test = X_test[:, duration_idx]
    X_users_test = X_test[:, users_idx]
    X_items_test = X_test[:, items_idx]
    X_suppliers_test = X_test[:, suppliers_idx]
    X_outcome_test = X_test[:, outcome_idx]  # NEW
    
    # Split items into quantity and line total
    items_qty_train = X_items_train[:, ::2].reshape(-1, 24)
    items_amt_train = X_items_train[:, 1::2].reshape(-1, 24)
    items_qty_val = X_items_val[:, ::2].reshape(-1, 24)
    items_amt_val = X_items_val[:, 1::2].reshape(-1, 24)
    items_qty_test = X_items_test[:, ::2].reshape(-1, 24)
    items_amt_test = X_items_test[:, 1::2].reshape(-1, 24)
    
    # Initialize and fit scalers
    scaler_freq = MinMaxScaler()
    scaler_duration = RobustScaler()
    scaler_users = MinMaxScaler()
    scaler_items_qty = StandardScaler()
    scaler_items_amt = RobustScaler()
    scaler_suppliers = MinMaxScaler()
    scaler_outcome = MinMaxScaler()  # NEW: For outcome features (already in 0-2 range)
    
    # Fit and transform
    X_freq_train_scaled = scaler_freq.fit_transform(X_freq_train)
    X_freq_val_scaled = scaler_freq.transform(X_freq_val)
    X_freq_test_scaled = scaler_freq.transform(X_freq_test)
    
    X_duration_train_scaled = scaler_duration.fit_transform(X_duration_train)
    X_duration_val_scaled = scaler_duration.transform(X_duration_val)
    X_duration_test_scaled = scaler_duration.transform(X_duration_test)
    
    X_users_train_scaled = scaler_users.fit_transform(X_users_train)
    X_users_val_scaled = scaler_users.transform(X_users_val)
    X_users_test_scaled = scaler_users.transform(X_users_test)
    
    items_qty_train_scaled = scaler_items_qty.fit_transform(items_qty_train)
    items_qty_val_scaled = scaler_items_qty.transform(items_qty_val)
    items_qty_test_scaled = scaler_items_qty.transform(items_qty_test)
    
    items_amt_train_scaled = scaler_items_amt.fit_transform(items_amt_train)
    items_amt_val_scaled = scaler_items_amt.transform(items_amt_val)
    items_amt_test_scaled = scaler_items_amt.transform(items_amt_test)
    
    X_suppliers_train_scaled = scaler_suppliers.fit_transform(X_suppliers_train)
    X_suppliers_val_scaled = scaler_suppliers.transform(X_suppliers_val)
    X_suppliers_test_scaled = scaler_suppliers.transform(X_suppliers_test)
    
    X_outcome_train_scaled = scaler_outcome.fit_transform(X_outcome_train)  # NEW
    X_outcome_val_scaled = scaler_outcome.transform(X_outcome_val)  # NEW
    X_outcome_test_scaled = scaler_outcome.transform(X_outcome_test)  # NEW
    
    # Interleave items back together
    items_train_scaled = np.empty((len(items_qty_train_scaled), 48))
    items_train_scaled[:, ::2] = items_qty_train_scaled
    items_train_scaled[:, 1::2] = items_amt_train_scaled
    
    items_val_scaled = np.empty((len(items_qty_val_scaled), 48))
    items_val_scaled[:, ::2] = items_qty_val_scaled
    items_val_scaled[:, 1::2] = items_amt_val_scaled
    
    items_test_scaled = np.empty((len(items_qty_test_scaled), 48))
    items_test_scaled[:, ::2] = items_qty_test_scaled
    items_test_scaled[:, 1::2] = items_amt_test_scaled
    
    # Concatenate all scaled features (now 417 dimensions)
    X_train_scaled = np.concatenate([
        X_freq_train_scaled, X_duration_train_scaled, X_users_train_scaled,
        items_train_scaled, X_suppliers_train_scaled, X_outcome_train_scaled  # NEW
    ], axis=1)
    
    X_val_scaled = np.concatenate([
        X_freq_val_scaled, X_duration_val_scaled, X_users_val_scaled,
        items_val_scaled, X_suppliers_val_scaled, X_outcome_val_scaled  # NEW
    ], axis=1)
    
    X_test_scaled = np.concatenate([
        X_freq_test_scaled, X_duration_test_scaled, X_users_test_scaled,
        items_test_scaled, X_suppliers_test_scaled, X_outcome_test_scaled  # NEW
    ], axis=1)
    
    scalers = {
        'freq': scaler_freq,
        'duration': scaler_duration,
        'users': scaler_users,
        'items_qty': scaler_items_qty,
        'items_amt': scaler_items_amt,
        'suppliers': scaler_suppliers,
        'outcome': scaler_outcome  # NEW
    }
    
    logger.info(f"✓ Normalization complete")
    logger.info(f"  Training features: {X_train_scaled.shape}")
    logger.info(f"  Validation features: {X_val_scaled.shape}")
    logger.info(f"  Test features: {X_test_scaled.shape}")
    
    return X_train_scaled, X_val_scaled, X_test_scaled, scalers


def build_model():
    """Build the KPI prediction model"""
    inputs = keras.Input(shape=(417,), name='process_features')  # Updated from 409 to 417
    
    # Shared layers with regularization
    x = keras.layers.Dense(256, kernel_regularizer=keras.regularizers.l2(0.0001))(inputs)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Activation('relu')(x)
    x = keras.layers.Dropout(0.3)(x)
    
    x = keras.layers.Dense(128, kernel_regularizer=keras.regularizers.l2(0.0001))(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Activation('relu')(x)
    x = keras.layers.Dropout(0.2)(x)
    
    x = keras.layers.Dense(64, kernel_regularizer=keras.regularizers.l2(0.0001))(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Activation('relu')(x)
    x = keras.layers.Dropout(0.1)(x)
    
    # 5 output heads
    on_time_delivery = keras.layers.Dense(1, activation='linear', name='on_time_delivery')(x)
    days_sales_outstanding = keras.layers.Dense(1, activation='linear', name='days_sales_outstanding')(x)
    order_accuracy = keras.layers.Dense(1, activation='linear', name='order_accuracy')(x)
    invoice_accuracy = keras.layers.Dense(1, activation='linear', name='invoice_accuracy')(x)
    avg_cost_delivery = keras.layers.Dense(1, activation='linear', name='avg_cost_delivery')(x)
    
    model = keras.Model(
        inputs=inputs,
        outputs=[on_time_delivery, days_sales_outstanding, order_accuracy, 
                invoice_accuracy, avg_cost_delivery]
    )
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001, clipnorm=1.0),
        loss=[keras.losses.Huber(delta=1.0) for _ in range(5)],
        metrics=[['mae'] for _ in range(5)]
    )
    
    logger.info("✓ Model architecture built: 256 → 128 → 64 → 5 outputs")
    return model


def train_model():
    """Main training pipeline"""
    logger.info("="*80)
    logger.info("🚀 STARTING MODEL TRAINING")
    logger.info("="*80)
    
    start_time = datetime.now()
    
    # Check data files
    if not check_data_files():
        logger.error("❌ Cannot proceed without required data files")
        return False
    
    # Prepare dataset
    X, y = prepare_dataset()
    
    # Split data (70% train, 15% val, 15% test)
    logger.info("Splitting dataset...")
    X_train, X_temp, y_train, y_temp = train_test_split(X, y, test_size=0.3, random_state=42)
    X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=0.5, random_state=42)
    
    logger.info(f"✓ Train: {len(X_train)} samples")
    logger.info(f"✓ Validation: {len(X_val)} samples")
    logger.info(f"✓ Test: {len(X_test)} samples")
    
    # Normalize features
    X_train_scaled, X_val_scaled, X_test_scaled, scalers = normalize_features(X_train, X_val, X_test)
    
    # Prepare targets (already normalized)
    y_train_list = [y_train[:, i:i+1] for i in range(5)]
    y_val_list = [y_val[:, i:i+1] for i in range(5)]
    
    # Build model
    logger.info("="*80)
    logger.info("BUILDING MODEL")
    logger.info("="*80)
    model = build_model()
    
    # Callbacks
    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor='val_loss',
            patience=50,
            restore_best_weights=True,
            verbose=1
        ),
        keras.callbacks.ReduceLROnPlateau(
            monitor='val_loss',
            factor=0.5,
            patience=15,
            min_lr=1e-6,
            verbose=1
        )
    ]
    
    # Train
    logger.info("="*80)
    logger.info("TRAINING MODEL")
    logger.info("="*80)
    logger.info("Training will stop early if validation loss doesn't improve")
    logger.info("This may take 5-10 minutes depending on your CPU...")
    
    history = model.fit(
        X_train_scaled,
        y_train_list,
        validation_data=(X_val_scaled, y_val_list),
        epochs=300,
        batch_size=32,
        callbacks=callbacks,
        verbose=1
    )
    
    # Save model and scalers
    logger.info("="*80)
    logger.info("SAVING MODEL")
    logger.info("="*80)
    MODELS_DIR.mkdir(exist_ok=True)
    
    model.save(MODELS_DIR / 'kpi_prediction_model.keras')
    logger.info(f"✓ Saved model to {MODELS_DIR / 'kpi_prediction_model.keras'}")
    
    for name, scaler in scalers.items():
        with open(MODELS_DIR / f'scaler_{name}.pkl', 'wb') as f:
            pickle.dump(scaler, f)
    logger.info(f"✓ Saved {len(scalers)} feature scalers")
    
    # Save normalization config
    normalization_config = {
        'on_time_delivery': 'value / 100',
        'days_sales_outstanding': 'value / 90',
        'order_accuracy': 'value / 100',
        'invoice_accuracy': 'value / 100',
        'avg_cost_delivery': 'value / 100'
    }
    with open(MODELS_DIR / 'kpi_normalization_config.json', 'w') as f:
        json.dump(normalization_config, f, indent=2)
    logger.info("✓ Saved KPI normalization config")
    
    # Calculate and save dataset hash
    from ml_model import calculate_dataset_hash
    dataset_hash = calculate_dataset_hash(DATA_DIR)
    with open(MODELS_DIR / 'dataset_hash.txt', 'w') as f:
        f.write(dataset_hash)
    logger.info(f"✓ Saved dataset hash: {dataset_hash[:16]}...")
    
    # Evaluate on test set
    logger.info("="*80)
    logger.info("EVALUATING ON TEST SET")
    logger.info("="*80)
    
    y_test_list = [y_test[:, i:i+1] for i in range(5)]
    test_results = model.evaluate(X_test_scaled, y_test_list, verbose=0)
    
    logger.info(f"Test Loss: {test_results[0]:.6f}")
    for i, kpi_name in enumerate(['on_time_delivery', 'days_sales_outstanding', 
                                   'order_accuracy', 'invoice_accuracy', 'avg_cost_delivery']):
        logger.info(f"  {kpi_name}_mae: {test_results[i*2+2]:.6f}")
    
    # Training summary
    elapsed_time = datetime.now() - start_time
    logger.info("="*80)
    logger.info("✅ TRAINING COMPLETE!")
    logger.info("="*80)
    logger.info(f"Total time: {elapsed_time}")
    logger.info(f"Final training loss: {history.history['loss'][-1]:.6f}")
    logger.info(f"Final validation loss: {history.history['val_loss'][-1]:.6f}")
    logger.info(f"Epochs trained: {len(history.history['loss'])}")
    logger.info("="*80)
    logger.info("🎉 Model ready for predictions!")
    logger.info("="*80)
    
    return True


if __name__ == "__main__":
    try:
        success = train_model()
        if success:
            print("\n✅ Model training completed successfully!")
            print("You can now start the backend with: python main.py")
            exit(0)
        else:
            print("\n❌ Model training failed. Check logs above.")
            exit(1)
    except Exception as e:
        logger.error(f"❌ Training failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        exit(1)

