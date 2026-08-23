/**
 * TimelineChart Component
 * Display 3 different timeline views
 */

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell, ResponsiveContainer } from 'recharts';

const TimelineChart = ({ timelines }) => {
  if (!timelines) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Timeline Analysis</h2>
        <div className="text-gray-500 text-center py-8">No timeline data available</div>
      </div>
    );
  }

  const data = [
    {
      name: 'Critical Path\n(PhysicalTests)', days: timelines.critical_path_days || 0, fill: '#DC2626', }, { name: 'Engineering\nWorkload', days: timelines.engineering_workload_days || 0, fill: '#F59E0B', }, { name: 'Parallel\nOptimized', days: timelines.parallel_optimized_days || 0, fill: '#10B981', }, ];

return ( <div className="bg-white rounded-lg shadow-md p-6"> <h2 className="text-xl font-bold text-gray-900 mb-4">Timeline Analysis</h2>

  <div className="mb-6">
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" style={{ fontSize: '12px' }} />
        <YAxis label={{ value: 'Days', angle: -90, position: 'insideLeft' }} />
        <Tooltip
          contentStyle={{ backgroundColor: '#fff', border: '1px solid #ccc' }}
          formatter={(value) => [`${value} days`, 'Duration']}
        />
        <Bar dataKey="days" radius={[8, 8, 0, 0]}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={entry.fill} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  </div>

  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
    <div className="bg-red-50 rounded-lg p-4 border border-red-200">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-red-900">Critical Path</span>
        <span className="text-xs text-red-600">Sequential</span>
      </div>
      <div className="text-2xl font-bold text-red-700">
        {timelines.critical_path_days} days
      </div>
      <div className="text-xs text-red-600 mt-1">
        Physical tests only (blocking)
      </div>
    </div>

    <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-yellow-900">Engineering</span>
        <span className="text-xs text-yellow-600">Total Workload</span>
      </div>
      <div className="text-2xl font-bold text-yellow-700">
        {timelines.engineering_workload_days} days
      </div>
      <div className="text-xs text-yellow-600 mt-1">
        Physical + Numerical tests
      </div>
    </div>

    <div className="bg-green-50 rounded-lg p-4 border border-green-200">
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-semibold text-green-900">Optimized</span>
        <span className="text-xs text-green-600">Parallel</span>
      </div>
      <div className="text-2xl font-bold text-green-700">
        {timelines.parallel_optimized_days} days
      </div>
      <div className="text-xs text-green-600 mt-1">
        With parallel execution
      </div>
    </div>
  </div>

  <div className="mt-4 pt-4 border-t border-gray-200">
    <div className="flex items-center justify-between text-sm">
      <span className="text-gray-600">Physical Tests:</span>
      <span className="font-semibold text-gray-900">
        {timelines.physical_test_count || 0}
      </span>
    </div>
    <div className="flex items-center justify-between text-sm mt-2">
      <span className="text-gray-600">Numerical Tests:</span>
      <span className="font-semibold text-gray-900">
        {timelines.numerical_test_count || 0}
      </span>
    </div>
  </div>
</div>
); };

export default TimelineChart;