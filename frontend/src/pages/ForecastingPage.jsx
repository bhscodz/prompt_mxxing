// File: frontend/src/pages/ForecastingPage.jsx
// Description: Advanced Forecasting Dashboard — PatchTST · XGBoost · ARIMA ensemble
//   with dual-mode depletion alert cards (Real-Time + Forecasted ETA).

import React, { useState, useEffect, useCallback } from 'react';
import {
  ComposedChart, Line, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts';
import {
  TrendingUp, AlertTriangle, Zap, Clock, ChevronDown,
  BarChart3, RefreshCw, Brain, Package
} from 'lucide-react';
import { getAuthHeaders } from '../services/authService';

const BASE = '/api/v1';

async function apiFetch(endpoint, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...getAuthHeaders(), ...(opts.headers || {}) };
  const res = await fetch(`${BASE}${endpoint}`, { ...opts, headers });
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${res.status}`); }
  return res.json();
}

const MODEL_COLORS = { patchtst: '#0d9488', xgboost: '#f59e0b', arima: '#6366f1', flat_fallback: '#94a3b8', patchtst_fallback: '#14b8a6' };
const SEVERITY_COLORS = { CRITICAL: 'rose', WARNING: 'amber' };

function AlertCard({ alert }) {
  const isType2 = alert.alert_type === 'TYPE_2_FORECASTED';
  const sev = alert.severity;
  const color = sev === 'CRITICAL' ? 'rose' : 'amber';
  return (
    <div className={`bg-${color}-50 border border-${color}-200 rounded-xl p-4`}>
      <div className="flex items-start gap-3">
        <AlertTriangle className={`w-5 h-5 text-${color}-500 shrink-0 mt-0.5`} />
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className={`text-xs font-bold uppercase px-2 py-0.5 rounded-full bg-${color}-100 text-${color}-700`}>
              {sev}
            </span>
            {isType2 ? (
              <span className="text-xs bg-indigo-100 text-indigo-700 font-semibold px-2 py-0.5 rounded-full">
                AI Forecast
              </span>
            ) : (
              <span className="text-xs bg-slate-100 text-slate-600 font-semibold px-2 py-0.5 rounded-full">
                Real-Time
              </span>
            )}
          </div>
          <p className="text-sm font-semibold text-slate-800">{alert.medicine_name}</p>
          <p className="text-xs text-slate-600 mt-0.5">{alert.message}</p>
          {alert.po_eta && (
            <p className="text-xs text-indigo-600 mt-1">
              📦 PO ETA: {alert.po_eta} · Gap: {alert.days_before_eta} days
            </p>
          )}
          {alert.model_used && (
            <p className="text-xs text-slate-400 mt-1">Model: {alert.model_used}</p>
          )}
        </div>
      </div>
    </div>
  );
}

function ForecastChart({ data, medicineName, modelUsed }) {
  if (!data || !data.predictions) return null;

  const chartData = data.predictions.map((val, i) => ({
    day: `D+${i + 1}`,
    forecast: Math.round(val * 10) / 10,
    lower: Math.round((data.confidence_lower[i] || 0) * 10) / 10,
    upper: Math.round((data.confidence_upper[i] || val) * 10) / 10,
  }));

  const modelColor = MODEL_COLORS[modelUsed] || '#0d9488';

  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-bold text-slate-800">{medicineName}</h3>
          <p className="text-xs text-slate-500">
            Model: <span className="font-semibold" style={{ color: modelColor }}>{modelUsed}</span>
            · Horizon: {data.horizon_days} days · Series: {data.series_length} points
          </p>
        </div>
        <span className="text-xs bg-teal-50 text-teal-700 font-semibold px-3 py-1 rounded-full border border-teal-200">
          {data.model_selected_by === 'auto' ? '🤖 Auto-Routed' : '⚙ Manual'}
        </span>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <ComposedChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
          <XAxis dataKey="day" tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={{ borderRadius: '8px', border: '1px solid #e2e8f0', fontSize: '12px' }}
          />
          <Legend wrapperStyle={{ fontSize: '12px' }} />
          {/* 95% CI band */}
          <Area
            type="monotone" dataKey="upper" stroke="none"
            fill={modelColor} fillOpacity={0.12} name="95% CI Upper"
          />
          <Area
            type="monotone" dataKey="lower" stroke="none"
            fill="#fff" fillOpacity={1} name="95% CI Lower" legendType="none"
          />
          {/* Point forecast */}
          <Line
            type="monotone" dataKey="forecast" stroke={modelColor}
            strokeWidth={2.5} dot={{ r: 3 }} name="Forecast"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export default function ForecastingPage({ facilities = [], selectedFacilityId }) {
  const [facilityId, setFacilityId] = useState(selectedFacilityId || '');
  const [stocks, setStocks]         = useState([]);
  const [selectedMed, setSelectedMed] = useState('');
  const [forecastData, setForecastData] = useState(null);
  const [alerts, setAlerts]         = useState(null);
  const [modelInfo, setModelInfo]   = useState(null);
  const [horizon, setHorizon]       = useState(14);
  const [model, setModel]           = useState('auto');
  const [loading, setLoading]       = useState(false);
  const [alertsLoading, setAlertsLoading] = useState(false);
  const [error, setError]           = useState('');

  // Load stocks when facility changes
  useEffect(() => {
    if (!facilityId) return;
    apiFetch(`/inventory?facility_id=${facilityId}`)
      .then(setStocks)
      .catch(() => setStocks([]));
  }, [facilityId]);

  // Auto-select first medicine when stocks load
  useEffect(() => {
    if (stocks.length > 0 && !selectedMed) setSelectedMed(stocks[0].id);
  }, [stocks]);

  const runForecast = useCallback(async () => {
    if (!selectedMed) return;
    setLoading(true); setError('');
    try {
      const data = await apiFetch(`/forecasting/medicine/${selectedMed}?horizon=${horizon}&model=${model}`);
      setForecastData(data);
      // Also fetch model routing info
      const info = await apiFetch(`/forecasting/model-info?series_length=${data.forecast?.series_length || 60}`);
      setModelInfo(info);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [selectedMed, horizon, model]);

  const runAlerts = useCallback(async () => {
    if (!facilityId) return;
    setAlertsLoading(true);
    try {
      const data = await apiFetch(`/forecasting/run-alerts/${facilityId}?forecast_horizon=30`, { method: 'POST' });
      setAlerts(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setAlertsLoading(false);
    }
  }, [facilityId]);

  const selectedStock = stocks.find(s => s.id === selectedMed);

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <BarChart3 className="w-6 h-6 text-teal-600" />
            Advanced Forecasting Engine
          </h1>
          <p className="text-slate-500 text-sm mt-1">
            PatchTST · XGBoost · ARIMA ensemble with dual-mode depletion alerts
          </p>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 text-sm px-4 py-3 rounded-xl">
          {error}
        </div>
      )}

      {/* Controls */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Facility */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Facility</label>
            <select
              value={facilityId}
              onChange={e => { setFacilityId(e.target.value); setForecastData(null); setAlerts(null); setSelectedMed(''); }}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="">Select facility…</option>
              {facilities.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
            </select>
          </div>
          {/* Medicine */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Medicine</label>
            <select
              value={selectedMed}
              onChange={e => setSelectedMed(e.target.value)}
              disabled={!stocks.length}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 disabled:opacity-50"
            >
              {stocks.map(s => <option key={s.id} value={s.id}>{s.medicine_name}</option>)}
            </select>
          </div>
          {/* Horizon */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Horizon (days)</label>
            <select
              value={horizon}
              onChange={e => setHorizon(Number(e.target.value))}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              {[7, 14, 21, 30, 60, 90].map(d => <option key={d} value={d}>{d} days</option>)}
            </select>
          </div>
          {/* Model */}
          <div>
            <label className="block text-xs font-semibold text-slate-500 uppercase mb-1">Model</label>
            <select
              value={model}
              onChange={e => setModel(e.target.value)}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="auto">🤖 Auto (Recommended)</option>
              <option value="patchtst">PatchTST (Transformer)</option>
              <option value="xgboost">XGBoost</option>
              <option value="arima">ARIMA</option>
            </select>
          </div>
        </div>
        <div className="flex gap-3 mt-4">
          <button
            onClick={runForecast}
            disabled={loading || !selectedMed}
            className="flex items-center gap-2 px-5 py-2.5 bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold rounded-xl disabled:opacity-50 transition"
          >
            {loading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Brain className="w-4 h-4" />}
            Run Forecast
          </button>
          <button
            onClick={runAlerts}
            disabled={alertsLoading || !facilityId}
            className="flex items-center gap-2 px-5 py-2.5 bg-rose-600 hover:bg-rose-700 text-white text-sm font-semibold rounded-xl disabled:opacity-50 transition"
          >
            {alertsLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <AlertTriangle className="w-4 h-4" />}
            Run Depletion Alerts
          </button>
        </div>
      </div>

      {/* Model Info */}
      {modelInfo && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Series Length', value: `${modelInfo.series_length} points` },
            { label: 'Auto-Selected Model', value: modelInfo.model_selected?.toUpperCase() || '—' },
            { label: 'Routing Mode', value: modelInfo.routing_mode || 'auto' },
          ].map(({ label, value }) => (
            <div key={label} className="bg-white border border-slate-200 rounded-xl p-4">
              <p className="text-xs text-slate-500 uppercase font-semibold">{label}</p>
              <p className="text-lg font-bold text-slate-800 mt-1">{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Forecast Chart */}
      {forecastData && selectedStock && (
        <ForecastChart
          data={forecastData.forecast}
          medicineName={forecastData.medicine_name}
          modelUsed={forecastData.forecast?.model_used}
        />
      )}

      {/* Current Stock Info */}
      {forecastData && selectedStock && (
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: 'Current Stock', value: `${forecastData.current_quantity} units`, icon: Package, color: 'teal' },
            { label: 'Daily Burn Rate', value: `${forecastData.daily_burn_rate}/day`, icon: TrendingUp, color: 'amber' },
            { label: 'Days of Supply', value: `${Math.round(forecastData.current_quantity / Math.max(1, forecastData.daily_burn_rate))} days`, icon: Clock, color: 'indigo' },
          ].map(({ label, value, icon: Icon, color }) => (
            <div key={label} className={`bg-${color}-50 border border-${color}-200 rounded-xl p-4`}>
              <div className="flex items-center gap-2 mb-1">
                <Icon className={`w-4 h-4 text-${color}-500`} />
                <p className={`text-xs font-semibold text-${color}-700 uppercase`}>{label}</p>
              </div>
              <p className={`text-xl font-bold text-${color}-800`}>{value}</p>
            </div>
          ))}
        </div>
      )}

      {/* Alerts */}
      {alerts && (
        <div>
          <div className="flex items-center gap-3 mb-4">
            <h2 className="text-lg font-bold text-slate-800">Depletion Alerts</h2>
            <span className="bg-rose-100 text-rose-700 text-xs font-bold px-2 py-0.5 rounded-full">
              {alerts.total_critical} Critical
            </span>
            <span className="bg-amber-100 text-amber-700 text-xs font-bold px-2 py-0.5 rounded-full">
              {alerts.total_warnings} Warnings
            </span>
            <span className="text-xs text-slate-500">
              {alerts.stocks_evaluated} medicines evaluated
            </span>
          </div>

          {alerts.total_alerts === 0 ? (
            <div className="bg-teal-50 border border-teal-200 rounded-xl p-6 text-center">
              <p className="text-teal-700 font-semibold">✅ No depletion alerts — all medicines are adequately stocked.</p>
            </div>
          ) : (
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-600 flex items-center gap-2">
                <Zap className="w-4 h-4 text-rose-500" /> Real-Time Alerts ({alerts.realtime_alerts.length})
              </h3>
              {alerts.realtime_alerts.map((a, i) => <AlertCard key={i} alert={a} />)}

              {alerts.forecasted_alerts.length > 0 && (
                <>
                  <h3 className="text-sm font-semibold text-slate-600 flex items-center gap-2 mt-4">
                    <Brain className="w-4 h-4 text-indigo-500" /> AI Forecasted Alerts ({alerts.forecasted_alerts.length})
                  </h3>
                  {alerts.forecasted_alerts.map((a, i) => <AlertCard key={i} alert={a} />)}
                </>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
