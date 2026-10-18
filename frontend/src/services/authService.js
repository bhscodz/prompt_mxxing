// File: frontend/src/services/authService.js
// Description: Authentication API service for SwasthyaGrid AI.
//   Handles login, logout, token refresh, profile management, and secure token storage.

const BASE_URL = '/api/v1/auth';
const ACCESS_TOKEN_KEY  = 'swasthya_access_token';
const REFRESH_TOKEN_KEY = 'swasthya_refresh_token';
const USER_KEY          = 'swasthya_user';

// ---------------------------------------------------------------------------
// Token storage (localStorage — suitable for PWA/web, not accessible to JS
// from other origins due to same-origin policy)
// ---------------------------------------------------------------------------

export const tokenStorage = {
  setTokens(accessToken, refreshToken) {
    localStorage.setItem(ACCESS_TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
  },

  getAccessToken() {
    return localStorage.getItem(ACCESS_TOKEN_KEY);
  },

  getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
  },

  setUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  getUser() {
    try {
      const raw = localStorage.getItem(USER_KEY);
      return raw ? JSON.parse(raw) : null;
    } catch {
      return null;
    }
  },

  clear() {
    localStorage.removeItem(ACCESS_TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },
};

// ---------------------------------------------------------------------------
// Fetch wrapper with automatic token injection and 401 refresh handling
// ---------------------------------------------------------------------------

let _isRefreshing = false;
let _refreshQueue = [];

async function authFetch(endpoint, options = {}) {
  const url = `${BASE_URL}${endpoint}`;
  const accessToken = tokenStorage.getAccessToken();

  const headers = {
    'Content-Type': 'application/json',
    ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(url, { ...options, headers });

  // Auto-refresh on 401 Unauthorized
  if (response.status === 401 && !options._retried) {
    if (_isRefreshing) {
      // Queue this request until refresh completes
      await new Promise((resolve) => _refreshQueue.push(resolve));
      return authFetch(endpoint, { ...options, _retried: true });
    }

    _isRefreshing = true;
    try {
      await authService.refreshAccessToken();
      _refreshQueue.forEach((resolve) => resolve());
      _refreshQueue = [];
      return authFetch(endpoint, { ...options, _retried: true });
    } catch {
      tokenStorage.clear();
      window.location.href = '/login';
      throw new Error('Session expired. Please log in again.');
    } finally {
      _isRefreshing = false;
    }
  }

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}));
    throw new Error(errData.detail || `HTTP ${response.status}: ${response.statusText}`);
  }

  // 204 No Content
  if (response.status === 204) return null;

  return response.json();
}

// ---------------------------------------------------------------------------
// Auth service methods
// ---------------------------------------------------------------------------

export const authService = {
  /**
   * Log in with username/email and password.
   * Stores tokens and user profile in localStorage.
   */
  async login(username, password) {
    const data = await fetch(`${BASE_URL}/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });

    if (!data.ok) {
      const err = await data.json().catch(() => ({}));
      throw new Error(err.detail || 'Login failed. Check your credentials.');
    }

    const result = await data.json();
    tokenStorage.setTokens(result.access_token, result.refresh_token);
    tokenStorage.setUser(result.user);
    return result;
  },

  /**
   * Log out — revoke refresh token on the server and clear local storage.
   */
  async logout() {
    const refreshToken = tokenStorage.getRefreshToken();
    if (refreshToken) {
      try {
        await authFetch('/logout', {
          method: 'POST',
          body: JSON.stringify({ refresh_token: refreshToken }),
        });
      } catch {
        // Best-effort logout; clear local storage regardless
      }
    }
    tokenStorage.clear();
  },

  /**
   * Exchange the stored refresh token for a new access token.
   */
  async refreshAccessToken() {
    const refreshToken = tokenStorage.getRefreshToken();
    if (!refreshToken) throw new Error('No refresh token available.');

    const response = await fetch(`${BASE_URL}/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      tokenStorage.clear();
      throw new Error('Token refresh failed. Please log in again.');
    }

    const data = await response.json();
    tokenStorage.setTokens(data.access_token, refreshToken);
    return data.access_token;
  },

  /**
   * Fetch the current user's profile from /auth/me.
   * Updates the cached user in localStorage.
   */
  async getMe() {
    const user = await authFetch('/me');
    if (user) tokenStorage.setUser(user);
    return user;
  },

  /**
   * Update own profile (name, email, language, password).
   */
  async updateProfile(updates) {
    const user = await authFetch('/me', {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
    if (user) tokenStorage.setUser(user);
    return user;
  },

  /** Check whether the user is currently authenticated (has a stored access token). */
  isAuthenticated() {
    return !!tokenStorage.getAccessToken();
  },

  /** Return the cached user object (may be stale — use getMe() for fresh data). */
  getCachedUser() {
    return tokenStorage.getUser();
  },

  // Admin: list users
  getUsers: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return authFetch(`/users${qs ? `?${qs}` : ''}`);
  },

  // Admin: update user role
  updateUserRole: (userId, body) =>
    authFetch(`/users/${userId}/role`, { method: 'PUT', body: JSON.stringify(body) }),

  // Admin: audit logs
  getAuditLogs: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return authFetch(`/audit-logs${qs ? `?${qs}` : ''}`);
  },

  // Register new user (admin)
  registerUser: (userData) =>
    authFetch('/register', { method: 'POST', body: JSON.stringify(userData) }),
};

/**
 * Returns the Authorization header for use in other services.
 * Imported by api.js to attach auth to all requests.
 */
export function getAuthHeaders() {
  const token = tokenStorage.getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}
