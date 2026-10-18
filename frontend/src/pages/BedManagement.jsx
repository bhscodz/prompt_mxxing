// File: frontend/src/pages/BedManagement.jsx
// Description: Real-time bed occupancy matrix, ward management, oxygen support tracking, and 1-click allocation/discharge

import React, { useState, useEffect } from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../services/api';
import {
  BedDouble,
  Activity,
  CheckCircle,
  User,
  Clock,
  Wind,
  Plus,
  X
} from 'lucide-react';

export default function BedManagement({ facilities = [], selectedFacilityId }) {
  const { t } = useLanguage();
  const [beds, setBeds] = useState([]);
  const [selectedWard, setSelectedWard] = useState('All');
  const [loading, setLoading] = useState(true);

  // Allocate Modal State
  const [allocateModalBed, setAllocateModalBed] = useState(null);
  const [patientName, setPatientName] = useState('');

  const fetchBeds = async () => {
    try {
      const params = selectedFacilityId ? { facility_id: selectedFacilityId } : {};
      const data = await api.getBeds(params);
      setBeds(data);
    } catch (err) {
      console.error("Error loading beds:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBeds();
    const interval = setInterval(fetchBeds, 10000);
    return () => clearInterval(interval);
  }, [selectedFacilityId]);

  const handleAllocate = async (e) => {
    e.preventDefault();
    if (!allocateModalBed) return;

    try {
      await api.allocateBed(allocateModalBed.id, {
        patient_name: patientName,
        oxygen_required: allocateModalBed.oxygen_supported
      });
      setAllocateModalBed(null);
      setPatientName('');
      fetchBeds();
    } catch (err) {
      alert("Bed allocation failed: " + err.message);
    }
  };

  const handleDischarge = async (bedId) => {
    if (!confirm("Are you sure you want to discharge this patient and mark bed available?")) return;
    try {
      await api.dischargeBed(bedId);
      fetchBeds();
    } catch (err) {
      alert("Discharge failed: " + err.message);
    }
  };

  const wards = [
    'All',
    'General Male',
    'General Female',
    'Maternity / Labor',
    'Pediatric',
    'Emergency / Triage',
    'ICU / High Dependency'
  ];

  const filteredBeds = selectedWard === 'All'
    ? beds
    : beds.filter(b => b.ward_type === selectedWard);

  const totalBeds = filteredBeds.length;
  const occupiedBeds = filteredBeds.filter(b => b.status === 'occupied').length;
  const occupancyPct = totalBeds > 0 ? Math.round((occupiedBeds / totalBeds) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <BedDouble className="w-5 h-5 text-teal-600" />
            {t('bedTitle')}
          </h2>
          <p className="text-xs text-slate-500 mt-1">{t('bedSubtitle')}</p>
        </div>

        <div className="flex items-center gap-4">
          <div className="text-right">
            <div className="text-[11px] font-semibold text-slate-400">Ward Occupancy</div>
            <div className="text-lg font-bold text-slate-900">{occupancyPct}% ({occupiedBeds}/{totalBeds})</div>
          </div>
          <div className="w-24 bg-slate-100 rounded-full h-2.5 overflow-hidden">
            <div
              className={`h-full rounded-full ${occupancyPct > 80 ? 'bg-red-500' : 'bg-teal-500'}`}
              style={{ width: `${occupancyPct}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Ward Filter Pills */}
      <div className="flex items-center gap-2 overflow-x-auto pb-1 text-xs">
        {wards.map((ward) => (
          <button
            key={ward}
            onClick={() => setSelectedWard(ward)}
            className={`px-3 py-1.5 rounded-xl font-bold transition whitespace-nowrap ${
              selectedWard === ward
                ? 'bg-teal-600 text-white shadow-sm'
                : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
            }`}
          >
            {ward === 'All' ? t('wardAll') : ward}
          </button>
        ))}
      </div>

      {/* Live Bed Matrix Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
        {filteredBeds.map((b) => {
          const isOccupied = b.status === 'occupied';

          return (
            <div
              key={b.id}
              className={`p-3.5 rounded-2xl border transition relative flex flex-col justify-between ${
                isOccupied
                  ? 'bg-rose-50/60 border-rose-200 hover:border-rose-300'
                  : 'bg-emerald-50/40 border-emerald-200 hover:border-emerald-400 shadow-sm'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-xs font-black text-slate-900">{b.bed_number}</span>
                  {b.oxygen_supported && (
                    <span className="p-1 rounded bg-teal-100 text-teal-800" title="Oxygen Supported">
                      <Wind className="w-3 h-3" />
                    </span>
                  )}
                </div>

                <div className="text-[10px] text-slate-500 font-semibold truncate mb-2">
                  {b.ward_type}
                </div>

                {isOccupied ? (
                  <div className="bg-white/80 p-2 rounded-xl border border-rose-100 mb-2">
                    <div className="text-[11px] font-bold text-slate-800 truncate flex items-center gap-1">
                      <User className="w-3 h-3 text-rose-500" />
                      {b.allocated_patient_name || 'Patient'}
                    </div>
                    <div className="text-[10px] text-slate-400 flex items-center gap-1 mt-0.5">
                      <Clock className="w-2.5 h-2.5" />
                      Admitted
                    </div>
                  </div>
                ) : (
                  <div className="text-[11px] font-bold text-emerald-700 py-3 text-center">
                    Available
                  </div>
                )}
              </div>

              <div>
                {isOccupied ? (
                  <button
                    onClick={() => handleDischarge(b.id)}
                    className="w-full py-1 rounded-lg bg-rose-100 hover:bg-rose-200 text-rose-800 text-[11px] font-bold transition"
                  >
                    {t('btnDischarge')}
                  </button>
                ) : (
                  <button
                    onClick={() => setAllocateModalBed(b)}
                    className="w-full py-1 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white text-[11px] font-bold transition shadow-sm"
                  >
                    {t('btnAllocateBed')}
                  </button>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Allocate Bed Modal */}
      {allocateModalBed && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <BedDouble className="w-4 h-4 text-teal-600" />
                Allocate {allocateModalBed.bed_number}
              </h3>
              <button onClick={() => setAllocateModalBed(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAllocate} className="space-y-4 mt-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-slate-600 space-y-1">
                <div>Ward: <strong className="text-slate-800">{allocateModalBed.ward_type}</strong></div>
                <div>Oxygen Supported: <strong className="text-slate-800">{allocateModalBed.oxygen_supported ? 'Yes' : 'No'}</strong></div>
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Patient Full Name *</label>
                <input
                  type="text"
                  required
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  placeholder="e.g. Anand Shinde"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500 text-xs"
                />
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setAllocateModalBed(null)}
                  className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold shadow-md shadow-teal-600/20"
                >
                  Confirm Admission
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

