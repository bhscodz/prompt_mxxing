// File: frontend/src/components/Sidebar.jsx
// Description: Sidebar navigation menu for SwasthyaGrid AI Phase 2
// Groups nav items into: Core Management | Staff | AI & Analytics | Finance
// Uses react-router-dom NavLink for active state detection

import React from 'react';
import { NavLink } from 'react-router-dom';
import { useLanguage } from '../i18n/LanguageContext';
import {
  // Core Management icons
  LayoutDashboard,
  Users,
  Pill,
  BedDouble,
  // Staff icons
  Stethoscope,
  FlaskConical,
  CalendarCheck,
  // AI & Analytics icons
  TrendingUp,
  TrendingUpIcon,
  ArrowLeftRight,
  ShieldAlert,
  MessageSquare,
  // Finance icons
  IndianRupee,
  BarChart3
} from 'lucide-react';

/**
 * NavItem — renders a single sidebar link using react-router NavLink.
 * Active state is detected by URL match rather than manual tab state.
 */
function NavItem({ to, icon: Icon, label, badge, badgeColor }) {
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-semibold transition ${
          isActive
            ? 'bg-teal-600 text-white shadow-sm shadow-teal-600/30'
            : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
        }`
      }
    >
      {({ isActive }) => (
        <>
          <div className="flex items-center gap-3">
            <Icon className={`w-4 h-4 ${isActive ? 'text-white' : 'text-slate-400'}`} aria-hidden="true" />
            <span className="truncate">{label}</span>
          </div>
          {badge > 0 && (
            <span
              aria-label={`${badge} ${label} notifications`}
              className={`text-[11px] font-bold px-2 py-0.5 rounded-full ${
                isActive
                  ? 'bg-white/20 text-white'
                  : badgeColor === 'red'
                  ? 'bg-rose-100 text-rose-700'
                  : badgeColor === 'amber'
                  ? 'bg-amber-100 text-amber-800'
                  : 'bg-teal-100 text-teal-800'
              }`}
            >
              {badge}
            </span>
          )}
        </>
      )}
    </NavLink>
  );
}

/**
 * SectionLabel — renders a small uppercase group header between nav sections.
 */
function SectionLabel({ label }) {
  return (
    <p className="px-3.5 pt-4 pb-1 text-[10px] font-bold uppercase tracking-widest text-slate-400 select-none">
      {label}
    </p>
  );
}

/**
 * Sidebar — full Phase 2 left navigation sidebar.
 * Groups:
 *   Core Management  → Dashboard, Patients, Inventory, Beds
 *   Staff            → Attendance, Diagnostics, Leave Management
 *   AI & Analytics   → AI Forecasts (legacy), Forecasting (Phase 2), Redistribution, Interventions, AI Assistant
 *   Finance          → Economics Dashboard
 */
export default function Sidebar({ counts = {} }) {
  const { t } = useLanguage();

  return (
    <aside
      className="w-64 bg-white border-r border-slate-200 flex flex-col shrink-0 min-h-[calc(100vh-4rem)]"
      aria-label="Main navigation"
      role="navigation"
    >
      <div className="p-4 space-y-0.5">

        {/* ── Group 1: Core Management ─────────────────────────────── */}
        <SectionLabel label="Core Management" />
        <NavItem
          to="/dashboard"
          icon={LayoutDashboard}
          label={t('navDashboard')}
        />
        <NavItem
          to="/patients"
          icon={Users}
          label={t('navCRM')}
          badge={counts.waitingPatients}
          badgeColor="teal"
        />
        <NavItem
          to="/inventory"
          icon={Pill}
          label={t('navInventory')}
          badge={counts.criticalStocks}
          badgeColor="red"
        />
        <NavItem
          to="/beds"
          icon={BedDouble}
          label={t('navBeds')}
        />

        {/* ── Group 2: Staff ───────────────────────────────────────── */}
        <SectionLabel label="Staff" />
        <NavItem
          to="/attendance"
          icon={Stethoscope}
          label={t('navAttendance')}
        />
        <NavItem
          to="/diagnostics"
          icon={FlaskConical}
          label={t('navDiagnostics')}
        />
        {/* Phase 2: Leave Management */}
        <NavItem
          to="/leave"
          icon={CalendarCheck}
          label="Leave Management"
        />

        {/* ── Group 3: AI & Analytics ──────────────────────────────── */}
        <SectionLabel label="AI & Analytics" />
        {/* Legacy Phase 1 Transformer Forecasts */}
        <NavItem
          to="/forecasts"
          icon={TrendingUp}
          label={t('navForecast')}
        />
        {/* Phase 2: Advanced Forecasting Engine */}
        <NavItem
          to="/forecasting"
          icon={BarChart3}
          label="Advanced Forecasting"
        />
        <NavItem
          to="/redistribution"
          icon={ArrowLeftRight}
          label={t('navRedistribution')}
          badge={counts.transfersPending}
          badgeColor="amber"
        />
        <NavItem
          to="/interventions"
          icon={ShieldAlert}
          label={t('navInterventions')}
          badge={counts.criticalAlerts}
          badgeColor="red"
        />
        {/* Phase 2: Multilingual AI Assistant */}
        <NavItem
          to="/ai-agent"
          icon={MessageSquare}
          label="AI Assistant"
        />

        {/* ── Group 4: Finance ─────────────────────────────────────── */}
        <SectionLabel label="Finance" />
        {/* Phase 2: Economics & Budget Dashboard */}
        <NavItem
          to="/economics"
          icon={IndianRupee}
          label="Economics"
        />
      </div>

      {/* Footer status widget */}
      <div className="mt-auto p-4 border-t border-slate-100">
        <div className="bg-slate-50 rounded-xl p-3 border border-slate-200 text-xs">
          <p className="font-bold text-slate-800">SwasthyaGrid Engine</p>
          <p className="text-slate-500 mt-0.5">Phase 2 · AI Agent · Economics</p>
          <div className="mt-2 flex items-center gap-1.5 text-[11px] font-medium text-teal-700">
            <span className="w-1.5 h-1.5 rounded-full bg-teal-600" />
            <span>All 6 Health Centrals Synced</span>
          </div>
        </div>
      </div>
    </aside>
  );
}
