import React, { useState, useEffect } from 'react';
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
  
  // Add one log for Case C002 (first step only)
  if (processSteps.length > 0) {
    const baseDate2 = new Date('2025-10-16 10:00');
    logs.push({
      caseId: 'C002',
      activity: processSteps[0].name,
      timestamp: baseDate2.toISOString().slice(0, 16).replace('T', ' '),
      throughputTime: processSteps[0].avgTime,
      cost: processSteps[0].avgCost,
      resource: getResourceForStep(processSteps[0].name)
    });
  }
  
  return logs;
};

// Calculate KPIs from event logs
export interface KPIData {
  onTimeDelivery: number; // percentage
  orderAccuracy: number; // percentage
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
  const baseAccuracy = 81.3;
  const baseDSO = 42;

  // Calculate improvements - only affects OTD and DSO, never accuracy
  let otdImprovement = 0;
  let dsoChange = 0;

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
  
  return {
    onTimeDelivery: Math.min(99, Math.max(70, baseOTD + otdImprovement)),
    orderAccuracy: baseAccuracy, // Always stays the same at 81.3% for base case
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

  // Fetch initial data from backend
  useEffect(() => {
    const fetchInitialData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        console.log('Fetching initial process data from backend...');

        // Fetch the most frequent variant
        const variantData = await getMostFrequentVariant();

        // Cache steps for fallback
        cachedFallbackSteps = variantData.steps;

        // Fetch real process flow metrics for edges
        const flowMetrics = await getProcessFlowMetrics();
        console.log('Received flow metrics:', flowMetrics);

        // Build a map of step names to IDs
        const stepNameToId: { [key: string]: string } = {};
        variantData.steps.forEach(step => {
          stepNameToId[step.name] = step.id;
        });

        // Convert flow metrics to ProcessEdge format
        const processEdges: ProcessEdge[] = variantData.edges.map((edge, index) => {
          const fromActivity = variantData.steps.find(s => s.id === edge.source)?.name || '';
          const toActivity = variantData.steps.find(s => s.id === edge.target)?.name || '';
          
          // Find matching flow metric
          const flowMetric = flowMetrics.edges.find(
            e => e.from === fromActivity && e.to === toActivity
          );

          return {
            from: edge.source,
            to: edge.target,
            cases: flowMetric?.cases || 100,
            avgDays: flowMetric?.avg_days || 0.1
          };
        });

        cachedFallbackEdges = processEdges;

        // Set steps and edges from variant
        setSteps(variantData.steps);
        setEdges(processEdges);

        // Fetch event log
        const activities = variantData.steps
          .filter(s => s.id !== 'start' && s.id !== 'end')
          .map(s => s.name);

        const eventLogResponse = await generateEventLog({
          activities,
          edges: [],
          kpis: {}
        });

        console.log('Received event log:', eventLogResponse);

        // Transform backend event log to frontend EventLog format
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
          // Fallback to generated logs if backend returns empty
          const fallbackLogs = generateEventLogsFromSteps(variantData.steps);
          setEventLogs(fallbackLogs);
        }

        // Update base KPIs with the loaded data
        const loadedLogs = generateEventLogsFromSteps(variantData.steps);
        baseKPIs = calculateKPIs(loadedLogs, variantData.steps);

        setIsLoading(false);
      } catch (err: any) {
        console.error('Error fetching initial data:', err);
        setError(err.message || 'Failed to load process data from backend');
        
        // Fallback to cached data (most frequent variant from previous load or default)
        console.log('Falling back to cached most frequent variant...');
        setSteps(cachedFallbackSteps);
        setEdges(cachedFallbackEdges);
        setEventLogs(generateEventLogsFromSteps(cachedFallbackSteps));
        setVariantName('Most Frequent Variant (Cached)');
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

    const afterIndex = steps.findIndex(s => s.id === afterStepId);
    const nextStep = steps[afterIndex + 1];
    
    const newStepId = stepName.toLowerCase().replace(/\s+/g, '-');
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
        } else {
          setEventLogs(generateEventLogsFromSteps(newSteps));
        }
      } catch (error) {
        console.error('Error fetching event logs:', error);
        setEventLogs(generateEventLogsFromSteps(newSteps));
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

    // Clear new flag after animation
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
    const step = steps.find(s => s.id === stepId);
    const newSteps = steps.map(s => 
      s.id === stepId ? { ...s, ...updates } : s
    );
    setSteps(newSteps);
    
    // Track change if time was updated
    if (updates.avgTime && step) {
      setProcessChanges([`Reduced '${step.name}' time from ${step.avgTime} to ${updates.avgTime}`]);
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
        } else {
          setEventLogs(generateEventLogsFromSteps(newSteps));
        }
      } catch (error) {
        console.error('Error fetching event logs:', error);
        setEventLogs(generateEventLogsFromSteps(newSteps));
      }
    })();
  };

  const handleSimulate = async () => {
    try {
      setIsSimulating(true);
      
      // Build process graph from current steps
      const activities = steps
        .filter(s => s.id !== 'start' && s.id !== 'end')
        .map(s => s.name);
      
      const graphEdges = edges.map((e, idx) => ({
        id: e.id || `edge-${idx}`,
        from: steps.find(s => s.id === e.from)?.name || '',
        to: steps.find(s => s.id === e.to)?.name || '',
        cases: e.cases || 0,
        avgDays: e.avgDays || 0
      })).filter(e => e.from && e.to && e.from !== 'Start' && e.from !== 'End' && e.to !== 'Start' && e.to !== 'End');
      
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
      
      // Format event logs for backend
      const formattedEventLogs = eventLogs.map(log => ({
        'Case ID': log.caseId,
        'Activity': log.activity,
        'Timestamp': log.timestamp,
        'Throughput Time': parseFloat(log.throughputTime.replace(/[^0-9.]/g, '')) || 0,
        'Cost': parseFloat(log.cost.replace(/[^0-9.]/g, '')) || 0
      }));
      
      const result = await simulateProcess(formattedEventLogs, {
        activities,
        edges: graphEdges,
        kpis
      });
      
      console.log('Simulation results:', result);
      setSimulationResults(result);
      setIsSimulationOpen(true);
      setIsSimulating(false);
    } catch (error: any) {
      console.error('Simulation error:', error);
      setIsSimulating(false);
      setMessages(prev => [...prev, {
        type: 'ai',
        text: `⚠️ Simulation failed: ${error.message}`
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
      
      // Call backend API to parse the prompt WITH current process context
      console.log('Parsing prompt with backend API:', prompt);
      console.log('Current process activities:', currentProcess.activities);
      const response = await parsePrompt(prompt, currentProcess);
      console.log('Parsed response:', response);
      
      // Handle different action types
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
        
        handleAddStep(referenceStepId, newActivity);
        setVariantName(`Optimized: Added ${newActivity}`);
        setMessages(prev => [...prev, {
          type: 'ai',
          text: `✓ Added step: '${newActivity}' to the process. This may increase cycle time but could improve quality or compliance.`
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
      
      <ResizablePanelGroup direction="vertical" className="flex-1">
        {/* Main Workspace */}
        <ResizablePanel defaultSize={70} minSize={40}>
          <ResizablePanelGroup direction="horizontal">
            {/* Left Panel - Prompt Workspace */}
            <ResizablePanel defaultSize={35} minSize={25} maxSize={50}>
              <PromptPanel 
                messages={messages}
                onPromptSubmit={handlePromptSubmit}
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
