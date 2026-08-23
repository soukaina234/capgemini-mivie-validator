/**
 * API Service - Handles all backend communication
 */

import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// ============================================
// TESTS API
// ============================================

export const testsAPI = {
  /**
   * Get filtered list of tests
   */
  getTests: async (filters = {}, pagination = { skip: 0, limit: 100 }) => {
    const params = { ...filters, ...pagination };
    const response = await api.get('/tests', { params });
    return response.data;
  },

  /**
   * Get filter options for dropdowns
   */
  getFilterOptions: async () => {
    const response = await api.get('/tests/filter-options');
    return response.data;
  },

  /**
   * Get single test details
   */
  getTestById: async (testId) => {
    const response = await api.get(`/tests/${testId}`);
    return response.data;
  },

  /**
   * Get test statistics
   */
  getStatistics: async () => {
    const response = await api.get('/tests/stats/summary');
    return response.data;
  },
};

// ============================================
// VALIDATION PLANS API
// ============================================

export const plansAPI = {
  /**
   * Create new validation plan
   */
  createPlan: async (planData) => {
    const response = await api.post('/plans/create', planData);
    return response.data;
  },

  /**
   * Get plan by ID
   */
  getPlanById: async (planId) => {
    const response = await api.get(`/plans/${planId}`);
    return response.data;
  },

  /**
   * List all plans
   */
  listPlans: async (pagination = { skip: 0, limit: 50 }) => {
    const response = await api.get('/plans', { params: pagination });
    return response.data;
  },

  /**
   * Delete plan
   */
  deletePlan: async (planId) => {
    const response = await api.delete(`/plans/${planId}`);
    return response.data;
  },

  /**
   * Compare all strategies
   */
  compareStrategies: async (planData) => {
    const response = await api.post('/plans/compare-strategies', planData);
    return response.data;
  },
};

// ============================================
// AI RECOMMENDATIONS API
// ============================================

export const aiAPI = {
  /**
   * Get AI recommendation
   */
  getRecommendation: async (planId, requestType) => {
    const response = await api.post('/ai/recommend', {
      plan_id: planId,
      request_type: requestType,
    });
    return response.data;
  },

  /**
   * Get batch recommendations (all types)
   */
  getBatchRecommendations: async (planId) => {
    const response = await api.post('/ai/batch-recommend', null, {
      params: { plan_id: planId },
    });
    return response.data;
  },

  /**
   * Get AI usage statistics
   */
  getUsageStats: async () => {
    const response = await api.get('/ai/usage');
    return response.data;
  },
};

// ============================================
// DATA UPLOAD API
// ============================================

export const uploadAPI = {
  /**
   * Upload CSV file
   */
  uploadCSV: async (file, onUploadProgress) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post('/upload/csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress,
    });
    return response.data;
  },

  /**
   * Get CSV template info
   */
  getTemplate: async () => {
    const response = await api.get('/upload/template');
    return response.data;
  },

  /**
   * Get validation rules
   */
  getValidationRules: async () => {
    const response = await api.get('/upload/validation-rules');
    return response.data;
  },
};

// ============================================
// EXPORT API
// ============================================

export const exportAPI = {
  /**
   * Download PDF report
   */
  downloadPDF: async (planId) => {
    const response = await api.get(`/export/pdf/${planId}`, {
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `validation_plan_${planId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return true;
  },

  /**
   * Download Excel report
   */
  downloadExcel: async (planId) => {
    const response = await api.get(`/export/excel/${planId}`, {
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `validation_plan_${planId}.xlsx`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    
    return true;
  },

  /**
   * Get available export formats
   */
  getFormats: async () => {
    const response = await api.get('/export/formats');
    return response.data;
  },
};

// ============================================
// HEALTH CHECK API
// ============================================

export const healthAPI = {
  /**
   * Check API health
   */
  checkHealth: async () => {
    const response = await api.get('/health', {
      baseURL: API_BASE_URL.replace('/api', ''),
    });
    return response.data;
  },
};

export default api;