/**
 * Utility functions for formatting data
 */

/**
 * Format currency (euros)
 */
export const formatCurrency = (amount) => {
  if (amount === null || amount === undefined) return '€0';
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
};

/**
 * Format number with thousands separator
 */
export const formatNumber = (num) => {
  if (num === null || num === undefined) return '0';
  return new Intl.NumberFormat('fr-FR').format(num);
};

/**
 * Format percentage
 */
export const formatPercentage = (value, decimals = 1) => {
  if (value === null || value === undefined) return '0%';
  return `${value.toFixed(decimals)}%`;
};

/**
 * Format duration (days)
 */
export const formatDuration = (days) => {
  if (days === null || days === undefined || days === 0) return '0 days';
  if (days === 1) return '1 day';
  return `${Math.round(days)} days`;
};

/**
 * Format date
 */
export const formatDate = (dateString) => {
  if (!dateString) return 'N/A';
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
};

/**
 * Get risk color class based on score
 */
export const getRiskColorClass = (score) => {
  if (score >= 90) return 'risk-green';
  if (score >= 75) return 'risk-yellow';
  if (score >= 60) return 'risk-orange';
  return 'risk-red';
};

/**
 * Get risk status based on score
 */
export const getRiskStatus = (score) => {
  if (score >= 90) return { label: 'FEASIBLE', emoji: '✅', color: 'green' };
  if (score >= 75) return { label: 'MARGINAL', emoji: '🟡', color: 'yellow' };
  if (score >= 60) return { label: 'RISKY', emoji: '🟠', color: 'orange' };
  return { label: 'IMPOSSIBLE', emoji: '❌', color: 'red' };
};

/**
 * Get tier badge class
 */
export const getTierClass = (tier) => {
  return `tier-${tier}`;
};

/**
 * Get tier label
 */
export const getTierLabel = (tier) => {
  const labels = {
    1: 'Mandatory',
    2: 'High Priority',
    3: 'Medium Priority',
    4: 'Optional',
  };
  return labels[tier] || 'Unknown';
};

/**
 * Truncate text
 */
export const truncate = (text, maxLength = 50) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '...';
};

/**
 * Get feasibility icon
 */
export const getFeasibilityIcon = (status) => {
  const icons = {
    FEASIBLE: '✅',
    MARGINAL: '⚠️',
    RISKY: '🔴',
    IMPOSSIBLE: '❌',
  };
  return icons[status] || '❓';
};

/**
 * Format test type (Physical/Numerical)
 */
export const getTestTypeLabel = (cost, strategy) => {
  if (cost === 0) return { label: 'Numerical', color: 'blue', icon: '🖥️' };
  if (strategy?.includes('Num')) return { label: 'Hybrid', color: 'purple', icon: '🔄' };
  return { label: 'Physical', color: 'green', icon: '🔬' };
};

/**
 * Calculate percentage
 */
export const calculatePercentage = (value, total) => {
  if (total === 0) return 0;
  return (value / total) * 100;
};

/**
 * Get modification level short name
 */
export const getModificationLevelShort = (level) => {
  if (!level) return 'N/A';
  const match = level.match(/Niveau\s*(\d)/i);
  return match ? `Niv ${match[1]}` : level;
};

/**
 * Get risk score color (hex)
 */
export const getRiskScoreColor = (score) => {
  if (score >= 90) return '#10B981'; // Green
  if (score >= 75) return '#F59E0B'; // Yellow
  if (score >= 60) return '#F97316'; // Orange
  return '#DC2626'; // Red
};

/**
 * Get feasibility color class
 */
export const getFeasibilityColorClass = (status) => {
  const colors = {
    FEASIBLE: 'status-feasible',
    MARGINAL: 'status-marginal',
    RISKY: 'status-risky',
    IMPOSSIBLE: 'status-impossible',
  };
  return colors[status] || 'bg-gray-500';
};

/**
 * Get tier color class
 */
export const getTierColorClass = (tier) => {
  const colors = {
    1: 'tier-1',
    2: 'tier-2',
    3: 'tier-3',
    4: 'tier-4',
  };
  return colors[tier] || 'bg-gray-500';
};

/**
 * Truncate text
 */
export const truncateText = (text, maxLength = 50) => {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return `${text.substring(0, maxLength)}...`;
};