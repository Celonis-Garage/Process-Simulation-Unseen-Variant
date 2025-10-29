import axios from 'axios';
import { ProcessGraph, PromptResponse, EventLogResponse, SimulationResult } from '../types';

// TODO: Replace with actual API URL when backend is deployed
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    
    // Handle common error cases
    if (error.response?.status === 404) {
      throw new Error('API endpoint not found. Make sure the backend is running.');
    } else if (error.response?.status === 500) {
      throw new Error('Internal server error. Check backend logs.');
    } else if (error.code === 'ECONNREFUSED') {
      throw new Error('Cannot connect to backend. Make sure it\'s running on port 8000.');
    }
    
    throw error;
  }
);

/**
 * Parse natural language prompt into structured process modification
 * POST /api/parse-prompt
 * Body: { prompt: string }
 * Returns: structured process modification JSON
 */
export const parsePrompt = async (prompt: string): Promise<PromptResponse> => {
  try {
    const response = await api.post('/api/parse-prompt', { prompt });
    return response.data;
  } catch (error: any) {
    console.error('Error parsing prompt:', error);
    throw new Error(error.response?.data?.detail || 'Failed to parse prompt');
  }
};

/**
 * Generate event log from current process graph
 * POST /api/generate-log
 * Body: { graph: ProcessGraph }
 * Returns: event log JSON with metadata
 */
export const generateEventLog = async (graph: ProcessGraph): Promise<EventLogResponse> => {
  try {
    const response = await api.post('/api/generate-log', { graph });
    return response.data;
  } catch (error: any) {
    console.error('Error generating event log:', error);
    throw new Error(error.response?.data?.detail || 'Failed to generate event log');
  }
};

/**
 * Run process simulation to predict KPI changes
 * POST /api/simulate
 * Body: { event_log: any[], graph: ProcessGraph }
 * Returns: KPI predictions and business impact analysis
 */
export const simulateProcess = async (
  eventLog: any[], 
  graph: ProcessGraph
): Promise<SimulationResult> => {
  try {
    const response = await api.post('/api/simulate', { 
      event_log: eventLog, 
      graph 
    });
    return response.data;
  } catch (error: any) {
    console.error('Error running simulation:', error);
    throw new Error(error.response?.data?.detail || 'Failed to run simulation');
  }
};

/**
 * Health check endpoint
 * GET /api/health
 */
export const healthCheck = async (): Promise<{ status: string; service: string }> => {
  try {
    const response = await api.get('/api/health');
    return response.data;
  } catch (error: any) {
    console.error('Health check failed:', error);
    throw new Error('Backend health check failed');
  }
};

/**
 * Test backend connectivity
 */
export const testConnection = async (): Promise<boolean> => {
  try {
    await healthCheck();
    return true;
  } catch (error) {
    return false;
  }
};

/**
 * Get data summary including event types with KPIs
 * GET /api/data-summary
 * Returns: summary statistics and event types with their KPIs
 */
export const getDataSummary = async (): Promise<{
  total_orders: number;
  total_events: number;
  unique_event_types: number;
  avg_events_per_order: number;
  avg_order_execution_time_hours: number;
  avg_order_execution_time_days: number;
  order_statuses: Record<string, number>;
  event_types: Array<{
    name: string;
    avg_time: number;
    cost: number;
  }>;
}> => {
  try {
    const response = await api.get('/api/data-summary');
    return response.data;
  } catch (error: any) {
    console.error('Error fetching data summary:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch data summary');
  }
};

/**
 * Get the most frequent process variant from the data
 * GET /api/most-frequent-variant
 * Returns: the most common process variant with steps and edges
 */
export const getMostFrequentVariant = async (): Promise<{
  variant: string;
  frequency: number;
  percentage: number;
  steps: Array<{
    id: string;
    name: string;
    avgTime: string;
    avgCost: string;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
  }>;
}> => {
  try {
    const response = await api.get('/api/most-frequent-variant');
    return response.data;
  } catch (error: any) {
    console.error('Error fetching most frequent variant:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch most frequent variant');
  }
};

/**
 * Get process flow metrics with real edge data
 * GET /api/process-flow-metrics
 * Returns: detailed flow statistics including case counts and timing
 */
export const getProcessFlowMetrics = async (): Promise<{
  edges: Array<{
    from: string;
    to: string;
    cases: number;
    avg_time_hours: number;
    avg_days: number;
    probability: number;
  }>;
  total_cases: number;
  unique_transitions: number;
}> => {
  try {
    const response = await api.get('/api/process-flow-metrics');
    return response.data;
  } catch (error: any) {
    console.error('Error fetching process flow metrics:', error);
    throw new Error(error.response?.data?.detail || 'Failed to fetch process flow metrics');
  }
};
