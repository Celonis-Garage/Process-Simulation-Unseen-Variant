# Process Simulation Studio

A machine learning-powered system for simulating and optimizing business process workflows. The system analyzes Order-to-Cash (O2C) processes and predicts KPI impacts when modifying process structures.

## Overview

This application combines deep learning with process mining to help organizations understand how changes to their workflows will affect key performance indicators. Users can modify process structures through natural language prompts and receive predictions on delivery times, costs, accuracy metrics, and cash flow impact.

## Key Features

- Natural language process modification using LLM integration (Groq API)
- ML-based KPI prediction using trained neural networks
- Interactive process visualization and editing
- Support for adding, removing, and reordering process activities
- Real-time simulation of process changes
- Comprehensive test suite with 16 validated scenarios

## Technology Stack

### Backend
- FastAPI for REST API
- TensorFlow/Keras for deep learning models
- Pandas for data processing
- NetworkX for graph operations
- Groq LLaMA 3.3 for natural language understanding

### Frontend
- React with TypeScript
- Tailwind CSS for styling
- React Flow for process visualization
- Axios for API communication

## Project Structure

```
Process-Simulation-Unseen-Variant/
├── backend/
│   ├── main.py                    # FastAPI application
│   ├── ml_model.py                # Neural network model management
│   ├── feature_extraction.py     # Feature engineering for ML
│   ├── scenario_generator.py     # Entity assignment logic
│   ├── real_data_loader.py       # O2C data loading and parsing
│   ├── llm_service.py             # Groq API integration
│   ├── train_model.py             # Model training script
│   ├── requirements.txt           # Python dependencies
│   └── trained_models/            # Saved ML models and scalers
├── data/
│   ├── o2c_data_orders_only.xml  # Order-to-Cash event log
│   ├── users.csv                  # User entities (7 users)
│   ├── items.csv                  # Product catalog (24 items)
│   ├── suppliers.csv              # Supplier database (16 suppliers)
│   ├── order_kpis.csv             # Historical KPIs per order
│   └── orders_enriched.csv        # Orders with entity links
├── frontend/
│   ├── src/
│   │   ├── App.tsx               # Main React component
│   │   ├── components/           # UI components
│   │   └── services/             # API client
│   └── package.json              # Node dependencies
├── run-system.sh                 # System startup script
└── README.md                     # This file
```

## Installation

### Prerequisites

- Python 3.13+
- Node.js 18+
- Virtual environment support
- 8GB+ RAM recommended for ML operations

### Setup Steps

1. Clone the repository:
```bash
cd /path/to/project
```

2. Run the automated setup script:
```bash
chmod +x run-system.sh
./run-system.sh
```

This script will:
- Create Python virtual environment
- Install backend dependencies
- Install frontend dependencies
- Train ML model (if not already trained)
- Start both backend and frontend servers

The system will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

### Manual Setup (Alternative)

If you prefer manual setup:

**Backend:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python train_model.py  # Train the ML model
uvicorn main:app --reload --port 8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## Usage

### Basic Workflow

1. Open the frontend at http://localhost:3000
2. The default O2C process will be displayed with 10 activities
3. Use natural language prompts to modify the process
4. Click "Simulate" to see predicted KPI impacts

### Example Prompts

**Adding Activities:**
- "Add Process Return Request after Ship Order"
- "Add Apply Discount after Approve Order"
- "Add Reject Order after Perform Credit Check"

**Removing Activities:**
- "Remove Generate Shipping Label"
- "Remove Schedule Order Fulfillment"

**Multiple Changes:**
- "Add Apply Discount after Approve Order and remove Schedule Order Fulfillment"
- "Remove Generate Shipping Label and remove Approve Order"

### Supported Activities

The system recognizes these activities from the O2C dataset:
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

## Predicted KPIs

The system predicts five key performance indicators:

1. **On-time Delivery (%)** - Percentage of orders delivered within promised timeframe
2. **Days Sales Outstanding (days)** - Average time to collect payment after delivery
3. **Order Accuracy (%)** - Percentage of orders fulfilled without errors
4. **Invoice Accuracy (%)** - Percentage of invoices generated correctly first time
5. **Average Cost of Delivery ($)** - Average operational cost per order

For each simulation, you'll see:
- Baseline values (most frequent variant performance)
- Predicted values (modified process performance)
- Percentage change and impact assessment

## Machine Learning Model

### Architecture

The system uses a multi-output deep neural network with:
- Input: 409-dimensional feature vector
  - Transition frequency matrix (13x13)
  - Transition duration matrix (13x13)
  - User involvement vector (7)
  - Item quantities (24) and amounts (24)
  - Supplier involvement vector (16)
- Hidden layers: 256 -> 128 -> 64 neurons with batch normalization
- Outputs: 5 KPIs (normalized to 0-1 range)
- Training data: 1500+ historical O2C orders

### Model Training

The model is automatically trained when you first run the system. Training typically takes 5-10 minutes and is stored in `backend/trained_models/`.

To retrain manually:
```bash
cd backend
source venv/bin/activate
python train_model.py
```

Training metrics are displayed in real-time and saved alongside the model.

## Testing

### Comprehensive Test Suite

The system includes 16 validated test scenarios covering:
- Baseline verification (2 tests)
- Single step additions (3 tests)
- Single step removals (3 tests)
- Multiple simultaneous changes (3 tests)
- KPI time modifications (3 tests)
- KPI cost modifications (2 tests)

### Test Results Summary

From the latest test run (November 3, 2025):
- **Structure Change Tests**: 11/11 passed (100%)
- **Baseline Detection**: Perfect (0% change for default process)
- **ML Business Logic**: Correctly identifies critical vs non-critical steps
- **Consistency**: Identical results on repeat runs

### Running Tests

Test scenarios are documented in `REVISED_TEST_SCENARIOS.md`. To review test results, see `REVISED_COMPREHENSIVE_TEST_REPORT.md`.

## Key Findings from Testing

### What Works Well

1. **Baseline Detection** - The system perfectly identifies when no changes have been made (0.00% change on all KPIs)

2. **ML Intelligence** - The model learned real business logic from data:
   - Correctly warns that removing "Approve Order" worsens KPIs by 15%
   - Identifies that removing "Shipping Label" causes 21% degradation
   - Understands that "Reject Order" activities are expensive (6% penalty)

3. **Context Awareness** - Same activity has different impact in different contexts:
   - Removing "Shipping Label" alone: -21% (disaster)
   - Removing "Label" + "Schedule" together: +3% (streamlined)

4. **Deterministic Behavior** - Same process always produces same predictions

### Current Limitations

1. **KPI Modifications Not Implemented** - Time and cost changes don't affect predictions
   - Cannot simulate "Change invoice time to 30 minutes"
   - Cannot model "Increase shipping cost to $200"
   - This is a known gap documented in test reports

2. **Activity Scope** - Only activities from the O2C dataset are recognized
   - Adding unlisted activities will be rejected by the system

3. **Magnitude Variance** - Predicted changes can range from 1-26% vs expected 2% per step
   - Direction is reliable, exact percentages vary based on context

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:
```
GROQ_API_KEY=your_groq_api_key_here
```

Get your Groq API key from: https://console.groq.com

### Model Parameters

Key parameters in `backend/ml_model.py`:
- Learning rate: 0.001
- Batch size: 32
- Epochs: 300 (with early stopping)
- Architecture: [409] -> 256 -> 128 -> 64 -> [5 outputs]

### Data Configuration

The system uses fixed entity counts:
- 7 users with defined roles (Order Manager, Credit Analyst, etc.)
- 24 items across 4 categories (Electronics, Furniture, Office Supplies, Packaging)
- 16 suppliers with various specializations
- 1500+ historical orders for training

## Development

### Adding New Activities

To add activities to the dataset:
1. Update `backend/utils.py` - add to `common_activities` list
2. Regenerate training data with new activity patterns
3. Retrain the model using `python train_model.py`

### Extending KPI Support

To add new KPIs:
1. Update `backend/EDA_O2C_Orders.ipynb` - add KPI calculation
2. Modify `backend/ml_model.py` - add output layer
3. Update `frontend/src/types/index.ts` - add interface fields
4. Retrain model with new target

### Code Quality

The codebase follows these practices:
- Type hints throughout Python code
- Pydantic models for API validation
- Centralized error handling
- Comprehensive logging
- Standardized imports and structure

## Troubleshooting

### Backend Won't Start

Check:
- Python version (requires 3.13+)
- Virtual environment activated
- All dependencies installed: `pip list`
- Port 8000 available: `lsof -i :8000`

### Frontend Build Errors

Check:
- Node version (requires 18+)
- Clean install: `rm -rf node_modules package-lock.json && npm install`
- Port 3000 available: `lsof -i :3000`

### ML Model Training Fails

Check:
- Available RAM (needs 4GB+ for training)
- Data files present in `data/` directory
- XML parsing working: `python -c "from lxml import etree; print('OK')"`

### Simulation Returns 0% Change

This is expected for:
- Default process (exact baseline match)
- KPI modifications (not yet implemented)

Unexpected 0% change indicates:
- Backend not receiving modified process
- Check browser console for API errors
- Verify backend logs: `tail -f backend/backend.log`

## Performance

### Response Times

- Prompt parsing (LLM): 1-2 seconds
- ML prediction: 50-100ms
- Event log generation: 100-200ms
- Total simulation: 2-3 seconds

### Resource Usage

- Backend memory: 500MB-1GB
- Frontend memory: 200-400MB
- Model size: 15MB (saved)
- Training data: 50MB

## Roadmap

### Planned Features

1. **KPI Modification Support** (High Priority)
   - Enable time optimization scenarios
   - Support cost adjustment modeling
   - Implement in feature extraction layer

2. **Activity Classification** (Medium Priority)
   - Categorize as control, value-add, admin, service
   - Apply category-specific complexity factors
   - Improve removal predictions

3. **Confidence Intervals** (Medium Priority)
   - Provide prediction uncertainty ranges
   - Help users assess reliability
   - Use ensemble or dropout-based methods

4. **Enhanced Explanations** (Low Priority)
   - Generate specific reasons for KPI changes
   - Provide actionable insights
   - Link predictions to training patterns

## Contributing

This is a research project developed for process optimization analysis. For questions or collaboration:
1. Review test reports in project root
2. Check API documentation at /docs endpoint
3. Examine training notebook: `backend/EDA_O2C_Orders.ipynb`

## License

Academic/Research use. Not for commercial deployment without proper testing and validation.

## Acknowledgments

- O2C dataset from process mining research
- Groq for LLM API access
- TensorFlow/Keras for ML framework
- React Flow for process visualization

---

Last Updated: November 2025
Version: 1.0.0 (ML-Enabled)
Status: Research Prototype - Structure Changes Validated, KPI Modifications Pending
