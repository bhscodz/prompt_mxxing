// File: frontend/src/services/api.js
// Description: Centralized REST API service with error handling for SwasthyaGrid AI

const BASE_URL = '/api/v1';

async function request(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  try {
    const response = await fetch(url, { ...options, headers });
    if (!response.ok) {
      const errData = await response.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP Error ${response.status}: ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`API Error on ${url}:`, error);
    throw error;
  }
}

export const api = {
  // Facilities
  getFacilities: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/facilities${qs ? `?${qs}` : ''}`);
  },
  getDistrictSummary: () => request('/facilities/summary'),
  createFacility: (data) => request('/facilities', { method: 'POST', body: JSON.stringify(data) }),

  // Inventory & Early Warnings
  getStocks: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/inventory${qs ? `?${qs}` : ''}`);
  },
  getEarlyWarnings: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/inventory/warnings${qs ? `?${qs}` : ''}`);
  },
  recordStockTransaction: (data) => request('/inventory/transaction', { method: 'POST', body: JSON.stringify(data) }),

  // Patient CRM & OPD Queue
  getPatients: (query = '') => request(`/crm/patients${query ? `?query=${encodeURIComponent(query)}` : ''}`),
  createPatient: (data) => request('/crm/patients', { method: 'POST', body: JSON.stringify(data) }),
  getOpdVisits: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/crm/opd-visits${qs ? `?${qs}` : ''}`);
  },
  registerOpdVisit: (data) => request('/crm/opd-visits', { method: 'POST', body: JSON.stringify(data) }),
  updateOpdVisit: (visitId, data) => request(`/crm/opd-visits/${visitId}`, { method: 'PATCH', body: JSON.stringify(data) }),

  // Beds Management
  getBeds: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/beds${qs ? `?${qs}` : ''}`);
  },
  allocateBed: (bedId, data) => request(`/beds/${bedId}/allocate`, { method: 'POST', body: JSON.stringify(data) }),
  dischargeBed: (bedId) => request(`/beds/${bedId}/discharge`, { method: 'POST' }),

  // Staff & Attendance
  getStaff: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/attendance${qs ? `?${qs}` : ''}`);
  },
  recordPunch: (data) => request('/attendance/punch', { method: 'POST', body: JSON.stringify(data) }),

  // Diagnostic Test Audits
  getDiagnosticAudits: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/diagnostic-tests${qs ? `?${qs}` : ''}`);
  },
  updateDiagnosticAudit: (testId, data) => request(`/diagnostic-tests/${testId}`, { method: 'PATCH', body: JSON.stringify(data) }),

  // AI Time Series Transformer Forecasts
  getAiForecast: (facilityId, metricType = 'patient_footfall', itemName = null) => {
    let url = `/ai/forecast?facility_id=${facilityId}&metric_type=${metricType}`;
    if (itemName) url += `&item_name=${encodeURIComponent(itemName)}`;
    return request(url);
  },

  // Smart Redistribution Engine
  getRedistributionRecommendations: () => request('/redistribution/recommendations'),
  getTransfers: (status = null) => request(`/redistribution/transfers${status ? `?status=${status}` : ''}`),
  createTransfer: (data) => request('/redistribution/transfers', { method: 'POST', body: JSON.stringify(data) }),
  executeTransferAction: (transferId, action, actorName) => request(`/redistribution/transfers/${transferId}/action`, {
    method: 'POST',
    body: JSON.stringify({ action, actor_name: actorName })
  }),

  // District Interventions
  getInterventions: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return request(`/interventions${qs ? `?${qs}` : ''}`);
  },
  createInterventionAlert: (data) => request('/interventions', { method: 'POST', body: JSON.stringify(data) }),
  dispatchInterventionAction: (alertId, data) => request(`/interventions/${alertId}/dispatch`, {
    method: 'POST',
    body: JSON.stringify(data)
  })
};

