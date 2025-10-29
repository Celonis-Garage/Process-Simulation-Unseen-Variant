import React from 'react';
import { X, TrendingUp, TrendingDown, ArrowRight, CheckCircle2, Info } from 'lucide-react';
import { Progress } from './ui/progress';
import { Badge } from './ui/badge';

interface SimulationResult {
  cycle_time_change: number;
  cost_change: number;
  revenue_impact: number;
  confidence: number;
  summary: string;
  cycle_time_hours: number;
  cycle_time_days: number;
  cost_dollars: number;
  baseline_cycle_time_hours: number;
  baseline_cycle_time_days: number;
  baseline_cost_dollars: number;
}

interface SimulationModalProps {
  isOpen: boolean;
  onClose: () => void;
  simulationResults: SimulationResult | null;
  variantName: string;
}

export function SimulationModal({ isOpen, onClose, simulationResults, variantName }: SimulationModalProps) {
  if (!isOpen || !simulationResults) return null;

  const {
    cycle_time_change,
    cost_change,
    revenue_impact,
    confidence,
    summary,
    cycle_time_hours,
    cycle_time_days,
    cost_dollars,
    baseline_cycle_time_hours,
    baseline_cycle_time_days,
    baseline_cost_dollars
  } = simulationResults;

  // Convert decimal changes to percentages
  const cycleTimePercent = cycle_time_change * 100;
  const costPercent = cost_change * 100;
  const revenuePercent = revenue_impact * 100;
  const confidencePercent = confidence * 100;

  // Detect if this is baseline (unchanged process)
  const isBaseline = Math.abs(cycleTimePercent) < 0.1 && Math.abs(costPercent) < 0.1;

  const kpiData = [
    {
      name: 'Cycle Time',
      before: baseline_cycle_time_days >= 1 
        ? `${baseline_cycle_time_days.toFixed(1)} days`
        : `${baseline_cycle_time_hours.toFixed(1)}h`,
      after: cycle_time_days >= 1 
        ? `${cycle_time_days.toFixed(1)} days`
        : `${cycle_time_hours.toFixed(1)}h`,
      change: cycleTimePercent > 0 ? `+${Math.abs(cycleTimePercent).toFixed(1)}%` : cycleTimePercent < 0 ? `-${Math.abs(cycleTimePercent).toFixed(1)}%` : '0%',
      trend: cycleTimePercent < -0.1 ? 'down' : cycleTimePercent > 0.1 ? 'up' : 'neutral',
      color: cycleTimePercent < -0.1 ? 'text-green-600' : cycleTimePercent > 0.1 ? 'text-orange-600' : 'text-gray-600',
      bgColor: cycleTimePercent < -0.1 ? 'bg-green-50' : cycleTimePercent > 0.1 ? 'bg-orange-50' : 'bg-gray-50'
    },
    {
      name: 'Total Cost',
      before: `$${baseline_cost_dollars.toFixed(2)}`,
      after: `$${cost_dollars.toFixed(2)}`,
      change: costPercent > 0 ? `+${Math.abs(costPercent).toFixed(1)}%` : costPercent < 0 ? `-${Math.abs(costPercent).toFixed(1)}%` : '0%',
      trend: costPercent < -0.1 ? 'down' : costPercent > 0.1 ? 'up' : 'neutral',
      color: costPercent < -0.1 ? 'text-green-600' : costPercent > 0.1 ? 'text-orange-600' : 'text-gray-600',
      bgColor: costPercent < -0.1 ? 'bg-green-50' : costPercent > 0.1 ? 'bg-orange-50' : 'bg-gray-50'
    },
    {
      name: 'Revenue Impact',
      before: '0%',
      after: revenuePercent > 0 ? `+${Math.abs(revenuePercent).toFixed(1)}%` : revenuePercent < 0 ? `-${Math.abs(revenuePercent).toFixed(1)}%` : '0%',
      change: revenuePercent > 0 ? `+${Math.abs(revenuePercent).toFixed(1)}%` : revenuePercent < 0 ? `-${Math.abs(revenuePercent).toFixed(1)}%` : '0%',
      trend: revenuePercent > 0.1 ? 'up' : revenuePercent < -0.1 ? 'down' : 'neutral',
      color: revenuePercent > 0.1 ? 'text-green-600' : revenuePercent < -0.1 ? 'text-orange-600' : 'text-gray-600',
      bgColor: revenuePercent > 0.1 ? 'bg-green-50' : revenuePercent < -0.1 ? 'bg-orange-50' : 'bg-gray-50'
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
            {/* 1. KPI Comparisons - Figma Design */}
            <div>
              <h3 className="text-gray-900 mb-4">Key Performance Indicators</h3>
              <div className="grid grid-cols-2 gap-4">
                {kpiData.map((kpi, index) => (
                  <div
                    key={index}
                    className={`${kpi.bgColor} border-2 ${kpi.bgColor.replace('bg-', 'border-').replace('-50', '-200')} rounded-lg p-4`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm text-gray-700">{kpi.name}</span>
                      {kpi.trend !== 'neutral' && (
                        <Badge className={`${kpi.color} bg-white`}>
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
                      <span className="text-gray-600">{kpi.before}</span>
                      <ArrowRight className="w-4 h-4 text-gray-400" />
                      <span className={kpi.color}>{kpi.after}</span>
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
                    {isBaseline ? (
                      <>
                        This is the baseline process configuration from your data. 
                        Current performance: {baseline_cycle_time_days.toFixed(1)} days cycle time 
                        and ${baseline_cost_dollars.toFixed(2)} per order cost. 
                        This variant serves as the reference point for comparing future process modifications.
                      </>
                    ) : (
                      <>{summary}</>
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* 4. Explanation Section - Only show if not baseline */}
            {!isBaseline && (cycleTimePercent !== 0 || costPercent !== 0) && (
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
                  {Math.abs(cycleTimePercent) > 0.1 && (
                    <div className="flex gap-3">
                      <div className={`w-1.5 h-1.5 ${cycleTimePercent < 0 ? 'bg-green-600' : 'bg-orange-600'} rounded-full mt-2 flex-shrink-0`}></div>
                      <div>
                        <p className="text-sm text-gray-900">Cycle Time {cycleTimePercent < 0 ? 'Improvement' : 'Increase'}</p>
                        <p className="text-xs text-gray-600 mt-1">
                          {cycleTimePercent < 0 ? (
                            <>Streamlining the process reduces overall cycle time, enabling faster order processing and more timely deliveries. Fewer handoffs mean less coordination overhead and fewer delays.</>
                          ) : (
                            <>Additional process steps increase overall cycle time, potentially delaying shipments and affecting delivery schedules.</>
                          )}
                        </p>
                      </div>
                    </div>
                  )}

                  {Math.abs(costPercent) > 0.1 && (
                    <div className="flex gap-3">
                      <div className={`w-1.5 h-1.5 ${costPercent < 0 ? 'bg-green-600' : 'bg-orange-600'} rounded-full mt-2 flex-shrink-0`}></div>
                      <div>
                        <p className="text-sm text-gray-900">Cost {costPercent < 0 ? 'Reduction' : 'Increase'}</p>
                        <p className="text-xs text-gray-600 mt-1">
                          {costPercent < 0 ? (
                            <>Process optimization reduces per-order costs by ${Math.abs(cost_dollars - baseline_cost_dollars).toFixed(2)}, improving overall efficiency.</>
                          ) : (
                            <>Additional processing adds ${Math.abs(cost_dollars - baseline_cost_dollars).toFixed(2)} per order. However, this may prevent costly downstream rework and errors, potentially yielding positive ROI over time.</>
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
                        <span className="text-gray-900">Real KPIs:</span> Cycle times and costs derived from actual event log data, not estimates.
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
