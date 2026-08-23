/**
 * AIRecommendation Component
 * Button to trigger AI recommendations with modal display
 */

import React, { useState } from 'react';
import { aiAPI } from '../services/api';

const AIRecommendation = ({ planId, disabled = false }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [recommendation, setRecommendation] = useState(null);
  const [requestType, setRequestType] = useState('gap_analysis');
  const [error, setError] = useState(null);
  const [usageStats, setUsageStats] = useState(null);

  const requestTypes = [
    { value: 'gap_analysis', label: 'Gap Analysis', icon: '🔍' },
    { value: 'optimization', label: 'Cost/Time Optimization', icon: '⚡' },
    { value: 'bundling', label: 'Test Bundling', icon: '📦' },
    { value: 'general', label: 'General Assessment', icon: '📊' },
  ];

  const handleOpen = async () => {
    setIsOpen(true);
    loadUsageStats();
  };

  const loadUsageStats = async () => {
    try {
      const stats = await aiAPI.getUsageStats();
      setUsageStats(stats);
    } catch (err) {
      console.error('Failed to load AI usage stats:', err);
    }
  };

  const handleGetRecommendation = async () => {
    if (!planId) {
      setError('No plan ID provided');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await aiAPI.getRecommendation(planId, requestType);
      setRecommendation(result);
    } catch (err) {
      setError(err.toString());
    } finally {
      setLoading(false);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setRecommendation(null);
    setError(null);
  };

  return (
    <>
      <button
        onClick={handleOpen}
        disabled={disabled || !planId}
        className="bg-capgemini-blue text-white px-6 py-3 rounded-lg font-semibold hover:bg-capgemini-darkblue transition-colors duration-200 disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center space-x-2"
      >
        <span>🤖</span>
        <span>Get AI Recommendation</span>
      </button>

      {isOpen && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Header */}
            <div className="bg-capgemini-blue text-white px-6 py-4 flex items-center justify-between">
              <h2 className="text-xl font-bold">AI-Powered Recommendations</h2>
              <button
                onClick={handleClose} className="text-white hover:text-gray-200 text-2xl" > × </button> </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Usage Stats */}
          {usageStats && (
            <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-semibold text-blue-900">API Usage This Week</span>
                <span className="text-xs text-blue-600">
                  Resets: {new Date(usageStats.current_week.resets_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex-1">
                  <div className="w-full bg-blue-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{
                        width: `${usageStats.rate_limit.percentage_used}%`,
                      }}
                    ></div>
                  </div>
                </div>
                <div className="text-sm font-semibold text-blue-900">
                  {usageStats.rate_limit.calls_remaining} / 100 remaining
                </div>
              </div>
            </div>
          )}

          {/* Request Type Selection */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Select Recommendation Type
            </label>
            <div className="grid grid-cols-2 gap-3">
              {requestTypes.map((type) => (
                <button
                  key={type.value}
                  onClick={() => setRequestType(type.value)}
                  className={`p-4 rounded-lg border-2 transition-all duration-200 text-left ${
                    requestType === type.value
                      ? 'border-capgemini-blue bg-capgemini-lightblue'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-center space-x-2 mb-1">
                    <span className="text-2xl">{type.icon}</span>
                    <span className="font-semibold text-sm">{type.label}</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGetRecommendation}
            disabled={loading || !planId}
            className="w-full bg-capgemini-blue text-white px-6 py-3 rounded-lg font-semibold hover:bg-capgemini-darkblue transition-colors duration-200 disabled:bg-gray-400 disabled:cursor-not-allowed mb-6"
          >
            {loading ? (
              <span className="flex items-center justify-center">
                <div className="spinner mr-3" style={{ width: '20px', height: '20px', borderWidth: '2px' }}></div>
                Generating Recommendation...
              </span>
            ) : (
              'Generate Recommendation'
            )}
          </button>

          {/* Error Display */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-start">
                <span className="text-red-600 mr-2">❌</span>
                <div className="flex-1">
                  <h4 className="text-sm font-semibold text-red-900 mb-1">Error</h4>
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          {/* Recommendation Display */}
          {recommendation && (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <span className="text-green-600">✓</span>
                  <span className="text-sm font-semibold text-green-900">
                    Recommendation Generated
                  </span>
                </div>
                {recommendation.used_ai ? (
                  <span className="text-xs text-green-600 flex items-center">
                    <span className="mr-1">🤖</span> AI-Powered
                  </span>
                ) : (
                  <span className="text-xs text-yellow-600 flex items-center">
                    <span className="mr-1">⚙️</span> Rule-Based
                  </span>
                )}
              </div>

              <div className="p-6 bg-gray-50 rounded-lg border border-gray-200">
                <div className="prose prose-sm max-w-none">
                  <div
                    className="text-gray-800 whitespace-pre-wrap"
                    style={{ lineHeight: '1.6' }}
                  >
                    {recommendation.recommendation}
                  </div>
                </div>
              </div>

              {recommendation.metadata && (
                <div className="text-xs text-gray-500 flex items-center justify-between">
                  <span>
                    Response time: {recommendation.metadata.response_time_ms}ms
                  </span>
                  {recommendation.metadata.tokens_used > 0 && (
                    <span>Tokens used: {recommendation.metadata.tokens_used}</span>
                  )}
                </div>
              )}
            </div>
          )}

          {/* Help Text */}
          {!recommendation && !loading && (
            <div className="text-sm text-gray-600 space-y-2">
              <p className="font-semibold">What each recommendation type provides:</p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li>
                  <strong>Gap Analysis:</strong> Identifies missing mandatory tests and coverage gaps
                </li>
                <li>
                  <strong>Cost/Time Optimization:</strong> Suggests ways to reduce budget and timeline
                </li>
                <li>
                  <strong>Test Bundling:</strong> Finds opportunities to combine tests at same location
                </li>
                <li>
                  <strong>General Assessment:</strong> Overall plan evaluation and strategic advice
                </li>
              </ul>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex justify-end">
          <button
            onClick={handleClose}
            className="px-6 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors duration-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  )}
</>
); };

export default AIRecommendation;