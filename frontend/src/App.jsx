// File: frontend/src/App.jsx
// Description: Root React Application with Phase 2 routing - Auth, Leave, Forecasting, AI Agent, Economics
// Uses react-router-dom v6 BrowserRouter with protected routes via AuthContext

import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LanguageProvider } from './i18n/LanguageContext';
import { AuthProvider, useAuth } from './context/AuthContext';
import { api } from './services/api';
import { wsService } from './services/websocket';

// Layout components
import Navbar from './components/Navbar';
import Sidebar from './components/Sidebar';

// ── Phase 1 Pages ──────────────────────────────────────────────────────────────
import Dashboard from './pages/Dashboard';
import PatientCRM from './pages/PatientCRM';
import InventoryStock from './pages/InventoryStock';
import BedManagement from './pages/BedManagement';
import DoctorAttendance from './pages/DoctorAttendance';
import DiagnosticAudits from './pages/DiagnosticAudits';
import AIForecasts from './pages/AIForecasts';
import RedistributionEngine from './pages/RedistributionEngine';
import DistrictInterventions from './pages/DistrictInterventions';

// ── Phase 2 Pages ──────────────────────────────────────────────────────────────
import LoginPage from './pages/LoginPage';
import LeaveManagementPage from './pages/LeaveManagementPage';
import AIAgentChat from './pages/AIAgentChat';
import EconomicsDashboard from './pages/EconomicsDashboard';
import ForecastingPage from './pages/ForecastingPage';

/**
 * ProtectedRoute — wraps any route that requires authentication.
 * Redirects unauthenticated users to /login preserving the intended URL.
 */
function ProtectedRoute({ children }) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    // Show a minimal loading spinner while auth state is resolved from storage
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-4 border-teal-500 border-t-transparent rounded-full animate-spin" />
          <p className="text-sm text-slate-500 font-medium">Loading SwasthyaGrid…</p>
        </div>
      </div>
    );
  }

  return isAuthenticated ? children : <Navigate to="/login" replace />;
}

/**
 * AppShell — the main authenticated layout shell.
 * Renders Navbar + Sidebar + dynamic page content.
 * Keeps badge counts and WebSocket state at this level so all children share them.
 */
function AppShell() {
  const [facilities, setFacilities] = useState([]);
  const [selectedFacilityId, setSelectedFacilityId] = useState(null);
  const [isWsConnected, setIsWsConnected] = useState(false);

  // Badge notification counts shown in Sidebar
  const [badgeCounts, setBadgeCounts] = useState({
    waitingPatients: 0,
    criticalStocks: 0,
    transfersPending: 0,
    criticalAlerts: 0
  });

  // Load the list of all facilities for the district-selector dropdown
  const fetchFacilities = async () => {
    try {
      const data = await api.getFacilities();
      setFacilities(data);
    } catch (err) {
      console.error('Error loading facilities:', err);
    }
  };

  // Refresh live badge counts (waiting patients, critical stocks, transfers, alerts)
  const fetchBadgeCounts = async () => {
    try {
      const [sum, recs, alerts, visits] = await Promise.all([
        api.getDistrictSummary().catch(() => ({})),
        api.getRedistributionRecommendations().catch(() => []),
        api.getInterventions({ status: 'pending_review' }).catch(() => []),
        api.getOpdVisits({ status: 'waiting' }).catch(() => [])
      ]);

      setBadgeCounts({
        waitingPatients: visits.length,
        criticalStocks: sum.critical_stockout_items || 0,
        transfersPending: recs.length,
        criticalAlerts: alerts.filter(a => a.severity === 'critical').length
      });
    } catch (err) {
      console.error('Badge counts error:', err);
    }
  };

  useEffect(() => {
    fetchFacilities();
    fetchBadgeCounts();

    // Connect to the district live WebSocket feed
    wsService.connect();
    const unsubStatus = wsService.onStatusChange(setIsWsConnected);
    const unsubMsg = wsService.subscribe(() => {
      // Any live event triggers a badge refresh
      fetchBadgeCounts();
    });

    // Periodic refresh every 20 seconds as fallback
    const interval = setInterval(fetchBadgeCounts, 20000);

    return () => {
      unsubStatus();
      unsubMsg();
      clearInterval(interval);
    };
  }, []);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      {/* Top Navigation Bar */}
      <Navbar
        isWsConnected={isWsConnected}
        facilities={facilities}
        selectedFacilityId={selectedFacilityId}
        onSelectFacility={setSelectedFacilityId}
      />

      {/* Main Body: Sidebar + Content */}
      <div className="flex-1 flex max-w-7xl w-full mx-auto">
        {/* Left Navigation Sidebar */}
        <Sidebar counts={badgeCounts} />

        {/* Content Panel — react-router renders page components here */}
        <main className="flex-1 p-6 overflow-y-auto">
          <Routes>
            {/* Default: redirect / to /dashboard */}
            <Route path="/" element={<Navigate to="/dashboard" replace />} />

            {/* ── Phase 1 Routes ───────────────────────────────────── */}
            <Route
              path="/dashboard"
              element={
                <Dashboard
                  facilities={facilities}
                  selectedFacilityId={selectedFacilityId}
                  onSelectFacility={setSelectedFacilityId}
                />
              }
            />
            <Route
              path="/patients"
              element={
                <PatientCRM
                  facilities={facilities}
                  selectedFacilityId={selectedFacilityId}
                />
              }
            />
            <Route
              path="/inventory"
              element={
                <InventoryStock
                  facilities={facilities}
                  selectedFacilityId={selectedFacilityId}
                />
              }
            />
            <Route
              path="/beds"
              element={
                <BedManagement
                  facilities={facilities}
                  selectedFacilityId={selectedFacilityId}
                />
              }
            />
            <Route
              path="/attendance"
              element={
                <DoctorAttendance
                  facilities={facilities}
                  selectedFacilityId={selectedFacilityId}
                />
              }
            />
            <Route
              path="/diagnostics"
              element={
                <DiagnosticAudits
                  facilities={facilities}
                  selectedFacilityId={selectedFacilityId}
                />
              }
            />
            {/* Legacy AI Forecasts page (Phase 1 transformer visualizer) */}
            <Route
              path="/forecasts"
              element={
                <AIForecasts
                  facilities={facilities}
                  selectedFacilityId={selectedFacilityId}
                />
              }
            />
            <Route
              path="/redistribution"
              element={<RedistributionEngine facilities={facilities} />}
            />
            <Route
              path="/interventions"
              element={<DistrictInterventions facilities={facilities} />}
            />

            {/* ── Phase 2 Routes ───────────────────────────────────── */}
            {/* Advanced Forecasting: PatchTST + XGBoost + ARIMA ensemble */}
            <Route
              path="/forecasting"
              element={
                <ForecastingPage
                  facilities={facilities}
                  selectedFacilityId={selectedFacilityId}
                />
              }
            />
            {/* Staff Leave Management & Approval Workflow */}
            <Route path="/leave" element={<LeaveManagementPage facilities={facilities} />} />
            {/* Multilingual AI Health Assistant Chat */}
            <Route
              path="/ai-agent"
              element={
                <AIAgentChat
                  facilities={facilities}
                  selectedFacilityId={selectedFacilityId}
                />
              }
            />
            {/* Economics: Budget · Expenditure · Purchase Orders */}
            <Route
              path="/economics"
              element={
                <EconomicsDashboard
                  facilities={facilities}
                  selectedFacilityId={selectedFacilityId}
                />
              }
            />

            {/* Catch-all: redirect unknown paths to dashboard */}
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </div>
  );
}

/**
 * App — root component.
 * Wraps everything in BrowserRouter, LanguageProvider, and AuthProvider.
 * Public routes (/login) are outside ProtectedRoute.
 */
export default function App() {
  return (
    <BrowserRouter>
      <LanguageProvider>
        <AuthProvider>
          <Routes>
            {/* Public route — no auth required */}
            <Route path="/login" element={<LoginPage />} />

            {/* All other routes require authentication */}
            <Route
              path="/*"
              element={
                <ProtectedRoute>
                  <AppShell />
                </ProtectedRoute>
              }
            />
          </Routes>
        </AuthProvider>
      </LanguageProvider>
    </BrowserRouter>
  );
}
