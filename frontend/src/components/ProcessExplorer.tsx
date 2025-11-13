import React, { useState, useRef, useEffect } from 'react';
import { ZoomIn, ZoomOut, Maximize2, Plus, Info, Trash2, GripVertical } from 'lucide-react';
import { DndProvider, useDrag, useDrop } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { ProcessStep, ProcessEdge } from '../App';
import { Badge } from './ui/badge';
import { EventInfoDialog } from './EventInfoDialog';
import { EventPalette } from './EventPalette';

interface ProcessExplorerProps {
  steps: ProcessStep[];
  edges: ProcessEdge[];
  onAddStep: (afterStepId: string, stepName?: string, stepData?: { avgTime: string; avgCost: string }) => void;
  onRemoveStep: (stepId: string) => void;
  onReorderSteps: (steps: ProcessStep[]) => void;
  onUpdateStep: (stepId: string, updates: Partial<ProcessStep>) => void;
}

const ItemType = {
  PROCESS_STEP: 'processStep',
  PALETTE_EVENT: 'paletteEvent'
};

interface DragItem {
  type: string;
  id?: string;
  index?: number;
  step?: ProcessStep;
  event?: { name: string; avgTime: string; avgCost: string };
}

interface DropZoneProps {
  beforeStepId: string;
  onDropPaletteEvent: (beforeStepId: string, event: { name: string; avgTime: string; avgCost: string }) => void;
}

function DropZone({ beforeStepId, onDropPaletteEvent }: DropZoneProps) {
  const [{ isOver, canDrop }, drop] = useDrop({
    accept: ItemType.PALETTE_EVENT,
    canDrop: (item) => {
      console.log('DropZone canDrop check:', { beforeStepId, item });
      return true;
    },
    drop: (item: DragItem) => {
      console.log('DropZone drop event:', { beforeStepId, item });
      if (item.event) {
        console.log('Calling onDropPaletteEvent with:', beforeStepId, item.event);
        onDropPaletteEvent(beforeStepId, item.event);
      } else {
        console.error('No event in dropped item:', item);
      }
    },
    collect: (monitor) => {
      const item = monitor.getItem();
      console.log('DropZone collect:', { beforeStepId, isOver: monitor.isOver(), canDrop: monitor.canDrop(), item });
      return {
        isOver: monitor.isOver(),
        canDrop: monitor.canDrop(),
      };
    },
  });

  const isActive = isOver && canDrop;

  return (
    <div
      ref={drop}
      className={`transition-all duration-200 ${
        isActive 
          ? 'h-12 bg-green-100 border-2 border-dashed border-green-500 rounded-lg flex items-center justify-center' 
          : canDrop
          ? 'h-8 bg-blue-50 border-2 border-dashed border-blue-300 rounded-lg'
          : 'h-2'
      }`}
    >
      {isActive && (
        <span className="text-xs text-green-700 font-medium">Drop here to add event</span>
      )}
    </div>
  );
}

function DraggableProcessNode({ 
  step, 
  index, 
  isStart, 
  isEnd, 
  edgeInfo,
  nextStep,
  onMove,
  onInfo,
  onRemove,
  onAddAfter,
  onDropPaletteEvent,
  onUpdate
}: {
  step: ProcessStep;
  index: number;
  isStart: boolean;
  isEnd: boolean;
  edgeInfo: ProcessEdge | undefined;
  nextStep: ProcessStep | undefined;
  onMove: (dragIndex: number, hoverIndex: number) => void;
  onInfo: (step: ProcessStep) => void;
  onRemove: (stepId: string) => void;
  onAddAfter: (stepId: string, stepName?: string, stepData?: { avgTime: string; avgCost: string }) => void;
  onDropPaletteEvent: (beforeStepId: string, event: { name: string; avgTime: string; avgCost: string }) => void;
  onUpdate: (stepId: string, updates: Partial<ProcessStep>) => void;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [editingField, setEditingField] = useState<'time' | 'cost' | null>(null);
  const [tempTime, setTempTime] = useState(step.avgTime);
  const [tempCost, setTempCost] = useState(step.avgCost);

  // Sync temp values when step changes
  useEffect(() => {
    setTempTime(step.avgTime);
    setTempCost(step.avgCost);
  }, [step.avgTime, step.avgCost]);

  const [{ isDragging }, drag, preview] = useDrag({
    type: ItemType.PROCESS_STEP,
    item: { type: ItemType.PROCESS_STEP, id: step.id, index, step },
    canDrag: !isStart && !isEnd,
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  const [{ isOver }, drop] = useDrop({
    accept: [ItemType.PROCESS_STEP, ItemType.PALETTE_EVENT],
    hover(item: DragItem, monitor) {
      if (!ref.current) return;
      
      if (item.type === ItemType.PROCESS_STEP && item.index !== undefined) {
        const dragIndex = item.index;
        const hoverIndex = index;

        if (dragIndex === hoverIndex) return;
        if (isStart || isEnd) return;
        if (dragIndex === 0 || hoverIndex === 0) return; // Can't move start
        
        onMove(dragIndex, hoverIndex);
        item.index = hoverIndex;
      }
    },
    collect: (monitor) => ({
      isOver: monitor.isOver(),
    }),
  });

  // Combine drag and drop refs
  if (!isStart && !isEnd) {
    drag(drop(ref));
  } else {
    drop(ref);
  }

  return (
    <>
      {/* Drop zone before this step */}
      {!isStart && (
        <DropZone 
          beforeStepId={step.id} 
          onDropPaletteEvent={onDropPaletteEvent} 
        />
      )}

      <div
        ref={ref}
        className={`
          relative bg-white border-2 rounded-lg px-3 py-1 shadow-sm hover:shadow-md transition-all duration-300 min-w-[160px] max-w-[160px]
          ${step.isNew ? 'border-blue-500 shadow-blue-200 animate-pulse' : 'border-gray-300'}
          ${isStart || isEnd ? 'bg-gray-50' : 'hover:border-blue-400'}
          ${isDragging ? 'opacity-50' : 'opacity-100'}
          ${isOver && !isStart && !isEnd ? 'border-green-500 bg-green-50' : ''}
          ${!isStart && !isEnd ? 'cursor-move' : ''}
        `}
        style={{
          animation: step.isNew ? 'glow 2s ease-in-out' : 'none',
          fontSize: '11px'
        }}
      >
        {/* Drag Handle */}
        {!isStart && !isEnd && (
          <div className="absolute left-1 top-1/2 -translate-y-1/2 text-gray-400 cursor-move">
            <GripVertical className="w-3 h-3" />
          </div>
        )}

        {/* Title row with action buttons */}
        <div className="flex items-center justify-between gap-1 mb-1">
          {/* Info button (left) */}
          {!isStart && !isEnd && (
            <button
              onClick={() => onInfo(step)}
              className="p-0.5 hover:bg-blue-100 rounded transition-colors flex-shrink-0"
              title="Info"
            >
              <Info className="w-3 h-3 text-blue-600" />
            </button>
          )}
          
          {/* Title (center) */}
          <h3 className="text-gray-900 flex-1 text-center" style={{ fontSize: '11px' }}>
            {step.name}
          </h3>
          
          {/* New badge or Delete button (right) */}
          {step.isNew ? (
            <Badge className="bg-blue-100 text-blue-700 flex-shrink-0" style={{ fontSize: '9px', padding: '1px 4px' }}>New</Badge>
          ) : !isStart && !isEnd ? (
            <button
              onClick={() => onRemove(step.id)}
              className="p-0.5 hover:bg-gray-100 rounded transition-colors flex-shrink-0"
              title="Remove"
            >
              <Trash2 className="w-3 h-3 text-gray-900" />
            </button>
          ) : (
            <div className="w-4"></div>
          )}
        </div>
        
        {/* Badges row - Editable */}
        {!isStart && !isEnd && (
          <div className="flex gap-1 justify-center">
            {/* Time Badge */}
            {editingField === 'time' ? (
              <input
                type="text"
                value={tempTime}
                onChange={(e) => setTempTime(e.target.value)}
                onBlur={() => {
                  onUpdate(step.id, { avgTime: tempTime });
                  setEditingField(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    onUpdate(step.id, { avgTime: tempTime });
                    setEditingField(null);
                  } else if (e.key === 'Escape') {
                    setTempTime(step.avgTime);
                    setEditingField(null);
                  }
                }}
                autoFocus
                className="w-12 px-1 text-center border border-blue-400 rounded"
                style={{ fontSize: '9px' }}
              />
            ) : (
              <Badge 
                variant="outline" 
                className="px-1 py-0 cursor-pointer hover:bg-blue-50 transition-colors" 
                style={{ fontSize: '9px' }}
                onClick={(e) => {
                  e.stopPropagation();
                  setTempTime(step.avgTime);
                  setEditingField('time');
                }}
                title="Click to edit"
              >
                ⏱ {step.avgTime}
              </Badge>
            )}
            
            {/* Cost Badge */}
            {editingField === 'cost' ? (
              <input
                type="text"
                value={tempCost}
                onChange={(e) => setTempCost(e.target.value)}
                onBlur={() => {
                  onUpdate(step.id, { avgCost: tempCost });
                  setEditingField(null);
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    onUpdate(step.id, { avgCost: tempCost });
                    setEditingField(null);
                  } else if (e.key === 'Escape') {
                    setTempCost(step.avgCost);
                    setEditingField(null);
                  }
                }}
                autoFocus
                className="w-12 px-1 text-center border border-blue-400 rounded"
                style={{ fontSize: '9px' }}
              />
            ) : (
              <Badge 
                variant="outline" 
                className="px-1 py-0 cursor-pointer hover:bg-blue-50 transition-colors" 
                style={{ fontSize: '9px' }}
                onClick={(e) => {
                  e.stopPropagation();
                  setTempCost(step.avgCost);
                  setEditingField('cost');
                }}
                title="Click to edit"
              >
                {step.avgCost}
              </Badge>
            )}
          </div>
        )}
      </div>

      {/* Edge with Add Button */}
      {nextStep && (
        <div className="flex flex-col items-center gap-0.5">
          {/* Arrow Line */}
          <div className="w-0.5 h-2 bg-gray-300 relative">
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-0 border-l-2 border-r-2 border-t-4 border-l-transparent border-r-transparent border-t-gray-300"></div>
          </div>

          {/* Edge Label */}
          {edgeInfo && (
            <div className="bg-blue-50 border border-blue-200 rounded px-1.5 py-0.5" style={{ fontSize: '9px' }}>
              {edgeInfo.cases} cases | {edgeInfo.avgDays}d
            </div>
          )}

          {/* Add Step Button */}
          {!isEnd && (
            <button
              onClick={() => onAddAfter(step.id)}
              className="group relative p-1 bg-white border-2 border-dashed border-gray-300 hover:border-blue-500 hover:bg-blue-50 rounded-full transition-all duration-200 hover:scale-110"
              title="Add step here"
            >
              <Plus className="w-2.5 h-2.5 text-gray-400 group-hover:text-blue-600" />
              <div className="absolute -bottom-5 left-1/2 -translate-x-1/2 bg-gray-900 text-white px-1.5 py-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none" style={{ fontSize: '9px' }}>
                Add step
              </div>
            </button>
          )}

          {/* Arrow Line continuation */}
          <div className="w-0.5 h-2 bg-gray-300"></div>
        </div>
      )}
    </>
  );
}

export function ProcessExplorer({ steps, edges, onAddStep, onRemoveStep, onReorderSteps, onUpdateStep }: ProcessExplorerProps) {
  const [zoom, setZoom] = useState(1); // Default zoom at 100%
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [infoStep, setInfoStep] = useState<ProcessStep | null>(null);
  const [showHelpDialog, setShowHelpDialog] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const contentRef = useRef<HTMLDivElement>(null);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.2, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.2, 0.3));
  const handleResetZoom = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };
  
  // Fullscreen functionality
  const [isFullscreen, setIsFullscreen] = useState(false);
  
  const handleFullscreen = () => {
    if (!containerRef.current) return;
    
    if (!document.fullscreenElement) {
      containerRef.current.requestFullscreen()
        .then(() => setIsFullscreen(true))
        .catch((err) => {
          console.error('Fullscreen request failed:', err);
        });
    } else {
      document.exitFullscreen()
        .then(() => setIsFullscreen(false))
        .catch((err) => {
          console.error('Exit fullscreen failed:', err);
        });
    }
  };
  
  // Listen for fullscreen changes
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement);
    };
    
    document.addEventListener('fullscreenchange', handleFullscreenChange);
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange);
  }, []);

  const getEdgeInfo = (fromId: string, toId: string) => {
    return edges.find(e => e.from === fromId && e.to === toId);
  };

  // Mouse wheel zoom
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        e.preventDefault();
        const delta = -e.deltaY * 0.001;
        setZoom(prev => Math.min(Math.max(prev + delta, 0.3), 3));
      }
    };

    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, []);

  // Pan handlers
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0 && (e.target as HTMLElement).closest('.process-canvas')) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  const handleMouseLeave = () => {
    setIsDragging(false);
  };

  const moveStep = (dragIndex: number, hoverIndex: number) => {
    const draggedStep = steps[dragIndex];
    const newSteps = [...steps];
    newSteps.splice(dragIndex, 1);
    newSteps.splice(hoverIndex, 0, draggedStep);
    onReorderSteps(newSteps);
  };

  const handleDropPaletteEvent = (beforeStepId: string, event: { name: string; avgTime: string; avgCost: string }) => {
    console.log('handleDropPaletteEvent called:', { beforeStepId, event });
    
    // Find the index of the step we want to insert before
    const beforeIndex = steps.findIndex(s => s.id === beforeStepId);
    console.log('beforeIndex:', beforeIndex);
    
    if (beforeIndex === -1) {
      console.error('Step not found:', beforeStepId);
      return;
    }
    
    // Get the previous step (the one before where we want to insert)
    // We insert AFTER the previous step to achieve inserting BEFORE the target step
    const prevStepId = beforeIndex > 0 ? steps[beforeIndex - 1].id : 'start';
    console.log('Inserting after step:', prevStepId);
    
    // Call onAddStep with the previous step's ID and the event data
    onAddStep(prevStepId, event.name, { avgTime: event.avgTime, avgCost: event.avgCost });
  };

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="h-full bg-white flex flex-row">
        {/* Main Process Area */}
        <div className="flex-1 flex flex-col">
          {/* Header */}
          <div className="p-4 border-b border-gray-200 flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div>
                <h2 className="text-gray-900">Order to Cash Flow</h2>
                <p className="text-sm text-gray-500 mt-1">Process Explorer View</p>
              </div>
              <button
                onClick={() => setShowHelpDialog(true)}
                className="p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
                title="How to use Process Explorer"
              >
                <Info className="w-4 h-4 text-gray-500" />
              </button>
            </div>
            <div className="flex items-center gap-2">
              <div className="flex items-center gap-1 bg-gray-100 rounded-lg p-1">
                <button
                  onClick={handleZoomOut}
                  className="p-1.5 hover:bg-white rounded transition-colors"
                  title="Zoom Out"
                >
                  <ZoomOut className="w-4 h-4 text-gray-600" />
                </button>
                <button
                  onClick={handleResetZoom}
                  className="px-2 py-1.5 hover:bg-white rounded transition-colors text-xs text-gray-600"
                  title="Reset Zoom"
                >
                  {Math.round(zoom * 100)}%
                </button>
                <button
                  onClick={handleZoomIn}
                  className="p-1.5 hover:bg-white rounded transition-colors"
                  title="Zoom In"
                >
                  <ZoomIn className="w-4 h-4 text-gray-600" />
                </button>
                <button
                  onClick={handleFullscreen}
                  className="p-1.5 hover:bg-white rounded transition-colors ml-1"
                  title={isFullscreen ? "Exit Fullscreen (Esc)" : "Enter Fullscreen"}
                >
                  <Maximize2 className={`w-4 h-4 ${isFullscreen ? 'text-blue-600' : 'text-gray-600'}`} />
                </button>
              </div>
            </div>
          </div>

          {/* Process Graph */}
          <div 
            ref={containerRef}
            className={`flex-1 overflow-auto relative bg-gray-50 process-canvas ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseLeave}
          >
            {/* 🎯 Empty State - Show when no process is selected */}
            {steps.filter(s => s.id !== 'start' && s.id !== 'end').length === 0 && (
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center max-w-md px-8">
                  <div className="mb-6">
                    <div className="w-24 h-24 mx-auto mb-4 rounded-full bg-gradient-to-br from-blue-100 to-blue-200 flex items-center justify-center">
                      <svg className="w-12 h-12 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                    </div>
                    <h3 className="text-2xl font-semibold text-gray-900 mb-2">No Process Selected Yet</h3>
                    <p className="text-gray-600 mb-4">
                      Describe the process scenario you want to explore using the prompt panel on the left.
                    </p>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-left">
                    <p className="text-sm font-medium text-blue-900 mb-2">✨ Try saying:</p>
                    <ul className="text-sm text-blue-800 space-y-1">
                      <li>• "I want to see a standard order fulfillment process"</li>
                      <li>• "Show me what happens when an order gets rejected"</li>
                      <li>• "I need a process where customers get discounts"</li>
                    </ul>
                  </div>
                </div>
              </div>
            )}
            
            {/* Process Flow - Show when process is loaded */}
            {steps.filter(s => s.id !== 'start' && s.id !== 'end').length > 0 && (
              <div className="absolute inset-0 flex items-start justify-center min-w-full min-h-full py-4 px-2">
                <div 
                  ref={contentRef}
                  className="flex flex-col items-center gap-1 transition-transform duration-150"
                  style={{ 
                    transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
                    transformOrigin: 'top center'
                  }}
                >
                  {steps.map((step, index) => {
                  const nextStep = steps[index + 1];
                  const edgeInfo = nextStep ? getEdgeInfo(step.id, nextStep.id) : null;
                  const isStart = step.id === 'start';
                  const isEnd = step.id === 'end';

                  return (
                    <DraggableProcessNode
                      key={step.id}
                      step={step}
                      index={index}
                      isStart={isStart}
                      isEnd={isEnd}
                      edgeInfo={edgeInfo}
                      nextStep={nextStep}
                      onMove={moveStep}
                      onInfo={setInfoStep}
                      onRemove={onRemoveStep}
                      onAddAfter={onAddStep}
                      onDropPaletteEvent={handleDropPaletteEvent}
                      onUpdate={onUpdateStep}
                    />
                  );
                })}
                </div>
              </div>
            )}

          </div>

          <style>{`
            @keyframes glow {
              0%, 100% {
                box-shadow: 0 0 5px rgba(59, 130, 246, 0.5);
              }
              50% {
                box-shadow: 0 0 20px rgba(59, 130, 246, 0.8);
              }
            }
          `}</style>
        </div>

        {/* Event Palette Sidebar */}
        <EventPalette />

        {/* Event Info Dialog */}
        {infoStep && (
          <EventInfoDialog
            step={infoStep}
            isOpen={!!infoStep}
            onClose={() => setInfoStep(null)}
            onRemove={() => {
              onRemoveStep(infoStep.id);
              setInfoStep(null);
            }}
            onUpdate={(stepId, updates) => {
              onUpdateStep(stepId, updates);
              setInfoStep(null);
            }}
          />
        )}

        {/* Help Dialog */}
        {showHelpDialog && (
          <div 
            className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 animate-in fade-in duration-200"
            onClick={() => setShowHelpDialog(false)}
          >
            <div 
              className="bg-white rounded-xl shadow-2xl max-w-lg w-full mx-4 animate-in zoom-in-95 duration-200"
              onClick={e => e.stopPropagation()}
            >
              {/* Header */}
              <div className="p-6 border-b border-gray-200">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Info className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-gray-900">How to Use Process Explorer</h3>
                    <p className="text-sm text-gray-500 mt-1">Modify and simulate your process</p>
                  </div>
                </div>
              </div>

              {/* Content */}
              <div className="p-6 space-y-4">
                <div className="space-y-3">
                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center">
                      <Plus className="w-4 h-4 text-blue-600" />
                    </div>
                    <div>
                      <h4 className="text-gray-900 mb-1">Add Process Steps</h4>
                      <p className="text-sm text-gray-600">
                        Click the <span className="text-blue-600">+</span> button between process steps to insert new activities into your workflow.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-purple-50 rounded-lg flex items-center justify-center">
                      <GripVertical className="w-4 h-4 text-purple-600" />
                    </div>
                    <div>
                      <h4 className="text-gray-900 mb-1">Drag from Event Palette</h4>
                      <p className="text-sm text-gray-600">
                        Drag events from the right sidebar directly into your process flow to quickly add new steps.
                      </p>
                    </div>
                  </div>

                  <div className="flex gap-3">
                    <div className="flex-shrink-0 w-8 h-8 bg-green-50 rounded-lg flex items-center justify-center">
                      <span className="text-green-600">⏱</span>
                    </div>
                    <div>
                      <h4 className="text-gray-900 mb-1">Edit Duration & Cost</h4>
                      <p className="text-sm text-gray-600">
                        Click on the time (⏱) or cost ($) badges on any process step to edit values and simulate <span className="text-green-600 font-medium">KPIs for unseen cases</span>.
                      </p>
                    </div>
                  </div>
                </div>

                <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-4">
                  <p className="text-sm text-amber-900">
                    <span className="font-medium">💡 Tip:</span> After making changes, click the <span className="font-medium">"Simulate"</span> button in the Event Log panel to see how your modifications impact KPIs like On Time Delivery, Order Accuracy, DSO, and Cost of Delivery.
                  </p>
                </div>
              </div>

              {/* Footer */}
              <div className="p-6 border-t border-gray-200 flex justify-end">
                <button
                  onClick={() => setShowHelpDialog(false)}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Got it!
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </DndProvider>
  );
}
