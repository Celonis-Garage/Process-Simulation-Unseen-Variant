import { useState, useEffect } from 'react';
import Scene from './Scene';
import Timeline from './components/Timeline';
import './App.css';

const API_BASE_URL = 'http://localhost:8000';

function App() {
  const [sceneData, setSceneData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [currentTime, setCurrentTime] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1); // 1x normal speed
  const [availableOrders, setAvailableOrders] = useState([]);
  const [selectedOrder, setSelectedOrder] = useState('order_1'); // Default to variant_1 sample
  const [selectedOrderInfo, setSelectedOrderInfo] = useState(null);

  useEffect(() => {
    fetchAvailableOrders();
  }, []);

  useEffect(() => {
    if (selectedOrder) {
      fetchSampleCase(selectedOrder);
    }
  }, [selectedOrder]);

  const fetchAvailableOrders = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/orders`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      const orders = data.orders || [];
      setAvailableOrders(orders);
      
      // Set info for the default selected order
      if (orders.length > 0) {
        const defaultOrder = orders.find(o => o.case_id === selectedOrder) || orders[0];
        setSelectedOrderInfo(defaultOrder);
      }
    } catch (err) {
      console.error('Error fetching available orders:', err);
      // Don't show error for order list failure, just use default
    }
  };

  const fetchSampleCase = async (caseId) => {
    try {
      setLoading(true);
      setError(null);
      setIsPlaying(false); // Pause animation when switching orders
      setCurrentTime(0); // Reset timeline

      // Fetch specific case
      const response = await fetch(`${API_BASE_URL}/api/sample?case_id=${caseId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      console.log('Sample case data:', data);

      // Fetch the scene JSON file
      const sceneResponse = await fetch(`${API_BASE_URL}/${data.scene_path}`);
      
      if (!sceneResponse.ok) {
        throw new Error(`Failed to load scene file: ${sceneResponse.status}`);
      }
      
      const scene = await sceneResponse.json();
      console.log('Scene data:', scene);

      setSceneData(scene);
      setLoading(false);
    } catch (err) {
      console.error('Error fetching sample case:', err);
      setError(err.message);
      setLoading(false);
    }
  };

  const handleTimeChange = (time) => {
    setCurrentTime(time);
  };

  const handlePlayPause = () => {
    setIsPlaying(!isPlaying);
  };

  const handleReset = () => {
    setCurrentTime(0);
    setIsPlaying(false);
  };

  const handleSpeedChange = (speed) => {
    setPlaybackSpeed(speed);
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Loading O2C Process Visualization...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Error Loading Visualization</h2>
        <p>{error}</p>
        <button onClick={() => fetchSampleCase(selectedOrder)}>Retry</button>
      </div>
    );
  }

  if (!sceneData) {
    return (
      <div className="error-container">
        <p>No scene data available</p>
        <button onClick={() => fetchSampleCase(selectedOrder)}>Load Sample</button>
      </div>
    );
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="header-top">
          <h1>🎬 O2C Process - 3D Visualization</h1>
          <div className="order-selector">
            <label htmlFor="order-select">Select Variant:</label>
            <select 
              id="order-select"
              value={selectedOrder} 
              onChange={(e) => {
                const caseId = e.target.value;
                setSelectedOrder(caseId);
                const orderInfo = availableOrders.find(o => o.case_id === caseId);
                setSelectedOrderInfo(orderInfo);
              }}
              className="order-dropdown"
            >
              {availableOrders.map((order) => (
                <option key={order.case_id} value={order.case_id}>
                  {order.variant_id}: {order.case_id} ({order.frequency_percentage.toFixed(1)}% of orders, {order.event_count} events)
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="header-info">
          <span className="case-id">Case: {sceneData?.case_id || 'N/A'}</span>
          {selectedOrderInfo && (
            <span className="variant-info" style={{ color: '#3b82f6', fontWeight: 'bold' }}>
              Variant: {selectedOrderInfo.variant_id} ({selectedOrderInfo.frequency_percentage.toFixed(1)}% frequency)
            </span>
          )}
          <span className="order-value">
            Order Value: ${sceneData?.order_info?.order_value?.toFixed(2) || '0.00'}
          </span>
          <span className="order-status">
            Status: {sceneData?.order_info?.order_status || 'Unknown'}
          </span>
        </div>
        {selectedOrderInfo && selectedOrderInfo.variant_description && (
          <div className="variant-description" style={{ 
            padding: '8px 16px', 
            background: 'rgba(59, 130, 246, 0.1)', 
            borderRadius: '4px',
            fontSize: '0.9em',
            color: '#1f2937',
            marginTop: '8px'
          }}>
            <strong>Variant Context:</strong> {selectedOrderInfo.variant_description}
          </div>
        )}
      </header>

      <div className="main-content">
        <div className="canvas-container">
          <Scene 
            sceneData={sceneData} 
            currentTime={currentTime}
            isPlaying={isPlaying}
            playbackSpeed={playbackSpeed}
            onTimeUpdate={handleTimeChange}
          />
          
          {/* Color Legend */}
          <div className="legend">
            <h4>Legend</h4>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#ea580c' }}></div>
              <span>Main Order</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#3b82f6' }}></div>
              <span>Electronics</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#10b981' }}></div>
              <span>Office Supplies</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#f59e0b' }}></div>
              <span>Furniture</span>
            </div>
            <div className="legend-item">
              <div className="legend-color" style={{ background: '#8b5cf6' }}></div>
              <span>Printing</span>
            </div>
          </div>
        </div>

        <aside className="info-panel">
          <section className="kpi-section">
            <h3>📊 KPIs</h3>
            <div className="kpi-grid">
              <div className="kpi-item">
                <span className="kpi-label">On-time Delivery</span>
                <span className="kpi-value">{sceneData?.kpis?.on_time_delivery || 0}%</span>
              </div>
              <div className="kpi-item">
                <span className="kpi-label">Days Sales Outstanding</span>
                <span className="kpi-value">{sceneData?.kpis?.days_sales_outstanding || 0} days</span>
              </div>
              <div className="kpi-item">
                <span className="kpi-label">Order Accuracy</span>
                <span className="kpi-value">{sceneData?.kpis?.order_accuracy || 0}%</span>
              </div>
              <div className="kpi-item">
                <span className="kpi-label">Invoice Accuracy</span>
                <span className="kpi-value">{sceneData?.kpis?.invoice_accuracy || 0}%</span>
              </div>
              <div className="kpi-item">
                <span className="kpi-label">Avg Cost of Delivery</span>
                <span className="kpi-value">${sceneData?.kpis?.avg_cost_delivery || 0}</span>
              </div>
            </div>
          </section>

          <section className="entities-section">
            <h3>👥 Entities</h3>
            <div className="entity-group">
              <h4>Users ({sceneData?.entities?.users?.length || 0})</h4>
              <div className="entity-list">
                {(sceneData?.entities?.users || []).map((user, idx) => (
                  <span key={idx} className="entity-badge">{user}</span>
                ))}
              </div>
            </div>
            <div className="entity-group">
              <h4>Items ({sceneData?.entities?.items?.length || 0})</h4>
              <div className="entity-list">
                {(sceneData?.entities?.items || []).map((item, idx) => (
                  <div key={idx} className="item-detail">
                    <span className="item-name">{item?.name || 'Unknown'}</span>
                    <span className="item-qty">x{item?.quantity || 0}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="entity-group">
              <h4>Suppliers ({sceneData?.entities?.suppliers?.length || 0})</h4>
              <div className="entity-list">
                {(sceneData?.entities?.suppliers || []).map((supplier, idx) => (
                  <span key={idx} className="entity-badge">{supplier}</span>
                ))}
              </div>
            </div>
          </section>
        </aside>
      </div>

      <Timeline
        duration={90}
        currentTime={currentTime}
        isPlaying={isPlaying}
        playbackSpeed={playbackSpeed}
        onTimeChange={handleTimeChange}
        onPlayPause={handlePlayPause}
        onReset={handleReset}
        onSpeedChange={handleSpeedChange}
        keyframes={sceneData?.animation?.keyframes || []}
        sceneData={sceneData}
      />
    </div>
  );
}

export default App;
