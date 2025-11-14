import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Play, Minimize2, Maximize2 } from 'lucide-react';
import { EventLog } from '../App';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { ScrollArea } from './ui/scroll-area';

interface EventLogPanelProps {
  eventLogs: EventLog[];
  onSimulate: () => void;
  isMinimized?: boolean;
  onToggleMinimize?: () => void;
}

export function EventLogPanel({ eventLogs, onSimulate, isMinimized = false, onToggleMinimize }: EventLogPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Sort event logs by timestamp in ascending order
  const sortedLogs = [...eventLogs].sort((a, b) => {
    return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
  });

  // If minimized, show compact horizontal bar
  if (isMinimized) {
    return (
      <div className="h-full bg-gray-50 border-t border-gray-200 flex items-center justify-center relative group">
        <div className="flex items-center gap-3">
          <span className="text-xs font-semibold text-gray-600">Event Log Panel</span>
          <span className="text-xs text-gray-500">({eventLogs.length} events)</span>
          <button
            onClick={onSimulate}
            className="px-3 py-1 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 transition-all flex items-center gap-1.5"
          >
            <Play className="w-3 h-3" />
            Simulate
          </button>
        </div>
        <button
          onClick={onToggleMinimize}
          className="absolute -top-3 left-1/2 -translate-x-1/2 bg-white border border-gray-300 rounded-full p-1.5 hover:bg-gray-50 shadow-md transition-all opacity-60 group-hover:opacity-100"
          title="Expand Event Log Panel"
        >
          <ChevronUp className="w-3.5 h-3.5 text-gray-600" />
        </button>
      </div>
    );
  }

  return (
    <div className="h-full bg-white border-t border-gray-200 flex flex-col relative overflow-hidden">
      {/* Minimize button */}
      <button
        onClick={onToggleMinimize}
        className="absolute -top-3 left-1/2 -translate-x-1/2 z-10 bg-white border border-gray-300 rounded-full p-1.5 hover:bg-gray-50 shadow-md transition-all"
        title="Minimize Event Log Panel"
      >
        <ChevronDown className="w-3.5 h-3.5 text-gray-600" />
      </button>

      {/* Header */}
      <div className="p-2.5 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            title={isCollapsed ? "Expand table" : "Collapse table"}
          >
            {isCollapsed ? (
              <ChevronUp className="w-3.5 h-3.5 text-gray-600" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-gray-600" />
            )}
          </button>
          <h2 className="text-sm font-semibold text-gray-900">Event Log Preview</h2>
          <span className="text-xs text-gray-500">({eventLogs.length} events)</span>
        </div>
      </div>

      {/* Event Log Table - Scrollable */}
      {!isCollapsed && (
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto overflow-x-auto p-2.5">
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <Table>
                <TableHeader className="sticky top-0 bg-gray-50 z-10">
                  <TableRow>
                    <TableHead className="text-xs py-2">Case ID</TableHead>
                    <TableHead className="text-xs py-2">Activity</TableHead>
                    <TableHead className="text-xs py-2">Timestamp</TableHead>
                    <TableHead className="text-xs py-2">Throughput Time</TableHead>
                    <TableHead className="text-xs py-2">Cost</TableHead>
                    <TableHead className="text-xs py-2">Resource</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedLogs.map((log, index) => (
                    <TableRow key={index} className="hover:bg-gray-50">
                      <TableCell className="text-xs py-1.5">{log.caseId}</TableCell>
                      <TableCell className="text-xs py-1.5">{log.activity}</TableCell>
                      <TableCell className="text-xs text-gray-600 py-1.5">{log.timestamp}</TableCell>
                      <TableCell className="text-xs text-gray-600 py-1.5">{log.throughputTime}</TableCell>
                      <TableCell className="text-xs text-gray-600 py-1.5">{log.cost}</TableCell>
                      <TableCell className="text-xs text-gray-600 py-1.5">{log.resource}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
          
          {/* Simulate Button at Bottom - Fixed */}
          <div className="border-t border-gray-200 p-2.5 flex justify-center flex-shrink-0">
            <button
              onClick={onSimulate}
              className="px-4 py-1.5 bg-green-600 text-white text-xs rounded-lg hover:bg-green-700 transition-all duration-200 flex items-center gap-1.5 shadow-md hover:shadow-lg hover:scale-105"
            >
              <Play className="w-3.5 h-3.5" />
              Simulate
            </button>
          </div>
        </div>
      )}

      {isCollapsed && (
        <div className="p-3 text-center text-gray-500 text-xs">
          Click to expand event log preview
        </div>
      )}
    </div>
  );
}
