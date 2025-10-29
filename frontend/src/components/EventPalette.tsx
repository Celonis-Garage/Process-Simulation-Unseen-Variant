import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Layers, Loader2, AlertCircle } from 'lucide-react';
import { ScrollArea } from './ui/scroll-area';
import { useDrag } from 'react-dnd';
import { getDataSummary } from '../services/api';

interface EventPaletteProps {
  // No props needed - drag and drop only
}

export interface PaletteEvent {
  id: string;
  name: string;
  avgTime: string;
  avgCost: string;
  category: string;
  icon: string;
}

// Helper function to categorize events based on name
const categorizeEvent = (eventName: string): { category: string; icon: string } => {
  const lowerName = eventName.toLowerCase();
  
  if (lowerName.includes('order') || lowerName.includes('receive')) {
    return { category: 'Order', icon: '📥' };
  } else if (lowerName.includes('credit') || lowerName.includes('payment') || lowerName.includes('invoice')) {
    return { category: 'Financial', icon: '💳' };
  } else if (lowerName.includes('approve') || lowerName.includes('validate')) {
    return { category: 'Approval', icon: '✓' };
  } else if (lowerName.includes('ship') || lowerName.includes('pack') || lowerName.includes('pick')) {
    return { category: 'Logistics', icon: '📦' };
  } else if (lowerName.includes('schedule') || lowerName.includes('fulfill')) {
    return { category: 'Planning', icon: '📅' };
  } else if (lowerName.includes('generate') || lowerName.includes('label')) {
    return { category: 'Documentation', icon: '📄' };
  } else {
    return { category: 'General', icon: '⚙️' };
  }
};

// Helper function to format time
const formatTime = (hours: number): string => {
  if (hours < 1) {
    return `${Math.round(hours * 60)}m`;
  } else if (hours < 24) {
    return `${Math.round(hours * 10) / 10}h`;
  } else {
    return `${Math.round((hours / 24) * 10) / 10}d`;
  }
};

export const ItemType = {
  PALETTE_EVENT: 'paletteEvent'
};

interface DraggablePaletteEventProps {
  event: PaletteEvent;
}

function DraggablePaletteEvent({ event }: DraggablePaletteEventProps) {
  const [{ isDragging }, drag] = useDrag({
    type: ItemType.PALETTE_EVENT,
    item: () => {
      console.log('Creating drag item for:', event.name);
      return { 
        type: ItemType.PALETTE_EVENT,
        event: event
      };
    },
    end: (item, monitor) => {
      console.log('Drag ended:', { didDrop: monitor.didDrop(), item });
    },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  });

  console.log('DraggablePaletteEvent render:', { eventName: event.name, isDragging });

  return (
    <div
      ref={drag}
      className={`w-full bg-white border-2 border-gray-200 hover:border-blue-400 hover:bg-blue-50 rounded-lg p-3 transition-all duration-200 ${
        isDragging ? 'opacity-50 cursor-grabbing' : 'cursor-grab'
      }`}
    >
      <div className="flex flex-col gap-1">
        <h4 className="text-sm text-gray-900">
          {event.name}
        </h4>
        <p className="text-xs text-gray-500">
          {event.category}
        </p>
        <div className="flex gap-2 mt-1">
          <span className="text-xs text-gray-600">⏱ {event.avgTime}</span>
          <span className="text-xs text-gray-600">{event.avgCost}</span>
        </div>
      </div>
    </div>
  );
}

export function EventPalette() {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [paletteEvents, setPaletteEvents] = useState<PaletteEvent[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchEventData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        console.log('Fetching event data from backend...');
        
        const summary = await getDataSummary();
        console.log('Received data summary:', summary);
        
        // Transform backend event types to PaletteEvent format
        const events: PaletteEvent[] = summary.event_types.map((event, index) => {
          const { category, icon } = categorizeEvent(event.name);
          return {
            id: `event-${index}`,
            name: event.name,
            avgTime: formatTime(event.avg_time),
            avgCost: `$${event.cost.toFixed(2)}`,
            category,
            icon
          };
        });
        
        console.log('Transformed events:', events);
        setPaletteEvents(events);
        setIsLoading(false);
      } catch (err: any) {
        console.error('Error fetching event data:', err);
        setError(err.message || 'Failed to load events from backend');
        setIsLoading(false);
      }
    };

    fetchEventData();
  }, []);

  return (
    <div 
      className={`h-full bg-white border-l border-gray-200 transition-all duration-300 ${
        isCollapsed ? 'w-12' : 'w-72'
      } flex flex-col`}
    >
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        {!isCollapsed && (
          <div className="flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-600" />
            <h3 className="text-gray-900">Event Palette</h3>
            {paletteEvents.length > 0 && (
              <span className="text-xs text-gray-500">({paletteEvents.length})</span>
            )}
          </div>
        )}
        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1.5 hover:bg-gray-100 rounded transition-colors"
          title={isCollapsed ? 'Expand' : 'Collapse'}
        >
          {isCollapsed ? (
            <ChevronLeft className="w-4 h-4 text-gray-600" />
          ) : (
            <ChevronRight className="w-4 h-4 text-gray-600" />
          )}
        </button>
      </div>

      {/* Content */}
      {!isCollapsed && (
        <>
          {/* Loading state */}
          {isLoading && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <Loader2 className="w-8 h-8 text-blue-600 animate-spin mx-auto mb-2" />
                <p className="text-sm text-gray-600">Loading events...</p>
              </div>
            </div>
          )}

          {/* Error state */}
          {error && !isLoading && (
            <div className="flex-1 flex items-center justify-center p-4">
              <div className="text-center">
                <AlertCircle className="w-8 h-8 text-red-500 mx-auto mb-2" />
                <p className="text-sm text-red-600 mb-2">{error}</p>
                <p className="text-xs text-gray-500">Make sure the backend is running on port 8000</p>
              </div>
            </div>
          )}

          {/* Success state with events */}
          {!isLoading && !error && paletteEvents.length > 0 && (
            <>
              <div className="p-4 bg-blue-50 border-b border-blue-200">
                <p className="text-xs text-blue-700">
                  Drag events and drop them anywhere in your process flow
                </p>
              </div>

              <div className="flex-1 overflow-hidden">
                <ScrollArea className="h-full">
                  <div className="p-4 space-y-2">
                    {paletteEvents.map((event) => (
                      <DraggablePaletteEvent
                        key={event.id}
                        event={event}
                      />
                    ))}
                  </div>
                </ScrollArea>
              </div>

              {/* Footer hint */}
              <div className="p-3 border-t border-gray-200 bg-gray-50">
                <p className="text-xs text-gray-600 text-center">
                  💡 Tip: Drag & drop for precise positioning
                </p>
              </div>
            </>
          )}
        </>
      )}

      {/* Collapsed state */}
      {isCollapsed && (
        <div className="flex-1 flex flex-col items-center justify-center gap-4 py-4">
          <Layers className="w-5 h-5 text-gray-400" />
          <div className="text-xs text-gray-500" style={{ writingMode: 'vertical-rl' }}>
            Events
          </div>
        </div>
      )}
    </div>
  );
}
