// File: frontend/src/context/AuthContext.jsx
// Description: React Context for authentication state management in SwasthyaGrid AI.
//   Provides: isAuthenticated, isLoading, user, login(), logout(), refreshUser()
//   All children can consume via useAuth() hook.

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authService, tokenStorage } from '../services/authService';

const AuthContext = createContext(null);

/**
 * AuthProvider wraps the application and manages authentication state.
 * On mount it tries to restore the session from localStorage by calling /auth/me.
 */
export function AuthProvider({ children }) {
  const [user, setUser]           = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  // ---------------------------------------------------------------------------
  // Restore session on page load
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const restoreSession = async () => {
      const cachedUser = tokenStorage.getUser();
      const hasToken   = authService.isAuthenticated();

      if (hasToken && cachedUser) {
        // Optimistically set cached user, then verify with server
        setUser(cachedUser);
        try {
          const freshUser = await authService.getMe();
          setUser(freshUser);
        } catch {
          // Token is invalid / expired → clear and show login
          tokenStorage.clear();
          setUser(null);
        }
      }

      setIsLoading(false);
    };

    restoreSession();
  }, []);

  // ---------------------------------------------------------------------------
  // Login
  // ---------------------------------------------------------------------------
  const login = useCallback(async (username, password) => {
    const result = await authService.login(username, password);
    setUser(result.user);
    return result;
  }, []);

  // ---------------------------------------------------------------------------
  // Logout
  // ---------------------------------------------------------------------------
  const logout = useCallback(async () => {
    await authService.logout();
    setUser(null);
  }, []);

  // ---------------------------------------------------------------------------
  // Refresh user profile (e.g. after profile update)
  // ---------------------------------------------------------------------------
  const refreshUser = useCallback(async () => {
    try {
      const freshUser = await authService.getMe();
      setUser(freshUser);
      return freshUser;
    } catch {
      return user;
    }
  }, [user]);

  // ---------------------------------------------------------------------------
  // Derived state
  // ---------------------------------------------------------------------------
  const isAuthenticated = !!user && authService.isAuthenticated();

  const value = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshUser,
    /** Convenience: check if current user has one of the given roles */
    hasRole: (...roles) => user && roles.includes(user.role),
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * useAuth — React hook to consume the AuthContext.
 * Must be used inside an AuthProvider.
 */
export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return ctx;
}

export default AuthContext;
