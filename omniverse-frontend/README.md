# O2C Process - 3D Omniverse Visualization

A 3D interactive visualization of Order-to-Cash (O2C) process flows using Three.js and React Three Fiber.

## Overview

This frontend provides an Omniverse-style 3D visualization of O2C process execution. It displays:

- **Animated Order Movement**: A sphere representing an order moves through different warehouse locations based on actual event timestamps
- **Process Locations**: Static 3D markers for each step (Sales Desk, Warehouse, Shipping Dock, etc.)
- **Timeline Controls**: Play/pause animation, scrub through time, and jump to specific events
- **KPI Dashboard**: Real-time display of process KPIs
- **Entity Information**: Users, items, and suppliers involved in the order

## Architecture

### Components

1. **App.jsx**: Main application component
   - Fetches sample case data from backend
   - Manages animation state (currentTime, isPlaying)
   - Displays KPI and entity information panels

2. **Scene.jsx**: 3D scene renderer using React Three Fiber
   - Renders warehouse locations as 3D boxes
   - Animates order sphere along process path
   - Implements camera controls (OrbitControls)
   - Interpolates positions between keyframes for smooth animation

3. **Timeline.jsx**: Timeline controls component
   - Play/pause/reset controls
   - Slider for time scrubbing
   - Event markers and timeline
   - Current event display

### Data Flow

```
Backend API (/api/sample)
    ↓
Scene JSON File
    ↓
Frontend State (sceneData)
    ↓
3D Scene Rendering + Timeline
```

## Features

### 3D Visualization

- **Dynamic Camera**: OrbitControls for pan, zoom, and rotate
- **Smooth Animation**: Interpolated movement between keyframes
- **Location Highlighting**: Active location glows when order arrives
- **Process Path**: Dashed line showing the complete route
- **Floating Effect**: Order sphere gently floats for visual appeal

### Timeline

- **Playback Control**: Play/pause the animation
- **Time Scrubbing**: Drag slider to any point in the timeline
- **Event Markers**: Visual indicators for each process step
- **Event List**: Clickable events to jump to specific timestamps
- **Progress Tracking**: Visual feedback for completed vs. pending events

### Information Panel

- **KPIs**: On-time Delivery, Days Sales Outstanding, Order Accuracy, Invoice Accuracy, Avg Cost of Delivery
- **Entities**: Users, items (with quantities), and suppliers
- **Order Info**: Order value, status, and ID

## Technology Stack

- **React**: UI framework
- **Vite**: Build tool and dev server
- **Three.js**: 3D graphics library
- **@react-three/fiber**: React renderer for Three.js
- **@react-three/drei**: Useful helpers for React Three Fiber

## Configuration

### Port

The application runs on port **5175** (configured in `vite.config.js`).

### API Connection

The frontend connects to the backend at `http://localhost:8000` to fetch:
- Sample case metadata (`/api/sample?seed=42`)
- Scene JSON file (`/exports/{case_id}_scene.json`)

The seed value (42) ensures consistent case selection across sessions.

## Scene Data Format

The backend generates a JSON file for each case with the following structure:

```json
{
  "case_id": "order_1",
  "order_info": {
    "order_value": 1234.56,
    "order_status": "Approved",
    "num_items": 3,
    "total_quantity": 10
  },
  "kpis": {
    "on_time_delivery": 85.5,
    "days_sales_outstanding": 30.2,
    "order_accuracy": 95.0,
    "invoice_accuracy": 98.5,
    "avg_cost_delivery": 45.20
  },
  "entities": {
    "users": ["U001", "U002"],
    "items": [
      {"id": "I001", "name": "Item A", "quantity": 5, "line_total": 500}
    ],
    "suppliers": ["S001", "S002"]
  },
  "animation": {
    "duration": 120.5,
    "keyframes": [
      {
        "time": 0,
        "position": [-10, 0, 0],
        "event": "Receive Customer Order",
        "label": "Sales Desk",
        "timestamp": "2023-01-01T10:00:00"
      }
      // ... more keyframes
    ]
  },
  "locations": [
    {
      "name": "Receive Customer Order",
      "label": "Sales Desk",
      "position": [-10, 0, 0]
    }
    // ... more locations
  ]
}
```

## Development

### Running Locally

```bash
# From the omniverse-frontend directory
npm install
npm run dev
```

Or use the unified startup script from the project root:

```bash
./run-system.sh
```

### Building for Production

```bash
npm run build
```

The production-ready files will be in the `dist/` directory.

## Customization

### Adjusting Location Positions

Edit the `LOCATIONS` object in `backend/usd_builder.py` to change the 3D coordinates of process steps.

### Changing Colors and Styling

- **3D Scene Colors**: Edit the material colors in `Scene.jsx`
- **UI Styling**: Modify `App.css` and `Timeline.css`
- **Theme**: Adjust color variables in the CSS files

### Animation Speed

Modify the interval in `Scene.jsx` (line ~211):

```javascript
const interval = setInterval(() => {
  onTimeUpdate((prev) => {
    const next = prev + 0.1;  // Change this value
    return next >= animation.duration ? 0 : next;
  });
}, 100);  // Change this interval (milliseconds)
```

## Browser Compatibility

- **Chrome**: ✅ Recommended
- **Firefox**: ✅ Supported
- **Safari**: ✅ Supported (WebGL required)
- **Edge**: ✅ Supported

Requires a browser with WebGL support.

## Performance

- **Lightweight**: JSON-based scene format (no heavy USD files)
- **Smooth Animation**: Uses requestAnimationFrame for optimal performance
- **Responsive**: Adapts to different screen sizes

## Future Enhancements

- [ ] Multiple order visualization (compare multiple cases)
- [ ] Heatmap overlay showing activity frequency
- [ ] Camera presets (top view, side view, etc.)
- [ ] Export animation as video
- [ ] VR support for immersive viewing
- [ ] Real USD file support (when Omniverse SDK is available)

## Troubleshooting

### "Failed to load scene file" Error

- Ensure backend is running on port 8000
- Check that the `/api/sample` endpoint returns a valid response
- Verify that the `backend/exports/` directory exists and contains the scene JSON

### Animation Not Playing

- Check browser console for errors
- Verify that the scene data has valid keyframes
- Ensure timestamps are in ISO format

### 3D Scene Not Rendering

- Check that WebGL is enabled in your browser
- Try a different browser
- Update your graphics drivers

## License

Part of the Process Simulation Studio project.
