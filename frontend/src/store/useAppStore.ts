import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { AppState, ProcessGraph, EventLogEntry, SimulationResult, EventLogResponse, DEFAULT_O2C_PROCESS } from '../types';

export const useAppStore = create<AppState>()(
  devtools(
    (set, get) => ({
      // Initial State
      processGraph: DEFAULT_O2C_PROCESS,
      eventLog: [],
      eventLogMetadata: null,
      simulationResult: null,
      isSimulating: false,
      selectedActivity: null,
      isPromptProcessing: false,
      showSimulationModal: false,

      // Basic Setters
      updateProcessGraph: (graph: ProcessGraph) => 
        set({ processGraph: graph }, false, 'updateProcessGraph'),

      setEventLog: (log: EventLogEntry[], metadata?: EventLogResponse['metadata']) =>
        set({ eventLog: log, eventLogMetadata: metadata || null }, false, 'setEventLog'),

      setSimulationResult: (result: SimulationResult | null) =>
        set({ simulationResult: result }, false, 'setSimulationResult'),

      setIsSimulating: (isSimulating: boolean) =>
        set({ isSimulating }, false, 'setIsSimulating'),

      setSelectedActivity: (activity: string | null) =>
        set({ selectedActivity: activity }, false, 'setSelectedActivity'),

      setIsPromptProcessing: (isProcessing: boolean) =>
        set({ isPromptProcessing: isProcessing }, false, 'setIsPromptProcessing'),

      setShowSimulationModal: (show: boolean) =>
        set({ showSimulationModal: show }, false, 'setShowSimulationModal'),

      // Complex Actions
      addActivity: (activity: string, position: string = 'after', insertAfter?: string) => {
        const currentGraph = get().processGraph;
        const activities = [...currentGraph.activities];
        const edges = [...currentGraph.edges];
        const kpis = { ...currentGraph.kpis };

        // Add default KPIs for new activity
        kpis[activity] = { avg_time: 1.0, cost: 5.0 };

        if (insertAfter && activities.includes(insertAfter)) {
          // Insert after specified activity
          const insertIndex = activities.indexOf(insertAfter);
          
          if (position === 'after') {
            activities.splice(insertIndex + 1, 0, activity);
            
            // Update edges
            const edgeToUpdate = edges.find(e => e.from === insertAfter);
            if (edgeToUpdate) {
              const originalTo = edgeToUpdate.to;
              edgeToUpdate.to = activity;
              
              // Add new edge from new activity to original target
              edges.push({
                id: `e${edges.length + 1}`,
                from: activity,
                to: originalTo
              });
            }
          } else {
            // Insert before
            activities.splice(insertIndex, 0, activity);
            
            // Update edges
            const edgeToUpdate = edges.find(e => e.to === insertAfter);
            if (edgeToUpdate) {
              edgeToUpdate.to = activity;
              
              // Add new edge from new activity to original target
              edges.push({
                id: `e${edges.length + 1}`,
                from: activity,
                to: insertAfter
              });
            }
          }
        } else {
          // Default: add at the end
          activities.push(activity);
          
          // Connect to the previous last activity
          if (activities.length > 1) {
            const previousActivity = activities[activities.length - 2];
            edges.push({
              id: `e${edges.length + 1}`,
              from: previousActivity,
              to: activity
            });
          }
        }

        set({
          processGraph: {
            activities,
            edges,
            kpis
          }
        }, false, 'addActivity');
      },

      removeActivity: (activity: string) => {
        const currentGraph = get().processGraph;
        const activities = currentGraph.activities.filter(a => a !== activity);
        const edges = currentGraph.edges.filter(e => e.from !== activity && e.to !== activity);
        const kpis = { ...currentGraph.kpis };
        delete kpis[activity];

        // Reconnect edges if needed
        const incomingEdge = currentGraph.edges.find(e => e.to === activity);
        const outgoingEdge = currentGraph.edges.find(e => e.from === activity);
        
        if (incomingEdge && outgoingEdge) {
          // Connect the incoming and outgoing activities directly
          edges.push({
            id: `e${edges.length + 1}`,
            from: incomingEdge.from,
            to: outgoingEdge.to
          });
        }

        set({
          processGraph: {
            activities,
            edges,
            kpis
          }
        }, false, 'removeActivity');
      },

      updateActivityKPIs: (activity: string, newKpis: Partial<{ avg_time: number; cost: number }>) => {
        const currentGraph = get().processGraph;
        const kpis = { ...currentGraph.kpis };
        
        if (kpis[activity]) {
          kpis[activity] = { ...kpis[activity], ...newKpis };
        }

        set({
          processGraph: {
            ...currentGraph,
            kpis
          }
        }, false, 'updateActivityKPIs');
      },

      resetToDefault: () => {
        set({
          processGraph: DEFAULT_O2C_PROCESS,
          eventLog: [],
          eventLogMetadata: null,
          simulationResult: null,
          isSimulating: false,
          selectedActivity: null,
          isPromptProcessing: false,
          showSimulationModal: false,
        }, false, 'resetToDefault');
      },
    }),
    {
      name: 'process-simulation-store',
    }
  )
);
