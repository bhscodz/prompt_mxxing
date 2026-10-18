// File: frontend/src/pages/EconomicsDashboard.jsx
// Description: Economics & Budget Dashboard for SwasthyaGrid AI.
//   KPI Cards · Budget vs Actual by category · Purchase Orders table · Burn Rate

import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, PieChart, Pie, Cell,
} from 'recharts';
import {
  IndianRupee, TrendingUp, TrendingDown, ShoppingCart,
  RefreshCw, AlertCircle, CheckCircle2, Clock, Package
} from 'lucide-react';
import { getAuthHeaders } from '../services/authService';

const BASE = '/api/v1/economics';

async function apiFetch(endpoint, opts = {}) {
  const headers = { 'Content-Type': 'application/json', ...getAuthHeaders(), ...(opts.headers || {}) };
  const res = await fetch(`${BASE}${endpoint}`, { ...opts, headers });
  if (!res.ok) { const e = await res.json().catch(() => ({})); throw new Error(e.detail || `HTTP ${res.status}`); }
  return res.json();
}

const INR = (v) => `₹${Number(v || 0).toLocaleString('en-IN')}`;
const PCT = (v) => `${Number(v || 0).toFixed(1)}%`;

const CATEGORY_COLORS = {
  MEDICINES: '#0d9488',
  EQUIPMENT: '#f59e0b',
  STAFF_SALARIES: '#6366f1',
  UTILITIES: '#3b82f6',
  MAINTENANCE: '#8b5cf6',
  CONSUMABLES: '#10b981',
  DIAGNOSTICS: '#ec4899',
};

const STATUS_MAP = {
  DRAFT:     { label: 'Draft',     color: 'slate',  icon: Clock },
  SUBMITTED: { label: 'Submitted', color: 'blue',   icon: RefreshCw },
  APPROVED:  { label: 'Approved',  color: 'teal',   icon: CheckCircle2 },
  DELIVERED: { label: 'Delivered', color: 'emerald',icon: CheckCircle2 },
  CANCELLED: { label: 'Cancelled', color: 'rose',   icon: AlertCircle },
};

function KPICard({ label, value, sub, icon: Icon, color = 'teal', trend }) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl p-5">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide">{label}</p>
          <p className={`text-2xl font-bold text-${color}-700 mt-1`}>{value}</p>
          {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
        </div>
        <div className={`w-10 h-10 bg-${color}-100 rounded-xl flex items-center justify-center`}>
          <Icon className={`w-5 h-5 text-${color}-600`} />
        </div>
      </div>
      {trend !== undefined && (
        <div className={`flex items-center gap-1 mt-3 text-xs font-semibold ${trend >= 0 ? 'text-rose-600' : 'text-teal-600'}`}>
          {trend >= 0 ? <TrendingUp className="w-3.5 h-3.5" /> : <TrendingDown className="w-3.5 h-3.5" />}
          <span>{Math.abs(trend).toFixed(1)}% vs last month</span>
        </div>
      )}
    </div>
  );
}

function POStatusBadge({ status }) {
  const s = STATUS_MAP[status] || { label: status, color: 'slate', icon: Clock };
  const Icon = s.icon;
  return (
    <span className={`inline-flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1 rounded-full bg-${s.color}-100 text-${s.color}-700`}>
      <Icon className="w-3 h-3" />
      {s.label}
    </span>
  );
}

export default function EconomicsDashboard({ facilities = [], selectedFacilityId }) {
  const [facilityId, setFacilityId] = useState(selectedFacilityId || '');
  const [summary, setSummary]       = useState(null);
  const [budgets, setBudgets]       = useState([]);
  const [pos, setPOs]               = useState([]);
  const [loading, setLoading]       = useState(false);
  const [error, setError]           = useState('');
  const [year, setYear]             = useState(new Date().getFullYear());

  const loadData = useCallback(async () => {
    setLoading(true); setError('');
    try {
      const qs = facilityId ? `?facility_id=${facilityId}` : '';
      const [summaryData, budgetData, poData] = await Promise.all([
        apiFetch(`/facility-summary${qs}&year=${year}`).catch(() => null),
        apiFetch(`/budget-allocations${qs}&fiscal_year=${year}`).catch(() => []),
        apiFetch(`/purchase-orders${qs}`).catch(() => []),
      ]);
      setSummary(summaryData);
      setBudgets(Array.isArray(budgetData) ? budgetData : budgetData?.items || []);
      setPOs(Array.isArray(poData) ? poData : poData?.items || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [facilityId, year]);

  useEffect(() => { loadData(); }, [loadData]);

  // Build chart data from budget allocations grouped by category
  const chartData = Object.entries(
    budgets.reduce((acc, b) => {
      acc[b.category] = acc[b.category] || { category: b.category, allocated: 0, spent: 0 };
      acc[b.category].allocated += b.allocated_amount;
      return acc;
    }, {})
  ).map(([, v]) => v);

  const pendingPOs = pos.filter(po => ['SUBMITTED', 'APPROVED'].includes(po.status));
  const overduePOs = pos.filter(po =>
    po.expected_delivery_date &&
    new Date(po.expected_delivery_date) < new Date() &&
    !['DELIVERED', 'CANCELLED'].includes(po.status)
  );

  const totalBudget = summary?.total_budget ?? budgets.reduce((s, b) => s + b.allocated_amount, 0);
  const totalSpent  = summary?.total_spent  ?? 0;
  const utilization = totalBudget > 0 ? (totalSpent / totalBudget * 100) : 0;
  const remaining   = totalBudget - totalSpent;
  const daysInYear  = 365;
  const daysPassed  = Math.floor((Date.now() - new Date(year, 0, 1)) / 86400000);
  const burnRate    = daysPassed > 0 ? totalSpent / daysPassed : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-2">
            <IndianRupee className="w-6 h-6 text-teal-600" />
            Economics Dashboard
          </h1>
          <p className="text-slate-500 text-sm mt-1">Budget · Expenditure · Purchase Orders · Burn Rate</p>
        </div>
        <div className="flex items-center gap-3">
          <select
            value={facilityId}
            onChange={e => setFacilityId(e.target.value)}
            className="text-sm px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            <option value="">All Facilities</option>
            {facilities.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
          <select
            value={year}
            onChange={e => setYear(Number(e.target.value))}
            className="text-sm px-3 py-2 border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500"
          >
            {[2024, 2025, 2026].map(y => <option key={y} value={y}>FY {y}-{(y + 1).toString().slice(2)}</option>)}
          </select>
          <button
            onClick={loadData}
            disabled={loading}
            className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-semibold rounded-xl disabled:opacity-50 transition"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-rose-50 border border-rose-200 text-rose-700 text-sm px-4 py-3 rounded-xl">
          {error}
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard
          label="Total Budget"
          value={INR(totalBudget)}
          sub={`FY ${year}-${(year + 1).toString().slice(2)}`}
          icon={IndianRupee}
          color="teal"
        />
        <KPICard
          label="Total Spent"
          value={INR(totalSpent)}
          sub={`${PCT(utilization)} utilized`}
          icon={TrendingUp}
          color="amber"
        />
        <KPICard
          label="Remaining"
          value={INR(remaining)}
          sub={remaining < 0 ? '⚠ Over budget' : 'Available balance'}
          icon={remaining >= 0 ? CheckCircle2 : AlertCircle}
          color={remaining >= 0 ? 'emerald' : 'rose'}
        />
        <KPICard
          label="Daily Burn Rate"
          value={INR(Math.round(burnRate))}
          sub={`${daysPassed} days elapsed`}
          icon={TrendingDown}
          color="violet"
        />
      </div>

      {/* Budget Utilization Bar */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-bold text-slate-800">Budget Utilization</h2>
          <span className={`text-sm font-bold ${utilization > 90 ? 'text-rose-600' : utilization > 70 ? 'text-amber-600' : 'text-teal-600'}`}>
            {PCT(utilization)}
          </span>
        </div>
        <div className="w-full h-4 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${utilization > 90 ? 'bg-rose-500' : utilization > 70 ? 'bg-amber-500' : 'bg-teal-500'}`}
            style={{ width: `${Math.min(100, utilization)}%` }}
          />
        </div>
        <div className="flex justify-between text-xs text-slate-500 mt-1">
          <span>₹0</span>
          <span>Budget: {INR(totalBudget)}</span>
        </div>
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {/* Budget by Category Bar Chart */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <h2 className="font-bold text-slate-800 mb-4">Allocated Budget by Category</h2>
          {chartData.length === 0 ? (
            <p className="text-slate-400 text-sm text-center py-8">No budget data available.</p>
          ) : (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={chartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" tick={{ fontSize: 10 }} tickFormatter={v => `₹${(v / 100000).toFixed(1)}L`} />
                <YAxis type="category" dataKey="category" tick={{ fontSize: 10 }} width={100} />
                <Tooltip formatter={(v) => INR(v)} />
                <Bar dataKey="allocated" name="Allocated">
                  {chartData.map((entry) => (
                    <Cell key={entry.category} fill={CATEGORY_COLORS[entry.category] || '#94a3b8'} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Budget Distribution Pie */}
        <div className="bg-white border border-slate-200 rounded-2xl p-5">
          <h2 className="font-bold text-slate-800 mb-4">Budget Distribution</h2>
          {chartData.length === 0 ? (
            <p className="text-slate-400 text-sm text-center py-8">No data.</p>
          ) : (
            <div className="flex items-center gap-4">
              <ResponsiveContainer width="55%" height={200}>
                <PieChart>
                  <Pie
                    data={chartData}
                    dataKey="allocated"
                    nameKey="category"
                    cx="50%"
                    cy="50%"
                    innerRadius={50}
                    outerRadius={85}
                  >
                    {chartData.map((entry) => (
                      <Cell key={entry.category} fill={CATEGORY_COLORS[entry.category] || '#94a3b8'} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => INR(v)} />
                </PieChart>
              </ResponsiveContainer>
              <div className="space-y-1.5">
                {chartData.map(({ category, allocated }) => (
                  <div key={category} className="flex items-center gap-2">
                    <span
                      className="w-3 h-3 rounded-full shrink-0"
                      style={{ background: CATEGORY_COLORS[category] || '#94a3b8' }}
                    />
                    <span className="text-xs text-slate-600 truncate max-w-[120px]">{category}</span>
                    <span className="text-xs font-semibold text-slate-800 ml-auto">
                      {totalBudget > 0 ? PCT((allocated / totalBudget) * 100) : '0%'}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Purchase Orders */}
      <div className="bg-white border border-slate-200 rounded-2xl p-5">
        <div className="flex items-center justify-between mb-4">
          <h2 className="font-bold text-slate-800 flex items-center gap-2">
            <ShoppingCart className="w-5 h-5 text-slate-400" />
            Purchase Orders
          </h2>
          <div className="flex items-center gap-2">
            {pendingPOs.length > 0 && (
              <span className="text-xs bg-blue-100 text-blue-700 font-semibold px-2 py-0.5 rounded-full">
                {pendingPOs.length} Pending
              </span>
            )}
            {overduePOs.length > 0 && (
              <span className="text-xs bg-rose-100 text-rose-700 font-semibold px-2 py-0.5 rounded-full">
                {overduePOs.length} Overdue
              </span>
            )}
          </div>
        </div>

        {pos.length === 0 ? (
          <p className="text-slate-400 text-sm text-center py-6">No purchase orders found.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-slate-100">
                  {['Item', 'Type', 'Qty', 'Total', 'Vendor', 'ETA', 'Status'].map(h => (
                    <th key={h} className="text-left text-xs font-semibold text-slate-500 uppercase py-2 px-3">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {pos.slice(0, 20).map(po => {
                  const isOverdue = po.expected_delivery_date &&
                    new Date(po.expected_delivery_date) < new Date() &&
                    !['DELIVERED', 'CANCELLED'].includes(po.status);
                  return (
                    <tr key={po.id} className={`border-b border-slate-50 hover:bg-slate-50 ${isOverdue ? 'bg-rose-50' : ''}`}>
                      <td className="py-2 px-3 font-medium text-slate-800 max-w-[160px] truncate">
                        <div className="flex items-center gap-2">
                          {isOverdue && <AlertCircle className="w-3.5 h-3.5 text-rose-500 shrink-0" />}
                          {po.item_name}
                        </div>
                      </td>
                      <td className="py-2 px-3 text-slate-600">{po.item_type}</td>
                      <td className="py-2 px-3 text-slate-600">{po.quantity}</td>
                      <td className="py-2 px-3 font-semibold text-slate-800">{INR(po.total_amount)}</td>
                      <td className="py-2 px-3 text-slate-600 max-w-[120px] truncate">{po.vendor || '—'}</td>
                      <td className={`py-2 px-3 text-xs font-medium ${isOverdue ? 'text-rose-600 font-bold' : 'text-slate-600'}`}>
                        {po.expected_delivery_date
                          ? new Date(po.expected_delivery_date).toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
                          : '—'}
                        {isOverdue && ' ⚠'}
                      </td>
                      <td className="py-2 px-3"><POStatusBadge status={po.status} /></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {pos.length > 20 && (
              <p className="text-xs text-slate-400 mt-2 text-center">Showing 20 of {pos.length} records.</p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
