/**
 * FilterPanel Component
 * Left sidebar with all filtering options
 */

import React, { useState, useEffect } from 'react';
import { testsAPI } from '../services/api';

const FilterPanel = ({ onFilterChange, currentFilters }) => {
  const [filterOptions, setFilterOptions] = useState({
    vehicle_categories: [],
    markets: [],
    test_categories: [],
    zones: [],niveaux: ['Niveau 1', 'Niveau 2', 'Niveau 3'], test_locations: [], }); 
   const [error, setError] = useState(null);

// Load filter options on mount useEffect(() => { loadFilterOptions(); }, []);
  useEffect(() => {
    loadFilterOptions();
  }, []);
  const loadFilterOptions = async () => {
    try {
      const options = await testsAPI.getFilterOptions();
      setFilterOptions(options);
      setError(null);
    } catch (err) {
      setError('Failed to load filter options');
      console.error('Filter options error:', err);
    }
  };
//const loadFilterOptions = async () => { try { setLoading(true); const options = await testsAPI.getFilterOptions(); setFilterOptions(options); setError(null); } catch (err) { setError('Failed to load filter options'); console.error('Filter options error:', err); } finally { setLoading(false); } };

const handleFilterChange = (filterName, value) => { const newFilters = { ...currentFilters };

if (value === '' || value === null) {
  delete newFilters[filterName];
} else {
  newFilters[filterName] = value;
}

onFilterChange(newFilters);
};

const handleCheckboxChange = (filterName, checked) => { handleFilterChange(filterName, checked); };

const clearAllFilters = () => { onFilterChange({}); };

//if (loading) { return ( <div className="w-64 bg-white shadow-lg p-6"> <div className="flex items-center justify-center h-64"> <div className="spinner"></div> </div> </div> ); }

if (error) { return ( <div className="w-64 bg-white shadow-lg p-6"> <div className="text-red-600 text-sm">{error}</div> <button onClick={loadFilterOptions} className="mt-4 text-blue-600 hover:text-blue-800 text-sm" > Retry </button> </div> ); }

return ( <div className="w-64 bg-white shadow-lg overflow-y-auto h-full"> <div className="p-6 border-b border-gray-200"> <div className="flex items-center justify-between mb-4"> <h2 className="text-xl font-bold text-capgemini-darkblue">Filters</h2> <button onClick={clearAllFilters} className="text-xs text-gray-600 hover:text-red-600 underline" > Clear All </button> </div> </div>

  <div className="p-6 space-y-6">
    {/* Mi-Vie Filter */}
    <div>
      <label className="block text-sm font-semibold text-gray-700 mb-2">
        Mi-Vie Test
      </label>
      <select
        value={currentFilters.mivie || ''}
        onChange={(e) => handleFilterChange('mivie', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-capgemini-blue focus:border-transparent text-sm"
      >
        <option value="">All</option>
        <option value="Oui">Yes (Oui)</option>
        <option value="Non">No (Non)</option>
      </select>
    </div>

    {/* Vehicle Category */}
    <div>
      <label className="block text-sm font-semibold text-gray-700 mb-2">
        Vehicle Category
      </label>
      <select
        value={currentFilters.vehicle_category || ''}
        onChange={(e) => handleFilterChange('vehicle_category', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-capgemini-blue focus:border-transparent text-sm"
      >
        <option value="">All Categories</option>
        {filterOptions.vehicle_categories.map((cat) => (
          <option key={cat} value={cat}>
            {cat}
          </option>
        ))}
      </select>
    </div>

    {/* Target Market */}
{/* Target Market */}
<div>
  <label className="block text-sm font-semibold text-gray-700 mb-2">
    Target Market
  </label>
  <select
    value={currentFilters.market || ''}
    onChange={(e) => handleFilterChange('market', e.target.value)}
    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-capgemini-blue focus:border-transparent text-sm"
  >
    <option value="">All Markets</option>
    {filterOptions.markets.map((market) => (
      <option key={market} value={market}>
        {market}
      </option>
    ))}
  </select>
</div>

{/* Test Type (Physical/Numerical) */}
<div>
  <label className="block text-sm font-semibold text-gray-700 mb-2">
    Test Type
  </label>
  <select
    value={currentFilters.test_type || ''}
    onChange={(e) => handleFilterChange('test_type', e.target.value)}
    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-capgemini-blue focus:border-transparent text-sm"
  >
    <option value="">All Types</option>
    <option value="physical">Physical Tests</option>
    <option value="numerical">Numerical Tests</option>
  </select>
</div>

    {/* Modification Zone */}
    <div>
      <label className="block text-sm font-semibold text-gray-700 mb-2">
        Modification Zone
      </label>
      <select
        value={currentFilters.zone || ''}
        onChange={(e) => handleFilterChange('zone', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-capgemini-blue focus:border-transparent text-sm"
      >
        <option value="">All Zones</option>
        {filterOptions.zones.map((zone) => (
          <option key={zone} value={zone}>
            {zone}
          </option>
        ))}
      </select>
    </div>

    {/* Modification Level */}
    <div>
      <label className="block text-sm font-semibold text-gray-700 mb-2">
        Modification Level
      </label>
      <select
        value={currentFilters.niveau || ''}
        onChange={(e) => handleFilterChange('niveau', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-capgemini-blue focus:border-transparent text-sm"
      >
        <option value="">All Levels</option>
        {filterOptions.niveaux.map((niveau) => (
          <option key={niveau} value={niveau}>
            {niveau}
          </option>
        ))}
      </select>
    </div>

    {/* Test Category */}
    <div>
      <label className="block text-sm font-semibold text-gray-700 mb-2">
        Test Category
      </label>
      <select
        value={currentFilters.test_category || ''}
        onChange={(e) => handleFilterChange('test_category', e.target.value)}
        className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-capgemini-blue focus:border-transparent text-sm"
      >
        <option value="">All Categories</option>
        {filterOptions.test_categories.map((cat) => (
          <option key={cat} value={cat}>
            {cat}
          </option>
        ))}
      </select>
    </div>

    {/* Advanced Options */}
    <div className="pt-4 border-t border-gray-200">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">Advanced</h3>
      
      <div className="space-y-3">
        <label className="flex items-center">
          <input
            type="checkbox"
            checked={currentFilters.homologation_only || false}
            onChange={(e) => handleCheckboxChange('homologation_only', e.target.checked)}
            className="h-4 w-4 text-capgemini-blue focus:ring-capgemini-blue border-gray-300 rounded"
          />
          <span className="ml-2 text-sm text-gray-700">
            Homologation Only
          </span>
        </label>
      </div>
    </div>

    {/* Active Filters Count */}
    <div className="pt-4 border-t border-gray-200">
      <div className="text-xs text-gray-500">
        {Object.keys(currentFilters).length} active filter(s)
      </div>
    </div>
  </div>
</div>
); };

export default FilterPanel;