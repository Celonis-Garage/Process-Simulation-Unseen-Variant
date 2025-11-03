"""
ML Model for KPI Prediction
Implements the deep learning model from the Jupyter notebook (Cells 45-49)
"""

import numpy as np
import pandas as pd
import pickle
import hashlib
import json
import logging
from pathlib import Path
from typing import Tuple, Dict, Optional
import tensorflow as tf
from tensorflow import keras

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
FEATURE_DIM = 409
NUM_KPIS = 5
KPI_NAMES = [
    'on_time_delivery',
    'days_sales_outstanding',
    'order_accuracy',
    'invoice_accuracy',
    'avg_cost_delivery'
]

# KPI denormalization multipliers
KPI_MULTIPLIERS = [100, 90, 100, 100, 100]


def build_kpi_model(input_dim: int = FEATURE_DIM, use_dropout: bool = True) -> keras.Model:
    """
    Build multi-output KPI prediction model with regularization for generalization
    
    Args:
        input_dim: Number of input features (default: 409)
        use_dropout: Whether to use dropout layers (default: True for generalization)
    
    Returns:
        Compiled Keras model
    """
    # Input layer
    inputs = keras.Input(shape=(input_dim,), name='process_features')
    
    # Shared dense layers with regularization
    x = keras.layers.Dense(256, kernel_regularizer=keras.regularizers.l2(0.0001))(inputs)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Activation('relu')(x)
    if use_dropout:
        x = keras.layers.Dropout(0.3)(x)
    
    x = keras.layers.Dense(128, kernel_regularizer=keras.regularizers.l2(0.0001))(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Activation('relu')(x)
    if use_dropout:
        x = keras.layers.Dropout(0.2)(x)
    
    x = keras.layers.Dense(64, kernel_regularizer=keras.regularizers.l2(0.0001))(x)
    x = keras.layers.BatchNormalization()(x)
    x = keras.layers.Activation('relu')(x)
    if use_dropout:
        x = keras.layers.Dropout(0.1)(x)
    
    # 5 separate output heads for each KPI
    on_time_delivery = keras.layers.Dense(1, activation='linear', name='on_time_delivery')(x)
    days_sales_outstanding = keras.layers.Dense(1, activation='linear', name='days_sales_outstanding')(x)
    order_accuracy = keras.layers.Dense(1, activation='linear', name='order_accuracy')(x)
    invoice_accuracy = keras.layers.Dense(1, activation='linear', name='invoice_accuracy')(x)
    avg_cost_delivery = keras.layers.Dense(1, activation='linear', name='avg_cost_delivery')(x)
    
    # Build model
    model = keras.Model(
        inputs=inputs,
        outputs=[on_time_delivery, days_sales_outstanding, order_accuracy, 
                invoice_accuracy, avg_cost_delivery]
    )
    
    # Compile with Huber loss (robust to outliers)
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001, clipnorm=1.0),
        loss=[keras.losses.Huber(delta=1.0) for _ in range(5)],
        metrics=[['mae', 'mse'] for _ in range(5)]
    )
    
    logger.info(f"✓ Model architecture defined: 256 → 128 → 64 → 5 outputs")
    return model


def calculate_dataset_hash(data_dir: Path) -> str:
    """
    Calculate hash of all dataset files to detect changes
    
    Args:
        data_dir: Path to data directory
    
    Returns:
        SHA256 hash string
    """
    hash_md5 = hashlib.sha256()
    
    # Files to hash
    files_to_hash = [
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
    
    for filename in sorted(files_to_hash):
        filepath = data_dir / filename
        if filepath.exists():
            with open(filepath, 'rb') as f:
                # Read in chunks for large files
                for chunk in iter(lambda: f.read(4096), b''):
                    hash_md5.update(chunk)
    
    return hash_md5.hexdigest()


def save_model_and_scalers(
    model: keras.Model,
    scalers: Dict,
    models_dir: Path,
    dataset_hash: str
):
    """
    Save trained model, scalers, and dataset hash
    
    Args:
        model: Trained Keras model
        scalers: Dictionary of fitted scalers
        models_dir: Directory to save models
        dataset_hash: Hash of the dataset
    """
    models_dir.mkdir(exist_ok=True)
    
    # Save model
    model.save(models_dir / 'kpi_prediction_model.keras')
    logger.info(f"✓ Saved model to {models_dir / 'kpi_prediction_model.keras'}")
    
    # Save scalers
    for name, scaler in scalers.items():
        scaler_path = models_dir / f'scaler_{name}.pkl'
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler, f)
    logger.info(f"✓ Saved {len(scalers)} scalers")
    
    # Save dataset hash
    with open(models_dir / 'dataset_hash.txt', 'w') as f:
        f.write(dataset_hash)
    logger.info(f"✓ Saved dataset hash")
    
    # Save normalization config
    normalization_config = {
        'on_time_delivery': 'value / 100',
        'days_sales_outstanding': 'value / 90',
        'order_accuracy': 'value / 100',
        'invoice_accuracy': 'value / 100',
        'avg_cost_delivery': 'value / 100'
    }
    with open(models_dir / 'kpi_normalization_config.json', 'w') as f:
        json.dump(normalization_config, f, indent=2)
    logger.info(f"✓ Saved KPI normalization config")


def load_model_and_scalers(models_dir: Path) -> Tuple[keras.Model, Dict]:
    """
    Load trained model and scalers from disk
    
    Args:
        models_dir: Directory containing saved models
    
    Returns:
        Tuple of (model, scalers_dict)
    """
    # Load model
    model = keras.models.load_model(models_dir / 'kpi_prediction_model.keras')
    logger.info(f"✓ Loaded model from {models_dir / 'kpi_prediction_model.keras'}")
    
    # Load scalers
    scaler_names = ['freq', 'duration', 'users', 'items_qty', 'items_amt', 'suppliers']
    scalers = {}
    for name in scaler_names:
        scaler_path = models_dir / f'scaler_{name}.pkl'
        with open(scaler_path, 'rb') as f:
            scalers[name] = pickle.load(f)
    logger.info(f"✓ Loaded {len(scalers)} scalers")
    
    return model, scalers


def check_cached_model(models_dir: Path, current_hash: str) -> bool:
    """
    Check if cached model exists and dataset hasn't changed
    
    Args:
        models_dir: Directory containing saved models
        current_hash: Current dataset hash
    
    Returns:
        True if cached model is valid, False otherwise
    """
    model_path = models_dir / 'kpi_prediction_model.keras'
    hash_path = models_dir / 'dataset_hash.txt'
    
    if not model_path.exists() or not hash_path.exists():
        logger.info("❌ No cached model found")
        return False
    
    with open(hash_path, 'r') as f:
        cached_hash = f.read().strip()
    
    if cached_hash != current_hash:
        logger.info("❌ Dataset has changed, need to retrain")
        return False
    
    logger.info("✓ Cached model is valid")
    return True


def denormalize_kpi(normalized_value: float, kpi_index: int) -> float:
    """
    Convert normalized KPI value back to original scale
    
    Args:
        normalized_value: Normalized value in [0, 1] range
        kpi_index: Index of the KPI (0-4)
    
    Returns:
        Denormalized value in original units
    """
    return normalized_value * KPI_MULTIPLIERS[kpi_index]


def denormalize_kpis(normalized_predictions: np.ndarray) -> Dict[str, float]:
    """
    Denormalize all KPI predictions
    
    Args:
        normalized_predictions: Array of shape (5,) with normalized KPI values
    
    Returns:
        Dictionary mapping KPI names to denormalized values
    """
    result = {}
    for i, kpi_name in enumerate(KPI_NAMES):
        result[kpi_name] = denormalize_kpi(normalized_predictions[i], i)
    return result


def predict_kpis(
    model: keras.Model,
    feature_vector: np.ndarray
) -> Dict[str, float]:
    """
    Predict KPIs for a given feature vector
    
    Args:
        model: Trained Keras model
        feature_vector: Feature vector of shape (1, 409) or (409,)
    
    Returns:
        Dictionary mapping KPI names to predicted values (denormalized)
    """
    # Ensure correct shape
    if feature_vector.ndim == 1:
        feature_vector = feature_vector.reshape(1, -1)
    
    # Predict (returns list of 5 arrays)
    predictions = model.predict(feature_vector, verbose=0)
    
    # Extract values (each prediction is shape (1, 1))
    normalized_values = np.array([pred[0, 0] for pred in predictions])
    
    # Denormalize
    denormalized_kpis = denormalize_kpis(normalized_values)
    
    return denormalized_kpis


class ModelManager:
    """
    Manager class for ML model lifecycle
    """
    def __init__(self, backend_dir: Path):
        self.backend_dir = backend_dir
        self.data_dir = backend_dir.parent / 'data'
        self.models_dir = backend_dir / 'trained_models'
        self.model: Optional[keras.Model] = None
        self.scalers: Optional[Dict] = None
        self.baseline_kpis: Optional[Dict[str, float]] = None
    
    def initialize(self, force_retrain: bool = False):
        """
        Initialize model - load from cache or train from scratch
        
        Args:
            force_retrain: Force retraining even if cached model exists
        """
        logger.info("="*80)
        logger.info("INITIALIZING ML MODEL FOR KPI PREDICTION")
        logger.info("="*80)
        
        # Calculate dataset hash
        current_hash = calculate_dataset_hash(self.data_dir)
        logger.info(f"Dataset hash: {current_hash[:16]}...")
        
        # Check if we can use cached model
        use_cached = not force_retrain and check_cached_model(self.models_dir, current_hash)
        
        if use_cached:
            try:
                logger.info("Loading cached model...")
                self.model, self.scalers = load_model_and_scalers(self.models_dir)
                logger.info("✓ Model loaded from cache")
            except Exception as e:
                logger.error(f"Failed to load cached model: {e}")
                logger.info("Will train from scratch...")
                use_cached = False
        
        if not use_cached:
            logger.info("Training model from scratch...")
            self._train_model(current_hash)
        
        # Load baseline KPIs (from most frequent variant)
        self._load_baseline_kpis()
        
        logger.info("="*80)
        logger.info("✓ MODEL INITIALIZATION COMPLETE")
        logger.info("="*80)
    
    def _train_model(self, dataset_hash: str):
        """
        Train model from scratch (placeholder - requires full implementation)
        """
        # This would require loading all the data and training
        # For now, we'll implement a simplified version
        logger.warning("Full training implementation required - using placeholder")
        raise NotImplementedError("Full model training not yet implemented")
    
    def _load_baseline_kpis(self):
        """
        Load baseline KPIs from most frequent variant
        """
        # Load order KPIs to calculate baseline
        kpis_path = self.data_dir / 'order_kpis.csv'
        if kpis_path.exists():
            df_kpis = pd.read_csv(kpis_path)
            
            # Calculate mean of normalized KPIs and denormalize
            self.baseline_kpis = {}
            for i, kpi_name in enumerate(KPI_NAMES):
                norm_col = f'{kpi_name}_normalized'
                if norm_col in df_kpis.columns:
                    mean_norm = df_kpis[norm_col].mean()
                    self.baseline_kpis[kpi_name] = denormalize_kpi(mean_norm, i)
            
            logger.info(f"✓ Loaded baseline KPIs: {self.baseline_kpis}")
        else:
            logger.warning(f"KPIs file not found: {kpis_path}")
            # Default baseline KPIs
            self.baseline_kpis = {
                'on_time_delivery': 79.8,
                'days_sales_outstanding': 38.0,
                'order_accuracy': 81.3,
                'invoice_accuracy': 76.5,
                'avg_cost_delivery': 33.48
            }
            logger.info(f"Using default baseline KPIs: {self.baseline_kpis}")
    
    def predict(self, feature_vector: np.ndarray) -> Dict[str, float]:
        """
        Predict KPIs for a given feature vector
        
        Args:
            feature_vector: Feature vector of shape (1, 409) or (409,)
        
        Returns:
            Dictionary mapping KPI names to predicted values
        """
        if self.model is None:
            raise ValueError("Model not initialized. Call initialize() first.")
        
        return predict_kpis(self.model, feature_vector)
    
    def get_baseline_kpis(self) -> Dict[str, float]:
        """
        Get baseline KPIs
        
        Returns:
            Dictionary mapping KPI names to baseline values
        """
        if self.baseline_kpis is None:
            self._load_baseline_kpis()
        return self.baseline_kpis

