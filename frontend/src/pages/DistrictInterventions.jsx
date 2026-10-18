// File: frontend/src/pages/DistrictInterventions.jsx
// Description: District administrator & CMO command portal with automated facility distress flags (HFDI) and administrative dispatch

import React, { useState, useEffect } from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../services/api';
import {
  ShieldAlert,
  AlertTriangle,
  Building2,
  CheckCircle,
  Clock,
  Send,
  FileText,
  UserCheck,
  X,
  Sparkles
} from 'lucide-react';

export default function DistrictInterventions({ facilities = [] }) {
  const { t } = useLanguage();
  const [alerts, setAlerts] = useState([]);
  const [selectedAlertForDispatch, setSelectedAlertForDispatch] = useState(null);
  const [adminNotes, setAdminNotes] = useState('');
  const [dispatchedBy, setDispatchedBy] = useState('Dr. R. Deshmukh (Chief Medical Officer)');
  const [dispatchSuccessMsg, setDispatchSuccessMsg] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchInterventions = async () => {
    try {
      const data = await api.getInterventions();
      setAlerts(data);
    } catch (err) {
      console.error("Error fetching interventions:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInterventions();
    const interval = setInterval(fetchInterventions, 12000);
    return () => clearInterval(interval);
  }, []);

  const handleDispatchAction = async (status) => {
    if (!selectedAlertForDispatch) return;

    try {
      await api.dispatchInterventionAction(selectedAlertForDispatch.id, {
        status: status,
        admin_notes: adminNotes || 'Administrative order dispatched by District Health Officer.',
        dispatched_by: dispatchedBy
      });

      setDispatchSuccessMsg(`Administrative action dispatched: [${status.toUpperCase()}]`);
      setSelectedAlertForDispatch(null);
      setAdminNotes('');
      fetchInterventions();
    } catch (err) {
      alert("Dispatch failed: " + err.message);
    }
  };

  // Sort facilities by distress score
  const distressedFacilities = [...facilities].sort((a, b) => b.distress_score - a.distress_score);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-red-50 rounded-xl text-red-700">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-slate-900">{t('intervTitle')}</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">{t('intervSubtitle')}</p>
        </div>

        <div className="flex items-center gap-2 text-xs font-semibold">
          <span className="px-3 py-1.5 rounded-xl bg-red-50 text-red-700 border border-red-200">
            {distressedFacilities.filter(f => f.distress_score >= 65).length} Critical Interventions
          </span>
        </div>
      </div>

      {dispatchSuccessMsg && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between">
          <span>{dispatchSuccessMsg}</span>
          <button onClick={() => setDispatchSuccessMsg(null)} className="font-bold">&times;</button>
        </div>
      )}

      {/* Facilities Ranked by Distress Index (HFDI) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <h3 className="text-sm font-bold text-slate-900 mb-1">
          District Health Facility Distress Index (HFDI) Ranking
        </h3>
        <p className="text-xs text-slate-400 mb-4">
          Composite algorithmic distress score combining: stockout hazard (30%), doctor absenteeism (25%), bed saturation (25%), and lab breakdowns (20%).
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {distressedFacilities.map((fac) => {
            const isRed = fac.distress_score >= 65;
            const isAmber = fac.distress_score >= 35 && fac.distress_score < 65;

            return (
              <div
                key={fac.id}
                className={`p-4 rounded-xl border transition ${
                  isRed
                    ? 'border-red-300 bg-red-50/50 shadow-sm'
                    : isAmber
                    ? 'border-amber-300 bg-amber-50/50'
                    : 'border-slate-200 bg-white'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wide">
                      {fac.code}
                    </span>
                    <h4 className="text-sm font-bold text-slate-900 mt-0.5">{fac.name}</h4>
                    <p className="text-xs text-slate-500">Block: {fac.block_name}</p>
                  </div>

                  <div className="text-right">
                    <span className="text-[10px] font-bold uppercase text-slate-400 block">HFDI Score</span>
                    <span className={`text-xl font-black ${isRed ? 'text-red-600' : isAmber ? 'text-amber-600' : 'text-emerald-600'}`}>
                      {fac.distress_score}
                    </span>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className={`px-2 py-0.5 rounded-full font-bold text-[10px] ${
                    isRed
                      ? 'bg-red-100 text-red-800'
                      : isAmber
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-emerald-100 text-emerald-800'
                  }`}>
                    {isRed ? 'RED FLAG: Action Required' : isAmber ? 'Strained: Monitor' : 'Healthy: Nominal'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* District Intervention Alerts Feed */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div>
            <h3 className="text-sm font-bold text-slate-900">Active Administrative Distress Alerts</h3>
            <p className="text-xs text-slate-400">Automated triggers sent to District Magistrate and CMO</p>
          </div>
          <span className="text-xs font-semibold text-slate-500">
            {alerts.length} Total Alerts Logged
          </span>
        </div>

        <div className="divide-y divide-slate-100">
          {alerts.length === 0 ? (
            <div className="py-8 text-center text-slate-400 text-xs">
              No outstanding administrative intervention alerts.
            </div>
          ) : (
            alerts.map((a) => {
              const isResolved = a.status === 'resolved';

              return (
                <div key={a.id} className="p-4 hover:bg-slate-50 transition flex flex-col md:flex-row md:items-center justify-between gap-4">
                  <div className="space-y-1 max-w-2xl">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full uppercase ${
                        a.severity === 'critical'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-amber-100 text-amber-800'
                      }`}>
                        {a.severity}
                      </span>
                      <span className="text-xs font-semibold text-slate-400">
                        {new Date(a.created_at).toLocaleDateString()}
                      </span>
                      <span className="text-xs font-bold text-slate-700 bg-slate-100 px-2 py-0.5 rounded">
                        {a.alert_type.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>

                    <h4 className="text-sm font-bold text-slate-900">{a.title}</h4>
                    <p className="text-xs text-slate-600">{a.description}</p>

                    {a.suggested_action && (
                      <p className="text-[11px] text-teal-800 bg-teal-50/80 p-2 rounded-lg border border-teal-200 mt-2">
                        <strong>AI Suggested Administrative Order:</strong> {a.suggested_action}
                      </p>
                    )}

                    {a.admin_notes && (
                      <p className="text-[11px] text-slate-600 bg-slate-100 p-2 rounded-lg mt-1 font-mono">
                        <strong>Dispatched Order:</strong> {a.admin_notes} (By: {a.dispatched_by})
                      </p>
                    )}
                  </div>

                  <div className="text-right shrink-0">
                    {!isResolved ? (
                      <button
                        onClick={() => {
                          setSelectedAlertForDispatch(a);
                          setAdminNotes(a.suggested_action || '');
                        }}
                        className="px-3 py-1.5 rounded-xl bg-red-600 hover:bg-red-700 text-white font-bold text-xs shadow-md shadow-red-600/20 transition flex items-center gap-1.5"
                      >
                        <Send className="w-3.5 h-3.5" />
                        <span>{t('btnTakeAction')}</span>
                      </button>
                    ) : (
                      <span className="inline-flex items-center gap-1 text-emerald-700 font-bold text-xs px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200">
                        <CheckCircle className="w-3.5 h-3.5" />
                        Resolved
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Action Dispatch Modal */}
      {selectedAlertForDispatch && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 text-red-600" />
                Dispatch Administrative Intervention
              </h3>
              <button onClick={() => setSelectedAlertForDispatch(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4 mt-4 text-xs">
              <div className="p-3 bg-red-50 rounded-xl border border-red-200 text-red-900">
                <span className="font-bold block mb-1">{selectedAlertForDispatch.title}</span>
                <p className="text-[11px] text-red-800">{selectedAlertForDispatch.description}</p>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Administrative Dispatch Order / Note</label>
                <textarea
                  rows="3"
                  value={adminNotes}
                  onChange={(e) => setAdminNotes(e.target.value)}
                  placeholder={t('adminNotesPlaceholder')}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-red-500 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Dispatched By (Authority)</label>
                <input
                  type="text"
                  value={dispatchedBy}
                  onChange={(e) => setDispatchedBy(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  onClick={() => setSelectedAlertForDispatch(null)}
                  className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-bold"
                >
                  Cancel
                </button>
                <button
                  onClick={() => handleDispatchAction('dispatched')}
                  className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-700 text-white font-bold"
                >
                  Dispatch to Block Officer
                </button>
                <button
                  onClick={() => handleDispatchAction('resolved')}
                  className="px-4 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold"
                >
                  Mark Resolved
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

