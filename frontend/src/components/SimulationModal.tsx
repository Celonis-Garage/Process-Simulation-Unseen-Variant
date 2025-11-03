import React from 'react';
import { X, TrendingUp, TrendingDown, ArrowRight, CheckCircle2, Info } from 'lucide-react';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';
import { SimulationResult } from '../types';

interface SimulationModalProps {
  isOpen: boolean;
  onClose: () => void;
  simulationResults: SimulationResult | null;
  variantName: string;
}

export function SimulationModal({ isOpen, onClose, simulationResults, variantName }: SimulationModalProps) {
  if (!isOpen || !simulationResults) return null;

  const {
    baseline_on_time_delivery,
    baseline_days_sales_outstanding,
    baseline_order_accuracy,
    baseline_invoice_accuracy,
    baseline_avg_cost_delivery,
    on_time_delivery,
    days_sales_outstanding,
    order_accuracy,
    invoice_accuracy,
    avg_cost_delivery,
    confidence,
    summary
  } = simulationResults;

  const confidencePercent = confidence * 100;

  // Calculate percentage changes for each KPI
  const otdChange = ((on_time_delivery - baseline_on_time_delivery) / baseline_on_time_delivery) * 100;
  const dsoChange = ((days_sales_outstanding - baseline_days_sales_outstanding) / baseline_days_sales_outstanding) * 100;
  const orderAccChange = ((order_accuracy - baseline_order_accuracy) / baseline_order_accuracy) * 100;
  const invoiceAccChange = ((invoice_accuracy - baseline_invoice_accuracy) / baseline_invoice_accuracy) * 100;
  const costChange = ((avg_cost_delivery - baseline_avg_cost_delivery) / baseline_avg_cost_delivery) * 100;

  // Detect if this is baseline (unchanged process)
  const isBaseline = Math.abs(otdChange) < 0.5 && Math.abs(dsoChange) < 0.5 && Math.abs(costChange) < 0.5;

  const kpiData = [
    {
      name: 'On-Time Delivery',
      before: `${baseline_on_time_delivery.toFixed(1)}%`,
      after: `${on_time_delivery.toFixed(1)}%`,
      change: otdChange > 0 ? `+${Math.abs(otdChange).toFixed(1)}%` : otdChange < 0 ? `-${Math.abs(otdChange).toFixed(1)}%` : '0%',
      trend: otdChange > 0.5 ? 'up' : otdChange < -0.5 ? 'down' : 'neutral',
      color: otdChange > 0.5 ? 'text-green-600' : otdChange < -0.5 ? 'text-orange-600' : 'text-gray-600',
      bgColor: otdChange > 0.5 ? 'bg-green-50' : otdChange < -0.5 ? 'bg-orange-50' : 'bg-gray-50',
      description: 'Percentage of orders delivered on time'
    },
    {
      name: 'Days Sales Outstanding',
      before: `${baseline_days_sales_outstanding.toFixed(0)} days`,
      after: `${days_sales_outstanding.toFixed(0)} days`,
      change: dsoChange < 0 ? `-${Math.abs(dsoChange).toFixed(1)}%` : dsoChange > 0 ? `+${Math.abs(dsoChange).toFixed(1)}%` : '0%',
      trend: dsoChange < -0.5 ? 'down' : dsoChange > 0.5 ? 'up' : 'neutral',
      color: dsoChange < -0.5 ? 'text-green-600' : dsoChange > 0.5 ? 'text-orange-600' : 'text-gray-600',
      bgColor: dsoChange < -0.5 ? 'bg-green-50' : dsoChange > 0.5 ? 'bg-orange-50' : 'bg-gray-50',
      description: 'Average time to collect payment'
    },
    {
      name: 'Order Accuracy',
      before: `${baseline_order_accuracy.toFixed(1)}%`,
      after: `${order_accuracy.toFixed(1)}%`,
      change: orderAccChange > 0 ? `+${Math.abs(orderAccChange).toFixed(1)}%` : orderAccChange < 0 ? `-${Math.abs(orderAccChange).toFixed(1)}%` : '0%',
      trend: orderAccChange > 0.5 ? 'up' : orderAccChange < -0.5 ? 'down' : 'neutral',
      color: orderAccChange > 0.5 ? 'text-green-600' : orderAccChange < -0.5 ? 'text-orange-600' : 'text-gray-600',
      bgColor: orderAccChange > 0.5 ? 'bg-green-50' : orderAccChange < -0.5 ? 'bg-orange-50' : 'bg-gray-50',
      description: 'Order fulfillment accuracy rate'
    },
    {
      name: 'Invoice Accuracy',
      before: `${baseline_invoice_accuracy.toFixed(1)}%`,
      after: `${invoice_accuracy.toFixed(1)}%`,
      change: invoiceAccChange > 0 ? `+${Math.abs(invoiceAccChange).toFixed(1)}%` : invoiceAccChange < 0 ? `-${Math.abs(invoiceAccChange).toFixed(1)}%` : '0%',
      trend: invoiceAccChange > 0.5 ? 'up' : invoiceAccChange < -0.5 ? 'down' : 'neutral',
      color: invoiceAccChange > 0.5 ? 'text-green-600' : invoiceAccChange < -0.5 ? 'text-orange-600' : 'text-gray-600',
      bgColor: invoiceAccChange > 0.5 ? 'bg-green-50' : invoiceAccChange < -0.5 ? 'bg-orange-50' : 'bg-gray-50',
      description: 'Invoicing accuracy and correctness'
    },
    {
      name: 'Avg Cost of Delivery',
      before: `$${baseline_avg_cost_delivery.toFixed(2)}`,
      after: `$${avg_cost_delivery.toFixed(2)}`,
      change: costChange < 0 ? `-${Math.abs(costChange).toFixed(1)}%` : costChange > 0 ? `+${Math.abs(costChange).toFixed(1)}%` : '0%',
      trend: costChange < -0.5 ? 'down' : costChange > 0.5 ? 'up' : 'neutral',
      color: costChange < -0.5 ? 'text-green-600' : costChange > 0.5 ? 'text-orange-600' : 'text-gray-600',
      bgColor: costChange < -0.5 ? 'bg-green-50' : costChange > 0.5 ? 'bg-orange-50' : 'bg-gray-50',
      description: 'Average cost per order delivery'
    }
  ];

  return (
    <div 
      className="fixed inset-0 bg-black/60 flex items-center justify-center z-50 animate-in fade-in duration-200"
      onClick={onClose}
    >
      <div 
        className="bg-white rounded-xl shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] flex flex-col animate-in zoom-in-95 duration-200"
        onClick={e => e.stopPropagation()}
      >
        {/* Header */}
        <div className="p-6 border-b border-gray-200 flex items-center justify-between flex-shrink-0">
          <div>
            <h2 className="text-gray-900">Simulation Results: {variantName}</h2>
            <p className="text-sm text-gray-500 mt-1">
              {isBaseline 
                ? 'Baseline process configuration - Current state analysis' 
                : 'Process optimization scenario'
              }
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5 text-gray-600" />
          </button>
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-auto">
          <div className="p-6 space-y-6">
            {/* 1. KPI Comparisons - 5 KPIs Display */}
            <div>
              <h3 className="text-gray-900 mb-4">Key Performance Indicators</h3>
              <div className="grid grid-cols-2 gap-4">
                {kpiData.slice(0, 4).map((kpi, index) => (
                  <div
                    key={index}
                    className={`${kpi.bgColor} border-2 ${kpi.bgColor.replace('bg-', 'border-').replace('-50', '-200')} rounded-lg p-4`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <span className="text-sm font-medium text-gray-700">{kpi.name}</span>
                        <p className="text-xs text-gray-500 mt-0.5">{kpi.description}</p>
                      </div>
                      {kpi.trend !== 'neutral' && (
                        <Badge className={`${kpi.color} bg-white flex-shrink-0`}>
                          {kpi.trend === 'up' ? (
                            <TrendingUp className="w-3 h-3 mr-1" />
                          ) : (
                            <TrendingDown className="w-3 h-3 mr-1" />
                          )}
                          {kpi.change}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-gray-600 font-medium">{kpi.before}</span>
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      <span className={`${kpi.color} font-semibold`}>{kpi.after}</span>
                    </div>
                  </div>
                ))}
              </div>
              {/* 5th KPI - Full Width */}
              <div className="mt-4">
                {kpiData.slice(4).map((kpi, index) => (
                  <div
                    key={index + 4}
                    className={`${kpi.bgColor} border-2 ${kpi.bgColor.replace('bg-', 'border-').replace('-50', '-200')} rounded-lg p-4`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div>
                        <span className="text-sm font-medium text-gray-700">{kpi.name}</span>
                        <p className="text-xs text-gray-500 mt-0.5">{kpi.description}</p>
                      </div>
                      {kpi.trend !== 'neutral' && (
                        <Badge className={`${kpi.color} bg-white flex-shrink-0`}>
                          {kpi.trend === 'up' ? (
                            <TrendingUp className="w-3 h-3 mr-1" />
                          ) : (
                            <TrendingDown className="w-3 h-3 mr-1" />
                          )}
                          {kpi.change}
                        </Badge>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="text-gray-600 font-medium">{kpi.before}</span>
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      <span className={`${kpi.color} font-semibold`}>{kpi.after}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* 2. Confidence Meter */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm text-gray-700">Prediction Confidence</span>
                <span className="text-blue-700">{confidencePercent.toFixed(0)}%</span>
              </div>
              <Progress value={confidencePercent} className="h-2" />
              <p className="text-xs text-gray-600 mt-2">
                Based on analysis of 2,000 orders from real O2C process data
              </p>
            </div>

            {/* 3. Natural Language Summary */}
            <div className="bg-gradient-to-r from-purple-50 to-blue-50 border border-purple-200 rounded-lg p-5">
              <div className="flex items-start gap-3">
                <CheckCircle2 className="w-5 h-5 text-purple-600 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="text-gray-900 mb-2">Summary</h3>
                  <p className="text-sm text-gray-700 leading-relaxed">
                    {summary}
                  </p>
                </div>
              </div>
            </div>

            {/* 4. Explanation Section - Only show if not baseline */}
            {!isBaseline && (
              <div className="border border-gray-200 rounded-lg p-5 bg-white">
                <div className="flex items-start gap-3 mb-4">
                  <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div>
                    <h3 className="text-gray-900 mb-2">Why These KPI Changes?</h3>
                    <p className="text-sm text-gray-700 leading-relaxed mb-3">
                      The observed changes are driven by several interconnected factors:
                    </p>
                  </div>
                </div>
                
                <div className="space-y-3 ml-8">
                  {Math.abs(otdChange) > 0.5 && (
                    <div className="flex gap-3">
                      <div className={`w-1.5 h-1.5 ${otdChange > 0 ? 'bg-green-600' : 'bg-orange-600'} rounded-full mt-2 flex-shrink-0`}></div>
                      <div>
                        <p className="text-sm text-gray-900">On-Time Delivery {otdChange > 0 ? 'Improvement' : 'Decline'}</p>
                        <p className="text-xs text-gray-600 mt-1">
                          {otdChange > 0 ? (
                            <>Process optimization reduced cycle time, enabling faster order processing and more timely deliveries. Fewer bottlenecks mean better adherence to delivery schedules.</>
                          ) : (
                            <>Additional process steps or longer activity times may delay shipments, affecting delivery schedules and customer satisfaction.</>
                          )}
                        </p>
                      </div>
                    </div>
                  )}

                  {Math.abs(dsoChange) > 0.5 && (
                    <div className="flex gap-3">
                      <div className={`w-1.5 h-1.5 ${dsoChange < 0 ? 'bg-green-600' : 'bg-orange-600'} rounded-full mt-2 flex-shrink-0`}></div>
                      <div>
                        <p className="text-sm text-gray-900">Days Sales Outstanding {dsoChange < 0 ? 'Improvement' : 'Increase'}</p>
                        <p className="text-xs text-gray-600 mt-1">
                          {dsoChange < 0 ? (
                            <>Faster process execution reduces the time between order fulfillment and payment collection, improving cash flow by {Math.abs(dsoChange).toFixed(0)}%.</>
                          ) : (
                            <>Longer cycle times delay invoicing and payment collection, potentially impacting working capital by {Math.abs(dsoChange).toFixed(0)}%.</>
                          )}
                        </p>
                      </div>
                    </div>
                  )}

                  {Math.abs(invoiceAccChange) > 0.5 && (
                    <div className="flex gap-3">
                      <div className={`w-1.5 h-1.5 ${invoiceAccChange > 0 ? 'bg-green-600' : 'bg-orange-600'} rounded-full mt-2 flex-shrink-0`}></div>
                      <div>
                        <p className="text-sm text-gray-900">Invoice Accuracy {invoiceAccChange > 0 ? 'Improvement' : 'Decline'}</p>
                        <p className="text-xs text-gray-600 mt-1">
                          {invoiceAccChange > 0 ? (
                            <>Adding validation and quality checks improves invoicing accuracy, reducing disputes and payment delays.</>
                          ) : (
                            <>Removing validation steps may increase invoicing errors, leading to more disputes and rework.</>
                          )}
                        </p>
                      </div>
                    </div>
                  )}

                  {Math.abs(costChange) > 0.5 && (
                    <div className="flex gap-3">
                      <div className={`w-1.5 h-1.5 ${costChange < 0 ? 'bg-green-600' : 'bg-orange-600'} rounded-full mt-2 flex-shrink-0`}></div>
                      <div>
                        <p className="text-sm text-gray-900">Delivery Cost {costChange < 0 ? 'Reduction' : 'Increase'}</p>
                        <p className="text-xs text-gray-600 mt-1">
                          {costChange < 0 ? (
                            <>Process optimization reduces per-order costs by ${Math.abs(avg_cost_delivery - baseline_avg_cost_delivery).toFixed(2)}, improving overall efficiency and profit margins.</>
                          ) : (
                            <>Additional processing adds ${Math.abs(avg_cost_delivery - baseline_avg_cost_delivery).toFixed(2)} per order. However, this may prevent costly downstream errors and rework, potentially yielding positive ROI over time.</>
                          )}
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Trust & Accuracy Section */}
            <div className="border border-amber-200 bg-amber-50 rounded-lg p-5">
              <div className="flex items-start gap-3">
                <Info className="w-5 h-5 text-amber-700 mt-0.5 flex-shrink-0" />
                <div>
                  <h3 className="text-gray-900 mb-2">How to Trust This Simulation</h3>
                  <div className="space-y-2 text-sm text-gray-700">
                    <div className="flex items-start gap-2">
                      <span className="text-amber-700">•</span>
                      <p>
                        <span className="text-gray-900">Training Data:</span> Analysis based on 2,000 historical orders with verified outcomes from real O2C process data.
                      </p>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-amber-700">•</span>
                      <p>
                        <span className="text-gray-900">Real KPIs:</span> On-time delivery, DSO, accuracy metrics, and costs derived from actual event log data, not estimates.
                      </p>
                    </div>
                    <div className="flex items-start gap-2">
                      <span className="text-amber-700">•</span>
                      <p>
                        <span className="text-gray-900">Confidence Level:</span> {confidencePercent.toFixed(0)}% confidence based on data quality and process complexity.
                      </p>
                    </div>
                  </div>
                  
                  {!isBaseline && (
                    <div className="mt-4 pt-4 border-t border-amber-200">
                      <p className="text-xs text-gray-600 italic">
                        💡 Recommendation: Test this variant with a small pilot before full rollout to validate predicted improvements.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 flex justify-end gap-3 flex-shrink-0">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg transition-colors"
          >
            Close Simulation
          </button>
        </div>
      </div>
    </div>
  );
}
