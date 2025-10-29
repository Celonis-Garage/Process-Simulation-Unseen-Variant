# Process Simulation Studio - Order-to-Cash MVP

A complete integrated MVP for AI-powered process simulation and optimization, featuring natural language process modification, interactive visualization, event log generation, and business impact prediction.

## ✨ Recent Updates

**Frontend Consolidation (Latest)**: The frontend has been completely restructured with the new Figma design, consolidating all design files and components into a single, clean `frontend/` directory. The new design features:

- Modern UI with Radix UI components (shadcn/ui)
- Enhanced process visualization with drag-and-drop
- Improved event log panel with collapsible view
- Comprehensive set of 48+ reusable UI components
- Integrated backend services (API, state management, types)
- Clean, structured codebase with proper TypeScript types

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** (for backend)
- **Node.js 16+** (for frontend)
- **npm or yarn** (package manager)

### 1. Backend Setup

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

The backend will start on `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend will start on `http://localhost:5173`

### 3. Access the Application

Open your browser and navigate to `http://localhost:5173`

## 🧩 Architecture Overview

```
Process Simulation Studio/
├── backend/                     # FastAPI Python Backend
│   ├── main.py                 # FastAPI app & endpoints
│   ├── simulation_engine.py    # Core simulation logic
│   ├── data_generator.py       # Dummy data generation
│   ├── real_data_loader.py     # Real data loading utilities
│   ├── filter_orders.py        # XML data filtering utility
│   ├── utils.py                # Helper functions
│   └── requirements.txt        # Python dependencies
├── frontend/                    # React TypeScript Frontend (Consolidated)
│   ├── src/
│   │   ├── components/         # React components
│   │   │   ├── ui/            # Radix UI components (shadcn/ui)
│   │   │   ├── figma/         # Figma design components
│   │   │   ├── EventLogPanel.tsx
│   │   │   ├── EventPalette.tsx
│   │   │   ├── ProcessExplorer.tsx
│   │   │   ├── PromptPanel.tsx
│   │   │   ├── SimulationModal.tsx
│   │   │   └── TopBar.tsx
│   │   ├── store/             # Zustand state management
│   │   ├── services/          # API integration (axios)
│   │   ├── types/             # TypeScript type definitions
│   │   ├── lib/               # Utility functions
│   │   ├── styles/            # Global styles
│   │   ├── guidelines/        # Design guidelines
│   │   └── App.tsx            # Main application component
│   ├── package.json           # Node dependencies
│   ├── vite.config.ts         # Vite configuration
│   ├── tailwind.config.js     # Tailwind CSS config
│   └── tsconfig.json          # TypeScript configuration
├── data/                        # Data files
│   ├── o2c_data.xml
│   └── o2c_data_orders_only.xml
└── README.md
```

## 🎯 MVP Features

### 1️⃣ Prompt-Driven Process Builder
- Natural language input for process modifications
- Examples: "Add payment validation after invoice creation"
- Real-time process graph updates
- Support for adding, removing, and modifying activities

### 2️⃣ Interactive Process Explorer
- D3.js-powered process visualization
- Drag-and-drop node positioning
- Click to select, double-click to edit KPIs
- Real-time visual feedback

### 3️⃣ Event Log Generation
- Automatic synthetic data generation
- Realistic O2C process simulation
- CSV export functionality
- Statistical summary dashboard

### 4️⃣ Simulation Engine
- NetworkX-based graph analysis
- ML-inspired KPI prediction
- Business impact assessment
- Confidence scoring

### 5️⃣ Results Visualization
- Comprehensive simulation results modal
- KPI change predictions (cycle time, cost, revenue)
- Natural language business summary
- Actionable insights

## 🔧 API Endpoints

### Backend Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/parse-prompt` | Parse natural language into process modifications |
| `POST` | `/api/generate-log` | Generate synthetic event log from process graph |
| `POST` | `/api/simulate` | Run simulation and predict KPI changes |
| `GET` | `/api/health` | Backend health check |

### Example API Usage

```bash
# Parse a prompt
curl -X POST "http://localhost:8000/api/parse-prompt" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Add credit check before order approval"}'

# Generate event log
curl -X POST "http://localhost:8000/api/generate-log" \
  -H "Content-Type: application/json" \
  -d '{"graph": {"activities": ["Order Received", "Order Approved"], "edges": [...], "kpis": {...}}}'
```

## 🎨 Frontend Components

### Component Structure
```
src/components/
├── TopBar.tsx               # Top navigation bar
├── PromptPanel.tsx          # Natural language input with chat interface
├── ProcessExplorer.tsx      # Interactive process flow visualization
├── EventLogPanel.tsx        # Event log table with collapsible view
├── EventPalette.tsx         # Palette of available process steps
├── SimulationModal.tsx      # KPI simulation results modal
├── ui/                      # Radix UI component library (48+ components)
│   ├── button.tsx
│   ├── dialog.tsx
│   ├── table.tsx
│   ├── resizable.tsx
│   └── ... (and more)
└── figma/                   # Figma design utilities
    └── ImageWithFallback.tsx
```

### State Management (Zustand)
```typescript
interface AppState {
  processGraph: ProcessGraph;
  eventLog: EventLogEntry[];
  simulationResult: SimulationResult | null;
  // ... actions and UI state
}
```

## 📊 Default O2C Process

The MVP starts with a standard Order-to-Cash process:

1. **Order Received** (1.0h, $5.00)
2. **Order Approved** (0.5h, $3.00)
3. **Invoice Created** (1.0h, $2.00)
4. **Payment Validation** (0.5h, $4.00)
5. **Payment Received** (0.3h, $1.00)

## 🔮 Simulation Logic

The simulation engine uses:

- **Graph Analysis**: NetworkX for process structure analysis
- **Variant Comparison**: Similarity to known O2C patterns
- **KPI Prediction**: Mock ML models for cycle time, cost, and revenue impact
- **Confidence Scoring**: Based on pattern similarity and complexity

### Example Simulation Output
```json
{
  "cycle_time_change": -0.12,
  "cost_change": 0.03,
  "revenue_impact": 0.02,
  "confidence": 0.85,
  "summary": "Adding Payment Validation increases compliance by 15% while slightly extending cycle time by 0.8 days."
}
```

## 🧪 Development

### Backend Development
```bash
cd backend
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Building for Production
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm run build
```

## 🚀 Deployment Notes

### Backend Deployment
- Deploy FastAPI app using services like:
  - **Heroku**: `git push heroku main`
  - **Railway**: Connect GitHub repo
  - **DigitalOcean App Platform**: One-click deploy

### Frontend Deployment
- Build and deploy to:
  - **Vercel**: `vercel --prod`
  - **Netlify**: Drag & drop `dist/` folder
  - **GitHub Pages**: Enable in repository settings

### Environment Variables
```bash
# Frontend (.env)
VITE_API_URL=https://your-backend-url.com

# Backend
PORT=8000
```

## 🔗 Extension Points

The MVP is designed for easy extension:

### 1. Real LLM Integration
```python
# Replace utils.py:parse_prompt_mock() with:
import openai
def parse_prompt_real(prompt: str):
    response = openai.ChatCompletion.create(...)
    return parse_llm_response(response)
```

### 2. Database Integration
```python
# Replace in-memory data with:
from sqlalchemy import create_engine
engine = create_engine("postgresql://...")
```

### 3. Advanced ML Models
```python
# Replace simulation_engine.py with:
import tensorflow as tf
model = tf.keras.models.load_model("process_predictor.h5")
```

### 4. Process Mining Integration
```python
# Add real process mining:
import pm4py
log = pm4py.read_xes("real_event_log.xes")
```

## 🐛 Troubleshooting

### Backend Issues
- **Port 8000 in use**: Change port in `uvicorn` command
- **Import errors**: Ensure all packages in `requirements.txt` are installed
- **CORS errors**: Check `allow_origins` in `main.py`

### Frontend Issues
- **API connection failed**: Ensure backend is running on port 8000
- **Build errors**: Check TypeScript types and imports
- **Styling issues**: Verify Tailwind CSS configuration

### Common Fixes
```bash
# Reset dependencies
rm -rf node_modules package-lock.json
npm install

# Clear Python cache
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

## 📚 Technology Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **Pandas**: Data manipulation and analysis
- **NetworkX**: Graph analysis and algorithms
- **Scikit-learn**: Machine learning utilities
- **Pydantic**: Data validation and settings

### Frontend
- **React 18**: UI library with hooks
- **TypeScript**: Type-safe JavaScript
- **Vite**: Fast build tool and dev server
- **Tailwind CSS**: Utility-first CSS framework
- **Zustand**: Lightweight state management
- **D3.js**: Data visualization library
- **Axios**: HTTP client for API calls

## 🎯 Next Steps

1. **Connect Real LLM**: Replace mock prompt parsing with OpenAI/Claude API
2. **Add Database**: Persist process definitions and simulation results
3. **Implement Authentication**: User accounts and process sharing
4. **Advanced Analytics**: More sophisticated ML models
5. **Process Mining**: Integration with real event logs
6. **Collaboration**: Multi-user editing and comments
7. **Export Options**: PDF reports, PowerPoint presentations

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Built with ❤️ for process optimization and AI-powered business insights**
