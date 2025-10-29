# Process Simulation - Unseen Variant

This project is a process simulation and optimization platform built for analyzing and redesigning business processes. It combines real Order-to-Cash (O2C) data analysis with an AI-powered natural language interface, allowing users to visualize, modify, and simulate business process changes before implementing them in production.

The system is designed to help business analysts, process managers, and operations teams understand how potential changes to their processes might affect key performance indicators like cycle time, cost, and revenue.

## What This Project Does

At its core, this application takes real process execution data (event logs) from business systems and helps you answer questions like:
- What are our most common process variants?
- What happens if we add a quality check step?
- How much time would we save by removing manual approval?
- What's the cost impact of parallelizing certain activities?

Instead of implementing changes and hoping they work, you can test them in a simulation environment first. The system uses actual historical data to make realistic predictions about how modifications will affect your processes.

## Key Capabilities

**Real Data Analysis**
The platform loads actual O2C process data from XML event logs, automatically identifying the most frequent process paths and calculating real KPIs from historical executions. It includes tools for data preprocessing, filtering, and statistical analysis.

**Natural Language Process Modification**
Rather than manually clicking and dragging to redesign processes, you can describe changes in plain English. For example: "Add quality check before Pack Items" or "Increase Generate Invoice time to 2 hours". The system uses Groq's LLM API to interpret these prompts and convert them into process modifications.

**Interactive Visualization**
The frontend provides a D3.js-powered process graph where you can see your process flow, drag activities around, and view KPIs for each step. The interface includes an activity palette with real timing and cost data pulled from your historical logs.

**Event Log Generation**
Once you've designed or modified a process, the system generates synthetic event logs that reflect what actual process executions would look like. These logs maintain realistic timing distributions and cost structures based on your data.

**Simulation Engine**
The simulation component uses NetworkX for graph analysis and compares your modified process against historical baselines. It predicts changes in cycle time, cost, and revenue, along with a confidence score based on how similar your modified process is to known variants in your data.

## Getting Started

### What You'll Need

The backend requires Python 3.8 or higher and uses FastAPI for the REST API. The frontend is built with React and TypeScript, so you'll need Node.js 16+ and npm.

### Quick Setup

We've included a startup script that handles all the setup automatically:

```bash
chmod +x run-system.sh
./run-system.sh
```

This script creates a Python virtual environment, installs all dependencies, and starts both servers. The backend will run on port 8000 and the frontend on port 3000 (or 5173 if you're using Vite).

### Manual Setup

If you prefer to set things up manually or run into issues with the automated script:

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at http://localhost:8000 and you can view the interactive API documentation at http://localhost:8000/docs.

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

The UI will be accessible at http://localhost:3000 or http://localhost:5173.

### Setting Up the LLM Integration

The system uses Groq's API for natural language processing. You'll need to set up your API key as an environment variable. The startup scripts handle this automatically, but if you're running things manually:

```bash
export GROQ_API_KEY="your_api_key_here"
```

Without this key, the system will fall back to a regex-based prompt parser that handles basic cases but isn't as flexible.

## Project Structure

Here's how the codebase is organized:

**Backend (Python/FastAPI)**
- `main.py` - Main API server with all REST endpoints
- `llm_service.py` - Groq API integration for natural language processing
- `llm_prompts.py` - System prompts and templates for the LLM
- `action_schemas.py` - Pydantic models defining structured LLM outputs
- `simulation_engine.py` - Core simulation logic and KPI prediction
- `real_data_loader.py` - Loads and processes O2C data from XML files
- `utils.py` - Helper functions, graph conversion, and legacy prompt parsing
- `data_generator.py` - Synthetic event log generation
- `filter_orders.py` - XML data filtering utilities
- `update_order_values.py` - Data preprocessing tools
- `EDA_O2C_Orders.ipynb` - Jupyter notebook for exploratory data analysis
- `requirements.txt` - Python dependencies

**Frontend (React/TypeScript)**
- `src/App.tsx` - Main application component and orchestration
- `src/components/PromptPanel.tsx` - Natural language input interface
- `src/components/ProcessExplorer.tsx` - D3.js process visualization
- `src/components/EventLogPanel.tsx` - Event log viewer and details
- `src/components/EventPalette.tsx` - Activity palette with drag-and-drop
- `src/components/SimulationModal.tsx` - Simulation results display
- `src/components/EventInfoDialog.tsx` - Event detail modal
- `src/components/TopBar.tsx` - Application header
- `src/store/useAppStore.ts` - Zustand state management
- `src/services/api.ts` - Axios HTTP client for API calls
- `src/types/index.ts` - TypeScript type definitions
- `src/components/ui/` - Radix UI component library (50+ components)

**Data**
- `data/o2c_data.xml` - Full O2C dataset
- `data/o2c_data_orders_only.xml` - Filtered orders dataset

**Scripts**
- `run-system.sh` - Automated startup script
- `start.sh` - Alternative startup script
- `test_backend.py` - Backend test suite

## How the System Works

When you first load the application, it retrieves the most frequent process variant from your historical data. This gives you a real starting point based on how your processes actually run.

From there, you can modify the process in several ways:
- Type natural language instructions in the prompt panel
- Drag activities from the palette to add new steps
- Click on activities to modify their KPIs
- Reorder activities by dragging them in the graph

When you submit a natural language prompt, it's sent to the backend where the LLM service (using Groq's API) parses your intent and determines what action to take. The system validates the action against your current process structure to ensure it makes sense.

Once you've made modifications, you can generate an event log to see what the execution data would look like. The system uses your custom KPIs (if you've modified any) and fills in the rest with values from the historical dataset.

Finally, you can run a simulation to see predicted impacts. The simulation engine builds a NetworkX graph representation of your process, compares it against historical baselines, and uses graph analysis plus statistical methods to predict how KPIs will change.

## API Endpoints

The backend exposes several REST endpoints:

**GET /**
Returns basic service information and data source status.

**GET /api/health**
Health check endpoint that reports whether the data has been loaded successfully and how many orders are in the dataset.

**GET /api/data-summary**
Returns statistical summary of the O2C data including total cases, events, and KPIs for each activity type.

**GET /api/most-frequent-variant**
Returns the most common process variant with its activities, frequency, and real KPIs from the dataset.

**GET /api/process-flow-metrics**
Provides detailed metrics about transitions between activities including frequency and timing.

**POST /api/parse-prompt**
Accepts a natural language prompt and returns a structured action describing how to modify the process. Requires the current process state for context-aware parsing.

Request body:
```json
{
  "prompt": "Add credit check before order approval",
  "current_process": {
    "activities": ["Order Received", "Order Approved"],
    "edges": [...],
    "kpis": {...}
  }
}
```

**POST /api/generate-log**
Generates a synthetic event log from a process graph definition. Uses custom KPIs if provided, otherwise falls back to dataset values.

Request body:
```json
{
  "graph": {
    "activities": ["Order Received", "Order Approved", "Invoice Created"],
    "edges": [...],
    "kpis": {
      "Order Received": {"avg_time": 1.0, "cost": 25.0}
    }
  }
}
```

**POST /api/simulate**
Runs simulation on a modified process and returns predicted KPI changes along with confidence scores.

Request body:
```json
{
  "event_log": [...],
  "graph": {
    "activities": [...],
    "edges": [...],
    "kpis": {...}
  }
}
```

## Natural Language Processing

The system uses a two-tier approach to prompt parsing:

**Primary: LLM-based (Groq API)**
When properly configured with an API key, the system uses Groq's llama-3.3-70b-versatile model to interpret natural language prompts. The LLM is given detailed instructions about available actions, current process context, and validation rules.

The LLM returns structured JSON responses with action types, parameters, confidence scores, and explanations. It's been specifically instructed to:
- Only respond to business process management queries
- Never change user intent or modify the prompt
- Request clarification when activities don't exist in the current process
- Provide confidence scores and suggestions

**Fallback: Regex-based**
If the LLM service fails to initialize, the system falls back to a regex-based parser in `utils.py`. This handles basic patterns but isn't as flexible or context-aware.

## Simulation Algorithm

The simulation engine uses several techniques to predict KPI changes:

**Graph Analysis**
Converts the process to a NetworkX directed graph and analyzes structural properties like path lengths, bottlenecks, and complexity metrics.

**Baseline Comparison**
Calculates average cycle time and cost from the historical O2C dataset. This serves as the baseline for comparison.

**Activity-Level KPIs**
Uses real timing and cost data for each activity. When you modify KPIs manually, those custom values take precedence over dataset averages.

**Confidence Scoring**
Assesses prediction reliability based on:
- How similar the modified process is to known variants
- Whether all activities have historical data
- Structural complexity of the process
- Number of modifications made

**Impact Calculation**
Computes percentage changes in cycle time, cost, and revenue by comparing the modified process metrics against the baseline. Returns both relative changes (percentages) and absolute values.

## Technology Stack

**Backend:**
- FastAPI 0.115.0 - Modern Python web framework with automatic API documentation
- Uvicorn 0.32.0 - ASGI server for running FastAPI
- Pandas 2.2.3 - Data manipulation and XML parsing
- NetworkX 3.4.2 - Graph analysis and algorithms
- Groq 0.33.0 - LLM API client for natural language processing
- Pydantic 2.9.2 - Data validation and schema definition
- Scikit-learn 1.5.2 - Machine learning utilities
- NumPy 2.1.2 - Numerical computing

**Frontend:**
- React 18.3.1 - UI framework
- TypeScript 5.0.2 - Type-safe JavaScript
- Vite 4.4.5 - Build tool and development server
- Tailwind CSS 3.3.0 - Utility-first CSS framework
- Radix UI - Accessible component primitives (Dialog, Dropdown, Toast, etc.)
- Zustand 4.4.1 - Lightweight state management
- Axios 1.5.0 - HTTP client
- D3.js (via React wrappers) - Process graph visualization
- Lucide React 0.487.0 - Icon library
- Sonner 2.0.3 - Toast notifications
- Recharts 2.15.2 - Charts for simulation results

**Development Tools:**
- Jupyter Notebook - For data exploration
- ESLint - Code linting
- PostCSS - CSS processing

## Testing

You can test the backend API using the included test suite:

```bash
python3 test_backend.py
```

This tests all major endpoints including data loading, prompt parsing, event log generation, and simulation.

For manual testing, the FastAPI docs interface at http://localhost:8000/docs provides an interactive way to test each endpoint.

## Common Issues and Solutions

**Port Already in Use**
If you get an error about port 8000 or 3000 being in use:
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
# Or use a different port
uvicorn main:app --port 8001
```

**Data File Not Found**
Make sure the data directory exists and contains `o2c_data_orders_only.xml`. The path is configured in `main.py` and should be relative to the backend directory.

**Import Errors**
If you see Python import errors, try recreating the virtual environment:
```bash
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**CORS Errors**
If the frontend can't connect to the backend, check the CORS configuration in `main.py`. The allowed origins should include your frontend URL (typically http://localhost:3000 or http://localhost:5173).

**LLM Not Working**
If natural language prompts aren't being parsed correctly, check that:
- The GROQ_API_KEY environment variable is set
- You see "LLM Service initialized successfully" in the backend logs
- The API key is valid and has sufficient quota

**Frontend Build Issues**
If npm install or build fails:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

## Extending the System

Here are some ideas if you want to build on this foundation:

**Process Mining**
You could integrate PM4Py to add conformance checking, process discovery from event logs, and more sophisticated process mining algorithms.

**Advanced ML Models**
The current simulation uses statistical methods and graph analysis. You could train machine learning models on your historical data to make more accurate predictions.

**Database Persistence**
Right now everything is stateless. Adding a database (PostgreSQL, MongoDB) would let you save process definitions, track simulation history, and manage user preferences.

**Real-time Collaboration**
WebSocket support would enable multiple users to work on the same process definition simultaneously.

**More Data Sources**
The system currently loads XML event logs. You could add support for CSV, database connections, or direct integration with BPM systems.

**Advanced Analytics**
Features like bottleneck detection, resource utilization analysis, and cost optimization recommendations would add significant value.

## Contributing

If you'd like to contribute to this project:

1. Fork the repository
2. Create a feature branch for your changes
3. Make your modifications
4. Ensure all tests pass
5. Submit a pull request with a clear description of what you've changed and why

Please follow the existing code style and include appropriate comments for complex logic.

## License

This project is available under the MIT License. See the LICENSE file for details.

## Acknowledgments

This project was built using several excellent open-source libraries and frameworks. Special thanks to the FastAPI team for their outstanding web framework, the Radix UI team for accessible component primitives, and the process mining research community for inspiration and methodologies.

The real O2C dataset used for testing comes from process mining case studies and represents typical order-to-cash workflows in enterprise systems.

---

For questions, issues, or feature requests, please use the GitHub Issues section. For general discussion, check the Discussions tab.
