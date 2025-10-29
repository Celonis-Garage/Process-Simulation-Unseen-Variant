import React from 'react';
import { X, Clock, DollarSign, Info, Trash2 } from 'lucide-react';
import { ProcessStep } from '../App';

interface EventInfoDialogProps {
  step: ProcessStep;
  isOpen: boolean;
  onClose: () => void;
  onRemove: () => void;
}

const eventDescriptions: { [key: string]: string } = {
  'order-received': 'Initial event triggered when a customer places an order. The system captures order details including items, quantities, and customer information.',
  'credit-check': 'Automated verification of customer creditworthiness and payment history. Helps reduce risk of non-payment and fraud.',
  'order-approved': 'Manual or automated approval of the order based on credit check, inventory availability, and business rules.',
  'inventory-check': 'Real-time verification of product availability in warehouse. Ensures items are in stock before proceeding with fulfillment.',
  'invoice-created': 'Generation of invoice document with itemized charges, tax calculations, and payment terms for the customer.',
  'payment-validation': 'Verification of payment authenticity, compliance checks, and fraud detection before finalizing the transaction.',
  'payment-received': 'Confirmation that payment has been received and cleared through the payment gateway or banking system.',
  'quality-review': 'Quality assurance check to ensure order accuracy and compliance with customer specifications.',
  'fraud-detection': 'Advanced AI-powered analysis to identify suspicious patterns or potential fraudulent activities.',
  'risk-assessment': 'Comprehensive evaluation of financial and operational risks associated with the order.',
  'compliance-check': 'Verification that the order meets all regulatory and company policy requirements.',
  'customer-notification': 'Automated communication sent to customer with order status updates and relevant information.',
  'document-verification': 'Validation of required documentation such as contracts, purchase orders, or shipping documents.'
};

export function EventInfoDialog({ step, isOpen, onClose, onRemove }: EventInfoDialogProps) {
  if (!isOpen) return null;

  const description = eventDescriptions[step.id] || 'This process step is part of your order-to-cash workflow. It contributes to the overall process efficiency and helps track case progression.';

  return (
    <div 
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-xl shadow-2xl max-w-md w-full mx-4"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-200 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Info className="w-5 h-5 text-blue-600" />
            </div>
            <div>
              <h2 className="text-gray-900">{step.name}</h2>
              <p className="text-sm text-gray-500">Process Step Information</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Description */}
          <div>
            <h3 className="text-gray-900 mb-2">Description</h3>
            <p className="text-sm text-gray-600 leading-relaxed">
              {description}
            </p>
          </div>

          {/* Metrics */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock className="w-4 h-4 text-blue-600" />
                <span className="text-sm text-gray-700">Avg Duration</span>
              </div>
              <p className="text-blue-700">{step.avgTime}</p>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="flex items-center gap-2 mb-2">
                <DollarSign className="w-4 h-4 text-green-600" />
                <span className="text-sm text-gray-700">Avg Cost</span>
              </div>
              <p className="text-green-700">{step.avgCost}</p>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 flex justify-between gap-3">
          <button
            onClick={onRemove}
            disabled={step.id === 'start' || step.id === 'end'}
            className="px-4 py-2 bg-red-600 text-white hover:bg-red-700 disabled:bg-gray-300 disabled:cursor-not-allowed rounded-lg transition-colors flex items-center gap-2"
          >
            <Trash2 className="w-4 h-4" />
            Remove Step
          </button>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
