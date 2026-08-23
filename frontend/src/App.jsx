import React, { useState, useEffect } from 'react';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import SummaryCards from './components/SummaryCards';
import FeasibilityGauge from './components/FeasibilityGauge';
import TimelineChart from './components/TimelineChart';
import StrategySelector from './components/StrategySelector';
import TestList from './components/TestList';
import AIRecommendation from './components/AIRecommendation';
import DataUpload from './components/DataUpload';

import { testsAPI, plansAPI, exportAPI } from './services/api';

function App() {
  const [planData, setPlanData] = useState({
    plan_name: '',
    vehicle_category: 'M1',
    is_mivie: true,
    modification_zones: [],
    modification_level: 'Niveau 2',
    target_markets: ['Europe'],
    max_budget: null,
    max_duration: null,
    strategy_type: 'balanced',
  });
  const [currentPlan, setCurrentPlan] = useState(null);
  const [loading, setLoading] = useState(false);
  const [availableZones, setAvailableZones] = useState([]);

  useEffect(() => {
    loadFilterOptions();
  }, []);

  const loadFilterOptions = async () => {
    try {
      const options = await testsAPI.getFilterOptions();
      setAvailableZones(options.zones || []);
    } catch (error) {
      console.error('Failed to load filter options:', error);
    }
  };

  const handleCreatePlan = async () => {
    if (!planData.plan_name) {
      toast.error('Please enter a plan name');
      return;
    }
    if (planData.modification_zones.length === 0) {
      toast.error('Please select at least one modification zone');
      return;
    }
    if (planData.target_markets.length === 0) {
      toast.error('Please select at least one target market');
      return;
    }
    const mappedMarkets = planData.target_markets.map(market => 
    market === 'All Markets' ? 'Toutes destinations' : market
  );
    try {
      setLoading(true);
      toast.info('Creating validation plan...');
      
      const result = await plansAPI.createPlan(planData);
      
      setCurrentPlan(result);
      toast.success(`Plan created! Risk Score: ${result.risk_score.toFixed(1)}`);
      
      // Scroll to results
      window.scrollTo({ top: 600, behavior: 'smooth' });
    } catch (error) {
      toast.error(`Failed to create plan: ${error}`);
      console.error('Plan creation error:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleZoneToggle = (zone) => {
    const zones = planData.modification_zones.includes(zone)
      ? planData.modification_zones.filter((z) => z !== zone)
      : [...planData.modification_zones, zone];
    
    setPlanData({ ...planData, modification_zones: zones });
  };

  const handleMarketToggle = (market) => {
    const markets = planData.target_markets.includes(market)
      ? planData.target_markets.filter((m) => m !== market)
      : [...planData.target_markets, market];
    
    setPlanData({ ...planData, target_markets: markets });
  };

  const handleExportPDF = () => {
    if (currentPlan) {
      exportAPI.downloadPDF(currentPlan.plan_id);
      toast.success('PDF export started');
    }
  };

  const handleExportExcel = () => {
    if (currentPlan) {
      exportAPI.downloadExcel(currentPlan.plan_id);
      toast.success('Excel export started');
    }
  };

  const handleUploadSuccess = (result) => {
    toast.success(`Upload successful! ${result.new_tests} new tests added.`);
  };

  const handleResetPlan = () => {
    setCurrentPlan(null);
    setPlanData({
      plan_name: '',
      vehicle_category: 'M1',
      is_mivie: true,
      modification_zones: [],
      modification_level: 'Niveau 2',
      target_markets: ['Europe'],
      max_budget: null,
      max_duration: null,
      strategy_type: 'balanced',
    });
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <ToastContainer position="top-right" autoClose={3000} />

      {/* Header */}
      <header className="bg-capgemini-darkblue text-white shadow-lg">
        <div className="max-w-7xl mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Capgemini Engineering</h1>
              <p className="text-sm text-gray-300 mt-1">Mi-Vie Validation Plan Generator</p>
            </div>
            <div className="flex items-center space-x-4">
              <DataUpload onUploadSuccess={handleUploadSuccess} />
              {currentPlan && (
                <>
                  <button
                    onClick={handleResetPlan}
                    className="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700 transition-colors duration-200 text-sm"
                  >
                    ↻ New Plan
                  </button>
                  <button
                    onClick={handleExportPDF}
                    className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors duration-200 text-sm"
                  >
                    📄 PDF
                  </button>
                  <button
                    onClick={handleExportExcel}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors duration-200 text-sm"
                  >
                    📊 Excel
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content - NO LEFT SIDEBAR */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        {/* Plan Configuration Form */}
        <div className="bg-white rounded-lg shadow-md p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Create Validation Plan</h2>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {/* Plan Name */}
            <div className="lg:col-span-1">
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Plan Name *
              </label>
              <input
                type="text"
                value={planData.plan_name}
                onChange={(e) => setPlanData({ ...planData, plan_name: e.target.value })}
                placeholder="e.g., M1 Mi-Vie Project 2024"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-capgemini-blue"
              />
            </div>

            {/* Vehicle Category */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Vehicle Category *
              </label>
              <select
                value={planData.vehicle_category}
                onChange={(e) => setPlanData({ ...planData, vehicle_category: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-capgemini-blue"
              >
                <option value="Toutes catégories">All Categories</option>
                <option value="M1">M1</option>
                <option value="N1">N1</option>
                <option value="M1, N1">M1, N1</option>
                <option value="M1, N1, L7">M1, N1, L7</option>
              </select>
            </div>

            {/* Modification Level */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Modification Level *
              </label>
              <select
                value={planData.modification_level}
                onChange={(e) => setPlanData({ ...planData, modification_level: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-capgemini-blue"
              >
                <option value="Niveau 1">Niveau 1 (Light)</option>
                <option value="Niveau 2">Niveau 2 (Medium)</option>
                <option value="Niveau 3">Niveau 3 (Heavy)</option>
              </select>
            </div>

            {/* Max Budget */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Max Budget (€) <span className="text-gray-500 text-xs">(Optional)</span>
              </label>
              <input
                type="number"
                value={planData.max_budget || ''}
                onChange={(e) =>
                  setPlanData({ ...planData, max_budget: e.target.value ? parseFloat(e.target.value) : null })
                }
                placeholder="e.g., 100000"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-capgemini-blue"
              />
            </div>

            {/* Max Duration */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Max Duration (days) <span className="text-gray-500 text-xs">(Optional)</span>
              </label>
              <input
                type="number"
                value={planData.max_duration || ''}
                onChange={(e) =>
                  setPlanData({ ...planData, max_duration: e.target.value ? parseInt(e.target.value) : null })
                }
                placeholder="e.g., 120"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-capgemini-blue"
              />
            </div>

            {/* Mi-Vie */}
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Mi-Vie Modification *
              </label>
              <div className="flex items-center space-x-6 mt-3">
                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    checked={planData.is_mivie === true}
                    onChange={() => setPlanData({ ...planData, is_mivie: true })}
                    className="h-4 w-4 text-capgemini-blue focus:ring-capgemini-blue"
                  />
                  <span className="ml-2 text-sm text-gray-700 font-medium">Yes</span>
                </label>
                <label className="flex items-center cursor-pointer">
                  <input
                    type="radio"
                    checked={planData.is_mivie === false}
                    onChange={() => setPlanData({ ...planData, is_mivie: false })}
                    className="h-4 w-4 text-capgemini-blue focus:ring-capgemini-blue"
                  />
                  <span className="ml-2 text-sm text-gray-700 font-medium">No</span>
                </label>
              </div>
            </div>
          </div>

          {/* Target Markets */}
          <div className="mt-6">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Target Markets * <span className="text-gray-500 text-xs">(Select at least one)</span>
            </label>
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
              {['All Markets', 'Europe', 'USA', 'Chine', 'Japon', 'Corée'].map((market) => (
                <button
                  key={market}
                  onClick={() => handleMarketToggle(market)}
                  className={`px-4 py-2 rounded-lg border-2 transition-all duration-200 text-sm font-medium ${
                    planData.target_markets.includes(market)
                      ? 'border-capgemini-blue bg-capgemini-lightblue text-capgemini-darkblue'
                      : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                  }`}
                >
                  {market}
                </button>
              ))}
            </div>
          </div>

          {/* Modification Zones */}
          <div className="mt-6">
            <label className="block text-sm font-semibold text-gray-700 mb-3">
              Modification Zones * <span className="text-gray-500 text-xs">(Select at least one)</span>
            </label>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {availableZones.slice(0, 16).map((zone) => (
                <button
                  key={zone}
                  onClick={() => handleZoneToggle(zone)}
                  className={`px-4 py-2 rounded-lg border-2 transition-all duration-200 text-sm ${
                    planData.modification_zones.includes(zone)
                      ? 'border-capgemini-blue bg-capgemini-lightblue text-capgemini-darkblue font-semibold'
                      : 'border-gray-300 bg-white text-gray-700 hover:border-gray-400'
                  }`}
                >
                  {zone}
                </button>
              ))}
            </div>
          </div>

          {/* Strategy Selector */}
          <div className="mt-8">
            <StrategySelector
              value={planData.strategy_type}
              onChange={(strategy) => setPlanData({ ...planData, strategy_type: strategy })}
              onCustomPreferencesChange={(prefs) => setPlanData({ ...planData, custom_preferences: prefs })}
            />
          </div>

          {/* Generate Button */}
          <div className="mt-8 flex justify-center">
            <button
              onClick={handleCreatePlan}
              disabled={loading}
              className="bg-capgemini-blue text-white px-12 py-4 rounded-lg font-bold text-lg hover:bg-capgemini-darkblue transition-colors duration-200 disabled:bg-gray-400 disabled:cursor-not-allowed shadow-lg"
            >
              {loading ? (
                <span className="flex items-center">
                  <div className="spinner mr-3" style={{ width: '24px', height: '24px', borderWidth: '3px' }}></div> Creating Plan... </span> ) : ( '🚀 Generate Validation Plan' )} </button> </div> </div>
                   {/* Results Section */}
    {currentPlan && (
      <>
        {/* Summary Cards */}
        <SummaryCards summary={currentPlan.summary} />

        {/* Feasibility and Timeline */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <FeasibilityGauge
            riskScore={currentPlan.risk_score}
            feasibilityStatus={currentPlan.feasibility_status}
          />
          <TimelineChart timelines={currentPlan.summary?.timelines} />
        </div>

        {/* AI Recommendation */}
        <div className="mb-8 flex justify-center">
          <AIRecommendation planId={currentPlan.plan_id} />
        </div>

        {/* Test List */}
        <TestList tests={currentPlan.selected_tests} />

        {/* Warnings */}
        {currentPlan.warnings && (
          <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-lg p-6">
            <h3 className="text-lg font-bold text-yellow-900 mb-4">⚠️ Warnings & Suggestions</h3>
            
            {currentPlan.warnings.missing_mandatory_tests?.length > 0 && (
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-yellow-900 mb-2">Missing Mandatory Tests:</h4>
                <ul className="list-disc list-inside text-sm text-yellow-800 space-y-1">
                  {currentPlan.warnings.missing_mandatory_tests.map((test, index) => (
                    <li key={index}>{test}</li>
                  ))}
                </ul>
              </div>
            )}

            {currentPlan.warnings.suggestions?.length > 0 && (
              <div>
                <h4 className="text-sm font-semibold text-yellow-900 mb-2">Suggestions:</h4>
                <ul className="space-y-2">
                  {currentPlan.warnings.suggestions.map((suggestion, index) => (
                    <li key={index} className="text-sm text-yellow-800 flex items-start">
                      <span className="mr-2">•</span>
                      <span>{suggestion.message}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </>
    )}

    {/* Empty State */}
    {!currentPlan && !loading && (
      <div className="bg-white rounded-lg shadow-md p-12 text-center">
        <div className="text-6xl mb-4">📋</div>
        <h3 className="text-2xl font-bold text-gray-900 mb-2">Ready to Create Your Validation Plan</h3>
        <p className="text-gray-600 mb-6">
          Fill in the form above and click "Generate Validation Plan"
        </p>
        <div className="text-sm text-gray-500 space-y-2">
          <p>✓ Select vehicle category and modification level</p>
          <p>✓ Choose at least one modification zone</p>
          <p>✓ Select target markets</p>
          <p>✓ Select your validation strategy</p>
          <p>✓ Optionally set budget and timeline constraints</p>
        </div>
      </div>
    )}
  </main>

  {/* Footer */}
  <footer className="bg-capgemini-darkblue text-white py-6 mt-12">
    <div className="max-w-7xl mx-auto px-6 text-center">
      <p className="text-sm">
        © 2024 Capgemini Engineering. Mi-Vie Validation Plan Generator v1.0
      </p>
      <p className="text-xs text-gray-400 mt-2">
        Powered by AI | PostgreSQL Database | React Frontend
      </p>
    </div>
  </footer>
</div>
); }

export default App;