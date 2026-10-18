// File: frontend/src/components/Navbar.jsx
// Description: Header navbar with district selector, live telemetry status, and language switch
// Accessibility: landmarks, aria-labels on all interactive elements

import React from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import LanguageSelector from './LanguageSelector';
import { Activity, Radio, Building2 } from 'lucide-react';

export default function Navbar({
  isWsConnected = true,
  facilities = [],
  selectedFacilityId,
  onSelectFacility
}) {
  const { t } = useLanguage();

  return (
    <header className="sticky top-0 z-40 bg-white/95 backdrop-blur border-b border-slate-200" role="banner">
      {/* Skip-to-content link for keyboard/screen reader users */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 bg-teal-600 text-white px-4 py-2 rounded-lg text-sm font-semibold z-50"
      >
        Skip to main content
      </a>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand identity */}
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl bg-gradient-to-tr from-teal-700 to-teal-500 flex items-center justify-center text-white shadow-md shadow-teal-700/20"
            aria-hidden="true"
          >
            <Activity className="w-6 h-6 stroke-[2.5]" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h1 className="text-lg font-extrabold text-slate-900 tracking-tight">
                {t('appTitle')}
              </h1>
              <span className="text-[10px] font-bold px-1.5 py-0.5 rounded bg-teal-100 text-teal-800 uppercase tracking-wide" aria-label="Version 1.0 AI">
                v1.0 AI
              </span>
            </div>
            <p className="text-xs text-slate-500 font-medium">
              {t('districtTag')} • Pune Rural & Western Ghats
            </p>
          </div>
        </div>

        {/* Center / Right controls */}
        <nav aria-label="Header controls" className="flex items-center gap-3">
          {/* Facility context dropdown */}
          <div className="hidden md:flex items-center gap-2 border border-slate-200 rounded-lg px-2.5 py-1.5 bg-slate-50 text-xs">
            <Building2 className="w-3.5 h-3.5 text-slate-500" aria-hidden="true" />
            <label htmlFor="facility-select" className="sr-only">Select health facility</label>
            <select
              id="facility-select"
              value={selectedFacilityId || ''}
              onChange={(e) => onSelectFacility(e.target.value || null)}
              aria-label="Select health facility"
              className="bg-transparent font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-teal-500 cursor-pointer rounded"
            >
              <option value="">{t('allCentres')}</option>
              {facilities.map((fac) => (
                <option key={fac.id} value={fac.id}>
                  {fac.name} ({fac.facility_type})
                </option>
              ))}
            </select>
          </div>

          {/* WebSocket Live Status */}
          <div
            role="status"
            aria-label={isWsConnected ? 'Live data connection active' : 'Data connection offline'}
            aria-live="polite"
            className="flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-slate-100 border border-slate-200"
          >
            <span className="relative flex h-2 w-2" aria-hidden="true">
              {isWsConnected && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              )}
              <span className={`relative inline-flex rounded-full h-2 w-2 ${isWsConnected ? 'bg-emerald-500' : 'bg-rose-500'}`}></span>
            </span>
            <span className={isWsConnected ? 'text-emerald-700' : 'text-rose-600'}>
              {isWsConnected ? t('liveStatus') : t('offlineStatus')}
            </span>
          </div>

          {/* Language Selector */}
          <LanguageSelector />
        </nav>
      </div>
    </header>
  );
}

