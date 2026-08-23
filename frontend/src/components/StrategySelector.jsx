import React, { useState } from 'react';

const StrategySelector = ({ value, onChange, disabled = false, onCustomPreferencesChange }) => {
  const [showCustomOptions, setShowCustomOptions] = useState(value === 'custom');
  const [customPrefs, setCustomPrefs] = useState({
    prioritize: 'balanced',
  });

  const strategies = [
    {
      value: 'minimum',
      name: 'Regulatory Minimum',
      description: 'Only mandatory tests + minimum coverage',
      risk: 'HIGH',
      color: 'text-red-600',
    },
    {
      value: 'balanced',
      name: 'Balanced (Recommended)',
      description: 'Optimal quality/cost/time tradeoff',
      risk: 'MEDIUM',
      color: 'text-green-600',
    },
    {
      value: 'comprehensive',
      name: 'Comprehensive',
      description: 'Maximum validation coverage',
      risk: 'LOW',
      color: 'text-blue-600',
    },
    {
      value: 'custom',
      name: 'Custom Optimization',
      description: 'User-defined priorities',
      risk: 'VARIABLE',
      color: 'text-purple-600',
    },
  ];

  const handleStrategyChange = (newValue) => {
    onChange(newValue);
    setShowCustomOptions(newValue === 'custom');
  };

  const handleCustomPrefChange = (pref) => {
    const newPrefs = { ...customPrefs, prioritize: pref };
    setCustomPrefs(newPrefs);
    if (onCustomPreferencesChange) {
      onCustomPreferencesChange(newPrefs);
    }
  };

  const selectedStrategy = strategies.find(s => s.value === value);

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h2 className="text-xl font-bold text-gray-900 mb-4">Validation Strategy</h2>

      <select
        value={value}
        onChange={(e) => handleStrategyChange(e.target.value)}
        disabled={disabled}
        className="w-full px-4 py-3 border border-gray-300 rounded-lg shadow-sm focus:outline-none focus:ring-2 focus:ring-capgemini-blue focus:border-transparent text-lg font-semibold"
      >
        {strategies.map((strategy) => (
          <option key={strategy.value} value={strategy.value}>
            {strategy.name}
          </option>
        ))}
      </select>

      {selectedStrategy && (
        <div className="mt-4 p-4 bg-gray-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold text-gray-700">Risk Level:</span>
            <span className={`text-sm font-bold ${selectedStrategy.color}`}>
              {selectedStrategy.risk}
            </span>
          </div>
          <p className="text-sm text-gray-600">{selectedStrategy.description}</p>
        </div>
      )}

      {/* CUSTOM STRATEGY OPTIONS */}
      {showCustomOptions && (
        <div className="mt-6 p-4 bg-purple-50 border-2 border-purple-200 rounded-lg">
          <h3 className="text-md font-bold text-purple-900 mb-3">🎯 Custom Priorities</h3>
          
          <div className="space-y-3">
            <label className="flex items-center p-3 bg-white rounded border-2 border-transparent hover:border-purple-300 cursor-pointer">
              <input
                type="radio"
                name="custom-priority"
                value="minimize_cost"
                checked={customPrefs.prioritize === 'minimize_cost'}
                onChange={(e) => handleCustomPrefChange(e.target.value)}
                className="h-4 w-4 text-purple-600"
              />
              <div className="ml-3">
                <span className="block font-semibold text-gray-900">💰 Minimize Cost</span>
                <span className="text-xs text-gray-600">Prefer numerical tests, skip expensive physical tests</span>
              </div>
            </label>

            <label className="flex items-center p-3 bg-white rounded border-2 border-transparent hover:border-purple-300 cursor-pointer">
              <input
                type="radio"
                name="custom-priority"
                value="minimize_time"
                checked={customPrefs.prioritize === 'minimize_time'}
                onChange={(e) => handleCustomPrefChange(e.target.value)}
                className="h-4 w-4 text-purple-600"
              />
              <div className="ml-3">
                <span className="block font-semibold text-gray-900">⏱️ Minimize Time</span>
                <span className="text-xs text-gray-600">Prefer short tests, skip long endurance tests</span>
              </div>
            </label>

            <label className="flex items-center p-3 bg-white rounded border-2 border-transparent hover:border-purple-300 cursor-pointer">
              <input
                type="radio"
                name="custom-priority"
                value="maximize_safety"
                checked={customPrefs.prioritize === 'maximize_safety'}
                onChange={(e) => handleCustomPrefChange(e.target.value)}
                className="h-4 w-4 text-purple-600"
              />
              <div className="ml-3">
                <span className="block font-semibold text-gray-900">🛡️ Maximize Safety</span>
                <span className="text-xs text-gray-600">Include all safety-related tests (crash, ADAS, braking)</span>
              </div>
            </label>

            <label className="flex items-center p-3 bg-white rounded border-2 border-transparent hover:border-purple-300 cursor-pointer">
              <input
                type="radio"
                name="custom-priority"
                value="maximize_coverage"
                checked={customPrefs.prioritize === 'maximize_coverage'}
                onChange={(e) => handleCustomPrefChange(e.target.value)}
                className="h-4 w-4 text-purple-600"
              />
              <div className="ml-3">
                <span className="block font-semibold text-gray-900">📍 Maximize Coverage</span>
                <span className="text-xs text-gray-600">Prefer multi-zone tests for better zone coverage</span>
              </div>
            </label>

            <label className="flex items-center p-3 bg-white rounded border-2 border-transparent hover:border-purple-300 cursor-pointer">
              <input
                type="radio"
                name="custom-priority"
                value="balanced"
                checked={customPrefs.prioritize === 'balanced'}
                onChange={(e) => handleCustomPrefChange(e.target.value)}
                className="h-4 w-4 text-purple-600"
              />
              <div className="ml-3">
                <span className="block font-semibold text-gray-900">⚖️ Balanced</span>
                <span className="text-xs text-gray-600">Equal weight to all factors</span>
              </div>
            </label>
          </div>
        </div>
      )}

      {/* Strategy Comparison */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">Strategy Comparison</h3>
        <div className="space-y-2">
          {strategies.map((strategy) => (
            <div
              key={strategy.value}
              className={`flex items-center justify-between p-2 rounded ${
                value === strategy.value ? 'bg-capgemini-lightblue' : ''
              }`}
            >
              <span className="text-xs text-gray-700">{strategy.name}</span>
              <span className={`text-xs font-semibold ${strategy.color}`}>
                {strategy.risk}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default StrategySelector;