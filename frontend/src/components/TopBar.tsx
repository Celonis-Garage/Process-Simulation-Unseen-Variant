import React from 'react';
import { Settings, Workflow } from 'lucide-react';
import { Avatar, AvatarFallback } from './ui/avatar';
import { Badge } from './ui/badge';

interface TopBarProps {
  variantName?: string;
}

export function TopBar({ variantName = 'Base Case' }: TopBarProps) {
  return (
    <div className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shadow-sm">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
          <Workflow className="w-5 h-5 text-white" />
        </div>
        <div className="flex items-center gap-3">
          <h1 className="text-gray-900">Order to Cash Simulation</h1>
          <Badge variant={variantName === 'Base Case' ? 'secondary' : 'default'} className="text-xs">
            {variantName}
          </Badge>
        </div>
      </div>
      
      <div className="flex items-center gap-4">
        <Avatar className="w-8 h-8">
          <AvatarFallback className="bg-blue-100 text-blue-700">JD</AvatarFallback>
        </Avatar>
        <button className="p-2 hover:bg-gray-100 rounded-lg transition-colors">
          <Settings className="w-5 h-5 text-gray-600" />
        </button>
      </div>
    </div>
  );
}
