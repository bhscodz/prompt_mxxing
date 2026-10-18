// File: frontend/src/components/ProtectedRoute.jsx
// Description: Higher-order route guard for SwasthyaGrid AI.
//   Redirects unauthenticated users to /login and optionally enforces role checks.

import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

/**
 * ProtectedRoute
 *
 * Props:
 *   children   — the page component to render when access is granted
 *   roles      — optional array of allowed role strings; if omitted, any auth user can access
 *
 * Behaviour:
 *   - While auth is loading → shows a spinner
 *   - If not authenticated → redirects to /login (preserving the intended URL)
 *   - If authenticated but wrong role → redirects to /dashboard with a flash-state
 *   - Otherwise → renders children
 */
export default function ProtectedRoute({ children, roles }) {
  const { isAuthenticated, isLoading, user } = useAuth();
  const location = useLocation();

  // Show loading spinner while restoring session
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-500 font-medium">Loading SwasthyaGrid…</p>
        </div>
      </div>
    );
  }

  // Not authenticated → send to login, preserving current path
  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Role check (optional)
  if (roles && roles.length > 0 && user) {
    if (!roles.includes(user.role)) {
      return (
        <Navigate
          to="/dashboard"
          state={{ accessDenied: true, requiredRoles: roles }}
          replace
        />
      );
    }
  }

  return children;
}
