from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import os
import logging
import traceback
from pathlib import Path

from simulation_engine import SimulationEngine
from real_data_loader import get_data_loader, get_baseline_kpis_from_data
from utils import parse_prompt_mock, graph_to_networkx
from llm_service import GroqLLMService
from ml_model import ModelManager
from scenario_generator import ScenarioGenerator
from session_manager import get_session_manager
from feature_extraction import (
    extract_features_from_scenario,
    enrich_edges_with_durations,
    parse_activity_duration
)
from usd_builder import generate_gltf_for_case, get_sample_case_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
HOURLY_RATE = 25.0  # Default hourly rate for cost calculation

app = FastAPI(title="Process Simulation Studio API", version="1.0.0")

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class PromptRequest(BaseModel):
    prompt: str
    current_process: Optional[Dict[str, Any]] = None  # Include current process state
    session_id: Optional[str] = None  # Session ID for entity consistency

class ProcessGraph(BaseModel):
    activities: List[str]
    edges: List[Dict[str, Any]]  # Changed from Dict[str, str] to Dict[str, Any] to accept id, cases, avgDays
    kpis: Dict[str, Dict[str, float]]

class EventLogRequest(BaseModel):
    graph: ProcessGraph
    session_id: Optional[str] = None  # Session ID for entity consistency

class SimulationRequest(BaseModel):
    event_log: List[Dict[str, Any]]
    graph: ProcessGraph
    session_id: Optional[str] = None  # Session ID for entity consistency

class PromptResponse(BaseModel):
    action: str
    activity: Optional[str] = None  # For remove_step action
    new_activity: Optional[str] = None
    position: Optional[Dict[str, str]] = None
    modifications: Optional[Dict[str, Any]] = None
    message: Optional[str] = None  # For clarification_needed responses
    explanation: Optional[str] = None  # For all responses
    confidence: Optional[float] = None  # Confidence score
    suggestions: Optional[List[str]] = None  # Suggestions for clarification
    
    # NEW: Fields for select_variant action (context-aware variant selection)
    variant_id: Optional[str] = None  # Selected variant ID
    activities: Optional[List[str]] = None  # List of activity names in the variant
    kpis: Optional[Dict[str, Dict[str, str]]] = None  # KPIs for each activity (avgTime, avgCost)
    suggested_prompts: Optional[List[str]] = None  # Suggested next prompts after variant selection

class SimulationResponse(BaseModel):
    # Baseline KPIs (before changes)
    baseline_on_time_delivery: float
    baseline_days_sales_outstanding: float
    baseline_order_accuracy: float
    baseline_invoice_accuracy: float
    baseline_avg_cost_delivery: float
    
    # Current KPIs (after changes)
    on_time_delivery: float
    days_sales_outstanding: float
    order_accuracy: float
    invoice_accuracy: float
    avg_cost_delivery: float
    
    # Metadata
    confidence: float
    summary: str

class NarrationRequest(BaseModel):
    event_name: str
    timestamp: str
    case_id: str
    order_value: Optional[float] = 0.0
    order_status: Optional[str] = "Processing"
    user: Optional[str] = "System"  # Single user who performed this event
    items: Optional[List[Dict[str, Any]]] = []  # Only items relevant to this event
    suppliers: Optional[List[str]] = []  # Only suppliers relevant to this event
    variant_id: Optional[str] = None
    current_time: Optional[float] = 0.0

class NarrationResponse(BaseModel):
    narration: str
    event_name: str
    timestamp: str

# Initialize
simulation_engine = SimulationEngine()
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = Path(current_dir)
data_dir = backend_dir.parent / 'data'
data_file_path = str(data_dir / 'o2c_data_orders_only.xml')
data_loader = get_data_loader(data_file_path)

# Initialize ML model manager and scenario generator
model_manager: Optional[ModelManager] = None
scenario_generator: Optional[ScenarioGenerator] = None
use_ml_predictions = False  # Flag to indicate if ML model is available

# Initialize LLM service (will be properly initialized after data_loader in startup)
llm_service = None

# Initialize Session Manager for entity consistency
session_manager = get_session_manager()
logger.info("✅ Session Manager initialized")


@app.on_event("startup")
async def startup_event():
    """Initialize ML model and scenario generator at startup"""
    global model_manager, scenario_generator, use_ml_predictions, llm_service
    
    logger.info("="*80)
    logger.info("🚀 BACKEND STARTUP - Initializing ML Model")
    logger.info("="*80)
    
    try:
        # Create exports directory for 3D visualization files
        exports_dir = backend_dir / 'exports'
        exports_dir.mkdir(exist_ok=True)
        logger.info(f"✓ Exports directory ready: {exports_dir}")
        
        # Mount static files for serving exported scenes
        try:
            app.mount("/exports", StaticFiles(directory=str(exports_dir)), name="exports")
            logger.info("✓ Static files mounted at /exports")
        except Exception as e:
            logger.warning(f"⚠️ Could not mount static files: {e}")
        
        # Create trained_models directory if it doesn't exist
        models_dir = backend_dir / 'trained_models'
        models_dir.mkdir(exist_ok=True)
        logger.info(f"✓ Models directory ready: {models_dir}")
        
        # Check if model and data files exist
        model_file = models_dir / 'kpi_prediction_model.keras'
        data_files_exist = all([
            (data_dir / f).exists() for f in [
                'users.csv', 'items.csv', 'suppliers.csv', 
                'order_kpis.csv', 'orders_enriched.csv'
            ]
        ])
        
        if model_file.exists() and data_files_exist:
            logger.info("✓ Model and data files found - initializing ML prediction system...")
            
            # Initialize Model Manager
            model_manager = ModelManager(backend_dir)
            try:
                model_manager.initialize(force_retrain=False)
                logger.info("✅ ML Model loaded successfully")
                
                # Initialize Scenario Generator
                scenario_generator = ScenarioGenerator(data_dir)
                logger.info("✅ Scenario Generator initialized")
                
                use_ml_predictions = True
                logger.info("✅ ML-BASED KPI PREDICTION ENABLED")
            except NotImplementedError:
                logger.warning("⚠️ Model training not yet implemented - using cached model if available")
                # Try to load cached model directly
                if model_file.exists():
                    try:
                        from ml_model import load_model_and_scalers
                        model_manager.model, model_manager.scalers = load_model_and_scalers(models_dir)
                        model_manager.baseline_kpis = get_baseline_kpis_from_data(str(data_dir))
                        scenario_generator = ScenarioGenerator(data_dir)
                        use_ml_predictions = True
                        logger.info("✅ ML Model loaded from cache (training skipped)")
                    except Exception as e2:
                        logger.error(f"Failed to load cached model: {e2}")
                        use_ml_predictions = False
        else:
            logger.warning("⚠️ Model or data files not found")
            logger.warning("   Missing files - ML predictions will not be available")
            logger.warning("   Please run the Jupyter notebook to generate required files")
            use_ml_predictions = False
            
    except Exception as e:
        logger.error(f"❌ ML Model initialization failed: {e}")
        logger.error(traceback.format_exc())
        logger.warning("⚠️ Falling back to rule-based KPI calculation")
        use_ml_predictions = False
    
    # Initialize LLM service with data_loader
    try:
        llm_service = GroqLLMService(data_loader=data_loader)
        logger.info("✅ LLM Service initialized with data_loader")
    except Exception as e:
        logger.warning(f"⚠️ LLM Service initialization failed: {e}")
        logger.warning("⚠️ Falling back to regex-based parser")
        llm_service = None
    
    logger.info("="*80)
    if use_ml_predictions:
        logger.info("✅ BACKEND READY - ML predictions enabled")
    else:
        logger.info("⚠️ BACKEND READY - Using rule-based predictions")
    logger.info("="*80)


@app.get("/")
async def root():
    return {"message": "Process Simulation Studio API is running", "data_source": "Real O2C Data"}

@app.get("/api/data-summary")
async def get_data_summary():
    try:
        summary = data_loader.get_summary_stats()
        
        # Add event types with their KPIs
        event_types = data_loader.get_all_event_types()
        event_kpis = []
        
        for event_name in event_types:
            kpi_data = data_loader.get_event_kpis_for_activities([event_name])
            if event_name in kpi_data:
                event_kpis.append({
                    "name": event_name,
                    "avg_time": kpi_data[event_name]["avg_time"],
                    "cost": round(kpi_data[event_name]["avg_time"] * HOURLY_RATE, 2)
                })
            else:
                event_kpis.append({
                    "name": event_name,
                    "avg_time": 1.0,
                    "cost": HOURLY_RATE
                })
        
        summary["event_types"] = event_kpis
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/most-frequent-variant")
async def get_most_frequent_variant():
    try:
        variants = data_loader.get_process_variants(top_n=1)
        if not variants:
            raise HTTPException(status_code=404, detail="No variants found")
        
        most_frequent = variants[0]
        activities = most_frequent['activities']
        
        # Get KPIs for these activities
        kpis = data_loader.get_event_kpis_for_activities(activities)
        
        # Build process steps with KPIs
        steps = []
        # Add start node
        steps.append({
            "id": "start",
            "name": "Start",
            "avgTime": "-",
            "avgCost": "-"
        })
        
        # Add actual activities with real KPIs from data
        for idx, activity in enumerate(activities):
            activity_id = f"step-{idx+1}"
            # Get real avg_time and cost from KPIs (not hardcoded!)
            avg_time = kpis.get(activity, {}).get("avg_time", 1.0)
            cost = kpis.get(activity, {}).get("cost", 50.0)  # Use real cost from data
            
            # Format time
            if avg_time < 1:
                time_str = f"{round(avg_time * 60)}m"
            elif avg_time < 24:
                time_str = f"{round(avg_time, 1)}h"
            else:
                time_str = f"{round(avg_time / 24, 1)}d"
            
            steps.append({
                "id": activity_id,
                "name": activity,
                "avgTime": time_str,
                "avgCost": f"${cost:.2f}"  # Format to 2 decimal places
            })
        
        # Add end node
        steps.append({
            "id": "end",
            "name": "End",
            "avgTime": "-",
            "avgCost": "-"
        })
        
        # Build edges (sequential flow)
        edges = []
        for i in range(len(steps) - 1):
            edges.append({
                "id": f"edge-{i}",
                "source": steps[i]["id"],
                "target": steps[i+1]["id"]
            })
        
        return {
            "variant": most_frequent['variant'],
            "frequency": most_frequent['frequency'],
            "percentage": most_frequent['percentage'],
            "steps": steps,
            "edges": edges
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/process-flow-metrics")
async def get_process_flow_metrics():
    """
    Get detailed process flow metrics including edge frequencies and timing.
    Returns real data about transitions between activities.
    """
    try:
        flow_metrics = data_loader.get_process_flow_metrics()
        return flow_metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/parse-prompt", response_model=PromptResponse)
async def parse_prompt(request: PromptRequest):
    try:
        # Extract entity constraints from prompt (first time only)
        is_initial_request = not request.current_process or len(request.current_process.get('activities', [])) == 0
        
        if is_initial_request and request.session_id:
            # Extract entity information from user prompt
            entity_constraints = session_manager.extract_entity_info_from_prompt(request.prompt)
            if entity_constraints:
                session_manager.store_entity_constraints(request.session_id, entity_constraints)
                logger.info(f"📝 Extracted and stored entity constraints: {entity_constraints}")
        
        # Use LLM service if available, otherwise fall back to regex
        if llm_service:
            logger.info(f"🤖 Using LLM service for prompt: {request.prompt}")
            logger.info(f"Current process: {request.current_process}")
            result = llm_service.parse_prompt(
                user_prompt=request.prompt,
                current_process=request.current_process
            )
            logger.info(f"LLM result action: {result.get('action')}")
        else:
            logger.info(f"📝 Using regex parser for prompt: {request.prompt}")
            result = parse_prompt_mock(request.prompt)
        
        return PromptResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error: {str(e)}")

@app.post("/api/generate-log")
async def generate_log(request: EventLogRequest):
    try:
        activities = request.graph.activities
        kpis = request.graph.kpis  # ✅ Get KPIs from request
        
        # Generate a single simulated order with user's designed process
        # Pass custom KPIs to override dataset defaults
        df = data_loader.get_event_log_for_activities(activities, n_cases=1, custom_kpis=kpis if kpis else None)
        
        if df.empty:
            return {"event_log": [], "metadata": {"total_cases": 0, "total_events": 0, "activities": activities, "data_source": "simulated", "message": "No data"}}
        
        event_log = df.to_dict('records')
        return {"event_log": event_log, "metadata": {"total_cases": len(df['Case ID'].unique()), "total_events": len(df), "activities": activities, "data_source": "simulated"}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.post("/api/simulate", response_model=SimulationResponse)
async def simulate_process(request: SimulationRequest):
    try:
        logger.info("📊 Simulation request received")
        logger.debug(f"   Activities: {request.graph.activities}")
        logger.debug(f"   Edges: {len(request.graph.edges)} edges")
        logger.debug(f"   Custom KPIs received: {request.graph.kpis}")
        
        # Check if ML predictions are available
        if use_ml_predictions and model_manager and scenario_generator:
            logger.info("🤖 Using ML-based KPI predictions")
            
            activities = request.graph.activities
            
            # 1. Check for existing entities in session
            stored_entities = None
            if request.session_id:
                stored_entities = session_manager.get_entities(request.session_id)
            
            if stored_entities:
                # Use stored entities from session
                user_ids = stored_entities['users']
                items_data = stored_entities['items']
                supplier_ids = stored_entities['suppliers']
                logger.info(f"✅ Using stored session entities: {len(user_ids)} users, {len(items_data)} items, {len(supplier_ids)} suppliers")
            else:
                # Generate new entities with constraints if available
                entity_constraints = None
                session_seed = None
                
                if request.session_id:
                    entity_constraints = session_manager.get_entity_constraints(request.session_id)
                    session_seed = session_manager.get_session_seed(request.session_id)
                    logger.info(f"🎲 Using session seed: {session_seed}, constraints: {entity_constraints}")
                
                user_ids, items_data, supplier_ids, order_value = scenario_generator.generate_scenario_entities(
                    activities,
                    num_users=None,
                    num_items=None,
                    session_seed=session_seed,
                    entity_constraints=entity_constraints
                )
                logger.debug(f"   Generated: {len(user_ids)} users, {len(items_data)} items, {len(supplier_ids)} suppliers")
                
                # Store entities in session for future use
                if request.session_id:
                    session_manager.store_entities(request.session_id, user_ids, items_data, supplier_ids)
                    logger.info("💾 Stored entities in session for consistency")
            
            # 2. Enrich edges with duration information from KPIs
            edges = request.graph.edges
            enriched_edges = enrich_edges_with_durations(activities, edges, request.graph.kpis)
            
            # 3. Extract 409-dimensional feature vector
            feature_vector = extract_features_from_scenario(
                activities,
                enriched_edges,
                user_ids,
                items_data,
                supplier_ids,
                scalers=model_manager.scalers
            )
            logger.debug(f"   Feature vector extracted: shape={feature_vector.shape}")
            
            # 4. Predict KPIs using ML model
            predicted_kpis_raw = model_manager.predict(feature_vector)
            logger.debug(f"   Raw ML predicted KPIs: {predicted_kpis_raw}")
            
            # 5. Apply process complexity adjustments and baseline detection
            # Check if this is the exact baseline process (most frequent variant)
            # Get baseline activities dynamically from data (most frequent variant)
            baseline_activities = data_loader.get_most_frequent_variant_activities()
            logger.debug(f"   Baseline activities from most frequent variant: {baseline_activities}")
            
            # Check if activities match baseline
            is_baseline_activities = sorted(activities) == sorted(baseline_activities)
            
            # Also check if KPIs match the baseline values from data (no user modifications)
            has_baseline_kpis = True
            if is_baseline_activities and request.graph.kpis:
                # Get baseline KPIs from data for comparison
                baseline_kpis_data = data_loader.get_event_kpis_for_activities(baseline_activities)
                
                for activity, kpi_vals in request.graph.kpis.items():
                    avg_time = kpi_vals.get('avg_time', 2.0)
                    baseline_time = baseline_kpis_data.get(activity, {}).get('avg_time', 2.0)
                    
                    # If any activity has significantly different time from baseline data, not baseline
                    if abs(avg_time - baseline_time) > 0.5:  # Allow 0.5h tolerance for rounding
                        has_baseline_kpis = False
                        logger.debug(f"   Activity '{activity}' has modified time: {avg_time}h vs baseline {baseline_time}h")
                        break
            
            is_baseline_process = is_baseline_activities and has_baseline_kpis
            
            if is_baseline_process:
                # For exact baseline process with default KPIs, use baseline KPIs directly
                logger.info("   📊 Detected baseline process with default KPIs - using baseline KPIs")
                baseline_kpis_temp = model_manager.get_baseline_kpis()
                predicted_kpis = baseline_kpis_temp.copy()
            else:
                # For modified processes, use ML model predictions
                # The model now learns business logic from outcome features (has_rejection, etc.)
                logger.info("   🤖 Using ML model predictions (with learned business logic)")
                predicted_kpis = predicted_kpis_raw.copy()
                
                # ===================================================================
                # MANUAL BUSINESS LOGIC REMOVED - NOW LEARNED BY ML MODEL
                # ===================================================================
                # The ML model now has 8 outcome features that capture:
                # - has_rejection, has_return, has_cancellation
                # - process_completed, completeness_ratio, rejection_position
                # - generates_revenue, has_discount
                # 
                # Training data was regenerated with realistic KPIs:
                # - Rejected orders: 15% on-time delivery (vs 87% for successful)
                # - Returns: 50% on-time delivery
                # - Successful: 87% on-time delivery
                #
                # The model learns these patterns automatically from the 417-dim
                # feature vector instead of relying on manual penalty rules.
                # ===================================================================
                
                logger.debug(f"   ML predicted KPIs (no manual adjustments): {predicted_kpis}")
            
            # 6. Get baseline KPIs
            baseline_kpis = model_manager.get_baseline_kpis()
            logger.debug(f"   Baseline KPIs: {baseline_kpis}")
            
            # 7. Generate summary with entity details
            summary = scenario_generator.generate_scenario_summary(
                user_ids,
                items_data,
                supplier_ids,
                predicted_kpis
            )
            
            # 8. Calculate confidence (fixed for now, could use model uncertainty)
            confidence = 0.85
            
            # 9. Build response
            response = SimulationResponse(
                baseline_on_time_delivery=baseline_kpis['on_time_delivery'],
                baseline_days_sales_outstanding=baseline_kpis['days_sales_outstanding'],
                baseline_order_accuracy=baseline_kpis['order_accuracy'],
                baseline_invoice_accuracy=baseline_kpis['invoice_accuracy'],
                baseline_avg_cost_delivery=baseline_kpis['avg_cost_delivery'],
                
                on_time_delivery=predicted_kpis['on_time_delivery'],
                days_sales_outstanding=predicted_kpis['days_sales_outstanding'],
                order_accuracy=predicted_kpis['order_accuracy'],
                invoice_accuracy=predicted_kpis['invoice_accuracy'],
                avg_cost_delivery=predicted_kpis['avg_cost_delivery'],
                
                confidence=confidence,
                summary=summary
            )
            
            logger.info("✅ ML-based simulation completed successfully")
            return response
            
        else:
            # Fallback to rule-based prediction (from frontend)
            logger.warning("⚠️ ML predictions not available, using rule-based fallback")
            logger.warning("   This endpoint expects ML predictions to be enabled")
            logger.warning("   Please run the Jupyter notebook to train the model")
            
            # Return baseline KPIs as both baseline and current
            baseline_kpis = get_baseline_kpis_from_data(str(data_dir))
            
            return SimulationResponse(
                baseline_on_time_delivery=baseline_kpis['on_time_delivery'],
                baseline_days_sales_outstanding=baseline_kpis['days_sales_outstanding'],
                baseline_order_accuracy=baseline_kpis['order_accuracy'],
                baseline_invoice_accuracy=baseline_kpis['invoice_accuracy'],
                baseline_avg_cost_delivery=baseline_kpis['avg_cost_delivery'],
                
                on_time_delivery=baseline_kpis['on_time_delivery'],
                days_sales_outstanding=baseline_kpis['days_sales_outstanding'],
                order_accuracy=baseline_kpis['order_accuracy'],
                invoice_accuracy=baseline_kpis['invoice_accuracy'],
                avg_cost_delivery=baseline_kpis['avg_cost_delivery'],
                
                confidence=0.5,  # Low confidence for rule-based
                summary="ML model not available. Showing baseline KPIs. Please train the model first."
            )
            
    except Exception as e:
        logger.error(f"❌ Simulation error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/orders")
async def get_available_orders():
    """
    Get list of sample orders (1 per variant) with metadata.
    Returns 8 sample orders representing each of the 8 process variants.
    
    Returns:
        List of sample orders with case_id, event_count, item_count, KPIs, and variant info
    """
    try:
        data_dir = backend_dir.parent / 'data'  # Data is in parent directory
        
        # Load sample orders (1 per variant)
        df_sample_orders = pd.read_csv(data_dir / 'variant_sample_orders.csv')
        df_kpis = pd.read_csv(data_dir / 'order_kpis.csv')
        df_order_items = pd.read_csv(data_dir / 'order_items.csv')
        
        # Load variant contexts for descriptions
        import json
        with open(data_dir / 'variant_contexts.json', 'r') as f:
            variant_contexts = json.load(f)
        
        # Create variant lookup
        variant_info = {v['variant_id']: v for v in variant_contexts['variants']}
        
        # Build order list (only sample orders)
        orders = []
        for _, sample_row in df_sample_orders.iterrows():
            order_id = sample_row['sample_order_id']
            variant_id = sample_row['variant_id']
            
            # Get KPIs for this order
            kpi_row = df_kpis[df_kpis['order_id'] == order_id]
            if kpi_row.empty:
                continue
            
            kpi_row = kpi_row.iloc[0]
            
            # Get event count
            events_df = data_loader.df_events[data_loader.df_events['order_id'] == order_id]
            event_count = len(events_df)
            
            # Get item count
            items_count = len(df_order_items[df_order_items['order_id'] == order_id])
            
            # Get variant description
            variant = variant_info.get(variant_id, {})
            variant_name = ' → '.join(variant.get('event_sequence', []))[:80] + '...'  # Truncate long names
            
            orders.append({
                'case_id': str(order_id),
                'variant_id': variant_id,
                'variant_name': variant_name,
                'variant_description': variant.get('context', '')[:200] + '...',  # Short description
                'frequency_percentage': float(variant.get('frequency_percentage', 0)),
                'event_count': int(event_count),
                'item_count': int(items_count),
                'on_time_delivery': float(kpi_row['on_time_delivery']),
                'days_sales_outstanding': float(kpi_row['days_sales_outstanding']),
                'order_accuracy': float(kpi_row['order_accuracy']),
            })
        
        logger.info(f"📋 Retrieved {len(orders)} sample orders (1 per variant)")
        return {'orders': orders, 'total': len(orders)}
        
    except Exception as e:
        logger.error(f"❌ Error fetching orders: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error fetching orders: {str(e)}")

@app.get("/api/sample")
async def get_sample_case(case_id: Optional[str] = None, seed: int = 42):
    """
    Get a sample O2C case with 3D visualization data.
    
    This endpoint:
    1. Fetches a sample case from the dataset (using seed for consistency)
    2. Generates a 3D scene JSON file with animation keyframes
    3. Returns the scene file path and metadata
    
    Args:
        case_id: Optional specific case ID (default: pick based on seed)
        seed: Random seed for consistent case selection (default: 42)
    """
    try:
        logger.info(f"📦 Fetching sample case (seed={seed})")
        
        # Create exports directory
        exports_dir = backend_dir / 'exports'
        exports_dir.mkdir(exist_ok=True)
        
        # Get sample case data
        case_id, events, order_info, users, items, suppliers, kpis = get_sample_case_data(
            data_loader, case_id, seed
        )
        
        logger.info(f"   Case ID: {case_id}")
        logger.info(f"   Events: {len(events)}")
        logger.info(f"   Users: {len(users)}")
        logger.info(f"   Items: {len(items)}")
        logger.info(f"   Suppliers: {len(suppliers)}")
        
        # Generate GLTF/JSON scene file
        scene_path, metadata = generate_gltf_for_case(
            case_id, events, order_info, users, items, suppliers, kpis, exports_dir
        )
        
        # Make path relative to backend directory for serving
        relative_path = Path(scene_path).relative_to(backend_dir)
        
        logger.info(f"✅ Generated 3D scene: {relative_path}")
        
        # Convert all values to native Python types (not numpy) for JSON serialization
        return {
            "case_id": str(case_id),
            "scene_path": str(relative_path),
            "absolute_path": str(scene_path),
            "metadata": {
                "case_id": str(metadata.get('case_id', '')),
                "duration": float(metadata.get('duration', 0)),
                "num_events": int(metadata.get('num_events', 0)),
                "start_time": str(metadata.get('start_time', '')) if metadata.get('start_time') else None,
                "end_time": str(metadata.get('end_time', '')) if metadata.get('end_time') else None,
            },
            "order_info": {
                "order_value": float(order_info.get('order_value', 0)),
                "order_status": str(order_info.get('order_status', '')),
                "num_items": int(order_info.get('num_items', 0)),
                "total_quantity": int(order_info.get('total_quantity', 0)),
            },
            "kpis": {
                "on_time_delivery": float(kpis.get('on_time_delivery', 0)),
                "days_sales_outstanding": float(kpis.get('days_sales_outstanding', 0)),
                "order_accuracy": float(kpis.get('order_accuracy', 0)),
                "invoice_accuracy": float(kpis.get('invoice_accuracy', 0)),
                "avg_cost_delivery": float(kpis.get('avg_cost_delivery', 0)),
            },
            "entities": {
                "users": users,
                "items": [
                    {
                        "id": str(item.get('item_id', '')),
                        "name": str(item.get('name', '')),
                        "quantity": int(item.get('quantity', 0)),
                    }
                    for item in items
                ],
                "suppliers": suppliers,
            }
        }
        
    except Exception as e:
        logger.error(f"❌ Error generating sample case: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error generating sample case: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Process Simulation Studio API", "data_loaded": data_loader.df_events is not None, "total_orders": len(data_loader.df_orders) if data_loader.df_orders is not None else 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


# ============================================================================
# Session Management Endpoints
# ============================================================================

@app.post("/api/session/start")
async def start_session():
    """
    Create a new session for entity consistency.
    Returns a session ID that should be included in subsequent requests.
    """
    try:
        session_id = session_manager.create_session()
        return {
            "session_id": session_id,
            "message": "Session created successfully"
        }
    except Exception as e:
        logger.error(f"Error starting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/session/reset")
async def reset_session(request: dict):
    """
    Reset a session (generates new entities but keeps session ID).
    """
    try:
        session_id = request.get("session_id")
        if not session_id:
            raise HTTPException(status_code=400, detail="session_id required")
        
        new_session_id = session_manager.reset_session(session_id)
        return {
            "session_id": new_session_id,
            "message": "Session reset - new entities will be generated"
        }
    except Exception as e:
        logger.error(f"Error resetting session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/session/info/{session_id}")
async def get_session_info(session_id: str):
    """
    Get information about a session.
    """
    try:
        info = session_manager.get_session_info(session_id)
        if not info:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session_id": session_id,
            "created_at": info['created_at'],
            "last_access": info['last_access'],
            "request_count": info['request_count']
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/narration")
async def generate_narration(request: NarrationRequest):
    """
    Generate real-time narration for a simulation event using LLM.
    
    This endpoint generates natural language commentary for the current event
    in the 3D simulation, explaining what's happening, who's involved, and
    what attributes are being processed.
    """
    try:
        logger.info(f"Generating narration for event: {request.event_name}")
        
        # Check if LLM service is available
        if llm_service is None:
            # Fallback narration in bullet format
            narration = (
                f"• Action: {request.event_name}\n"
                f"• User: {request.user}\n"
                f"• Status: In Progress"
            )
            
            return NarrationResponse(
                narration=narration,
                event_name=request.event_name,
                timestamp=request.timestamp
            )
        
        # Convert request to dictionary for LLM service
        event_data = {
            'event_name': request.event_name,
            'timestamp': request.timestamp,
            'case_id': request.case_id,
            'order_value': request.order_value,
            'order_status': request.order_status,
            'user': request.user,  # Single user
            'items': request.items,
            'suppliers': request.suppliers,
            'variant_id': request.variant_id,
            'current_time': request.current_time
        }
        
        # Generate narration using LLM
        narration = llm_service.generate_event_narration(event_data)
        
        logger.info(f"✅ Narration generated: {narration[:100]}...")
        
        return NarrationResponse(
            narration=narration,
            event_name=request.event_name,
            timestamp=request.timestamp
        )
        
    except Exception as e:
        logger.error(f"❌ Error generating narration: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Always provide a fallback narration to avoid breaking the UI
        fallback_narration = (
            f"• Action: {request.event_name}\n"
            f"• By: {request.user}\n"
            f"• Status: Processing"
        )
        
        return NarrationResponse(
            narration=fallback_narration,
            event_name=request.event_name,
            timestamp=request.timestamp
        )

