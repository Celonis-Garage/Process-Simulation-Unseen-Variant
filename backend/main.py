from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import pandas as pd
import os
import logging
import traceback

from simulation_engine import SimulationEngine
from real_data_loader import get_data_loader
from utils import parse_prompt_mock, graph_to_networkx
from llm_service import GroqLLMService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
HOURLY_RATE = 25.0  # Default hourly rate for cost calculation

app = FastAPI(title="Process Simulation Studio API", version="1.0.0")

# Configure CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class PromptRequest(BaseModel):
    prompt: str
    current_process: Optional[Dict[str, Any]] = None  # Include current process state

class ProcessGraph(BaseModel):
    activities: List[str]
    edges: List[Dict[str, Any]]  # Changed from Dict[str, str] to Dict[str, Any] to accept id, cases, avgDays
    kpis: Dict[str, Dict[str, float]]

class EventLogRequest(BaseModel):
    graph: ProcessGraph

class SimulationRequest(BaseModel):
    event_log: List[Dict[str, Any]]
    graph: ProcessGraph

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

class SimulationResponse(BaseModel):
    cycle_time_change: float
    cost_change: float
    revenue_impact: float
    confidence: float
    summary: str
    # Absolute KPI values
    cycle_time_hours: float
    cycle_time_days: float
    cost_dollars: float
    baseline_cycle_time_hours: float
    baseline_cycle_time_days: float
    baseline_cost_dollars: float

# Initialize
simulation_engine = SimulationEngine()
current_dir = os.path.dirname(os.path.abspath(__file__))
data_file_path = os.path.join(current_dir, '..', 'data', 'o2c_data_orders_only.xml')
data_loader = get_data_loader(data_file_path)

# Initialize LLM service
try:
    llm_service = GroqLLMService()
    logger.info("✅ LLM Service initialized successfully")
except Exception as e:
    logger.warning(f"⚠️ LLM Service initialization failed: {e}")
    logger.warning("⚠️ Falling back to regex-based parser")
    llm_service = None

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
        # Use LLM service if available, otherwise fall back to regex
        if llm_service:
            logger.info(f"🤖 Using LLM service for prompt: {request.prompt}")
            result = llm_service.parse_prompt(
                user_prompt=request.prompt,
                current_process=request.current_process
            )
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
        logger.debug(f"   Event log entries: {len(request.event_log)}")
        logger.debug(f"   Custom KPIs received: {request.graph.kpis}")
        
        nx_graph = graph_to_networkx(request.graph)
        df = pd.DataFrame(request.event_log)
        
        logger.debug(f"   Event log columns: {df.columns.tolist()}")
        logger.debug(f"   Event log shape: {df.shape}")
        
        # Use custom KPIs from frontend (user-modified values)
        # These override the dataset KPIs
        custom_kpis = request.graph.kpis
        
        # Get dataset KPIs as fallback for activities not modified by user
        activities = request.graph.activities
        dataset_kpis = data_loader.get_event_kpis_for_activities(activities)
        
        # Merge: custom KPIs override dataset KPIs
        merged_kpis = {**dataset_kpis, **custom_kpis}
        logger.debug(f"   Using KPIs (custom merged with dataset): {merged_kpis}")
        
        # Get baseline metrics (time and cost) from original dataset
        order_times = data_loader.calculate_order_execution_times()
        
        # Pass merged KPIs to simulation (custom values take precedence)
        result = simulation_engine.simulate(nx_graph, df, real_kpis=merged_kpis, baseline_metrics=order_times)
        logger.info("✅ Simulation completed successfully")
        return SimulationResponse(**result)
    except Exception as e:
        logger.error(f"❌ Simulation error: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "Process Simulation Studio API", "data_loaded": data_loader.df_events is not None, "total_orders": len(data_loader.df_orders) if data_loader.df_orders is not None else 0}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
