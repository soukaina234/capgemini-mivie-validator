import React from 'react';
import { formatCurrency, formatDuration, formatCompactNumber } from '../utils/formatters';

const SummaryCards = ({ summary }) => {
  if (!summary) {
    return null;
  }

  const cards = [
    {
      title: 'Total Tests',
      value: summary.total_tests || 0,
      icon: '📋',
      color: 'bg-blue-500',
      formatter: (val) => val,
    },
    {
      title: 'Total Cost',
      value: summary.total_cost || 0,
      icon: '💰',
      color: 'bg-green-500',
      formatter: formatCurrency,
    },
    {
      title: 'Physical Duration',
      value: summary.timelines?.critical_path_days || 0,
      icon: '⏱️',
      color: 'bg-yellow-500',
      formatter: formatDuration,
    },
    {
      title: 'Engineering Duration',
      value: summary.timelines?.engineering_workload_days || 0,
      icon: '🔧',
      color: 'bg-purple-500',
      formatter: formatDuration,
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
      {cards.map((card, index) => (
        <div
          key={index}
          className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-300"
        >
          <div className="flex items-center justify-between mb-4">
            <div className={`${card.color} w-12 h-12 rounded-full flex items-center justify-center text-2xl`}>
              {card.icon}
            </div>
          </div>
          <h3 className="text-gray-600 text-sm font-medium mb-1">{card.title}</h3>
          <p className="text-2xl font-bold text-gray-900">
            {card.formatter(card.value)}
          </p>
        </div>
      ))}
    </div>
  );
};

export default SummaryCards;