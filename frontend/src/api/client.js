const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

/**
 * Base API client
 */
export async function apiClient(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`;
  
  const headers = { ...options.headers };
  
  // Only set application/json if body is not FormData
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `Request failed with status ${response.status}`);
    }
    if (response.status === 204) {
      return null;
    }
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    const text = await response.text();
    try {
      return text ? JSON.parse(text) : null;
    } catch {
      return text;
    }
  } catch (error) {
    console.error(`API request error on ${url}:`, error);
    throw error;
  }
}

/**
 * Health check service
 */
export const healthService = {
  checkHealth: () => apiClient('/health'),
};

/**
 * Company management service
 */
export const companyService = {
  getCompanies: (includeInactive = true) => 
    apiClient(`/companies?include_inactive=${includeInactive}`),
  
  getCompany: (id) => 
    apiClient(`/companies/${id}`),
  
  createCompany: (data) => 
    apiClient('/companies', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  updateCompany: (id, data) => 
    apiClient(`/companies/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),
  
  deactivateCompany: (id) => 
    apiClient(`/companies/${id}`, {
      method: 'DELETE',
    }),

  getMasterDocInfo: (id) =>
    apiClient(`/companies/${id}/document/info`),

  getMasterDocxUrl: (id) =>
    `${API_BASE_URL}/companies/${id}/document/word`,

  getMasterPdfUrl: (id) =>
    `${API_BASE_URL}/companies/${id}/document/pdf`,
};

/**
 * Duty Slip management service
 */
export const dutySlipService = {
  getDutySlips: (params = {}) => {
    const query = new URLSearchParams();
    if (typeof params === 'string') {
      query.append('company_id', params);
    } else if (params && typeof params === 'object') {
      if (params.companyId || params.company_id) query.append('company_id', params.companyId || params.company_id);
      if (params.status) query.append('status', params.status);
      if (params.search) query.append('search', params.search);
    }
    const queryString = query.toString();
    return apiClient(`/duty-slips${queryString ? `?${queryString}` : ''}`);
  },


  getDutySlip: (id) => 
    apiClient(`/duty-slips/${id}`),

  createDutySlip: (formData) => 
    apiClient('/duty-slips', {
      method: 'POST',
      body: formData,
    }),

  updateDutySlip: (id, data) => 
    apiClient(`/duty-slips/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    }),

  deleteDutySlip: (id) => 
    apiClient(`/duty-slips/${id}`, {
      method: 'DELETE',
    }),

  getScanUrl: (dutySlipId, side) => 
    `${API_BASE_URL}/duty-slips/${dutySlipId}/${side}`,

  getFrontImageUrl: (dutySlipId) =>
    `${API_BASE_URL}/duty-slips/${dutySlipId}/front`,

  getBackImageUrl: (dutySlipId) =>
    `${API_BASE_URL}/duty-slips/${dutySlipId}/back`,


  generateWordBill: (dutySlipId) =>
    apiClient(`/duty-slips/${dutySlipId}/generate-word`, {
      method: 'POST',
    }),

  getWordBillUrl: (dutySlipId) =>
    `${API_BASE_URL}/duty-slips/${dutySlipId}/word-bill`,
};


/**
 * OCR / Vision Extraction service
 */
export const extractionService = {
  extract: (dutySlipId) => 
    apiClient(`/duty-slips/${dutySlipId}/extract`, {
      method: 'POST',
    }),

  getExtraction: (dutySlipId) => 
    apiClient(`/duty-slips/${dutySlipId}/extraction`),

  updateExtraction: (dutySlipId, fields, reviewer = 'reviewer', notes = null) =>
    apiClient(`/duty-slips/${dutySlipId}/extraction`, {
      method: 'PUT',
      body: JSON.stringify({ fields, reviewer, notes }),
    }),

  verifyExtraction: (dutySlipId, reviewer = 'reviewer', notes = null) =>
    apiClient(`/duty-slips/${dutySlipId}/verify`, {
      method: 'POST',
      body: JSON.stringify({ reviewer, notes }),
    }),
};

