# Process Simulation Studio with Order-to-Cash 3D Visualization

An intelligent system for simulating and visualizing Order-to-Cash (O2C) business processes with real-time 3D animation. The system combines machine learning for KPI prediction with immersive 3D visualization powered by Three.js and React Three Fiber.

## Overview

This application enables organizations to design, modify, and visualize their Order-to-Cash workflows. Users can interact with process flows through natural language, predict KPI impacts using trained ML models, and watch their orders flow through a complete 3D supply chain visualization showing warehouses, suppliers, and item movements in real-time.

## Key Features

### Process Design & Modification
- **Natural Language Interface**: Modify processes using conversational prompts powered by Groq LLM (Llama 3.3)
- **Variant Selection**: Choose from 8 pre-analyzed process variants based on real O2C data
- **Interactive Process Explorer**: Visual process flow with editable event durations and costs
- **Undo/Redo Support**: Full history management for iterative process design

### Machine Learning & Prediction
- **ML-Based KPI Prediction**: Deep neural network trained on 2000 real orders
- **5 Key Performance Indicators**: On-time delivery, days sales outstanding, order accuracy, invoice accuracy, average cost
- **Context-Aware Predictions**: Same activity has different impacts in different process contexts
- **Deterministic Behavior**: Consistent predictions for reproducible analysis

### 3D Visualization
- **Complete Supply Chain View**: Watch orders flow through 13 process stations from receipt to invoice
- **Item Tracking**: Individual items animated from supplier locations to warehouse convergence
- **Event-Driven Animation**: Items procured based on process events (not arbitrary time delays)
- **Interactive Timeline**: 90-second animation with adjustable playback speed (0.5× to 8×)
- **Real-Time Process Updates**: LLM-powered commentary explaining what's happening at each step
- **User Assignment**: Each event shows which user performed it based on station/role
- **Realistic 3D Stations**: Context-aware models representing actual station functions

## Technology Stack

### Backend
- **FastAPI**: REST API for process management and predictions
- **TensorFlow/Keras**: Deep learning models for KPI prediction (417-dimensional feature vectors)
- **Groq API**: LLM integration for natural language understanding
- **Pandas**: Data processing and event log manipulation
- **NetworkX**: Graph operations for process flow management
- **PM4Py**: Process mining from XES event logs

### Frontend - Process Designer
- **React + TypeScript**: Type-safe UI development
- **Tailwind CSS**: Modern, responsive styling
- **React Flow**: Interactive process diagram editor
- **Axios**: HTTP client for API communication
- **Zustand**: State management

### Frontend - 3D Visualization
- **React + Three.js**: Declarative 3D scene rendering
- **React Three Fiber (@react-three/fiber)**: React renderer for Three.js
- **React Three Drei (@react-three/drei)**: Useful 3D helpers and abstractions
- **Vite**: Fast development server and optimized builds

## Project Structure

```
Process-Simulation-Unseen-Variant/
├── backend/
│   ├── main.py                           # FastAPI application
│   ├── llm_service.py                    # Groq API integration + narration generation
│   ├── ml_model.py                       # Neural network model management
│   ├── real_data_loader.py               # O2C data loading from XES
│   ├── usd_builder.py                    # 3D scene generator with user assignments
│   ├── feature_extraction.py             # Feature engineering for ML
│   ├── scenario_generator.py             # Entity assignment logic
│   ├── session_manager.py                # User session management
│   ├── requirements.txt                  # Python dependencies
│   ├── trained_models/                   # Saved models and scalers
│   │   ├── kpi_prediction_model.keras
│   │   └── scaler_*.pkl
│   └── exports/                          # Generated 3D scene files
│       ├── order_1_scene.json            # variant_1 (45.2% frequency)
│       ├── order_101_scene.json          # variant_2 (with discount)
│       ├── order_102_scene.json          # variant_3 (rejected)
│       ├── order_1042_scene.json         # variant_4 (with return)
│       ├── order_1073_scene.json         # variant_5 (rejected)
│       ├── order_1092_scene.json         # variant_6 (return + discount)
│       ├── order_1202_scene.json         # variant_7 (rejected + return)
│       └── order_1654_scene.json         # variant_8 (all three)
├── data/
│   ├── o2c_data_orders_only.xml          # Event log (2000 orders, 19K+ events)
│   ├── users.csv                         # User entities (7 users)
│   ├── items.csv                         # Product catalog (24 items)
│   ├── suppliers.csv                     # Supplier database (16 suppliers)
│   ├── order_kpis.csv                    # Historical KPIs per order
│   ├── orders_enriched.csv               # Orders with entity relationships
│   ├── variant_contexts.json             # 8 process variants with descriptions
│   └── variant_sample_orders.csv         # Sample orders (1 per variant)
├── frontend/                             # Process Designer UI
│   ├── src/
│   │   ├── App.tsx                       # Main application
│   │   ├── components/                   # UI components
│   │   │   ├── ProcessExplorer.tsx       # Visual process flow
│   │   │   ├── EventInfoDialog.tsx       # Edit event duration/cost
│   │   │   ├── EventLogPanel.tsx         # Preview event log
│   │   │   └── SimulationModal.tsx       # KPI prediction results
│   │   ├── store/useAppStore.ts          # State management
│   │   └── services/api.ts               # API client
│   └── package.json
├── omniverse-frontend/                   # 3D Visualization UI
│   ├── src/
│   │   ├── App.jsx                       # Main 3D viewer app
│   │   ├── Scene.jsx                     # Three.js 3D scene
│   │   └── components/
│   │       ├── Timeline.jsx              # Animation timeline controls
│   │       ├── NarrationBox.jsx          # Real-time process updates
│   │       ├── NarrationBox.css          # Narration styling
│   │       └── Timeline.css              # Timeline styling
│   └── package.json
├── run-system.sh                         # Automated startup script
└── README.md                             # This file
```

## Installation

### Prerequisites

- **Python 3.13+**
- **Node.js 18+**
- **8GB+ RAM** (recommended for ML training)
- **Modern browser** with WebGL 2.0 support

### Quick Start

1. **Clone the repository**
```bash
git clone <repository-url>
cd Process-Simulation-Unseen-Variant
```

2. **Run the automated setup**
```bash
chmod +x run-system.sh
./run-system.sh
```

The script will:
- Create Python virtual environment
- Install all dependencies (backend + both frontends)
- Train ML model (if not already trained)
- Generate 3D scene files for 8 variants
- Start all three servers

**Access the system:**
- **Process Designer**: http://localhost:3000
- **3D Visualization**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Manual Setup (Alternative)

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set up Groq API key
echo "GROQ_API_KEY=your_key_here" > .env

# Train model (first time only)
python train_model.py

# Start server
uvicorn main:app --reload
```

**Process Designer Frontend:**
```bash
cd frontend
npm install
npm run dev  # Runs on port 3000
```

**3D Visualization Frontend:**
```bash
cd omniverse-frontend
npm install
npm run dev  # Runs on port 5173
```

## Usage Guide

### 1. Process Designer (Port 3000)

**Initial Setup:**
1. Open http://localhost:3000
2. Use natural language to select a process variant:
   - "Show me a standard order fulfillment process"
   - "I want to see orders with returns"
   - "Show rejected orders"

**Modifying the Process:**
- **Add activities**: "Add Process Return Request after Ship Order"
- **Remove activities**: "Remove Generate Shipping Label"
- **Edit properties**: Click the info icon (ⓘ) on any activity to edit duration/cost
- **Undo/Redo**: Use the undo ⟲ and redo ⟳ buttons

**Run Simulation:**
1. Click "Simulate Process" button
2. View predicted KPI changes
3. Compare baseline vs. modified performance

### 2. 3D Visualization (Port 5173)

**Select a Variant:**
- Use the dropdown to choose from 8 process variants
- Each variant represents a different order scenario (standard, rejected, with returns, etc.)

**Playback Controls:**
- **▶ Play/Pause**: Start or stop the animation
- **⏮ Reset**: Return to start
- **Speed**: Click to cycle through 0.5×, 1×, 2×, 4×, 8× playback speeds
- **Timeline Slider**: Scrub to any point in time
- **Event Cards**: Click to jump to specific events

**Camera Controls:**
- **Left Click + Drag**: Rotate camera
- **Right Click + Drag**: Pan view
- **Scroll Wheel**: Zoom in/out

**What You'll See:**
- **Orange sphere**: Main order flowing through stations
- **Colored spheres**: Individual items (blue=electronics, green=office supplies, etc.)
- **3D stations**: Realistic models representing warehouses, offices, shipping docks
- **Green factories**: Supplier locations with country labels
- **Progressive paths**: Lines showing order and item movement
- **Process Updates**: Real-time narration explaining current actions

### Supported Activities

The system recognizes these O2C activities:
1. Receive Customer Order
2. Validate Customer Order
3. Perform Credit Check
4. Approve Order
5. Reject Order
6. Schedule Order Fulfillment
7. Generate Pick List
8. Pack Items
9. Generate Shipping Label
10. Ship Order
11. Generate Invoice
12. Apply Discount
13. Process Return Request
14. Receive Payment
15. Close Order
16. Cancel Order

## 3D Visualization Features

### Real-Time Process Updates

The narration box provides live commentary during simulation:
- **Action-focused bullets**: What's happening right now
- **User assignment**: Which user is performing each event (based on station/role)
- **Relevant data only**: Only shows items, suppliers, etc. when relevant to current event
- **LLM-generated**: Intelligent narration powered by Groq Llama 3.1

**Example narration:**
```
• Action: Packing items for shipment
• By: Diana Lopez
• Items: Laptop, Mouse, Keyboard, Monitor
```

### User-to-Event Assignment

Each event is assigned to a specific user based on their role:
- **Reception**: Customer service (Receive Order)
- **Validation**: Order processor (Validate Order)
- **Finance**: Credit team (Credit Check)
- **Management**: Managers (Approve/Reject/Cancel)
- **Planning**: Supply chain (Schedule Fulfillment)
- **Warehouse**: Warehouse staff (Pick List, Pack Items)
- **Shipping**: Shipping team (Ship Order, Generate Label)
- **Accounting**: Billing team (Generate Invoice, Receive Payment)

### Event-Driven Item Procurement

Items are not time-based but triggered by specific process events:
- **Trigger Event**: "Approve Order" → Items depart from suppliers
- **Arrival Event**: "Generate Pick List" → Items reach warehouse
- **Merge Event**: "Pack Items" → Items combine with order

**Special handling:**
- Rejected/cancelled orders: Items remain at suppliers (never procured)
- Staggered departure: Items leave suppliers 10 seconds apart for visibility

### 8 Process Variants

| Variant | Description | Frequency | Events |
|---------|-------------|-----------|---------|
| variant_1 | Standard flow | 45.2% | 11 |
| variant_2 | With discount | 17.5% | 12 |
| variant_3 | Rejected order | 13.1% | 4 |
| variant_4 | With return | 9.8% | 12 |
| variant_5 | Rejected order | 6.2% | 4 |
| variant_6 | Return + discount | 4.7% | 13 |
| variant_7 | Rejected + return | 2.1% | 5 |
| variant_8 | All three | 1.4% | 6 |

### Animation Timeline

**Duration**: 90 seconds (adjustable with speed controls)

**Timeline breakdown:**
- **0-30s**: Order initiation, validation, credit check
- **30-60s**: Approval, scheduling, item procurement from suppliers
- **60-90s**: Warehouse operations, packing, shipping, invoicing
- **Post-events**: Discounts, returns, payments (normalized to appear shortly after main flow)

### Visual Intelligence

**Color Coding:**
- **Order**: Orange (#ea580c)
- **Electronics**: Blue (#3b82f6)
- **Office Supplies**: Green (#10b981)
- **Furniture**: Amber (#f59e0b)
- **Printing**: Purple (#8b5cf6)

**Station Colors:**
- Reception: Indigo | Validation: Purple | Office: Sky Blue
- Planning: Cyan | Warehouse: Green | Packing: Amber
- Shipping: Red | Accounting: Pink | Rejection: Dark Red

**3D Models:**
- Reception: Desk with counter
- Warehouse: Large building with shelves
- Packing: Table with boxes
- Shipping: Loading dock
- Office: Desk with monitor
- Accounting: Computer workstation
- Suppliers: Factory buildings with chimneys

## Machine Learning Architecture

### Model Design

**Input Layer (417 dimensions):**
- Transition frequency matrix: 13×13 = 169 features
- Transition duration matrix: 13×13 = 169 features
- User involvement: 7 features
- Item quantities: 24 features
- Item amounts: 24 features
- Supplier involvement: 16 features
- Outcome features: 8 features (rejection, return, cancellation, etc.)

**Hidden Layers:**
- Dense(256) + BatchNorm + Dropout(0.3)
- Dense(128) + BatchNorm + Dropout(0.3)
- Dense(64) + BatchNorm + Dropout(0.3)

**Output Layer:**
- 5 KPI predictions (normalized 0-1)

**Training:**
- Dataset: 2000 orders from real O2C event log
- Optimizer: Adam (lr=0.001)
- Epochs: 300 with early stopping (patience=20)
- Batch size: 32
- Validation split: 20%

### Predicted KPIs

1. **On-time Delivery (%)**: Orders delivered within promised timeframe
2. **Days Sales Outstanding (days)**: Time to collect payment
3. **Order Accuracy (%)**: Orders fulfilled without errors
4. **Invoice Accuracy (%)**: Invoices correct on first attempt
5. **Average Cost of Delivery ($)**: Operational cost per order

### Model Intelligence

**Learned Business Logic:**
- Removing critical steps (Approve Order, Shipping Label) worsens KPIs by 15-21%
- Rejection activities increase costs by ~6%
- Streamlining can improve performance (+3% when removing redundant steps)
- Context matters: Same activity has different impacts in different process variants

## Configuration

### Environment Variables

Create `backend/.env`:
```bash
GROQ_API_KEY=your_groq_api_key_here
```

Get your API key from: https://console.groq.com

### Model Parameters

Modify in `backend/ml_model.py`:
- Learning rate: `0.001`
- Batch size: `32`
- Architecture: `[417] -> 256 -> 128 -> 64 -> [5]`
- Dropout: `0.3`

### Data Configuration

Fixed entity counts (from enriched O2C dataset):
- **7 users**: Various roles (managers, analysts, coordinators)
- **24 items**: 4 categories (Electronics, Furniture, Office Supplies, Packaging)
- **16 suppliers**: Domestic and international
- **2000 orders**: Training data with real timestamps and KPIs

## Performance Metrics

### Response Times
- Prompt parsing (LLM): 1-2 seconds
- ML prediction: 50-100ms
- Event log generation: 100-200ms
- 3D scene generation: 200-500ms
- Narration generation: 600-1700ms
- Total simulation: 2-3 seconds

### Resource Usage
- Backend memory: 500MB-1GB
- Frontend memory: 200-400MB (each)
- Model size: 15MB
- Scene file size: 50-100KB per variant

### 3D Visualization Performance
- Frame rate: 60 FPS (even at 8× playback)
- Objects: 20-30 animated simultaneously
- Load time: 2-3 seconds (including API fetch)

## Browser Compatibility

**Tested and verified:**
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+ (macOS/iOS)
- ✅ Edge 90+

**Requirements:**
- WebGL 2.0 support (standard in all modern browsers)
- JavaScript enabled
- Minimum 1920×1080 resolution recommended for best experience

## Troubleshooting

### Backend Issues

**Won't start:**
- Check Python version: `python3 --version` (needs 3.13+)
- Verify virtual environment: `which python` (should be in venv/)
- Check port 8000: `lsof -i :8000`
- Review logs: `tail -f backend/backend.log`

**ML predictions returning 0%:**
- Expected for default process (perfect baseline match)
- Check if process actually changed in browser console
- Verify backend received modified process in logs

### Frontend Issues

**Build errors:**
- Check Node version: `node --version` (needs 18+)
- Clean install: `rm -rf node_modules package-lock.json && npm install`
- Clear cache: `npm cache clean --force`

**3D visualization blank screen:**
- Ensure backend is running on port 8000
- Check browser console for errors
- Verify scene files exist in `backend/exports/`
- Check Network tab for failed API calls to `/api/orders` or `/api/sample`

**Low frame rate:**
- Reduce playback speed
- Close other browser tabs
- Check GPU acceleration is enabled

### API Issues

**Groq API errors:**
- Verify API key in `.env` file
- Check API quota/limits at console.groq.com
- Review backend logs for specific error messages

**CORS errors:**
- Backend should allow origins: `localhost:3000`, `localhost:5173`
- Check CORS middleware in `backend/main.py`

## Development

### Adding New Activities

1. Update `backend/utils.py`: Add to `common_activities` list
2. Regenerate training data with new patterns
3. Retrain model: `python backend/train_model.py`
4. Update variant contexts if needed

### Extending KPIs

1. Add KPI calculation in `backend/regenerate_kpis.py`
2. Modify `backend/ml_model.py`: Add output layer
3. Update TypeScript interfaces in `frontend/src/types/index.ts`
4. Retrain model with new target

### Customizing 3D Visualization

**Change station positions:**
- Edit `generate_dynamic_activity_positions()` in `backend/usd_builder.py`

**Add new supplier locations:**
- Update `generate_dynamic_supplier_positions()` in `backend/usd_builder.py`

**Modify colors:**
- Update `CATEGORY_COLORS` constant in `backend/usd_builder.py`

**Adjust animation timing:**
- Modify `duration` prop in `omniverse-frontend/src/App.jsx`
- Change `TARGET_DURATION` in `omniverse-frontend/src/Scene.jsx`

### Code Quality Standards

- Type hints in Python code
- Pydantic models for API validation
- TypeScript for frontend type safety
- Comprehensive error handling
- Structured logging
- Component-based architecture

## Project Status

**Current Version**: 2.0.0 (December 2024)

**Status**: Production-ready

**Validated Features:**
- ✅ Process modification via natural language
- ✅ ML-based KPI prediction with business logic
- ✅ Interactive process designer with undo/redo
- ✅ 8-variant process library with real data
- ✅ Complete 3D supply chain visualization
- ✅ Event-driven item procurement
- ✅ Real-time process narration
- ✅ User-to-event role assignment
- ✅ Session-based entity persistence

**Known Limitations:**
- KPI time/cost modifications don't affect predictions (feature gap)
- Activity scope limited to O2C dataset (by design)
- Narration requires Groq API key (fallback available)

## License

Academic/Research use. Not for commercial deployment without thorough validation.

## Acknowledgments

- **O2C Dataset**: Process mining research community
- **Groq**: LLM API access (Llama 3.3, Llama 3.1)
- **TensorFlow/Keras**: ML framework
- **Three.js & React Three Fiber**: 3D rendering engine
- **React Flow**: Process visualization library
- **PM4Py**: Process mining toolkit
- **FastAPI**: High-performance Python web framework

---

**Last Updated**: December 2024  
**Maintained By**: Process Optimization Research Team  
**Documentation**: See `/frontend/README.md` and `/omniverse-frontend/README.md` for component-specific details
