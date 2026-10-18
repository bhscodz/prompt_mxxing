// File: frontend/src/components/AlertBanner.jsx
// Description: Emergency alert notification banner for district distress and stockout hazards
// Accessibility: role="alert" + aria-live="assertive" for screen reader announcements

import React from 'react';
import { AlertTriangle, ArrowRight, ShieldAlert } from 'lucide-react';

export default function AlertBanner({ alerts = [], onNavigateToInterventions }) {
  if (!alerts || alerts.length === 0) return null;

  const criticalAlert = alerts.find(a => a.severity === 'critical') || alerts[0];

  return (
    <div
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
      className="bg-gradient-to-r from-red-600 to-rose-700 text-white px-4 py-3 rounded-2xl shadow-lg mb-6 flex flex-col md:flex-row items-start md:items-center justify-between gap-3 animate-in fade-in slide-in-from-top-3"
    >
      <div className="flex items-center gap-3">
        <div className="p-2 bg-white/20 rounded-xl backdrop-blur-sm animate-pulse" aria-hidden="true">
          <ShieldAlert className="w-5 h-5 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-bold uppercase tracking-wider bg-white/25 px-2 py-0.5 rounded-full">
              District Emergency Alert ({alerts.length})
            </span>
            <span className="text-xs font-semibold text-rose-100">{criticalAlert.title}</span>
          </div>
          <p className="text-xs text-white/90 mt-0.5 max-w-3xl line-clamp-1">
            {criticalAlert.description}
          </p>
        </div>
      </div>

      <button
        onClick={onNavigateToInterventions}
        aria-label={`Review and intervene for: ${criticalAlert.title}`}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white text-red-700 hover:bg-rose-50 focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-red-600 text-xs font-bold transition shadow-sm whitespace-nowrap self-end md:self-center"
      >
        <span>Review & Intervene</span>
        <ArrowRight className="w-3.5 h-3.5" aria-hidden="true" />
      </button>
    </div>
  );
}

