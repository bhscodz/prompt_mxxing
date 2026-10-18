// File: frontend/src/pages/InventoryStock.jsx
// Description: Real-time medicine stock monitoring, burn rate recalculation, batch expiry tracker, and early stockout warnings

import React, { useState, useEffect } from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../services/api';
import { rpcClient } from '../services/rpcClient';
import {
  Pill,
  AlertTriangle,
  Plus,
  Minus,
  Search,
  Filter,
  PackageCheck,
  Zap,
  Clock,
  X
} from 'lucide-react';

export default function InventoryStock({ facilities = [], selectedFacilityId }) {
  const { t } = useLanguage();
  const [stocks, setStocks] = useState([]);
  const [warnings, setWarnings] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');
  const [showCriticalOnly, setShowCriticalOnly] = useState(false);
  const [loading, setLoading] = useState(true);

  // Dispense Modal State
  const [dispenseModalStock, setDispenseModalStock] = useState(null);
  const [dispenseQty, setDispenseQty] = useState(10);
  const [useFastRpc, setUseFastRpc] = useState(true);
  const [perfNotice, setPerfNotice] = useState(null);

  const fetchInventoryData = async () => {
    try {
      const params = selectedFacilityId ? { facility_id: selectedFacilityId } : {};
      const [stocksData, warningsData] = await Promise.all([
        api.getStocks(params),
        api.getEarlyWarnings(params)
      ]);
      setStocks(stocksData);
      setWarnings(warningsData);
    } catch (err) {
      console.error("Error loading inventory:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInventoryData();
    const interval = setInterval(fetchInventoryData, 12000);
    return () => clearInterval(interval);
  }, [selectedFacilityId]);

  const handleDispense = async (e) => {
    e.preventDefault();
    if (!dispenseModalStock) return;

    try {
      if (useFastRpc) {
        // High-speed JSON-RPC 2.0 dispensation call
        const rpcRes = await rpcClient.call('inventory.reportDispensation', {
          stock_id: dispenseModalStock.id,
          quantity: parseInt(dispenseQty) || 1,
          notes: 'OPD Pharmacy Dispensation'
        });
        setPerfNotice(`Dispensed via Fast RPC in ${rpcRes.executionTimeMs} ms! Remaining: ${rpcRes.result.remaining_quantity}`);
      } else {
        await api.recordStockTransaction({
          facility_id: dispenseModalStock.facility_id,
          medicine_stock_id: dispenseModalStock.id,
          transaction_type: 'dispensation',
          quantity: parseInt(dispenseQty) || 1,
          notes: 'Standard REST Dispensation'
        });
      }

      setDispenseModalStock(null);
      fetchInventoryData();
    } catch (err) {
      alert("Dispensation failed: " + err.message);
    }
  };

  const categories = Array.from(new Set(stocks.map(s => s.category))).filter(Boolean);

  const filteredStocks = stocks.filter(s => {
    if (showCriticalOnly && s.days_of_supply > 7.0 && s.current_quantity > s.reorder_level) return false;
    if (selectedCategory && s.category !== selectedCategory) return false;
    if (searchQuery && !s.medicine_name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Pill className="w-5 h-5 text-teal-600" />
            {t('invTitle')}
          </h2>
          <p className="text-xs text-slate-500 mt-1">{t('invSubtitle')}</p>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold px-3 py-1.5 rounded-xl bg-slate-100 text-slate-700">
            Total Catalog: {stocks.length} Items
          </span>
        </div>
      </div>

      {perfNotice && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between">
          <span>{perfNotice}</span>
          <button onClick={() => setPerfNotice(null)} className="font-bold">&times;</button>
        </div>
      )}

      {/* Search and Filters */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex items-center gap-3 flex-1 min-w-[260px]">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search by drug name (e.g. Paracetamol, ASV, Oxytocin)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500"
            />
          </div>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="border border-slate-200 rounded-lg px-3 py-2 bg-white font-medium text-slate-700 focus:outline-none"
          >
            <option value="">All Categories</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        <button
          onClick={() => setShowCriticalOnly(!showCriticalOnly)}
          className={`flex items-center gap-2 px-3 py-2 rounded-lg border font-bold transition ${
            showCriticalOnly
              ? 'bg-red-50 border-red-300 text-red-700 shadow-sm'
              : 'border-slate-200 text-slate-600 hover:bg-slate-50'
          }`}
        >
          <AlertTriangle className={`w-3.5 h-3.5 ${showCriticalOnly ? 'text-red-600' : 'text-slate-400'}`} />
          <span>{t('filterCriticalOnly')}</span>
        </button>
      </div>

      {/* Medicine Stock Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">{t('thMedicine')}</th>
                <th className="px-4 py-3">{t('thCategory')}</th>
                <th className="px-4 py-3">{t('thBatch')}</th>
                <th className="px-4 py-3">{t('thCurrentStock')}</th>
                <th className="px-4 py-3">{t('thDailyBurn')}</th>
                <th className="px-4 py-3">{t('thDaysRemaining')}</th>
                <th className="px-4 py-3">{t('thRiskLevel')}</th>
                <th className="px-4 py-3 text-right">{t('thActions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredStocks.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-slate-400">
                    No medication stocks match current criteria.
                  </td>
                </tr>
              ) : (
                filteredStocks.map((s) => {
                  const isCritical = s.days_of_supply <= 2.0 || s.current_quantity < (s.reorder_level * 0.3);
                  const isWarning = !isCritical && (s.days_of_supply <= 7.0 || s.current_quantity <= s.reorder_level);

                  return (
                    <tr key={s.id} className="hover:bg-slate-50 transition">
                      <td className="px-4 py-3 font-bold text-slate-900">
                        <div className="text-sm">{s.medicine_name}</div>
                        <div className="text-[11px] text-slate-400 font-normal">
                          Safety Reorder: {s.reorder_level} {s.unit}
                        </div>
                      </td>

                      <td className="px-4 py-3 text-slate-600 font-medium">
                        {s.category}
                      </td>

                      <td className="px-4 py-3">
                        <div className="font-mono text-slate-700">{s.batch_number}</div>
                        <div className="text-[11px] text-slate-400">Exp: {s.expiry_date}</div>
                      </td>

                      <td className="px-4 py-3 font-bold text-slate-900">
                        {s.current_quantity.toLocaleString()} {s.unit}
                      </td>

                      <td className="px-4 py-3 text-slate-600">
                        ~{s.daily_burn_rate} {s.unit}/day
                      </td>

                      <td className="px-4 py-3">
                        <div className="flex items-center gap-1.5">
                          <Clock className={`w-3.5 h-3.5 ${isCritical ? 'text-red-500' : isWarning ? 'text-amber-500' : 'text-emerald-500'}`} />
                          <span className={`font-bold ${isCritical ? 'text-red-600' : isWarning ? 'text-amber-700' : 'text-slate-800'}`}>
                            {s.days_of_supply} days
                          </span>
                        </div>
                      </td>

                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-bold text-[11px] ${
                          isCritical
                            ? 'bg-red-100 text-red-800 animate-pulse'
                            : isWarning
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${isCritical ? 'bg-red-600' : isWarning ? 'bg-amber-600' : 'bg-emerald-600'}`}></span>
                          {isCritical ? t('hazardCritical') : isWarning ? t('hazardWarning') : t('hazardOptimal')}
                        </span>
                      </td>

                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => {
                            setDispenseModalStock(s);
                            setDispenseQty(Math.min(10, s.current_quantity));
                          }}
                          className="px-2.5 py-1 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 font-bold text-[11px] transition"
                        >
                          {t('btnRecordDispense')}
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Fast Dispense Modal */}
      {dispenseModalStock && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Pill className="w-4 h-4 text-teal-600" />
                Dispense {dispenseModalStock.medicine_name}
              </h3>
              <button onClick={() => setDispenseModalStock(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleDispense} className="space-y-4 mt-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200">
                <div className="flex justify-between text-slate-600 mb-1">
                  <span>Current Available:</span>
                  <span className="font-bold text-slate-900">{dispenseModalStock.current_quantity} {dispenseModalStock.unit}</span>
                </div>
                <div className="flex justify-between text-slate-600">
                  <span>Daily Burn Rate:</span>
                  <span className="font-bold text-slate-900">~{dispenseModalStock.daily_burn_rate}/day</span>
                </div>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Units to Dispense</label>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setDispenseQty(Math.max(1, dispenseQty - 5))}
                    className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 font-bold"
                  >
                    <Minus className="w-3.5 h-3.5" />
                  </button>
                  <input
                    type="number"
                    min="1"
                    max={dispenseModalStock.current_quantity}
                    value={dispenseQty}
                    onChange={(e) => setDispenseQty(parseInt(e.target.value) || 1)}
                    className="flex-1 text-center font-bold px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  />
                  <button
                    type="button"
                    onClick={() => setDispenseQty(Math.min(dispenseModalStock.current_quantity, dispenseQty + 5))}
                    className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 font-bold"
                  >
                    <Plus className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              <div className="flex items-center justify-between p-2.5 bg-teal-50 rounded-xl border border-teal-200">
                <span className="text-[11px] font-bold text-teal-800 flex items-center gap-1.5">
                  <Zap className="w-3.5 h-3.5 text-teal-600" />
                  Use Fast Sub-ms RPC
                </span>
                <input
                  type="checkbox"
                  checked={useFastRpc}
                  onChange={(e) => setUseFastRpc(e.target.checked)}
                  className="rounded text-teal-600 focus:ring-teal-500 w-4 h-4"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setDispenseModalStock(null)}
                  className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold shadow-md shadow-teal-600/20"
                >
                  Confirm Dispensation
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

