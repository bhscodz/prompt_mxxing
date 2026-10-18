// File: frontend/src/pages/Dashboard.jsx
// Description: Real-time district command center dashboard with operational KPIs and facility grid

import React, { useState, useEffect } from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../services/api';
import StatCard from '../components/StatCard';
import AlertBanner from '../components/AlertBanner';
import {
  Building2,
  AlertTriangle,
  BedDouble,
  Stethoscope,
  ShieldAlert,
  ArrowRight,
  TrendingDown,
  Pill,
  Users
} from 'lucide-react';

export default function Dashboard({
  facilities = [],
  selectedFacilityId,
  onNavigateTab,
  onSelectFacility
}) {
  const { t } = useLanguage();
  const [summary, setSummary] = useState(null);
  const [warnings, setWarnings] = useState([]);
  const [interventions, setInterventions] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [sumData, warnData, intData] = await Promise.all([
        api.getDistrictSummary(),
        api.getEarlyWarnings(selectedFacilityId ? { facility_id: selectedFacilityId } : {}),
        api.getInterventions({ status: 'pending_review' })
      ]);
      setSummary(sumData);
      setWarnings(warnData);
      setInterventions(intData);
    } catch (err) {
      console.error("Dashboard fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 15000);
    return () => clearInterval(interval);
  }, [selectedFacilityId]);

  const displayedFacilities = selectedFacilityId
    ? facilities.filter(f => f.id === selectedFacilityId)
    : facilities;

  return (
    <div className="space-y-6">
      {/* Emergency Alert Banner */}
      <AlertBanner
        alerts={interventions}
        onNavigateToInterventions={() => onNavigateTab('interventions')}
      />

      {/* Top District KPIs */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title={t('kpiTotalFacilities')}
          value={summary?.total_facilities || facilities.length}
          subtitle={`${summary?.phc_count || 4} PHCs • ${summary?.chc_count || 2} CHCs`}
          icon={Building2}
          color="blue"
        />

        <StatCard
          title={t('kpiCriticalStockouts')}
          value={summary?.critical_stockout_items ?? 0}
          subtitle="Medicines under 48h buffer"
          icon={Pill}
          color="red"
          badgeText={summary?.critical_stockout_items > 0 ? "Action Req." : "Safe"}
          badgeColor={summary?.critical_stockout_items > 0 ? "red" : "emerald"}
        />

        <StatCard
          title={t('kpiBedOccupancy')}
          value={`${summary?.bed_occupancy_pct || 0}%`}
          subtitle={`${summary?.occupied_beds || 0} of ${summary?.total_beds || 0} total beds`}
          icon={BedDouble}
          color="amber"
          badgeText={summary?.bed_occupancy_pct > 80 ? "High Load" : "Nominal"}
          badgeColor={summary?.bed_occupancy_pct > 80 ? "amber" : "emerald"}
        />

        <StatCard
          title={t('kpiDoctorAttendance')}
          value={`${summary?.doctor_attendance_pct || 0}%`}
          subtitle={`${summary?.present_doctors_staff || 0} / ${summary?.total_doctors_staff || 0} staff on duty`}
          icon={Stethoscope}
          color="teal"
          badgeText={summary?.doctor_attendance_pct >= 85 ? "Optimal" : "Gaps Noted"}
          badgeColor={summary?.doctor_attendance_pct >= 85 ? "emerald" : "amber"}
        />
      </div>

      {/* District Facility Health Grid */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-base font-bold text-slate-900">Health Facilities Operational Status</h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Live distress score (HFDI) calculated from stock, attendance, bed load, and diagnostic audits
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600">
            {displayedFacilities.length} Centres Active
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {displayedFacilities.map((fac) => {
            const isRed = fac.distress_score >= 65;
            const isAmber = fac.distress_score >= 35 && fac.distress_score < 65;
            return (
              <div
                key={fac.id}
                onClick={() => onSelectFacility(fac.id)}
                className={`p-4 rounded-xl border transition cursor-pointer hover:shadow-md ${
                  isRed
                    ? 'border-red-300 bg-red-50/40'
                    : isAmber
                    ? 'border-amber-300 bg-amber-50/40'
                    : 'border-slate-200 bg-white hover:border-teal-400'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      {fac.code} • {fac.facility_type}
                    </span>
                    <h3 className="text-sm font-bold text-slate-900 leading-tight mt-0.5">
                      {fac.name}
                    </h3>
                    <p className="text-xs text-slate-500 mt-1">Block: {fac.block_name}</p>
                  </div>
                  <div className="text-right">
                    <div className="text-xs font-semibold text-slate-400">HFDI Distress</div>
                    <div className={`text-lg font-black ${isRed ? 'text-red-600' : isAmber ? 'text-amber-600' : 'text-emerald-600'}`}>
                      {fac.distress_score}
                    </div>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className={`px-2 py-0.5 rounded-full font-semibold text-[11px] ${
                    isRed
                      ? 'bg-red-100 text-red-800'
                      : isAmber
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-emerald-100 text-emerald-800'
                  }`}>
                    {isRed ? 'Critical Distress' : isAmber ? 'Strained' : 'Nominal'}
                  </span>
                  <span className="text-teal-700 hover:text-teal-800 font-semibold flex items-center gap-1">
                    Manage Centre <ArrowRight className="w-3 h-3" />
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Two Column Grid: Early Stockout Warnings & Quick Actions */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Early Stockout Warnings List */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                AI Early Stock-out Warnings
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Dynamic exhaustion countdown computed by PyTorch Time Series Transformer
              </p>
            </div>
            <button
              onClick={() => onNavigateTab('inventory')}
              className="text-xs font-bold text-teal-700 hover:text-teal-800 flex items-center gap-1"
            >
              Full Inventory <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-100 max-h-80 overflow-y-auto">
            {warnings.length === 0 ? (
              <p className="text-xs text-slate-500 py-6 text-center">
                All essential medications are currently at safe buffer levels.
              </p>
            ) : (
              warnings.slice(0, 5).map((w, idx) => (
                <div key={idx} className="py-3 flex items-center justify-between gap-4">
                  <div>
                    <div className="flex items-center gap-2">
                      <h4 className="text-sm font-bold text-slate-800">{w.medicine_name}</h4>
                      <span className="text-[11px] font-medium text-slate-400">({w.category})</span>
                    </div>
                    <p className="text-xs text-slate-500 mt-0.5">
                      Facility: <span className="font-semibold text-slate-700">{w.facility_name}</span> • Current Stock: {w.current_stock}
                    </p>
                  </div>

                  <div className="text-right">
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      w.urgency_level === 'CRITICAL_HAZARD'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-amber-100 text-amber-800'
                    }`}>
                      {w.days_until_stockout} Days Left
                    </span>
                    <p className="text-[11px] text-slate-400 mt-1">Burn: {w.predicted_daily_demand}/day</p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Quick Operational Shortcuts */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <h2 className="text-base font-bold text-slate-900 mb-1">Quick Operational Actions</h2>
            <p className="text-xs text-slate-500 mb-4">Fast one-click workflows for healthcare staff</p>

            <div className="space-y-2.5">
              <button
                onClick={() => onNavigateTab('crm')}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-teal-50 border border-slate-200 hover:border-teal-300 transition text-left group"
              >
                <div className="flex items-center gap-3">
                  <Users className="w-4 h-4 text-teal-600" />
                  <div>
                    <div className="text-xs font-bold text-slate-800 group-hover:text-teal-900">
                      Register OPD Patient
                    </div>
                    <div className="text-[11px] text-slate-400">Issue queue token & triage vitals</div>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600" />
              </button>

              <button
                onClick={() => onNavigateTab('redistribution')}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-teal-50 border border-slate-200 hover:border-teal-300 transition text-left group"
              >
                <div className="flex items-center gap-3">
                  <ArrowRight className="w-4 h-4 text-teal-600" />
                  <div>
                    <div className="text-xs font-bold text-slate-800 group-hover:text-teal-900">
                      Smart Redistribution
                    </div>
                    <div className="text-[11px] text-slate-400">Transfer surplus stock to deficit PHCs</div>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600" />
              </button>

              <button
                onClick={() => onNavigateTab('forecasts')}
                className="w-full flex items-center justify-between p-3 rounded-xl bg-slate-50 hover:bg-teal-50 border border-slate-200 hover:border-teal-300 transition text-left group"
              >
                <div className="flex items-center gap-3">
                  <Pill className="w-4 h-4 text-teal-600" />
                  <div>
                    <div className="text-xs font-bold text-slate-800 group-hover:text-teal-900">
                      AI Demand Forecasts
                    </div>
                    <div className="text-[11px] text-slate-400">14-day transformer projections</div>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-teal-600" />
              </button>
            </div>
          </div>

          <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
            <span>District Admin Hotline</span>
            <span className="font-bold text-slate-800">+91 020 2612 1234</span>
          </div>
        </div>
      </div>
    </div>
  );
}

