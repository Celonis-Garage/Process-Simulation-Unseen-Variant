import React, { useState, useRef, useEffect } from 'react';
import { Mic, Send } from 'lucide-react';
import { Message } from '../App';
import { ScrollArea } from './ui/scroll-area';

interface PromptPanelProps {
  messages: Message[];
  onPromptSubmit: (prompt: string) => void;
}

export function PromptPanel({ messages, onPromptSubmit }: PromptPanelProps) {
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

  const samplePrompts = [
    "Remove 'Generate Pick List'",
    "Add 'Apply Discount' step after 'Schedule Order Fulfillment'",
    "Add 'Process Return Request' after 'Generate Pick List'",
  ];

  const handleSamplePromptClick = (prompt: string) => {
    setInputValue(prompt);
  };

  return (
    <div className="h-full bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-gray-900">Prompt to Design</h2>
        <p className="text-sm text-gray-500 mt-1">Describe process changes in natural language</p>
      </div>

      {/* Chat Area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && !isProcessing && (
          <div className="space-y-3">
            <p className="text-sm text-gray-600 mb-4">Try these sample prompts:</p>
            {samplePrompts.map((prompt, index) => (
              <button
                key={index}
                onClick={() => handleSamplePromptClick(prompt)}
                className="w-full text-left px-4 py-3 bg-gray-50 hover:bg-gray-100 border border-gray-200 rounded-lg transition-colors group"
              >
                <p className="text-sm text-gray-700 group-hover:text-gray-900">{prompt}</p>
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
              className={`max-w-[85%] rounded-lg px-4 py-3 ${
                message.type === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-900'
              }`}
            >
              <p className="text-sm">{message.text}</p>
            </div>
          </div>
        ))}
        
        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-3">
              <div className="flex items-center gap-2">
                <div className="flex gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
                <span className="text-sm text-gray-600">Processing...</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-end gap-2">
          <div className="flex-1 bg-white border border-gray-300 rounded-lg flex items-center px-3 py-2 focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your process change request..."
              className="flex-1 outline-none text-sm"
              disabled={isProcessing}
            />
            <button className="p-1 hover:bg-gray-100 rounded transition-colors">
              <Mic className="w-4 h-4 text-gray-500" />
            </button>
          </div>
          <button
            onClick={handleSubmit}
            disabled={!inputValue.trim() || isProcessing}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            <Send className="w-4 h-4" />
            Generate
          </button>
        </div>
      </div>
    </div>
  );
}
