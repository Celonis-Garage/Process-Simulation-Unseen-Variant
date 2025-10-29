import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Play } from 'lucide-react';
import { EventLog } from '../App';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './ui/table';
import { ScrollArea } from './ui/scroll-area';

interface EventLogPanelProps {
  eventLogs: EventLog[];
  onSimulate: () => void;
}

export function EventLogPanel({ eventLogs, onSimulate }: EventLogPanelProps) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  // Sort event logs by timestamp in ascending order
  const sortedLogs = [...eventLogs].sort((a, b) => {
    return new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime();
  });

  return (
    <div className="h-full bg-white border-t border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsCollapsed(!isCollapsed)}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            {isCollapsed ? (
              <ChevronUp className="w-4 h-4 text-gray-600" />
            ) : (
              <ChevronDown className="w-4 h-4 text-gray-600" />
            )}
          </button>
          <h2 className="text-gray-900">Event Log Preview</h2>
          <span className="text-sm text-gray-500">({eventLogs.length} events)</span>
        </div>
      </div>

      {/* Event Log Table */}
      {!isCollapsed && (
        <div className="flex-1 flex flex-col overflow-hidden">
          <div className="flex-1 overflow-auto p-4">
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <Table>
                <TableHeader className="sticky top-0 bg-gray-50 z-10">
                  <TableRow>
                    <TableHead>Case ID</TableHead>
                    <TableHead>Activity</TableHead>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Throughput Time</TableHead>
                    <TableHead>Cost</TableHead>
                    <TableHead>Resource</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {sortedLogs.map((log, index) => (
                    <TableRow key={index} className="hover:bg-gray-50">
                      <TableCell>{log.caseId}</TableCell>
                      <TableCell>{log.activity}</TableCell>
                      <TableCell className="text-gray-600">{log.timestamp}</TableCell>
                      <TableCell className="text-gray-600">{log.throughputTime}</TableCell>
                      <TableCell className="text-gray-600">{log.cost}</TableCell>
                      <TableCell className="text-gray-600">{log.resource}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </div>
          
          {/* Simulate Button at Bottom */}
          <div className="border-t border-gray-200 p-4 flex justify-center">
            <button
              onClick={onSimulate}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-all duration-200 flex items-center gap-2 shadow-md hover:shadow-lg hover:scale-105"
            >
              <Play className="w-4 h-4" />
              Simulate
            </button>
          </div>
        </div>
      )}

      {isCollapsed && (
        <div className="p-4 text-center text-gray-500 text-sm">
          Click to expand event log preview
        </div>
      )}
    </div>
  );
}
