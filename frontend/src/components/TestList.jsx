/**
 * TestList Component
 * Display list of tests with tier badges
 */

import React from 'react';
import { formatCurrency, formatDuration, getTierColorClass, getTierLabel, truncateText } from '../utils/formatters';

const TestList = ({ tests, onRemoveTest }) => {
  if (!tests || tests.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Selected Tests</h2>
        <div className="text-gray-500 text-center py-8">
          No tests selected. Please create a validation plan.
        </div>
      </div>
    );
  }

  // Group tests by tier
  const groupedTests = tests.reduce((acc, test) => {
    const tier = test.tier || 4;
    if (!acc[tier]) acc[tier] = [];
    acc[tier].push(test);
    return acc;
  }, {});

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">
          Selected Tests ({tests.length})
        </h2>
      </div>

      <div className="space-y-6">
        {[1, 2, 3, 4].map((tier) => {
          const tierTests = groupedTests[tier] || [];
          if (tierTests.length === 0) return null;

          return (
            <div key={tier} className="border border-gray-200 rounded-lg overflow-hidden">
              <div className={`${getTierColorClass(tier)} px-4 py-3`}>
                <div className="flex items-center justify-between">
                  <h3 className="text-sm font-bold text-white">
                    {getTierLabel(tier)}
                  </h3>
                  <span className="text-xs text-white opacity-90">
                    {tierTests.length} test(s)
                  </span>
                </div>
              </div>

              <div className="divide-y divide-gray-200">
                {tierTests.map((test, index) => (
                  <div
                    key={test.id || index}
                    className="p-4 hover:bg-gray-50 transition-colors duration-150"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-semibold text-gray-900 mb-1">
                          {truncateText(test.nom || test.name, 80)}
                        </h4>
                        <div className="flex flex-wrap items-center gap-3 text-xs text-gray-600">
                          <span className="flex items-center">
                            💰 {formatCurrency(test.prix || 0)}
                          </span>
                          <span className="flex items-center">
                            ⏱️ {formatDuration(test.duree || 0)}
                          </span>
                          {test.zone && (
                            <span className="flex items-center">
                              📍 {truncateText(test.zone, 30)}
                            </span>
                          )}
                          {test.is_homologation && (
                            <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-semibold">
                              Homologation
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="flex items-center space-x-2 ml-4">
                        {test.is_removable && onRemoveTest && (
                          <button
                            onClick={() => onRemoveTest(test.id)}
                            className="text-red-600 hover:text-red-800 text-sm"
                            title="Remove test"
                          >
                            ✕
                          </button>
                        )}
                        {!test.is_removable && (
                          <span className="text-xs text-gray-500 italic">
                            Required
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default TestList;