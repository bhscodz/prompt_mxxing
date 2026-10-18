// File: frontend/src/components/StatCard.jsx
// Description: Stat and KPI card component with color accents and status tags
// Accessibility: aria-label on card, aria-hidden on decorative icons

import React from 'react';

export default function StatCard({ title, value, subtitle, icon: Icon, color = 'teal', badgeText, badgeColor = 'emerald' }) {
  const colorMap = {
    teal: 'bg-teal-50 text-teal-600 border-teal-100',
    red: 'bg-red-50 text-red-600 border-red-100',
    amber: 'bg-amber-50 text-amber-600 border-amber-100',
    blue: 'bg-blue-50 text-blue-600 border-blue-100',
    purple: 'bg-purple-50 text-purple-600 border-purple-100',
  };

  const badgeMap = {
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    red: 'bg-red-50 text-red-700 border-red-200 animate-pulse',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    blue: 'bg-blue-50 text-blue-700 border-blue-200',
  };

  return (
    <article
      aria-label={`${title}: ${value}${badgeText ? `, ${badgeText}` : ''}`}
      className="bg-white rounded-2xl p-5 border border-slate-200 shadow-sm hover:shadow-md transition"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1" id={`stat-label-${title.replace(/\s+/g, '-')}`}>
            {title}
          </p>
          <div className="flex items-baseline gap-2">
            <h3 className="text-2xl font-bold text-slate-900" aria-describedby={`stat-label-${title.replace(/\s+/g, '-')}`}>
              {value}
            </h3>
            {badgeText && (
              <span
                className={`text-[11px] font-semibold px-2 py-0.5 rounded-full border ${badgeMap[badgeColor] || badgeMap.emerald}`}
                aria-label={badgeText}
              >
                {badgeText}
              </span>
            )}
          </div>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
        </div>
        {Icon && (
          <div
            className={`p-3 rounded-xl border ${colorMap[color] || colorMap.teal}`}
            aria-hidden="true"
            role="presentation"
          >
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
    </article>
  );
}

