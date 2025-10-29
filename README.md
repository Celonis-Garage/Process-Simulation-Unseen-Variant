# Process Simulation Studio - Unseen Variant

An advanced process simulation platform that combines real Order-to-Cash (O2C) data analysis with AI-powered process optimization. The system enables natural language process modifications, interactive visualization, real-time event log generation, and data-driven business impact predictions.

## 🌟 Key Features

- **Real Data Integration**: Analyzes actual O2C process data from XML event logs
- **Process Variant Discovery**: Automatically identifies and visualizes most frequent process variants
- **AI-Powered Modifications**: Natural language interface for process redesign
- **Interactive Visualization**: Drag-and-drop process explorer with D3.js
- **Simulation Engine**: Predicts KPI changes based on process modifications
- **Event Log Generation**: Creates realistic event logs from process definitions

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **npm** (package manager)

### Option 1: Automated Setup (Recommended)

Use the provided startup script to automatically set up and run both servers:

```bash
chmod +x run-system.sh
./run-system.sh
```

The script will:
- Create and activate Python virtual environment
- Install all dependencies
- Start backend on `http://localhost:8000`
- Start frontend on `http://localhost:3000` or `http://localhost:5173`
- Validate both services are running

### Option 2: Manual Setup

#### Backend Setup

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Backend API: `http://localhost:8000`  
API Documentation: `http://localhost:8000/docs`

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend UI: `http://localhost:3000` or `http://localhost:5173`

### Testing the Backend

Run the test suite to verify all endpoints:

```bash
python3 test_backend.py
```

## 🧩 Architecture Overview

```
Process-Simulation-Unseen-Variant/
├── backend/                          # FastAPI Python Backend
│   ├── main.py                       # FastAPI app & REST endpoints
│   ├── simulation_engine.py          # KPI prediction & simulation logic
│   ├── data_generator.py             # Synthetic event log generation
│   ├── real_data_loader.py           # Real O2C data loader from XML
│   ├── filter_orders.py              # XML data filtering utilities
│   ├── update_order_values.py        # Data preprocessing tools
│   ├── utils.py                      # Helper functions & prompt parsing
│   ├── EDA_O2C_Orders.ipynb          # Exploratory Data Analysis notebook
│   ├── requirements.txt              # Python dependencies
│   ├── venv/                         # Python virtual environment
│   └── backend.log                   # Backend runtime logs
│
├── frontend/                         # React TypeScript Frontend
│   ├── src/
│   │   ├── components/               # React components
│   │   │   ├── ui/                   # Radix UI library (50+ components)
│   │   │   ├── figma/                # Figma design utilities
│   │   │   ├── EventLogPanel.tsx     # Event log viewer
│   │   │   ├── EventInfoDialog.tsx   # Event details modal
│   │   │   ├── EventPalette.tsx      # Activity palette
│   │   │   ├── ProcessExplorer.tsx   # D3.js process graph
│   │   │   ├── PromptPanel.tsx       # Natural language input
│   │   │   ├── SimulationModal.tsx   # Simulation results
│   │   │   └── TopBar.tsx            # Application header
│   │   ├── store/                    # Zustand state management
│   │   │   └── useAppStore.ts        # Global app state
│   │   ├── services/                 # Backend API integration
│   │   │   └── api.ts                # Axios HTTP client
│   │   ├── types/                    # TypeScript interfaces
│   │   │   └── index.ts              # Type definitions
│   │   ├── lib/                      # Utility functions
│   │   ├── styles/                   # Global CSS styles
│   │   ├── guidelines/               # Design system docs
│   │   └── App.tsx                   # Root application
│   ├── package.json                  # Node dependencies
│   ├── vite.config.ts                # Vite build config
│   ├── tailwind.config.js            # Tailwind CSS config
│   ├── tsconfig.json                 # TypeScript config
│   └── frontend.log                  # Frontend runtime logs
│
├── data/                             # Real O2C Event Logs
│   ├── o2c_data.xml                  # Full O2C dataset
│   └── o2c_data_orders_only.xml      # Filtered orders only
│
├── run-system.sh                     # Automated startup script
├── start.sh                          # Alternative startup script
├── test_backend.py                   # Backend test suite
├── .gitignore                        # Git ignore rules
└── README.md                         # This file
```

## 🎯 Core Features

### 1️⃣ Real Data Integration
- **XML Event Log Loading**: Parses real O2C process data
- **Process Variant Discovery**: Identifies most frequent process paths
- **Statistical Analysis**: Calculates actual KPIs from historical data
- **Data Preprocessing**: Filters and transforms event logs
- **Exploratory Analysis**: Jupyter notebook for data insights

### 2️⃣ Process Visualization
- **Interactive Process Graph**: D3.js-powered visualization with drag-and-drop
- **Most Frequent Variant Display**: Automatically loads the most common process flow
- **Activity Palette**: Library of available process steps with real KPIs
- **Real-Time Updates**: Dynamic graph updates based on modifications
- **KPI Display**: Shows average time and cost per activity

### 3️⃣ Natural Language Modification
- **Prompt-Based Editing**: Modify processes using natural language
  - "Add payment validation after invoice creation"
  - "Remove order approval step"
  - "Increase invoice creation time to 2 hours"
- **Smart Parsing**: Interprets user intent and maps to process changes
- **Context-Aware**: Understands process structure and dependencies

### 4️⃣ Event Log Generation
- **Synthetic Data Creation**: Generate realistic event logs from process definitions
- **Activity-Based Simulation**: Uses real timing and cost data
- **Multiple Cases**: Simulate single or multiple process instances
- **Metadata Tracking**: Track cases, events, and activities

### 5️⃣ Simulation & Prediction
- **KPI Impact Analysis**: Predict changes in cycle time, cost, and revenue
- **NetworkX Graph Analysis**: Analyze process structure and complexity
- **Baseline Comparison**: Compare modified process against historical data
- **Confidence Scoring**: Assess prediction reliability
- **Business Insights**: Generate natural language impact summaries

### 6️⃣ Modern UI/UX
- **Radix UI Components**: 50+ accessible, customizable components
- **Responsive Design**: Works on desktop and tablet devices
- **Collapsible Panels**: Event log and activity palette can be hidden
- **Modal Dialogs**: Detailed views for simulations and event details
- **Toast Notifications**: Real-time feedback on user actions

## 🔧 API Endpoints

### Backend REST API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API root - service information |
| `GET` | `/api/health` | Health check with data loading status |
| `GET` | `/api/data-summary` | Statistical summary of O2C data |
| `GET` | `/api/most-frequent-variant` | Most common process variant with KPIs |
| `GET` | `/api/process-flow-metrics` | Detailed flow metrics and transitions |
| `POST` | `/api/parse-prompt` | Parse natural language into process modifications |
| `POST` | `/api/generate-log` | Generate synthetic event log from process graph |
| `POST` | `/api/simulate` | Run simulation and predict KPI changes |

### Example API Usage

**Get Data Summary**
```bash
curl http://localhost:8000/api/data-summary
```

**Get Most Frequent Variant**
```bash
curl http://localhost:8000/api/most-frequent-variant
```

**Parse Natural Language Prompt**
```bash
curl -X POST "http://localhost:8000/api/parse-prompt" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Add credit check before order approval"}'
```

**Generate Event Log**
```bash
curl -X POST "http://localhost:8000/api/generate-log" \
  -H "Content-Type: application/json" \
  -d '{
    "graph": {
      "activities": ["Order Received", "Order Approved", "Invoice Created"],
      "edges": [{"from": "Order Received", "to": "Order Approved"}],
      "kpis": {"Order Received": {"avg_time": 1.0, "cost": 5.0}}
    }
  }'
```

**Run Simulation**
```bash
curl -X POST "http://localhost:8000/api/simulate" \
  -H "Content-Type: application/json" \
  -d '{
    "event_log": [...],
    "graph": {...}
  }'
```

## 🎨 Frontend Components

### Main Components

| Component | Purpose | Key Features |
|-----------|---------|--------------|
| `TopBar.tsx` | Application header | Branding, navigation, actions |
| `PromptPanel.tsx` | Natural language input | Chat-style interface, prompt suggestions |
| `ProcessExplorer.tsx` | Process visualization | D3.js graph, drag-and-drop, real-time updates |
| `EventLogPanel.tsx` | Event log viewer | Collapsible table, event details |
| `EventPalette.tsx` | Activity library | Draggable activities with KPIs |
| `EventInfoDialog.tsx` | Event details modal | Detailed event information |
| `SimulationModal.tsx` | Results display | KPI changes, business insights, confidence |

### UI Component Library (Radix UI)

50+ production-ready components including:
- **Forms**: Input, Textarea, Select, Checkbox, Radio, Switch
- **Overlays**: Dialog, Popover, Dropdown, Tooltip, Sheet
- **Navigation**: Tabs, Accordion, Breadcrumb, Menu
- **Data Display**: Table, Card, Avatar, Badge
- **Feedback**: Alert, Toast (Sonner), Progress
- **Layout**: Resizable panels, Scroll area, Separator

### State Management

**Zustand Store** (`store/useAppStore.ts`):
```typescript
interface AppState {
  // Process data
  processGraph: ProcessGraph;
  eventLog: EventLogEntry[];
  simulationResult: SimulationResult | null;
  
  // UI state
  selectedNode: string | null;
  isSimulationModalOpen: boolean;
  
  // Actions
  updateProcessGraph: (graph: ProcessGraph) => void;
  generateEventLog: () => Promise<void>;
  runSimulation: () => Promise<void>;
}
```

### API Integration

**Axios Service** (`services/api.ts`):
- Centralized HTTP client
- Error handling
- Request/response interceptors
- Type-safe API calls

## 📊 Real O2C Data

The system loads real Order-to-Cash process data from XML event logs containing:

- **Event Logs**: Actual process executions with timestamps
- **Case IDs**: Unique order identifiers
- **Activities**: Real process steps from historical data
- **Resources**: People/systems that performed activities
- **Timestamps**: Start and completion times

### Most Frequent Process Variant

The application automatically identifies and displays the most common process path, including:
- **Variant sequence**: Ordered list of activities
- **Frequency**: Number of cases following this path
- **Percentage**: Share of total cases
- **Real KPIs**: Average time and cost per activity (from data)

### Sample Activities from Real Data
- Order Received
- Order Approved
- Invoice Created
- Payment Validation
- Payment Received
- Shipment Prepared
- Goods Delivered
- *(and more based on actual data)*

## 🔮 Simulation Engine

### How It Works

1. **Graph Construction**: Builds NetworkX graph from process definition
2. **Baseline Calculation**: Computes metrics from historical O2C data
3. **Variant Analysis**: Compares modified process to known patterns
4. **KPI Prediction**: Estimates cycle time, cost, and revenue impact
5. **Confidence Scoring**: Assesses prediction reliability based on:
   - Pattern similarity to historical variants
   - Structural complexity
   - Data availability

### Prediction Outputs

```json
{
  "cycle_time_change": -0.12,           // 12% reduction
  "cost_change": 0.03,                  // 3% increase
  "revenue_impact": 0.02,               // 2% increase
  "confidence": 0.85,                   // 85% confidence
  "cycle_time_hours": 24.5,             // New absolute value
  "baseline_cycle_time_hours": 27.8,    // Original value
  "cost_dollars": 145.50,               // New cost
  "baseline_cost_dollars": 141.20,      // Original cost
  "summary": "Adding Payment Validation increases compliance by 15% while slightly extending cycle time by 0.8 days."
}
```

### Simulation Features
- **Real Data Baseline**: Uses actual historical metrics
- **Activity-Level KPIs**: Real timing and cost per activity
- **Process Complexity**: Graph-based complexity metrics
- **Business Impact**: Natural language summaries

## 🧪 Development

### Backend Development

**Run with auto-reload:**
```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Access API documentation:**
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

**Explore data with Jupyter:**
```bash
cd backend
source venv/bin/activate
jupyter notebook EDA_O2C_Orders.ipynb
```

### Frontend Development

**Run development server:**
```bash
cd frontend
npm run dev
```

**Lint code:**
```bash
npm run lint
```

**Type checking:**
```bash
npx tsc --noEmit
```

### Building for Production

**Backend:**
```bash
cd backend
pip install -r requirements.txt
# Deploy with gunicorn or uvicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

**Frontend:**
```bash
cd frontend
npm run build
# Output in dist/ directory
npm run preview  # Preview production build
```

## 🚀 Deployment

### Backend Deployment Options

**Railway / Render / Fly.io:**
```bash
# Ensure requirements.txt is up to date
pip freeze > requirements.txt
# Follow platform-specific deployment guide
```

**Docker (Optional):**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**AWS EC2 / DigitalOcean:**
```bash
# SSH into server
git clone <repo>
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
# Use supervisor or systemd to keep running
```

### Frontend Deployment Options

**Vercel (Recommended):**
```bash
cd frontend
vercel deploy --prod
```

**Netlify:**
```bash
cd frontend
npm run build
# Drag & drop dist/ folder to Netlify
```

**Nginx (Self-hosted):**
```bash
npm run build
# Copy dist/ to /var/www/html
# Configure nginx to serve static files
```

### Environment Configuration

**Frontend** (`.env`):
```bash
VITE_API_URL=https://api.yourdomain.com
```

**Backend** (environment variables):
```bash
PORT=8000
CORS_ORIGINS=https://yourdomain.com
DATA_PATH=../data/o2c_data_orders_only.xml
```

## 🔗 Extension & Enhancement Ideas

### 1. Advanced LLM Integration
**Current**: Mock prompt parsing with pattern matching  
**Enhancement**: Integrate OpenAI/Anthropic for sophisticated NLP

```python
# utils.py
import openai
def parse_prompt_with_llm(prompt: str):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "Parse process modification..."}]
    )
    return parse_llm_response(response)
```

### 2. Process Mining with PM4Py
**Enhancement**: Add conformance checking and process discovery

```python
import pm4py
# Discover process model from event log
net, im, fm = pm4py.discover_petri_net_inductive(event_log)
# Check conformance
fitness = pm4py.fitness_token_based_replay(event_log, net, im, fm)
```

### 3. Advanced ML Models
**Enhancement**: Train deep learning models for KPI prediction

```python
import tensorflow as tf
# Load trained process prediction model
model = tf.keras.models.load_model("process_kpi_predictor.h5")
predictions = model.predict(process_features)
```

### 4. Database Integration
**Enhancement**: Persist processes, simulations, and user data

```python
from sqlalchemy import create_engine
engine = create_engine("postgresql://user:pass@localhost/processdb")
# Store process definitions, simulation results, user preferences
```

### 5. Real-Time Collaboration
**Enhancement**: Multi-user editing with WebSockets

```python
# FastAPI WebSocket endpoint
@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket):
    # Broadcast process changes to all connected users
```

### 6. Advanced Analytics
- **Process bottleneck detection**: Identify slow activities
- **Resource utilization**: Analyze which resources are overloaded
- **Cost optimization**: Suggest cost-reduction opportunities
- **Time series forecasting**: Predict future KPI trends

## 🐛 Troubleshooting

### Backend Issues

**Port 8000 already in use:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
# Or use different port
uvicorn main:app --port 8001
```

**Data file not found:**
```bash
# Ensure data directory exists
ls ../data/o2c_data_orders_only.xml
# Check path in main.py (line 64)
```

**Import errors:**
```bash
cd backend
pip install -r requirements.txt
# Or recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**CORS errors:**
- Check `allow_origins` in `main.py` (line 18)
- Ensure frontend URL is in allowed origins list

### Frontend Issues

**API connection failed:**
```bash
# Verify backend is running
curl http://localhost:8000/api/health
# Check console for CORS errors
# Verify API_URL in services/api.ts
```

**Build errors:**
```bash
# Type check
npx tsc --noEmit
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**UI components not rendering:**
- Check browser console for errors
- Verify all Radix UI packages are installed
- Clear browser cache

### Common Fixes

**Reset Python environment:**
```bash
cd backend
deactivate  # If venv is active
rm -rf venv __pycache__ *.pyc
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Reset Node.js environment:**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

**Check logs:**
```bash
# Backend logs
tail -f backend/backend.log

# Frontend logs
tail -f frontend/frontend.log
```

## 📚 Technology Stack

### Backend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.8+ | Core language |
| **FastAPI** | 0.115.0 | REST API framework |
| **Uvicorn** | 0.32.0 | ASGI server |
| **Pandas** | 2.2.3 | Data manipulation & XML parsing |
| **NetworkX** | 3.4.2 | Graph analysis & algorithms |
| **Scikit-learn** | 1.5.2 | ML utilities & metrics |
| **Pydantic** | 2.9.2 | Data validation & schemas |
| **NumPy** | 2.1.2 | Numerical computing |

### Frontend Technologies

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 18.3.1 | UI framework |
| **TypeScript** | 5.0.2 | Type-safe JavaScript |
| **Vite** | 4.4.5 | Build tool & dev server |
| **Tailwind CSS** | 3.3.0 | Utility-first CSS |
| **Radix UI** | Multiple | Accessible component library |
| **Zustand** | 4.4.1 | State management |
| **Axios** | 1.5.0 | HTTP client |
| **Lucide React** | 0.487.0 | Icon library |
| **React DnD** | 16.0.1 | Drag and drop |
| **Framer Motion** | 11.0.0 | Animation library |
| **Recharts** | 2.15.2 | Chart components |
| **Sonner** | 2.0.3 | Toast notifications |

### Development Tools

- **Jupyter Notebook**: Data exploration (EDA_O2C_Orders.ipynb)
- **ESLint**: JavaScript/TypeScript linting
- **PostCSS**: CSS processing
- **Autoprefixer**: CSS vendor prefixing

## 🎯 Roadmap & Future Enhancements

### Phase 1: Core Improvements
- [ ] Integrate real LLM (OpenAI/Anthropic) for advanced NLP
- [ ] Add process discovery from event logs (PM4Py)
- [ ] Implement conformance checking
- [ ] Train ML models for accurate KPI prediction

### Phase 2: Data & Persistence
- [ ] Database integration (PostgreSQL/MongoDB)
- [ ] User authentication & authorization
- [ ] Save/load process definitions
- [ ] Simulation history tracking

### Phase 3: Advanced Features
- [ ] Real-time collaboration (WebSockets)
- [ ] Process variant comparison
- [ ] Bottleneck detection algorithms
- [ ] Resource optimization recommendations
- [ ] What-if scenario analysis

### Phase 4: Enterprise Features
- [ ] Multi-tenancy support
- [ ] Role-based access control
- [ ] Audit logging
- [ ] Export to PDF/PowerPoint/Excel
- [ ] Integration with BPM tools (Camunda, etc.)
- [ ] REST API for third-party integrations

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/AmazingFeature`)
3. **Commit** your changes (`git commit -m 'Add some AmazingFeature'`)
4. **Push** to the branch (`git push origin feature/AmazingFeature`)
5. **Open** a Pull Request

Please ensure:
- Code follows existing style conventions
- All tests pass (`python test_backend.py`)
- TypeScript types are properly defined
- Documentation is updated

## 📄 License

This project is licensed under the MIT License.

## 📞 Support

- **Issues**: Report bugs or request features via GitHub Issues
- **Discussions**: Join community discussions on GitHub
- **Documentation**: Check inline code comments and API docs

## 🙏 Acknowledgments

- **FastAPI** for the excellent Python web framework
- **Radix UI** for accessible component primitives
- **Vercel** for hosting and deployment infrastructure
- Process mining research community for inspiration

---

**Built with ❤️ for process optimization, business intelligence, and AI-powered insights**

*Empowering organizations to simulate, analyze, and optimize their business processes*
