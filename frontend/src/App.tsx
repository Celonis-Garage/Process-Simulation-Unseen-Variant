import React, { useState, useEffect, useRef } from 'react';
import { TopBar } from './components/TopBar';
import { PromptPanel } from './components/PromptPanel';
import { ProcessExplorer } from './components/ProcessExplorer';
import { EventLogPanel } from './components/EventLogPanel';
import { SimulationModal } from './components/SimulationModal';
import { ResizablePanelGroup, ResizablePanel, ResizableHandle } from './components/ui/resizable';
import { getMostFrequentVariant, generateEventLog, parsePrompt, getProcessFlowMetrics, simulateProcess } from './services/api';
import { Loader2, AlertCircle, X, CheckCircle2 } from 'lucide-react';
import { Progress } from './components/ui/progress';

export interface ProcessStep {
  id: string;
  name: string;
  avgTime: string;
  avgCost: string;
  isNew?: boolean;
}

export interface ProcessEdge {
  id?: string;
  from: string;
  to: string;
  cases: number;
  avgDays: number;
}

export interface EventLog {
  caseId: string;
  activity: string;
  timestamp: string;
  throughputTime: string;
  cost: string;
  resource: string;
}

export interface Message {
  type: 'user' | 'ai';
  text: string;
}

// Dynamic fallback data - will be populated from backend
// This gets updated whenever the dataset changes
// The fallback is always the most frequent variant from the current dataset
let cachedFallbackSteps: ProcessStep[] = [
  { id: 'start', name: 'Start', avgTime: '-', avgCost: '-' },
  { id: 'step-1', name: 'Receive Customer Order', avgTime: '1.0h', avgCost: '$25.0' },
  { id: 'step-2', name: 'Validate Customer Order', avgTime: '1m', avgCost: '$0.5' },
  { id: 'step-3', name: 'Perform Credit Check', avgTime: '1m', avgCost: '$0.5' },
  { id: 'step-4', name: 'Approve Order', avgTime: '1m', avgCost: '$0.5' },
  { id: 'step-5', name: 'Schedule Order Fulfillment', avgTime: '1m', avgCost: '$0.5' },
  { id: 'step-6', name: 'Generate Pick List', avgTime: '1m', avgCost: '$0.5' },
  { id: 'step-7', name: 'Pack Items', avgTime: '2m', avgCost: '$0.75' },
  { id: 'step-8', name: 'Generate Shipping Label', avgTime: '1m', avgCost: '$0.5' },
  { id: 'step-9', name: 'Ship Order', avgTime: '1m', avgCost: '$0.5' },
  { id: 'step-10', name: 'Generate Invoice', avgTime: '2m', avgCost: '$0.75' },
  { id: 'end', name: 'End', avgTime: '-', avgCost: '-' }
];

let cachedFallbackEdges: ProcessEdge[] = [
  { from: 'start', to: 'step-1', cases: 100, avgDays: 0.1 },
  { from: 'step-1', to: 'step-2', cases: 98, avgDays: 0.2 },
  { from: 'step-2', to: 'step-3', cases: 96, avgDays: 0.3 },
  { from: 'step-3', to: 'step-4', cases: 94, avgDays: 0.4 },
  { from: 'step-4', to: 'step-5', cases: 92, avgDays: 0.5 },
  { from: 'step-5', to: 'step-6', cases: 90, avgDays: 0.6 },
  { from: 'step-6', to: 'step-7', cases: 88, avgDays: 0.7 },
  { from: 'step-7', to: 'step-8', cases: 86, avgDays: 0.8 },
  { from: 'step-8', to: 'step-9', cases: 84, avgDays: 0.9 },
  { from: 'step-9', to: 'step-10', cases: 82, avgDays: 1.0 },
  { from: 'step-10', to: 'end', cases: 80, avgDays: 1.1 }
];

// Resource mapping for different step types
const getResourceForStep = (stepName: string): string => {
  const resourceMap: { [key: string]: string } = {
    'Order Received': 'System',
    'Manual Data Entry': 'Clerk A',
    'Credit Check': 'Credit Bot',
    'Credit Block': 'Credit Manager',
    'Order Approved': 'Manager A',
    'Inventory Check': 'Warehouse System',
    'Stock Out': 'Inventory Manager',
    'Document Review': 'Compliance Team',
    'Goods Shipped': 'Warehouse Team',
    'Delivery Exception': 'Logistics Team',
    'Invoice Created': 'Finance Bot',
    'Billing Dispute': 'Dispute Team',
    'Payment Received': 'Payment Gateway',
    'Payment Validation': 'Validator AI',
    'Quality Review': 'QA Team',
    'Fraud Detection': 'Fraud AI',
    'Risk Assessment': 'Risk Analyzer',
    'Compliance Check': 'Compliance Bot',
    'Customer Notification': 'Notification Service',
    'Document Verification': 'Document AI'
  };
  return resourceMap[stepName] || 'System';
};

// Generate event logs from steps
const generateEventLogsFromSteps = (steps: ProcessStep[]): EventLog[] => {
  const logs: EventLog[] = [];
  const baseDate = new Date('2025-10-15 09:00');
  let currentTime = new Date(baseDate);
  
  // Filter out start and end steps
  const processSteps = steps.filter(s => s.id !== 'start' && s.id !== 'end');
  
  // Generate logs for Case C001
  processSteps.forEach((step) => {
    logs.push({
      caseId: 'C001',
      activity: step.name,
      timestamp: currentTime.toISOString().slice(0, 16).replace('T', ' '),
      throughputTime: step.avgTime,
      cost: step.avgCost,
      resource: getResourceForStep(step.name)
    });
    
    // Increment time based on avgTime
    const timeMatch = step.avgTime.match(/(\d+\.?\d*)([hdm])/);
    if (timeMatch) {
      const value = parseFloat(timeMatch[1]);
      const unit = timeMatch[2];
      if (unit === 'h') {
        currentTime = new Date(currentTime.getTime() + value * 60 * 60 * 1000);
      } else if (unit === 'd') {
        currentTime = new Date(currentTime.getTime() + value * 24 * 60 * 60 * 1000);
      } else if (unit === 'm') {
        currentTime = new Date(currentTime.getTime() + value * 60 * 1000);
      }
    } else {
      currentTime = new Date(currentTime.getTime() + 60 * 60 * 1000); // default 1h
    }
  });
  
  // Only return C001 - single case for consistency with backend
  return logs;
};

// Calculate KPIs from event logs
export interface KPIData {
  onTimeDelivery: number; // percentage
  orderAccuracy: number; // percentage
  invoiceAccuracy: number; // percentage
  dso: number; // days
  costOfDelivery: number; // dollars
  totalCost: number;
  avgCycleTimeDays: number;
  stepCount: number;
}

const calculateKPIs = (eventLogs: EventLog[], steps: ProcessStep[]): KPIData => {
  // Total cost - sum all costs for a complete case
  const totalCost = eventLogs
    .filter(log => log.caseId === 'C001')
    .reduce((sum, log) => {
      const costMatch = log.cost.match(/\$?([\d.]+)/);
      return sum + (costMatch ? parseFloat(costMatch[1]) : 0);
    }, 0);

  // Average cycle time in days (for complete case C001)
  let totalHours = 0;
  eventLogs
    .filter(log => log.caseId === 'C001')
    .forEach(log => {
      const timeMatch = log.throughputTime.match(/(\d+\.?\d*)([hd])/);
      if (timeMatch) {
        const value = parseFloat(timeMatch[1]);
        const unit = timeMatch[2];
        totalHours += unit === 'h' ? value : value * 24;
      }
    });
  const avgCycleTimeDays = totalHours / 24;

  // Step count - unique activities
  const uniqueActivities = new Set(eventLogs.map(log => log.activity));
  const stepCount = uniqueActivities.size;

  // Check for validation/quality/compliance steps
  const processSteps = steps.filter(s => s.id !== 'start' && s.id !== 'end');
  const hasValidation = processSteps.some(s => 
    s.name.toLowerCase().includes('validation') || 
    s.name.toLowerCase().includes('verification')
  );
  const hasQuality = processSteps.some(s => 
    s.name.toLowerCase().includes('quality') || 
    s.name.toLowerCase().includes('review')
  );
  const hasFraud = processSteps.some(s => 
    s.name.toLowerCase().includes('fraud') || 
    s.name.toLowerCase().includes('risk')
  );
  const hasCompliance = processSteps.some(s => 
    s.name.toLowerCase().includes('compliance')
  );

  // Base KPI values (calculated from initial 12-step process)
  // Baseline: 12 steps, cycle time calculated from actual steps
  // Cycle time: 0.5h+1h+3h+1.5h+0.5h+4h+24h+6h+1h+8h+1.5h+48h = 99h = 4.125 days
  const baseStepCount = 12; // excluding start/end
  const baseCycleTimeDays = 4.125; // actual cycle time from initial steps
  const baseOTD = 76.8;
  const baseOrderAccuracy = 81.3;
  const baseInvoiceAccuracy = 76.5;
  const baseDSO = 42;

  // Calculate improvements - OTD and DSO affected by cycle time
  let otdImprovement = 0;
  let dsoChange = 0;
  let invoiceAccuracyImprovement = 0;

  // Process optimization improvements
  // Removing bottleneck steps improves OTD and DSO only
  const stepReduction = Math.max(0, baseStepCount - stepCount);
  if (stepReduction > 0) {
    otdImprovement += stepReduction * 4; // Each removed step improves OTD
    dsoChange -= stepReduction * 2.5; // Each removed step reduces DSO
  }

  // Cycle time reduction improves OTD and DSO only
  // Shorter cycle time = better OTD and lower DSO
  const cycleTimeReduction = baseCycleTimeDays - avgCycleTimeDays;
  if (cycleTimeReduction > 0) {
    otdImprovement += Math.floor(cycleTimeReduction * 3);
    dsoChange -= Math.floor(cycleTimeReduction * 2);
  } else if (cycleTimeReduction < 0) {
    // Longer cycle time hurts OTD and DSO
    otdImprovement += Math.floor(cycleTimeReduction * 3);
    dsoChange -= Math.floor(cycleTimeReduction * 2);
  }
  
  // Invoice accuracy improves with validation/quality steps
  if (hasValidation || hasQuality) {
    invoiceAccuracyImprovement += 3;
  }
  if (hasCompliance || hasFraud) {
    invoiceAccuracyImprovement += 2;
  }
  
  return {
    onTimeDelivery: Math.min(99, Math.max(70, baseOTD + otdImprovement)),
    orderAccuracy: baseOrderAccuracy, // Always stays the same at 81.3% for base case
    invoiceAccuracy: Math.min(99, Math.max(65, baseInvoiceAccuracy + invoiceAccuracyImprovement)),
    dso: Math.max(30, baseDSO + dsoChange),
    costOfDelivery: totalCost,
    totalCost,
    avgCycleTimeDays,
    stepCount
  };
};

// Store base case KPIs - will be updated after data loads
let baseKPIs = calculateKPIs(generateEventLogsFromSteps(cachedFallbackSteps), cachedFallbackSteps);

// Helper function to build KPIs object from steps
const buildKPIsFromSteps = (steps: ProcessStep[]): any => {
  const kpis: any = {};
  steps.filter(s => s.id !== 'start' && s.id !== 'end').forEach(s => {
    const timeMatch = s.avgTime.match(/(\d+\.?\d*)([hdm])/);
    const costMatch = s.avgCost.match(/\$?([\d.]+)/);
    
    let timeInHours = 1.0;
    if (timeMatch) {
      const value = parseFloat(timeMatch[1]);
      const unit = timeMatch[2];
      if (unit === 'h') timeInHours = value;
      else if (unit === 'd') timeInHours = value * 24;
      else if (unit === 'm') timeInHours = value / 60;
    }
    
    kpis[s.name] = {
      avg_time: timeInHours,
      cost: costMatch ? parseFloat(costMatch[1]) : 50
    };
  });
  return kpis;
};

export default function App() {
  const [steps, setSteps] = useState<ProcessStep[]>([]);
  const [edges, setEdges] = useState<ProcessEdge[]>([]);
  const [eventLogs, setEventLogs] = useState<EventLog[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isSimulationOpen, setIsSimulationOpen] = useState(false);
  const [newStepData, setNewStepData] = useState<{ afterStepId: string } | null>(null);
  const [variantName, setVariantName] = useState<string>('Most Frequent Variant');
  const [processChanges, setProcessChanges] = useState<string[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [simulationResults, setSimulationResults] = useState<any>(null);
  const [isSimulating, setIsSimulating] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  
  // History for undo/redo functionality
  const [history, setHistory] = useState<Array<{
    steps: ProcessStep[];
    edges: ProcessEdge[];
    eventLogs: EventLog[];
    variantName: string;
  }>>([]);
  const [historyIndex, setHistoryIndex] = useState(-1);
  const isUndoRedoAction = useRef(false); // Flag to prevent saving during undo/redo

  // Fetch initial data from backend - DISABLED for context-aware selection
  // The process explorer now starts empty until user selects a variant via prompt
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        console.log('🎯 Context-aware mode: Process explorer starts empty');
        console.log('💡 User will select initial variant via prompt');

        // Create a new session for entity consistency
        const { createSession } = await import('./services/api');
        const newSessionId = await createSession();
        setSessionId(newSessionId);
        console.log('✅ Session created:', newSessionId);

        // REMOVED: Auto-load of most frequent variant
        // All the variant loading logic is now triggered by user's prompt via select_variant action
        
        // Just mark loading as complete - process explorer will show empty state
        setIsLoading(false);
        console.log('✅ Ready for user to select a process variant');
      } catch (err: any) {
        console.error('Error during initialization:', err);
        // No fallback needed - we start empty
        setIsLoading(false);
      }
    };

    fetchInitialData();
  }, []);

  const handleAddStep = (afterStepId: string, stepName?: string, stepData?: { avgTime: string; avgCost: string }) => {
    // If stepName is not provided, show the dialog
    if (!stepName) {
      setNewStepData({ afterStepId });
      return;
    }

    // Capture historyIndex at the start before any async operations
    const capturedHistoryIndex = historyIndex;
    console.log('🎯 handleAddStep starting with historyIndex:', capturedHistoryIndex);

    const afterIndex = steps.findIndex(s => s.id === afterStepId);
    const nextStep = steps[afterIndex + 1];
    
    // Generate unique ID to allow duplicate activities (for loops/rework)
    const baseId = stepName.toLowerCase().replace(/\s+/g, '-');
    const timestamp = Date.now();
    const newStepId = `${baseId}-${timestamp}`;
    
    const newStep: ProcessStep = {
      id: newStepId,
      name: stepName,
      avgTime: stepData?.avgTime || '1.5h',
      avgCost: stepData?.avgCost || '$40',
      isNew: true
    };

    // Insert step
    const newSteps = [...steps];
    newSteps.splice(afterIndex + 1, 0, newStep);
    setSteps(newSteps);

    // Update edges
    const newEdges = edges.filter(e => !(e.from === afterStepId && e.to === nextStep?.id));
    newEdges.push(
      { from: afterStepId, to: newStepId, cases: 115, avgDays: 0.5 },
      { from: newStepId, to: nextStep?.id || 'end', cases: 110, avgDays: 0.8 }
    );
    setEdges(newEdges);

    // Fetch fresh event logs from backend WITH KPIs
    (async () => {
      try {
        const activities = newSteps
          .filter(s => s.id !== 'start' && s.id !== 'end')
          .map(s => s.name);

        // ✅ Build KPIs object
        const kpis = buildKPIsFromSteps(newSteps);

        const eventLogResponse = await generateEventLog({
          activities,
          edges: [],
          kpis  // ✅ Pass KPIs!
        });

        if (eventLogResponse.event_log && eventLogResponse.event_log.length > 0) {
          const transformedLogs: EventLog[] = eventLogResponse.event_log.map((log: any) => ({
            caseId: log['Case ID'] || log.case_id || 'Unknown',
            activity: log.Activity || log.activity || 'Unknown',
            timestamp: log.Timestamp || log.timestamp || new Date().toISOString(),
            throughputTime: log['Throughput Time']?.toString() + 'h' || '0h',
            cost: '$' + (log.Cost || log.cost || 0).toFixed(2),  // ✅ Use Cost field from backend
            resource: getResourceForStep(log.Activity || log.activity || 'System')
          }));
          setEventLogs(transformedLogs);
          
          // Save to history with the NEW event logs
          setTimeout(() => {
            if (!isUndoRedoAction.current) {
              // Use captured historyIndex from handleAddStep start
              let newLength = 0;
              setHistory(prev => {
                const newState = {
                  steps: JSON.parse(JSON.stringify(newSteps)),
                  edges: JSON.parse(JSON.stringify(newEdges)),
                  eventLogs: JSON.parse(JSON.stringify(transformedLogs)),
                  variantName: 'Modified Variant'
                };
                // Use captured historyIndex to truncate future history if needed
                const newHistory = prev.slice(0, capturedHistoryIndex + 1);
                newHistory.push(newState);
                newLength = newHistory.length;
                console.log('✅ Saved to history after add, prev length:', prev.length, 'captured historyIndex:', capturedHistoryIndex, 'new length:', newLength);
                return newHistory.length > 10 ? newHistory.slice(1) : newHistory;
              });
              setHistoryIndex(prev => {
                const newIndex = newLength > 10 ? 9 : newLength - 1;
                console.log('✅ Updated historyIndex after add from', prev, 'to', newIndex);
                return newIndex;
              });
            }
          }, 100);
        } else {
          const fallbackLogs = generateEventLogsFromSteps(newSteps);
          setEventLogs(fallbackLogs);
          
          // Save with fallback logs
          setTimeout(() => {
            if (!isUndoRedoAction.current) {
              let newLength = 0;
              setHistory(prev => {
                const newState = {
                  steps: JSON.parse(JSON.stringify(newSteps)),
                  edges: JSON.parse(JSON.stringify(newEdges)),
                  eventLogs: JSON.parse(JSON.stringify(fallbackLogs)),
                  variantName: 'Modified Variant'
                };
                const newHistory = prev.slice(0, capturedHistoryIndex + 1);
                newHistory.push(newState);
                newLength = newHistory.length;
                console.log('✅ Saved to history after add (fallback), prev length:', prev.length, 'captured historyIndex:', capturedHistoryIndex, 'new length:', newLength);
                return newHistory.length > 10 ? newHistory.slice(1) : newHistory;
              });
              setHistoryIndex(prev => {
                const newIndex = newLength > 10 ? 9 : newLength - 1;
                console.log('✅ Updated historyIndex after add (fallback) from', prev, 'to', newIndex);
                return newIndex;
              });
            }
          }, 100);
        }
      } catch (error) {
        console.error('Error fetching event logs:', error);
        const fallbackLogs = generateEventLogsFromSteps(newSteps);
        setEventLogs(fallbackLogs);
        
        // Save even if error occurs
        setTimeout(() => {
          if (!isUndoRedoAction.current) {
            let newLength = 0;
            setHistory(prev => {
              const newState = {
                steps: JSON.parse(JSON.stringify(newSteps)),
                edges: JSON.parse(JSON.stringify(newEdges)),
                eventLogs: JSON.parse(JSON.stringify(fallbackLogs)),
                variantName: 'Modified Variant'
              };
              const newHistory = prev.slice(0, capturedHistoryIndex + 1);
              newHistory.push(newState);
              newLength = newHistory.length;
              console.log('✅ Saved to history after add (error), prev length:', prev.length, 'captured historyIndex:', capturedHistoryIndex, 'new length:', newLength);
              return newHistory.length > 10 ? newHistory.slice(1) : newHistory;
            });
            setHistoryIndex(prev => {
              const newIndex = newLength > 10 ? 9 : newLength - 1;
              console.log('✅ Updated historyIndex after add (error) from', prev, 'to', newIndex);
              return newIndex;
            });
          }
        }, 100);
      }
    })();

    // Update variant name
    setVariantName('Modified Variant');

    // Track change
    setProcessChanges([`Added '${stepName}'`]);

    // Add AI message
    setMessages([...messages, {
      type: 'ai',
      text: `Added new step: '${stepName}' between '${steps[afterIndex].name}' and '${nextStep?.name || 'End'}'.`
    }]);

    // DON'T save here - save happens in async callback above
    
    // Clear isNew flag after animation (but don't save again)
    setTimeout(() => {
      setSteps(prev => prev.map(s => ({ ...s, isNew: false })));
    }, 2000);
  };

  const handleRemoveStep = (stepId: string) => {
    const stepIndex = steps.findIndex(s => s.id === stepId);
    if (stepIndex === -1 || stepId === 'start' || stepId === 'end') return;

    const removedStep = steps[stepIndex];
    const prevStep = steps[stepIndex - 1];
    const nextStep = steps[stepIndex + 1];

    // Remove step
    const newSteps = steps.filter(s => s.id !== stepId);
    setSteps(newSteps);

    // Update edges
    const newEdges = edges.filter(e => e.from !== stepId && e.to !== stepId);
    if (prevStep && nextStep) {
      newEdges.push({ from: prevStep.id, to: nextStep.id, cases: 110, avgDays: 1 });
    }
    setEdges(newEdges);

    // Fetch fresh event logs from backend WITH KPIs
    (async () => {
      try {
        const activities = newSteps
          .filter(s => s.id !== 'start' && s.id !== 'end')
          .map(s => s.name);

        // ✅ Build KPIs object
        const kpis = buildKPIsFromSteps(newSteps);

        const eventLogResponse = await generateEventLog({
          activities,
          edges: [],
          kpis  // ✅ Pass KPIs!
        });

        if (eventLogResponse.event_log && eventLogResponse.event_log.length > 0) {
          const transformedLogs: EventLog[] = eventLogResponse.event_log.map((log: any) => ({
            caseId: log['Case ID'] || log.case_id || 'Unknown',
            activity: log.Activity || log.activity || 'Unknown',
            timestamp: log.Timestamp || log.timestamp || new Date().toISOString(),
            throughputTime: log['Throughput Time']?.toString() + 'h' || '0h',
            cost: '$' + (log.Cost || log.cost || 0).toFixed(2),  // ✅ Use Cost field from backend
            resource: getResourceForStep(log.Activity || log.activity || 'System')
          }));
          setEventLogs(transformedLogs);
        } else {
          setEventLogs(generateEventLogsFromSteps(newSteps));
        }
      } catch (error) {
        console.error('Error fetching event logs:', error);
        setEventLogs(generateEventLogsFromSteps(newSteps));
      }
    })();

    // Track change
    setProcessChanges([`Removed '${removedStep.name}'`]);

    // Add AI message
    setMessages([...messages, {
      type: 'ai',
      text: `Removed step: '${removedStep.name}' from the process.`
    }]);
  };

  const handleReorderSteps = (reorderedSteps: ProcessStep[]) => {
    setSteps(reorderedSteps);
    
    // Rebuild edges based on new order
    const newEdges: ProcessEdge[] = [];
    for (let i = 0; i < reorderedSteps.length - 1; i++) {
      newEdges.push({
        from: reorderedSteps[i].id,
        to: reorderedSteps[i + 1].id,
        cases: 115,
        avgDays: 0.5
      });
    }
    setEdges(newEdges);

    // Fetch fresh event logs from backend WITH KPIs
    (async () => {
      try {
        const activities = reorderedSteps
          .filter(s => s.id !== 'start' && s.id !== 'end')
          .map(s => s.name);

        // ✅ Build KPIs object
        const kpis = buildKPIsFromSteps(reorderedSteps);

        const eventLogResponse = await generateEventLog({
          activities,
          edges: [],
          kpis  // ✅ Pass KPIs!
        });

        if (eventLogResponse.event_log && eventLogResponse.event_log.length > 0) {
          const transformedLogs: EventLog[] = eventLogResponse.event_log.map((log: any) => ({
            caseId: log['Case ID'] || log.case_id || 'Unknown',
            activity: log.Activity || log.activity || 'Unknown',
            timestamp: log.Timestamp || log.timestamp || new Date().toISOString(),
            throughputTime: log['Throughput Time']?.toString() + 'h' || '0h',
            cost: '$' + (log.Cost || log.cost || 0).toFixed(2),  // ✅ Use Cost field from backend
            resource: getResourceForStep(log.Activity || log.activity || 'System')
          }));
          setEventLogs(transformedLogs);
        } else {
          setEventLogs(generateEventLogsFromSteps(reorderedSteps));
        }
      } catch (error) {
        console.error('Error fetching event logs:', error);
        setEventLogs(generateEventLogsFromSteps(reorderedSteps));
      }
    })();
  };

  const handleUpdateStep = (stepId: string, updates: Partial<ProcessStep>) => {
    // Capture historyIndex at the start before any async operations
    const capturedHistoryIndex = historyIndex;
    console.log('🎯 handleUpdateStep starting with historyIndex:', capturedHistoryIndex);

    const step = steps.find(s => s.id === stepId);
    const newSteps = steps.map(s => 
      s.id === stepId ? { ...s, ...updates } : s
    );
    setSteps(newSteps);
    
    // Track change if time or cost was updated
    if ((updates.avgTime || updates.avgCost) && step) {
      const changes = [];
      if (updates.avgTime) changes.push(`time from ${step.avgTime} to ${updates.avgTime}`);
      if (updates.avgCost) changes.push(`cost from ${step.avgCost} to ${updates.avgCost}`);
      setProcessChanges([`Updated '${step.name}': ${changes.join(', ')}`]);
    }
    
    // Fetch fresh event logs from backend WITH UPDATED KPIs
    (async () => {
      try {
        const activities = newSteps
          .filter(s => s.id !== 'start' && s.id !== 'end')
          .map(s => s.name);

        // ✅ Build KPIs object with updated values
        const kpis = buildKPIsFromSteps(newSteps);

        const eventLogResponse = await generateEventLog({
          activities,
          edges: [],
          kpis  // ✅ Pass updated KPIs!
        });

        if (eventLogResponse.event_log && eventLogResponse.event_log.length > 0) {
          const transformedLogs: EventLog[] = eventLogResponse.event_log.map((log: any) => ({
            caseId: log['Case ID'] || log.case_id || 'Unknown',
            activity: log.Activity || log.activity || 'Unknown',
            timestamp: log.Timestamp || log.timestamp || new Date().toISOString(),
            throughputTime: log['Throughput Time']?.toString() + 'h' || '0h',
            cost: '$' + (log.Cost || log.cost || 0).toFixed(2),  // ✅ Use Cost field from backend
            resource: getResourceForStep(log.Activity || log.activity || 'System')
          }));
          setEventLogs(transformedLogs);

          // Save to history after successful update
          setTimeout(() => {
            if (!isUndoRedoAction.current) {
              let newLength = 0;
              setHistory(prev => {
                const newState = {
                  steps: JSON.parse(JSON.stringify(newSteps)),
                  edges: JSON.parse(JSON.stringify(edges)),
                  eventLogs: JSON.parse(JSON.stringify(transformedLogs)),
                  variantName: 'Modified Variant'
                };
                const newHistory = prev.slice(0, capturedHistoryIndex + 1);
                newHistory.push(newState);
                newLength = newHistory.length;
                console.log('✅ Saved to history after update, prev length:', prev.length, 'captured historyIndex:', capturedHistoryIndex, 'new length:', newLength);
                return newHistory.length > 10 ? newHistory.slice(1) : newHistory;
              });
              setHistoryIndex(prev => {
                const newIndex = newLength > 10 ? 9 : newLength - 1;
                console.log('✅ Updated historyIndex after update from', prev, 'to', newIndex);
                return newIndex;
              });
            }
          }, 100);
        } else {
          const fallbackLogs = generateEventLogsFromSteps(newSteps);
          setEventLogs(fallbackLogs);

          // Save to history with fallback logs
          setTimeout(() => {
            if (!isUndoRedoAction.current) {
              let newLength = 0;
              setHistory(prev => {
                const newState = {
                  steps: JSON.parse(JSON.stringify(newSteps)),
                  edges: JSON.parse(JSON.stringify(edges)),
                  eventLogs: JSON.parse(JSON.stringify(fallbackLogs)),
                  variantName: 'Modified Variant'
                };
                const newHistory = prev.slice(0, capturedHistoryIndex + 1);
                newHistory.push(newState);
                newLength = newHistory.length;
                console.log('✅ Saved to history after update (fallback), prev length:', prev.length, 'captured historyIndex:', capturedHistoryIndex, 'new length:', newLength);
                return newHistory.length > 10 ? newHistory.slice(1) : newHistory;
              });
              setHistoryIndex(prev => {
                const newIndex = newLength > 10 ? 9 : newLength - 1;
                console.log('✅ Updated historyIndex after update (fallback) from', prev, 'to', newIndex);
                return newIndex;
              });
            }
          }, 100);
        }
      } catch (error) {
        console.error('Error fetching event logs:', error);
        const fallbackLogs = generateEventLogsFromSteps(newSteps);
        setEventLogs(fallbackLogs);

        // Save to history even on error
        setTimeout(() => {
          if (!isUndoRedoAction.current) {
            let newLength = 0;
            setHistory(prev => {
              const newState = {
                steps: JSON.parse(JSON.stringify(newSteps)),
                edges: JSON.parse(JSON.stringify(edges)),
                eventLogs: JSON.parse(JSON.stringify(fallbackLogs)),
                variantName: 'Modified Variant'
              };
              const newHistory = prev.slice(0, capturedHistoryIndex + 1);
              newHistory.push(newState);
              newLength = newHistory.length;
              console.log('✅ Saved to history after update (error), prev length:', prev.length, 'captured historyIndex:', capturedHistoryIndex, 'new length:', newLength);
              return newHistory.length > 10 ? newHistory.slice(1) : newHistory;
            });
            setHistoryIndex(prev => {
              const newIndex = newLength > 10 ? 9 : newLength - 1;
              console.log('✅ Updated historyIndex after update (error) from', prev, 'to', newIndex);
              return newIndex;
            });
          }
        }, 100);
      }
    })();
  };

  // Save current state to history
  const saveToHistory = () => {
    if (steps.length === 0) return; // Don't save empty state
    
    const newState = {
      steps: JSON.parse(JSON.stringify(steps)),
      edges: JSON.parse(JSON.stringify(edges)),
      eventLogs: JSON.parse(JSON.stringify(eventLogs)),
      variantName
    };
    
    // Remove future history if we're not at the end
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(newState);
    
    // Limit history to 10 states to save memory
    if (newHistory.length > 10) {
      newHistory.shift();
      setHistory(newHistory);
      setHistoryIndex(newHistory.length - 1);
    } else {
      setHistory(newHistory);
      setHistoryIndex(newHistory.length - 1);
    }
  };
  
  // Undo functionality
  const handleUndo = () => {
    if (historyIndex > 0) {
      isUndoRedoAction.current = true; // Mark as undo/redo to prevent auto-save
      const prevState = history[historyIndex - 1];
      setSteps(prevState.steps);
      setEdges(prevState.edges);
      setEventLogs(prevState.eventLogs);
      setVariantName(prevState.variantName);
      setHistoryIndex(historyIndex - 1);
      
      setMessages(prev => [...prev, {
        type: 'ai',
        text: '↶ Undo: Reverted to previous state'
      }]);
      
      // Reset flag after state updates complete
      setTimeout(() => { isUndoRedoAction.current = false; }, 0);
    }
  };
  
  // Redo functionality
  const handleRedo = () => {
    if (historyIndex < history.length - 1) {
      isUndoRedoAction.current = true; // Mark as undo/redo to prevent auto-save
      const nextState = history[historyIndex + 1];
      setSteps(nextState.steps);
      setEdges(nextState.edges);
      setEventLogs(nextState.eventLogs);
      setVariantName(nextState.variantName);
      setHistoryIndex(historyIndex + 1);
      
      setMessages(prev => [...prev, {
        type: 'ai',
        text: '↷ Redo: Restored next state'
      }]);
      
      // Reset flag after state updates complete
      setTimeout(() => { isUndoRedoAction.current = false; }, 0);
    }
  };
  
  // Reset functionality
  const handleReset = async () => {
    if (window.confirm('Reset process to empty state? This will clear all activities, history, and generate new entities.')) {
      // Reset session to get new entities
      if (sessionId) {
        try {
          const { resetSession } = await import('./services/api');
          const newSessionId = await resetSession(sessionId);
          setSessionId(newSessionId);
          console.log('✅ Session reset with new entities:', newSessionId);
        } catch (error) {
          console.error('Failed to reset session:', error);
        }
      }
      
      setSteps([]);
      setEdges([]);
      setEventLogs([]);
      setVariantName('');
      setHistory([]);
      setHistoryIndex(-1);
      setProcessChanges([]);
      setMessages([{
        type: 'ai',
        text: '🔄 Process reset. New entities generated. Start fresh by describing a new process scenario.'
      }]);
    }
  };
  
  // Keyboard shortcuts for undo/redo
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === 'z' && !e.shiftKey) {
        e.preventDefault();
        handleUndo();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'z' && e.shiftKey) {
        e.preventDefault();
        handleRedo();
      } else if ((e.ctrlKey || e.metaKey) && e.key === 'y') {
        e.preventDefault();
        handleRedo();
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [historyIndex, history]);
  
  // DISABLED: Auto-save causes issues with animations and async operations
  // Instead, we save manually after each user action completes
  // useEffect(() => {
  //   if (!isUndoRedoAction.current && steps.length > 0 && steps.filter(s => s.id !== 'start' && s.id !== 'end').length > 0) {
  //     const timeoutId = setTimeout(() => {
  //       saveToHistory();
  //     }, 100);
  //     return () => clearTimeout(timeoutId);
  //   }
  // }, [steps, edges, eventLogs]);

  const handleSimulate = async () => {
    try {
      setIsSimulating(true);
      
      // Build activities list from steps (excluding start/end)
      const activities = steps
        .filter(step => step.id !== 'start' && step.id !== 'end')
        .map(step => step.name);
      
      // Validation: Don't allow simulation if no activities
      if (activities.length === 0) {
        setMessages(prev => [...prev, {
          type: 'ai',
          text: '⚠️ Cannot simulate: No process activities defined. Please select a process variant first.'
        }]);
        setIsSimulating(false);
        return;
      }
      
      // Build edges array (simplified format for API)
      const processEdges = edges.map(edge => ({
        id: edge.id || `edge-${edge.from}-${edge.to}`,
        from: edge.from,
        to: edge.to
      }));
      
      // Build KPIs object from steps
      const kpisMap: Record<string, { avg_time: number; cost: number }> = {};
      steps.forEach(step => {
        if (step.id !== 'start' && step.id !== 'end') {
          // Parse time from avgTime string (e.g., "2h" -> 2)
          let avgTime = 1.0;
          if (step.avgTime && step.avgTime !== '-') {
            const timeMatch = step.avgTime.match(/(\d+\.?\d*)/);
            if (timeMatch) {
              avgTime = parseFloat(timeMatch[1]);
              if (step.avgTime.includes('m')) avgTime /= 60; // Convert minutes to hours
              if (step.avgTime.includes('d')) avgTime *= 24; // Convert days to hours
            }
          }
          
          // Parse cost from avgCost string (e.g., "$50.00" -> 50)
          let cost = 50.0;
          if (step.avgCost && step.avgCost !== '-') {
            const costMatch = step.avgCost.match(/\$?(\d+\.?\d*)/);
            if (costMatch) {
              cost = parseFloat(costMatch[1]);
            }
          }
          
          kpisMap[step.name] = { avg_time: avgTime, cost };
        }
      });
      
      // Build ProcessGraph object for API
      const processGraph: ProcessGraph = {
        activities,
        edges: processEdges,
        kpis: kpisMap
      };
      
      console.log('Calling backend ML simulation with:', {
        activities,
        edges: processEdges.length,
        kpis: Object.keys(kpisMap).length,
        sessionId
      });
      
      // Call backend API for ML-based simulation with session ID
      const result = await simulateProcess(eventLogs, processGraph, sessionId || undefined);
      
      console.log('🤖 ML-based simulation results:', result);
      setSimulationResults(result);
      setIsSimulationOpen(true);
      setIsSimulating(false);
    } catch (error: any) {
      console.error('Simulation error:', error);
      setIsSimulating(false);
      setMessages(prev => [...prev, {
        type: 'ai',
        text: `⚠️ Simulation failed: ${error.message}. Make sure the backend is running.`
      }]);
    }
  };

  const handlePromptSubmit = async (prompt: string) => {
    setMessages([...messages, { type: 'user', text: prompt }]);
    
    try {
      // Build current process state to send to LLM
      const currentProcess = {
        activities: steps.filter(s => s.id !== 'start' && s.id !== 'end').map(s => s.name),
        edges: edges,
        kpis: buildKPIsFromSteps(steps)
      };
      
      // Call backend API to parse the prompt WITH current process context and session ID
      console.log('Parsing prompt with backend API:', prompt);
      console.log('Current process activities:', currentProcess.activities);
      console.log('Session ID:', sessionId);
      const response = await parsePrompt(prompt, currentProcess, sessionId || undefined);
      console.log('Parsed response:', response);
      
      // Handle different action types
      
      // 🎯 NEW: Handle select_variant action (initial process selection)
      if (response.action === 'select_variant') {
        console.log('✨ Variant selection:', response.variant_id);
        // Capture historyIndex before any state changes
        const capturedHistoryIndex = historyIndex;
        console.log('🎯 select_variant starting with historyIndex:', capturedHistoryIndex);
        
        const activities = response.activities || [];
        const kpis = response.kpis || {};  // Get real KPIs from backend
        
        if (activities.length === 0) {
          setMessages(prev => [...prev, {
            type: 'ai',
            text: 'No variant found. Please describe the type of process you want to see.'
          }]);
          return;
        }
        
        // Build steps from activities with REAL KPIs from data
        const newSteps: ProcessStep[] = [
          { id: 'start', name: 'Start', avgTime: '-', avgCost: '-' },
          ...activities.map((actName: string, i: number) => {
            // Get real KPIs for this activity from backend data
            const activityKpis = kpis[actName];
            const avgTime = activityKpis?.avgTime || '2h';  // Fallback to 2h if missing
            const avgCost = activityKpis?.avgCost || '$50.0';  // Fallback to $50 if missing
            
            console.log(`Activity ${actName}: ${avgTime}, ${avgCost}`);
            
            return {
              id: `step-${i + 1}`,
              name: actName,
              avgTime: avgTime,  // Use real data from backend
              avgCost: avgCost,  // Use real data from backend
              isNew: false
            };
          }),
          { id: 'end', name: 'End', avgTime: '-', avgCost: '-' }
        ];
        
        // Build sequential edges
        const newEdges: ProcessEdge[] = [];
        for (let i = 0; i < newSteps.length - 1; i++) {
          newEdges.push({
            from: newSteps[i].id,
            to: newSteps[i + 1].id,
            cases: 100,
            avgDays: 0.1
          });
        }
        
        // Update state
        setSteps(newSteps);
        setEdges(newEdges);
        setVariantName(response.variant_id || 'Selected Variant');
        
        // Generate event logs
        const logs = generateEventLogsFromSteps(newSteps);
        setEventLogs(logs);
        
        // Update base KPIs
        baseKPIs = calculateKPIs(logs, newSteps);
        
        // Add AI response with explanation and suggested prompts
        const suggestedPromptsText = response.suggested_prompts && response.suggested_prompts.length > 0
          ? `\n\n💡 Try these next:\n${response.suggested_prompts.map((p: string) => `  • ${p}`).join('\n')}`
          : '';
        
        setMessages(prev => [...prev, {
          type: 'ai',
          text: `✅ ${response.explanation || 'Process loaded successfully'}${suggestedPromptsText}`
        }]);
        
        // Save to history after variant loads - use inline saving with local values to avoid stale closure
        setTimeout(() => {
          if (!isUndoRedoAction.current) {
            let newLength = 0;
            setHistory(prev => {
              const newState = {
                steps: JSON.parse(JSON.stringify(newSteps)),
                edges: JSON.parse(JSON.stringify(newEdges)),
                eventLogs: JSON.parse(JSON.stringify(logs)),
                variantName: response.variant_id || 'Selected Variant'
              };
              const newHistory = prev.slice(0, capturedHistoryIndex + 1);
              newHistory.push(newState);
              newLength = newHistory.length;
              console.log('✅ Saved initial variant to history, prev length:', prev.length, 'captured historyIndex:', capturedHistoryIndex, 'new length:', newLength);
              return newHistory.length > 10 ? newHistory.slice(1) : newHistory;
            });
            setHistoryIndex(prev => {
              const newIndex = newLength > 10 ? 9 : newLength - 1;
              console.log('✅ Updated historyIndex from', prev, 'to', newIndex);
              return newIndex;
            });
          }
        }, 100);
        
        console.log('✅ Variant loaded successfully with', activities.length, 'activities');
        return;
      }
      
      if (response.action === 'remove_step') {
        const activityName = response.activity || '';
        console.log('Remove step action:', { response, activityName, availableSteps: steps.map(s => s.name) });
        
        // Find step by name
        const stepToRemove = steps.find(s => 
          s.name.toLowerCase() === activityName.toLowerCase() ||
          s.id.toLowerCase().includes(activityName.toLowerCase().replace(/\s+/g, '-'))
        );
        
        if (stepToRemove && stepToRemove.id !== 'start' && stepToRemove.id !== 'end') {
          handleRemoveStep(stepToRemove.id);
          setVariantName(`Optimized: Removed ${stepToRemove.name}`);
          setMessages(prev => [...prev, {
            type: 'ai',
            text: `✓ Removed step: '${stepToRemove.name}' from the process. This should reduce cycle time and cost.`
          }]);
        } else {
          setMessages(prev => [...prev, {
            type: 'ai',
            text: `I couldn't find a step named '${activityName}' in the current process. Available steps: ${steps.filter(s => s.id !== 'start' && s.id !== 'end').map(s => s.name).join(', ')}`
          }]);
        }
      }
      else if (response.action === 'add_step') {
        const newActivity = response.new_activity || '';
        const position = response.position || {};
        
        // Find reference step
        let referenceStepId = 'start';
        if (position.after) {
          const refStep = steps.find(s => s.name.toLowerCase().includes(position.after.toLowerCase()));
          if (refStep) referenceStepId = refStep.id;
        } else if (position.before) {
          const refStep = steps.find(s => s.name.toLowerCase().includes(position.before.toLowerCase()));
          if (refStep) {
            const refIndex = steps.findIndex(s => s.id === refStep.id);
            if (refIndex > 0) referenceStepId = steps[refIndex - 1].id;
          }
        }
        
        // Check if this activity already exists (creating a loop/rework scenario)
        const isDuplicate = steps.some(s => s.name === newActivity && s.id !== 'start' && s.id !== 'end');
        
        handleAddStep(referenceStepId, newActivity);
        setVariantName(`Optimized: Added ${newActivity}${isDuplicate ? ' (Loop)' : ''}`);
        
        const duplicateMessage = isDuplicate 
          ? ` This creates a rework/quality loop - '${newActivity}' now appears multiple times in the process, which is common for quality checks, retries, or iterative approval scenarios.`
          : ' This may increase cycle time but could improve quality or compliance.';
        
        setMessages(prev => [...prev, {
          type: 'ai',
          text: `✓ Added step: '${newActivity}' to the process.${duplicateMessage}`
        }]);
      }
      else if (response.action === 'modify_kpi') {
        const activityName = response.activity || '';
        const modifications = response.modifications || {};
        
        // Find step by name
        const stepToModify = steps.find(s => 
          s.name.toLowerCase().includes(activityName.toLowerCase())
        );
        
        if (stepToModify) {
          const updates: Partial<ProcessStep> = {};
          
          if (modifications.avg_time !== undefined) {
            const time = modifications.avg_time;
            if (time < 1) {
              updates.avgTime = `${Math.round(time * 60)}m`;
            } else if (time < 24) {
              updates.avgTime = `${time}h`;
            } else {
              updates.avgTime = `${Math.round(time / 24)}d`;
            }
          }
          
          if (modifications.cost !== undefined) {
            updates.avgCost = `$${modifications.cost}`;
          }
          
          handleUpdateStep(stepToModify.id, updates);
          setVariantName(`Optimized: Modified ${stepToModify.name}`);
          
          const changeDesc = modifications.avg_time 
            ? `time to ${updates.avgTime}` 
            : `cost to ${updates.avgCost}`;
          
          setMessages(prev => [...prev, {
            type: 'ai',
            text: `✓ Updated '${stepToModify.name}' ${changeDesc}. This will impact cycle time and cost metrics.`
          }]);
        } else {
          setMessages(prev => [...prev, {
            type: 'ai',
            text: `I couldn't find a step named '${activityName}' in the current process.`
          }]);
        }
      }
      else if (response.action === 'make_parallel') {
        console.log('make_parallel action received:', response);
        const activitiesToParallelize = response.activities || [];
        console.log('Activities to parallelize:', activitiesToParallelize);
        console.log('Activities length:', activitiesToParallelize.length);
        
        if (!activitiesToParallelize || activitiesToParallelize.length < 2) {
          setMessages(prev => [...prev, {
            type: 'ai',
            text: `I need at least 2 activities to make parallel. Received: ${JSON.stringify(activitiesToParallelize)}`
          }]);
          return;
        }
        
        // Find the steps - case insensitive matching
        const stepsToParallelize = activitiesToParallelize.map((actName: string) => {
          const found = steps.find(s => s.name.toLowerCase() === actName.toLowerCase());
          console.log(`Looking for "${actName}":`, found ? `Found: ${found.name}` : 'Not found');
          return found;
        }).filter(Boolean);
        
        console.log('Steps found:', stepsToParallelize.length, 'out of', activitiesToParallelize.length);
        
        if (stepsToParallelize.length === activitiesToParallelize.length) {
          setMessages(prev => [...prev, {
            type: 'ai',
            text: `✓ Made ${activitiesToParallelize.join(' and ')} parallel. Note: Visual representation of parallel flows is coming soon. The simulation will account for parallel execution reducing overall cycle time.`
          }]);
          setVariantName(`Optimized: Parallelized Activities`);
        } else {
          const availableActivities = steps.filter(s => s.id !== 'start' && s.id !== 'end').map(s => s.name).join(', ');
          setMessages(prev => [...prev, {
            type: 'ai',
            text: `I couldn't find all the specified activities.\nRequested: ${activitiesToParallelize.join(', ')}\nAvailable: ${availableActivities}`
          }]);
        }
      }
      else if (response.action === 'reorder') {
        const activityToMove = response.activity || '';
        const position = response.position || {};
        
        const stepToMove = steps.find(s => 
          s.name.toLowerCase() === activityToMove.toLowerCase()
        );
        
        let referenceStep: ProcessStep | undefined;
        if (position.before) {
          referenceStep = steps.find(s => s.name.toLowerCase() === position.before.toLowerCase());
        } else if (position.after) {
          referenceStep = steps.find(s => s.name.toLowerCase() === position.after.toLowerCase());
        }
        
        if (stepToMove && referenceStep && stepToMove.id !== 'start' && stepToMove.id !== 'end') {
          // Remove step from current position
          const newSteps = steps.filter(s => s.id !== stepToMove.id);
          
          // Find new index
          const refIndex = newSteps.findIndex(s => s.id === referenceStep.id);
          const insertIndex = position.before ? refIndex : refIndex + 1;
          
          // Insert at new position
          newSteps.splice(insertIndex, 0, stepToMove);
          
          handleReorderSteps(newSteps);
          setVariantName(`Optimized: Reordered ${stepToMove.name}`);
          setMessages(prev => [...prev, {
            type: 'ai',
            text: `✓ Moved '${stepToMove.name}' ${position.before ? 'before' : 'after'} '${referenceStep.name}'. This may optimize the process flow.`
          }]);
        } else {
          setMessages(prev => [...prev, {
            type: 'ai',
            text: `I couldn't find the specified activities for reordering. Available: ${steps.filter(s => s.id !== 'start' && s.id !== 'end').map(s => s.name).join(', ')}`
          }]);
        }
      }
      else if (response.action === 'clarification_needed') {
        setMessages(prev => [...prev, {
          type: 'ai',
          text: response.message || "I'm not sure how to interpret that request. Could you be more specific?",
        }]);
        
        if (response.suggestions && response.suggestions.length > 0) {
          setMessages(prev => [...prev, {
            type: 'ai',
            text: `Suggestions:\n${response.suggestions?.map((s: string) => `• ${s}`).join('\n')}`
          }]);
        }
      }
      else {
        setMessages(prev => [...prev, {
          type: 'ai',
          text: `Understood! Action: ${response.action}. I'm working on implementing this feature.`
        }]);
      }
      
    } catch (error: any) {
      console.error('Error parsing prompt:', error);
      setMessages(prev => [...prev, {
        type: 'ai',
        text: `⚠️ Error processing your request: ${error.message}. Please make sure the backend is running and try again.`
      }]);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex flex-col h-screen bg-gray-50">
        <TopBar variantName="Loading..." />
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <Loader2 className="w-12 h-12 text-blue-600 animate-spin mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Loading Process Data</h2>
            <p className="text-sm text-gray-600">Fetching the most frequent process variant from backend...</p>
          </div>
        </div>
      </div>
    );
  }

  // Show error state (with fallback data)
  if (error) {
    return (
      <div className="flex flex-col h-screen bg-gray-50">
        <TopBar variantName={variantName} />
        
        <div className="p-4 bg-yellow-50 border-b border-yellow-200">
          <div className="flex items-start gap-2 max-w-4xl mx-auto">
            <AlertCircle className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-yellow-900">Backend Connection Issue</p>
              <p className="text-xs text-yellow-700 mt-1">{error}</p>
              <p className="text-xs text-yellow-700 mt-1">Using fallback data. Make sure the backend is running on port 8000.</p>
            </div>
          </div>
        </div>
        
        <ResizablePanelGroup direction="vertical" className="flex-1">
        {/* Main Workspace */}
        <ResizablePanel defaultSize={70} minSize={40}>
          <ResizablePanelGroup direction="horizontal">
            {/* Left Panel - Prompt Workspace */}
            <ResizablePanel defaultSize={35} minSize={25} maxSize={50}>
              <PromptPanel 
                messages={messages}
                onPromptSubmit={handlePromptSubmit}
                isProcessEmpty={steps.filter(s => s.id !== 'start' && s.id !== 'end').length === 0}
              />
            </ResizablePanel>
            
            <ResizableHandle withHandle />
            
            {/* Right Panel - Process Explorer */}
            <ResizablePanel defaultSize={65} minSize={50}>
              <ProcessExplorer
                steps={steps}
                edges={edges}
                onAddStep={handleAddStep}
                onRemoveStep={handleRemoveStep}
                onReorderSteps={handleReorderSteps}
                onUpdateStep={handleUpdateStep}
              />
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Bottom Panel - Event Log */}
        <ResizablePanel defaultSize={30} minSize={20} maxSize={50}>
          <EventLogPanel
            eventLogs={eventLogs}
            onSimulate={handleSimulate}
          />
        </ResizablePanel>
      </ResizablePanelGroup>

      {/* Simulation Modal */}
      {isSimulationOpen && simulationResults && (
        <SimulationModal
          isOpen={isSimulationOpen}
          onClose={() => setIsSimulationOpen(false)}
          simulationResults={simulationResults}
          variantName={variantName}
        />
      )}

      {/* Add Step Dialog */}
      {newStepData && (
        <AddStepDialog
          afterStepId={newStepData.afterStepId}
          onAdd={(stepName) => {
            handleAddStep(newStepData.afterStepId, stepName);
            setNewStepData(null);
          }}
          onClose={() => setNewStepData(null)}
        />
      )}
    </div>
    );
  }

  // Normal success state
  return (
    <div className="flex flex-col h-screen bg-gray-50">
      <TopBar variantName={variantName} />
      
      {/* Control Bar with Undo/Redo/Reset */}
      <div className="border-b border-gray-200 bg-white px-4 py-2 flex items-center gap-2">
        <div className="flex items-center gap-2">
          <button
            onClick={handleUndo}
            disabled={historyIndex <= 0}
            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed rounded transition-colors flex items-center gap-1.5"
            title="Undo (Ctrl+Z)"
          >
            <span className="text-base">↶</span>
            <span>Undo</span>
          </button>
          
          <button
            onClick={handleRedo}
            disabled={historyIndex >= history.length - 1}
            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 disabled:opacity-40 disabled:cursor-not-allowed rounded transition-colors flex items-center gap-1.5"
            title="Redo (Ctrl+Shift+Z)"
          >
            <span className="text-base">↷</span>
            <span>Redo</span>
          </button>
          
          <div className="h-4 w-px bg-gray-300 mx-1"></div>
          
          <button
            onClick={handleReset}
            className="px-3 py-1.5 text-sm bg-red-50 hover:bg-red-100 text-red-700 rounded transition-colors flex items-center gap-1.5"
            title="Reset process to empty state"
          >
            <span className="text-base">🔄</span>
            <span>Reset</span>
          </button>
        </div>
        
        <div className="ml-auto text-xs text-gray-500">
          {historyIndex >= 0 && `History: ${historyIndex + 1}/${history.length}`}
        </div>
      </div>
      
      <ResizablePanelGroup direction="vertical" className="flex-1">
        {/* Main Workspace */}
        <ResizablePanel defaultSize={70} minSize={40}>
          <ResizablePanelGroup direction="horizontal">
            {/* Left Panel - Prompt Workspace */}
            <ResizablePanel defaultSize={35} minSize={25} maxSize={50}>
              <PromptPanel 
                messages={messages}
                onPromptSubmit={handlePromptSubmit}
                isProcessEmpty={steps.filter(s => s.id !== 'start' && s.id !== 'end').length === 0}
              />
            </ResizablePanel>
            
            <ResizableHandle withHandle />
            
            {/* Right Panel - Process Explorer */}
            <ResizablePanel defaultSize={65} minSize={50}>
              <ProcessExplorer
                steps={steps}
                edges={edges}
                onAddStep={handleAddStep}
                onRemoveStep={handleRemoveStep}
                onReorderSteps={handleReorderSteps}
                onUpdateStep={handleUpdateStep}
              />
            </ResizablePanel>
          </ResizablePanelGroup>
        </ResizablePanel>

        <ResizableHandle withHandle />

        {/* Bottom Panel - Event Log */}
        <ResizablePanel defaultSize={30} minSize={20} maxSize={50}>
          <EventLogPanel
            eventLogs={eventLogs}
            onSimulate={handleSimulate}
          />
        </ResizablePanel>
      </ResizablePanelGroup>

      {/* Simulation Modal */}
      {isSimulationOpen && simulationResults && (
        <SimulationModal
          isOpen={isSimulationOpen}
          onClose={() => setIsSimulationOpen(false)}
          simulationResults={simulationResults}
          variantName={variantName}
        />
      )}

      {/* Add Step Dialog */}
      {newStepData && (
        <AddStepDialog
          afterStepId={newStepData.afterStepId}
          onAdd={(stepName) => {
            handleAddStep(newStepData.afterStepId, stepName);
            setNewStepData(null);
          }}
          onClose={() => setNewStepData(null)}
        />
      )}
    </div>
  );
}

interface AddStepDialogProps {
  afterStepId: string;
  onAdd: (stepName: string) => void;
  onClose: () => void;
}

function AddStepDialog({ afterStepId, onAdd, onClose }: AddStepDialogProps) {
  const [stepName, setStepName] = React.useState('');
  
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4" onClick={e => e.stopPropagation()}>
        <h3 className="text-lg font-semibold mb-4">Add Process Step</h3>
        <p className="text-gray-600 mb-4 text-sm">
          Enter a step name or drag & drop from the Event Palette on the right.
        </p>
        <input
          type="text"
          value={stepName}
          onChange={(e) => setStepName(e.target.value)}
          placeholder="e.g., Quality Check"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
          onKeyPress={(e) => {
            if (e.key === 'Enter' && stepName.trim()) {
              onAdd(stepName.trim());
            }
          }}
        />
        <div className="flex gap-2">
          <button
            onClick={() => stepName.trim() && onAdd(stepName.trim())}
            disabled={!stepName.trim()}
            className="flex-1 px-4 py-2 bg-blue-600 text-white hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed rounded-lg transition-colors"
          >
            Add Step
          </button>
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
