/**
 * FeasibilityGauge Component
 * Visual risk score gauge with color coding
 */

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { getRiskScoreColor, getFeasibilityIcon, getFeasibilityColorClass } from '../utils/formatters';

const FeasibilityGauge = ({ riskScore, feasibilityStatus }) => {
  const score = riskScore || 0;
  const data = [
    { name: 'Score', value: score },
    { name: 'Remaining', value: 100 - score },
  ];

  const COLORS = [getRiskScoreColor(score), '#E5E7EB'];

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Feasibility Assessment</h2>

      <div className="flex items-center justify-center mb-6">
        <ResponsiveContainer width="100%" height={200}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              startAngle={180}
              endAngle={0}
              innerRadius={60}
              outerRadius={80}
              fill="#8884d8"
              paddingAngle={0}
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index]} />
              ))}
            </Pie>
          </PieChart>
        </ResponsiveContainer>
      </div>

      <div className="text-center mb-6">
        <div className="text-5xl font-bold" style={{ color: getRiskScoreColor(score) }}>
          {score.toFixed(1)}
        </div>
        <div className="text-gray-600 text-sm mt-1">Risk Score (out of 100)</div>
      </div>

      <div className="text-center">
        <span
          className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-semibold ${getFeasibilityColorClass(feasibilityStatus)}`}
        >
          <span className="mr-2 text-lg">{getFeasibilityIcon(feasibilityStatus)}</span>
          {feasibilityStatus || 'UNKNOWN'}
        </span>
      </div>

      <div className="mt-6 pt-6 border-t border-gray-200">
        <div className="text-xs text-gray-600 space-y-2">
          <div className="flex items-center justify-between">
            <span>✅ 90-100: FEASIBLE</span>
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#10B981' }}></div>
          </div>
          <div className="flex items-center justify-between">
            <span>🟡 75-89: MARGINAL</span>
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#F59E0B' }}></div>
          </div>
          <div className="flex items-center justify-between">
            <span>🟠 60-74: RISKY</span>
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#F97316' }}></div>
          </div>
          <div className="flex items-center justify-between">
            <span>❌ &lt;60: IMPOSSIBLE</span>
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: '#DC2626' }}></div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default FeasibilityGauge;