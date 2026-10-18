// File: frontend/src/pages/RedistributionEngine.jsx
// Description: Intra-district smart resource redistribution optimizer transferring surplus stock to deficit PHCs

import React, { useState, useEffect } from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../services/api';
import {
  ArrowLeftRight,
  Truck,
  CheckCircle,
  MapPin,
  Clock,
  Send,
  Sparkles,
  AlertTriangle,
  Building
} from 'lucide-react';

export default function RedistributionEngine({ facilities = [] }) {
  const { t } = useLanguage();
  const [recommendations, setRecommendations] = useState([]);
  const [transfers, setTransfers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('recommendations'); // recommendations | active_transfers

  const fetchRedistributionData = async () => {
    try {
      const [recs, trans] = await Promise.all([
        api.getRedistributionRecommendations(),
        api.getTransfers()
      ]);
      setRecommendations(recs);
      setTransfers(trans);
    } catch (err) {
      console.error("Error fetching redistribution:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRedistributionData();
    const interval = setInterval(fetchRedistributionData, 12000);
    return () => clearInterval(interval);
  }, []);

  const handleApprove = async (rec) => {
    try {
      await api.createTransfer({
        source_facility_id: rec.source_facility_id,
        target_facility_id: rec.target_facility_id,
        item_type: rec.item_type || 'medicine',
        item_name: rec.item_name,
        quantity: rec.quantity,
        unit: rec.unit,
        haversine_distance_km: rec.haversine_distance_km,
        estimated_transit_hours: rec.estimated_transit_hours,
        urgency_reason: rec.urgency_reason,
        status: 'approved_by_admin'
      });
      fetchRedistributionData();
      setActiveTab('active_transfers');
    } catch (err) {
      alert("Transfer approval failed: " + err.message);
    }
  };

  const handleExecuteAction = async (transferId, action) => {
    try {
      await api.executeTransferAction(transferId, action, 'District Medical Officer');
      fetchRedistributionData();
    } catch (err) {
      alert(`Action '${action}' failed: ` + err.message);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <div className="p-2 bg-teal-50 rounded-xl text-teal-700">
              <ArrowLeftRight className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold text-slate-900">{t('redistTitle')}</h2>
          </div>
          <p className="text-xs text-slate-500 mt-1">{t('redistSubtitle')}</p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition ${
              activeTab === 'recommendations'
                ? 'bg-teal-600 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            AI Recommendations ({recommendations.length})
          </button>
          <button
            onClick={() => setActiveTab('active_transfers')}
            className={`px-3 py-1.5 rounded-xl font-bold text-xs transition ${
              activeTab === 'active_transfers'
                ? 'bg-teal-600 text-white shadow-sm'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            Dispatched Transfers ({transfers.length})
          </button>
        </div>
      </div>

      {activeTab === 'recommendations' ? (
        /* AI Suggested Transfers Grid */
        <div className="space-y-4">
          {recommendations.length === 0 ? (
            <div className="bg-white p-8 rounded-2xl border border-slate-200 text-center shadow-sm">
              <CheckCircle className="w-8 h-8 text-emerald-500 mx-auto mb-2" />
              <h3 className="text-sm font-bold text-slate-800">District Resources Perfectly Balanced</h3>
              <p className="text-xs text-slate-500 mt-1 max-w-md mx-auto">
                No acute stock deficits detected across the district's PHCs and CHCs. All buffer levels comply with 14-day safety thresholds.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recommendations.map((rec, idx) => (
                <div
                  key={idx}
                  className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:border-teal-300 transition flex flex-col justify-between"
                >
                  <div>
                    {/* Header item */}
                    <div className="flex items-start justify-between gap-3 mb-3 pb-3 border-b border-slate-100">
                      <div>
                        <span className="text-[10px] font-bold uppercase tracking-wider text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full flex items-center gap-1 w-fit mb-1">
                          <Sparkles className="w-3 h-3 text-teal-600" />
                          Algorithmic Balancing Order
                        </span>
                        <h3 className="text-base font-bold text-slate-900">{rec.item_name}</h3>
                      </div>
                      <div className="text-right">
                        <span className="text-base font-black text-teal-700">
                          {rec.quantity} {rec.unit}
                        </span>
                        <div className="text-[10px] text-slate-400">Transfer Batch</div>
                      </div>
                    </div>

                    {/* Transfer Direction Flow */}
                    <div className="grid grid-cols-5 items-center gap-2 p-3 bg-slate-50 rounded-xl mb-3 text-xs">
                      {/* Source */}
                      <div className="col-span-2">
                        <span className="text-[10px] font-bold text-emerald-700 uppercase block">Source (Surplus)</span>
                        <div className="font-bold text-slate-800 text-xs truncate">{rec.source_facility_name}</div>
                        <span className="text-[10px] text-slate-400">Surplus Safe</span>
                      </div>

                      {/* Distance Icon */}
                      <div className="col-span-1 text-center">
                        <Truck className="w-4 h-4 text-teal-600 mx-auto animate-bounce" />
                        <div className="text-[10px] font-bold text-slate-500 mt-0.5">{rec.haversine_distance_km} km</div>
                      </div>

                      {/* Target */}
                      <div className="col-span-2 text-right">
                        <span className="text-[10px] font-bold text-rose-700 uppercase block">Target (Deficit)</span>
                        <div className="font-bold text-slate-800 text-xs truncate">{rec.target_facility_name}</div>
                        <span className="text-[10px] text-rose-600 font-semibold">Immediate Need</span>
                      </div>
                    </div>

                    {/* Transit & Reason */}
                    <div className="space-y-1.5 text-xs text-slate-600 mb-4">
                      <div className="flex items-center gap-1.5 text-[11px] text-slate-500">
                        <Clock className="w-3.5 h-3.5 text-slate-400" />
                        <span>Estimated Rural Transit Time: <strong>~{rec.estimated_transit_hours} hours</strong></span>
                      </div>
                      <p className="text-[11px] text-slate-600 bg-amber-50/60 p-2 rounded-lg border border-amber-200">
                        <strong>Urgency:</strong> {rec.urgency_reason}
                      </p>
                    </div>
                  </div>

                  {/* 1-Click Approve Button */}
                  <button
                    onClick={() => handleApprove(rec)}
                    className="w-full flex items-center justify-center gap-2 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs shadow-md shadow-teal-600/20 transition"
                  >
                    <Send className="w-3.5 h-3.5" />
                    <span>{t('btnApproveTransfer')}</span>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Dispatched & In-Transit Transfers Table */
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                <tr>
                  <th className="px-4 py-3">{t('thItem')}</th>
                  <th className="px-4 py-3">{t('thQuantity')}</th>
                  <th className="px-4 py-3">{t('thDistance')}</th>
                  <th className="px-4 py-3">{t('thTransitTime')}</th>
                  <th className="px-4 py-3">Status</th>
                  <th className="px-4 py-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {transfers.length === 0 ? (
                  <tr>
                    <td colSpan="6" className="py-8 text-center text-slate-400">
                      No transfer consignments have been dispatched yet.
                    </td>
                  </tr>
                ) : (
                  transfers.map((tr) => (
                    <tr key={tr.id} className="hover:bg-slate-50 transition">
                      <td className="px-4 py-3 font-bold text-slate-900">
                        {tr.item_name}
                      </td>

                      <td className="px-4 py-3 font-bold text-teal-800">
                        {tr.quantity} {tr.unit}
                      </td>

                      <td className="px-4 py-3 text-slate-600">
                        {tr.haversine_distance_km} km
                      </td>

                      <td className="px-4 py-3 text-slate-600">
                        ~{tr.estimated_transit_hours} hrs
                      </td>

                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-bold text-[11px] ${
                          tr.status === 'received'
                            ? 'bg-emerald-100 text-emerald-800'
                            : tr.status === 'in_transit'
                            ? 'bg-blue-100 text-blue-800 animate-pulse'
                            : 'bg-amber-100 text-amber-800'
                        }`}>
                          {tr.status === 'received' ? 'Received & Stock Credited' : tr.status === 'in_transit' ? 'In Transit' : 'Approved & Awaiting Dispatch'}
                        </span>
                      </td>

                      <td className="px-4 py-3 text-right">
                        {tr.status === 'approved_by_admin' && (
                          <button
                            onClick={() => handleExecuteAction(tr.id, 'dispatch')}
                            className="px-2.5 py-1 rounded-lg bg-blue-50 hover:bg-blue-100 text-blue-700 font-bold text-[11px] transition"
                          >
                            Mark In Transit
                          </button>
                        )}
                        {tr.status === 'in_transit' && (
                          <button
                            onClick={() => handleExecuteAction(tr.id, 'receive')}
                            className="px-2.5 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-bold text-[11px] transition"
                          >
                            Confirm Receipt & Adjust Stocks
                          </button>
                        )}
                        {tr.status === 'received' && (
                          <span className="text-[11px] text-slate-400 font-semibold">Completed</span>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

