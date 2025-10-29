// Core data types for the Process Simulation Studio

export interface ProcessActivity {
  id: string;
  name: string;
  position: { x: number; y: number };
  kpis: {
    avg_time: number;
    cost: number;
  };
}

export interface ProcessEdge {
  id: string;
  from: string;
  to: string;
}

export interface ProcessGraph {
  activities: string[];
  edges: ProcessEdge[];
  kpis: Record<string, { avg_time: number; cost: number }>;
}

export interface EventLogEntry {
  'Case ID': string;
  Activity: string;
  Timestamp: string;
  'Throughput Time': number;
  Cost: number;
}

export interface SimulationResult {
  cycle_time_change: number;
  cost_change: number;
  revenue_impact: number;
  confidence: number;
  summary: string;
}

export interface PromptResponse {
  action: string;
  new_activity?: string;
  position?: Record<string, string>;
  modifications?: Record<string, any>;
  activity?: string;
  activities?: string[];
  message?: string;
  suggestions?: string[];
}

// API response types
export interface EventLogResponse {
  event_log: EventLogEntry[];
  metadata: {
    total_cases: number;
    total_events: number;
    activities: string[];
  };
}

// UI State types
export interface AppState {
  // Process Graph State
  processGraph: ProcessGraph;
  
  // Event Log State
  eventLog: EventLogEntry[];
  eventLogMetadata: EventLogResponse['metadata'] | null;
  
  // Simulation State
  simulationResult: SimulationResult | null;
  isSimulating: boolean;
  
  // UI State
  selectedActivity: string | null;
  isPromptProcessing: boolean;
  showSimulationModal: boolean;
  
  // Actions
  updateProcessGraph: (graph: ProcessGraph) => void;
  setEventLog: (log: EventLogEntry[], metadata?: EventLogResponse['metadata']) => void;
  setSimulationResult: (result: SimulationResult | null) => void;
  setIsSimulating: (isSimulating: boolean) => void;
  setSelectedActivity: (activity: string | null) => void;
  setIsPromptProcessing: (isProcessing: boolean) => void;
  setShowSimulationModal: (show: boolean) => void;
  
  // Complex actions
  addActivity: (activity: string, position?: string, insertAfter?: string) => void;
  removeActivity: (activity: string) => void;
  updateActivityKPIs: (activity: string, kpis: Partial<{ avg_time: number; cost: number }>) => void;
  resetToDefault: () => void;
}

// Default O2C process data
export const DEFAULT_O2C_PROCESS: ProcessGraph = {
  activities: [
    "Order Received",
    "Order Approved", 
    "Invoice Created",
    "Payment Validation",
    "Payment Received"
  ],
  edges: [
    { id: "e1", from: "Order Received", to: "Order Approved" },
    { id: "e2", from: "Order Approved", to: "Invoice Created" },
    { id: "e3", from: "Invoice Created", to: "Payment Validation" },
    { id: "e4", from: "Payment Validation", to: "Payment Received" }
  ],
  kpis: {
    "Order Received": { avg_time: 1.0, cost: 5.0 },
    "Order Approved": { avg_time: 0.5, cost: 3.0 },
    "Invoice Created": { avg_time: 1.0, cost: 2.0 },
    "Payment Validation": { avg_time: 0.5, cost: 4.0 },
    "Payment Received": { avg_time: 0.3, cost: 1.0 }
  }
};
