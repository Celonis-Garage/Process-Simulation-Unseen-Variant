import React, { useState, useRef, useEffect } from 'react';
import { Mic, Send, ChevronLeft, ChevronRight } from 'lucide-react';
import { Message } from '../App';

interface PromptPanelProps {
  messages: Message[];
  onPromptSubmit: (prompt: string) => void;
  isProcessEmpty?: boolean;  // NEW: Track if process is empty
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

export function PromptPanel({ messages, onPromptSubmit, isProcessEmpty = false, isCollapsed = false, onToggleCollapse }: PromptPanelProps) {
  const [inputValue, setInputValue] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages]);

  const handleSubmit = () => {
    if (!inputValue.trim() || isProcessing) return;
    
    onPromptSubmit(inputValue);
    setInputValue('');
    setIsProcessing(true);
    
    setTimeout(() => {
      setIsProcessing(false);
    }, 1500);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // 🎯 Different prompts based on whether process is selected
  const initialSelectionPrompts = [
    "I want to see a standard order fulfillment process",
    "Show me what happens when an order gets rejected",
    "I need a process where customers get discounts",
    "Show me how customer returns are handled",
    "Display a simple quick order process",
  ];

  const modificationPrompts = [
    "Remove 'Generate Pick List'",
    "Add 'Apply Discount' step after 'Schedule Order Fulfillment'",
    "Change 'Generate Invoice' time to 30 minutes",
    "Make 'Generate Pick List' and 'Pack Items' parallel",
  ];

  // Choose prompts based on process state
  const samplePrompts = isProcessEmpty ? initialSelectionPrompts : modificationPrompts;

  const handleSamplePromptClick = (prompt: string) => {
    setInputValue(prompt);
  };

  // If collapsed, show minimal vertical bar
  if (isCollapsed) {
    return (
      <div className="h-full bg-gray-50 border-r border-gray-200 flex items-center justify-center relative group">
        <div className="transform -rotate-90 whitespace-nowrap text-xs font-semibold text-gray-600">
          Prompt Panel
        </div>
        <button
          onClick={onToggleCollapse}
          className="absolute -right-3 top-1/2 -translate-y-1/2 bg-white border border-gray-300 rounded-full p-1.5 hover:bg-gray-50 shadow-md transition-all opacity-60 group-hover:opacity-100"
          title="Expand Prompt Panel"
        >
          <ChevronRight className="w-3.5 h-3.5 text-gray-600" />
        </button>
      </div>
    );
  }

  return (
    <div className="h-full bg-white border-r border-gray-200 flex flex-col relative overflow-hidden">
      {/* Collapse button */}
      <button
        onClick={onToggleCollapse}
        className="absolute -right-3 top-1/2 -translate-y-1/2 z-10 bg-white border border-gray-300 rounded-full p-1.5 hover:bg-gray-50 shadow-md transition-all"
        title="Collapse Prompt Panel"
      >
        <ChevronLeft className="w-3.5 h-3.5 text-gray-600" />
      </button>

      {/* Header */}
      <div className="p-3 border-b border-gray-200 flex-shrink-0">
        <h2 className="text-base font-semibold text-gray-900">Prompt to Design</h2>
        <p className="text-xs text-gray-500 mt-0.5">
          {isProcessEmpty 
            ? 'Describe the process scenario you want to explore'
            : 'Describe process changes in natural language'}
        </p>
      </div>

      {/* Chat Area - Scrollable */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto overflow-x-hidden p-3 space-y-2.5">
        {/* Always show sample prompts when process is empty, even if there are messages */}
        {isProcessEmpty && !isProcessing && (
          <div className="space-y-2">
            <p className="text-xs text-gray-600 mb-2">
              ✨ Select a process to begin:
            </p>
            {samplePrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleSamplePromptClick(prompt)}
                className="w-full text-left px-3 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors group"
              >
                <p className="text-xs text-gray-700 group-hover:text-gray-900">{prompt}</p>
              </button>
            ))}
          </div>
        )}
        
        {/* Show sample prompts when no messages yet and process is loaded */}
        {!isProcessEmpty && messages.length === 0 && !isProcessing && (
          <div className="space-y-2">
            <p className="text-xs text-gray-600 mb-2">
              Try these sample prompts:
            </p>
            {samplePrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleSamplePromptClick(prompt)}
                className="w-full text-left px-3 py-2 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors group"
              >
                <p className="text-xs text-gray-700 group-hover:text-gray-900">{prompt}</p>
              </button>
            ))}
          </div>
        )}
        
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg px-3 py-2 ${
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-xs">{message.text}</p>
            </div>
          </div>
        ))}
        
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-3 py-2">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-1.5 h-1.5 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-xs text-gray-600">Processing...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area - Fixed at bottom */}
      <div className="p-3 border-t border-gray-200 bg-gray-50 flex-shrink-0">
        <div className="flex items-end gap-2">
          <div className="flex-1 bg-white border border-gray-300 rounded-lg flex items-center px-2 py-1.5 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your process change request..."
              className="flex-1 outline-none text-xs"
              disabled={isProcessing}
            />
            <button className="p-1 hover:bg-gray-100 rounded transition-colors">
              <Mic className="w-3.5 h-3.5 text-gray-500" />
            </button>
          </div>
          <button
            onClick={handleSubmit}
            disabled={!inputValue.trim() || isProcessing}
            className="px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-1.5 text-xs"
          >
            <Send className="w-3.5 h-3.5" />
            Generate
          </button>
        </div>
      </div>
    </div>
  );
}
