/**
 * NPN Bank Employee Dashboard — API Service
 * Centralised fetch wrapper with JWT auth for all backend calls.
 */

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// ── Token helpers ────────────────────────────────────────────────────────────

export const getToken = () => localStorage.getItem('npn_token');
export const setToken = (token) => localStorage.setItem('npn_token', token);
export const clearToken = () => localStorage.removeItem('npn_token');
export const getEmployee = () => {
  try {
    return JSON.parse(localStorage.getItem('npn_employee') || 'null');
  } catch {
    return null;
  }
};
export const setEmployee = (emp) =>
  localStorage.setItem('npn_employee', JSON.stringify(emp));
export const clearEmployee = () => localStorage.removeItem('npn_employee');

// ── Core fetch wrapper ───────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  };

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers });

  if (res.status === 401) {
    clearToken();
    clearEmployee();
    // Reload to trigger the login screen
    window.location.reload();
    return;
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `API error ${res.status}`);
  }

  return res.json();
}

// ── Auth ─────────────────────────────────────────────────────────────────────

/**
 * Login with email + password.
 * Uses OAuth2PasswordRequestForm (application/x-www-form-urlencoded).
 */
export async function login(email, password) {
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch(`${BASE_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: body.toString(),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(err.detail || 'Login failed');
  }

  const data = await res.json();
  setToken(data.access_token);
  setEmployee({
    name:  data.employee_name,
    role:  data.employee_role,
    email: data.employee_email,
  });
  return data;
}

export function logout() {
  clearToken();
  clearEmployee();
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

/** GET /api/dashboard/stats */
export const getDashboardStats = () => apiFetch('/api/dashboard/stats');

// ── Customers ─────────────────────────────────────────────────────────────────

/**
 * GET /api/customers
 * @param {Object} params - { search, segment, limit, offset }
 */
export const getCustomers = (params = {}) => {
  const qs = new URLSearchParams();
  if (params.search) qs.set('search', params.search);
  if (params.segment && params.segment !== 'ALL') qs.set('segment', params.segment);
  if (params.limit !== undefined) qs.set('limit', params.limit);
  if (params.offset !== undefined) qs.set('offset', params.offset);
  return apiFetch(`/api/customers?${qs.toString()}`);
};

/** GET /api/customers/{id}/analyze */
export const analyzeCustomer = (customerId) =>
  apiFetch(`/api/customers/${customerId}/analyze`);

// ── Segments ─────────────────────────────────────────────────────────────────

/** GET /api/segments */
export const getSegments = () => apiFetch('/api/segments');

// ── Campaigns ─────────────────────────────────────────────────────────────────

/** GET /api/campaigns */
export const getCampaigns = () => apiFetch('/api/campaigns');

/**
 * POST /api/campaigns
 * @param {Object} campaign
 */
export const createCampaign = (campaign) =>
  apiFetch('/api/campaigns', {
    method: 'POST',
    body: JSON.stringify(campaign),
  });

/**
 * PATCH /api/campaigns/{id}/status
 * @param {string} id
 * @param {string} status
 */
export const updateCampaignStatus = (id, status) =>
  apiFetch(`/api/campaigns/${id}/status`, {
    method: 'PATCH',
    body: JSON.stringify({ status }),
  });

/**
 * POST /api/campaigns/generate-content
 * @param {Object} params - { product, segment, tone }
 */
export const generateCampaignContent = (params) =>
  apiFetch('/api/campaigns/generate-content', {
    method: 'POST',
    body: JSON.stringify(params),
  });

// ── Analytics ─────────────────────────────────────────────────────────────────

/** GET /api/analytics */
export const getAnalytics = () => apiFetch('/api/analytics');

// ── Personalised Campaign APIs ────────────────────────────────────────────────

/**
 * GET /api/campaigns/{product}/customers
 * Returns all NBO customers for a given product (auto-population)
 */
export const getCampaignCustomers = (product, limit = 200) => {
  const qs = new URLSearchParams({ limit });
  return apiFetch(`/api/campaigns/${encodeURIComponent(product)}/customers?${qs}`);
};

/**
 * POST /api/campaigns/generate-personalised-message
 * Generate Groq-powered age-aware personalised email or SMS
 * @param {Object} params - { customer_id, product, channel, age_group }
 */
export const generatePersonalisedMessage = (params) =>
  apiFetch('/api/campaigns/generate-personalised-message', {
    method: 'POST',
    body: JSON.stringify(params),
  });

/**
 * POST /api/campaigns/{id}/analytics/event
 * Record an analytics event for a campaign
 */
export const recordCampaignEvent = (campaignId, event) =>
  apiFetch(`/api/campaigns/${campaignId}/analytics/event`, {
    method: 'POST',
    body: JSON.stringify(event),
  });

/**
 * GET /api/campaigns/{id}/analytics
 * Get full analytics for a specific campaign
 */
export const getCampaignAnalytics = (campaignId) =>
  apiFetch(`/api/campaigns/${campaignId}/analytics`);

/**
 * GET /api/campaigns/insights
 * AI self-learning insights across all campaigns
 */
export const getCampaignInsights = () => apiFetch('/api/campaigns/insights');

// ── Health ────────────────────────────────────────────────────────────────────

export const healthCheck = () => apiFetch('/health');
