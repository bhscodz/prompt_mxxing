// File: frontend/src/pages/PatientCRM.jsx
// Description: Full Patient CRM with digital OPD token queue, emergency triage classification, and clinical consultation drawer

import React, { useState, useEffect } from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../services/api';
import { rpcClient } from '../services/rpcClient';
import {
  Users,
  UserPlus,
  Search,
  CheckCircle,
  Clock,
  HeartPulse,
  Stethoscope,
  X,
  Zap
} from 'lucide-react';

export default function PatientCRM({ facilities = [], selectedFacilityId }) {
  const { t } = useLanguage();
  const [visits, setVisits] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [showRegisterModal, setShowRegisterModal] = useState(false);
  const [selectedVisitForConsult, setSelectedVisitForConsult] = useState(null);
  const [consultNotes, setConsultNotes] = useState('');
  const [consultRx, setConsultRx] = useState('');
  const [useFastRpc, setUseFastRpc] = useState(false);
  const [rpcPerfNotice, setRpcPerfNotice] = useState(null);

  // New Patient Form State
  const [formData, setFormData] = useState({
    full_name: '',
    abha_id: '',
    age: '',
    gender: 'Female',
    village: '',
    phone: '',
    chief_complaint: '',
    triage_category: 'standard_green',
    systolic_bp: 120,
    diastolic_bp: 80,
    pulse_rate: 76,
    temperature_f: 98.6,
    spo2: 98,
    facility_id: selectedFacilityId || (facilities[0]?.id || '')
  });

  const fetchVisits = async () => {
    try {
      const data = await api.getOpdVisits(selectedFacilityId ? { facility_id: selectedFacilityId } : {});
      setVisits(data);
    } catch (err) {
      console.error("Error loading visits:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVisits();
    const interval = setInterval(fetchVisits, 10000);
    return () => clearInterval(interval);
  }, [selectedFacilityId]);

  const handleRegisterPatient = async (e) => {
    e.preventDefault();
    const targetFacility = selectedFacilityId || formData.facility_id || facilities[0]?.id;

    try {
      if (useFastRpc) {
        // High-speed JSON-RPC 2.0 path
        const rpcResult = await rpcClient.call('patient.quickRegisterTriage', {
          facility_id: targetFacility,
          full_name: formData.full_name,
          abha_id: formData.abha_id,
          age: parseInt(formData.age) || 30,
          gender: formData.gender,
          village: formData.village || 'Local',
          phone: formData.phone,
          chief_complaint: formData.chief_complaint,
          triage_category: formData.triage_category,
          systolic_bp: parseInt(formData.systolic_bp) || 120,
          diastolic_bp: parseInt(formData.diastolic_bp) || 80,
          spo2: parseInt(formData.spo2) || 98
        });

        setRpcPerfNotice(`Registered via Fast RPC in ${rpcResult.executionTimeMs} ms! Token: ${rpcResult.result.token_number}`);
      } else {
        // Standard REST path
        await api.registerOpdVisit({
          facility_id: targetFacility,
          chief_complaint: formData.chief_complaint,
          triage_category: formData.triage_category,
          systolic_bp: parseInt(formData.systolic_bp) || null,
          diastolic_bp: parseInt(formData.diastolic_bp) || null,
          pulse_rate: parseInt(formData.pulse_rate) || null,
          temperature_f: parseFloat(formData.temperature_f) || null,
          spo2: parseInt(formData.spo2) || null,
          patient_data: {
            full_name: formData.full_name,
            abha_id: formData.abha_id || null,
            age: parseInt(formData.age) || 25,
            gender: formData.gender,
            village: formData.village || 'Local',
            phone: formData.phone || null
          }
        });
      }

      setShowRegisterModal(false);
      fetchVisits();
      setFormData({
        full_name: '',
        abha_id: '',
        age: '',
        gender: 'Female',
        village: '',
        phone: '',
        chief_complaint: '',
        triage_category: 'standard_green',
        systolic_bp: 120,
        diastolic_bp: 80,
        pulse_rate: 76,
        temperature_f: 98.6,
        spo2: 98,
        facility_id: targetFacility
      });
    } catch (err) {
      alert("Registration failed: " + err.message);
    }
  };

  const handleCompleteConsult = async () => {
    if (!selectedVisitForConsult) return;
    try {
      await api.updateOpdVisit(selectedVisitForConsult.id, {
        status: 'completed',
        diagnosis_notes: consultNotes,
        prescribed_medicines: consultRx
      });
      setSelectedVisitForConsult(null);
      setConsultNotes('');
      setConsultRx('');
      fetchVisits();
    } catch (err) {
      alert("Consult update failed: " + err.message);
    }
  };

  const filteredVisits = visits.filter(v => {
    if (!searchQuery) return true;
    const patName = v.patient?.full_name?.toLowerCase() || '';
    const abha = v.patient?.abha_id?.toLowerCase() || '';
    const token = v.token_number?.toLowerCase() || '';
    return patName.includes(searchQuery.toLowerCase()) || abha.includes(searchQuery.toLowerCase()) || token.includes(searchQuery.toLowerCase());
  });

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Users className="w-5 h-5 text-teal-600" />
            {t('crmTitle')}
          </h2>
          <p className="text-xs text-slate-500 mt-1">{t('crmSubtitle')}</p>
        </div>

        <button
          onClick={() => setShowRegisterModal(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold transition shadow-sm shadow-teal-600/30 whitespace-nowrap self-start sm:self-center"
        >
          <UserPlus className="w-4 h-4" />
          <span>{t('btnRegisterPatient')}</span>
        </button>
      </div>

      {rpcPerfNotice && (
        <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center justify-between">
          <span>{rpcPerfNotice}</span>
          <button onClick={() => setRpcPerfNotice(null)} className="font-bold">&times;</button>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="flex items-center gap-3 bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
          <input
            type="text"
            placeholder="Search patient by name, ABHA ID, or token number..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500"
          />
        </div>
        <span className="text-xs font-semibold text-slate-500">
          Total Queue: {filteredVisits.length}
        </span>
      </div>

      {/* OPD Visits Queue Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">{t('thToken')}</th>
                <th className="px-4 py-3">{t('thPatient')}</th>
                <th className="px-4 py-3">{t('thAgeGender')}</th>
                <th className="px-4 py-3">{t('thTriage')}</th>
                <th className="px-4 py-3">{t('thComplaint')}</th>
                <th className="px-4 py-3">{t('thVitals')}</th>
                <th className="px-4 py-3">{t('thStatus')}</th>
                <th className="px-4 py-3 text-right">{t('thActions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredVisits.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-slate-400">
                    No OPD patients in queue for this health centre.
                  </td>
                </tr>
              ) : (
                filteredVisits.map((v) => {
                  const isImmediate = v.triage_category === 'immediate_red';
                  const isUrgent = v.triage_category === 'urgent_yellow';

                  return (
                    <tr key={v.id} className="hover:bg-slate-50 transition">
                      <td className="px-4 py-3 font-bold text-slate-900">
                        <span className="px-2 py-1 rounded bg-slate-100 border border-slate-200">
                          {v.token_number}
                        </span>
                      </td>

                      <td className="px-4 py-3">
                        <div className="font-bold text-slate-800">{v.patient?.full_name || 'Walk-in'}</div>
                        <div className="text-[11px] text-slate-400">ABHA: {v.patient?.abha_id || 'Not linked'}</div>
                      </td>

                      <td className="px-4 py-3 text-slate-600">
                        {v.patient?.age || '-'}y / {v.patient?.gender || '-'}
                      </td>

                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-bold text-[11px] ${
                          isImmediate
                            ? 'bg-red-100 text-red-800 animate-pulse'
                            : isUrgent
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-emerald-100 text-emerald-800'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${isImmediate ? 'bg-red-600' : isUrgent ? 'bg-amber-600' : 'bg-emerald-600'}`}></span>
                          {isImmediate ? t('triageImmediate') : isUrgent ? t('triageUrgent') : t('triageStandard')}
                        </span>
                      </td>

                      <td className="px-4 py-3 text-slate-700 max-w-xs truncate">
                        {v.chief_complaint}
                      </td>

                      <td className="px-4 py-3 text-slate-600 font-mono text-[11px]">
                        {v.systolic_bp && v.diastolic_bp ? `${v.systolic_bp}/${v.diastolic_bp} BP` : ''}
                        {v.pulse_rate ? ` • ${v.pulse_rate} bpm` : ''}
                        {v.spo2 ? ` • ${v.spo2}% SpO2` : ''}
                      </td>

                      <td className="px-4 py-3">
                        <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                          v.status === 'completed'
                            ? 'bg-slate-100 text-slate-600'
                            : v.status === 'in_consultation'
                            ? 'bg-blue-100 text-blue-800'
                            : 'bg-teal-100 text-teal-800'
                        }`}>
                          {v.status === 'completed' ? t('statusCompleted') : v.status === 'in_consultation' ? t('statusConsulting') : t('statusWaiting')}
                        </span>
                      </td>

                      <td className="px-4 py-3 text-right">
                        {v.status !== 'completed' ? (
                          <button
                            onClick={() => {
                              setSelectedVisitForConsult(v);
                              setConsultNotes(v.diagnosis_notes || '');
                              setConsultRx(v.prescribed_medicines || '');
                            }}
                            className="px-2.5 py-1 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 font-bold text-[11px] transition"
                          >
                            {t('btnConsult')}
                          </button>
                        ) : (
                          <span className="text-[11px] text-slate-400 font-medium">Done</span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* New Patient Registration Modal */}
      {showRegisterModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                <UserPlus className="w-5 h-5 text-teal-600" />
                {t('btnRegisterPatient')}
              </h3>
              <button onClick={() => setShowRegisterModal(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleRegisterPatient} className="space-y-4 mt-4 text-xs">
              {/* Fast RPC Toggle */}
              <div className="flex items-center justify-between p-2.5 bg-teal-50/70 rounded-xl border border-teal-200">
                <div className="flex items-center gap-2 text-teal-900 font-semibold">
                  <Zap className="w-4 h-4 text-teal-600" />
                  <span>Use Fast RPC Ingestion (Sub-millisecond)</span>
                </div>
                <input
                  type="checkbox"
                  checked={useFastRpc}
                  onChange={(e) => setUseFastRpc(e.target.checked)}
                  className="rounded text-teal-600 focus:ring-teal-500 w-4 h-4 cursor-pointer"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-slate-600 font-bold mb-1">Full Name *</label>
                  <input
                    type="text"
                    required
                    value={formData.full_name}
                    onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500"
                    placeholder="e.g. Ramesh Jadhav"
                  />
                </div>
                <div>
                  <label className="block text-slate-600 font-bold mb-1">ABHA Health ID</label>
                  <input
                    type="text"
                    value={formData.abha_id}
                    onChange={(e) => setFormData({ ...formData, abha_id: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500"
                    placeholder="91-XXXX-XXXX-XXXX"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-slate-600 font-bold mb-1">Age *</label>
                  <input
                    type="number"
                    required
                    value={formData.age}
                    onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500"
                  />
                </div>
                <div>
                  <label className="block text-slate-600 font-bold mb-1">Gender *</label>
                  <select
                    value={formData.gender}
                    onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500 bg-white"
                  >
                    <option value="Female">Female</option>
                    <option value="Male">Male</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="block text-slate-600 font-bold mb-1">Village / Hamlet</label>
                  <input
                    type="text"
                    value={formData.village}
                    onChange={(e) => setFormData({ ...formData, village: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-600 font-bold mb-1">Chief Complaint *</label>
                <input
                  type="text"
                  required
                  value={formData.chief_complaint}
                  onChange={(e) => setFormData({ ...formData, chief_complaint: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500"
                  placeholder="e.g. Acute chest pain, high fever, abdominal cramps"
                />
              </div>

              <div>
                <label className="block text-slate-600 font-bold mb-1">Triage Priority *</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'immediate_red', label: t('triageImmediate'), color: 'border-red-400 bg-red-50 text-red-800' },
                    { id: 'urgent_yellow', label: t('triageUrgent'), color: 'border-amber-400 bg-amber-50 text-amber-800' },
                    { id: 'standard_green', label: t('triageStandard'), color: 'border-emerald-400 bg-emerald-50 text-emerald-800' },
                  ].map((tr) => (
                    <button
                      type="button"
                      key={tr.id}
                      onClick={() => setFormData({ ...formData, triage_category: tr.id })}
                      className={`p-2 rounded-lg border text-center font-bold text-[11px] transition ${
                        formData.triage_category === tr.id ? `${tr.color} ring-2 ring-teal-500` : 'border-slate-200 bg-slate-50 text-slate-600'
                      }`}
                    >
                      {tr.label}
                    </button>
                  ))}
                </div>
              </div>

              {/* Vitals */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 space-y-2">
                <span className="font-bold text-slate-700 block">Baseline Triage Vitals</span>
                <div className="grid grid-cols-4 gap-2">
                  <div>
                    <label className="text-[10px] text-slate-500 font-medium">Systolic BP</label>
                    <input
                      type="number"
                      value={formData.systolic_bp}
                      onChange={(e) => setFormData({ ...formData, systolic_bp: e.target.value })}
                      className="w-full px-2 py-1 bg-white border border-slate-200 rounded"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-500 font-medium">Diastolic BP</label>
                    <input
                      type="number"
                      value={formData.diastolic_bp}
                      onChange={(e) => setFormData({ ...formData, diastolic_bp: e.target.value })}
                      className="w-full px-2 py-1 bg-white border border-slate-200 rounded"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-500 font-medium">SpO2 (%)</label>
                    <input
                      type="number"
                      value={formData.spo2}
                      onChange={(e) => setFormData({ ...formData, spo2: e.target.value })}
                      className="w-full px-2 py-1 bg-white border border-slate-200 rounded"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] text-slate-500 font-medium">Temp (°F)</label>
                    <input
                      type="number"
                      step="0.1"
                      value={formData.temperature_f}
                      onChange={(e) => setFormData({ ...formData, temperature_f: e.target.value })}
                      className="w-full px-2 py-1 bg-white border border-slate-200 rounded"
                    />
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setShowRegisterModal(false)}
                  className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold shadow-md shadow-teal-600/20"
                >
                  Issue OPD Token
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Clinical Consultation Drawer / Modal */}
      {selectedVisitForConsult && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-teal-100 text-teal-800">
                  {selectedVisitForConsult.token_number}
                </span>
                <h3 className="text-base font-bold text-slate-900 mt-1">
                  Doctor Consultation: {selectedVisitForConsult.patient?.full_name}
                </h3>
              </div>
              <button onClick={() => setSelectedVisitForConsult(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="mt-4 space-y-4 text-xs">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 text-slate-700">
                <span className="font-bold text-slate-900 block mb-1">Chief Complaint</span>
                {selectedVisitForConsult.chief_complaint}
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Clinical Diagnosis & Notes</label>
                <textarea
                  rows="3"
                  value={consultNotes}
                  onChange={(e) => setConsultNotes(e.target.value)}
                  placeholder="Enter diagnosis, symptoms, clinical findings..."
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500 text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Prescription & Medical Orders</label>
                <textarea
                  rows="2"
                  value={consultRx}
                  onChange={(e) => setConsultRx(e.target.value)}
                  placeholder="e.g. Tab Paracetamol 500mg TDS x 3 days, Tab Amoxicillin 250mg BD"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500 text-xs font-mono"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  onClick={() => setSelectedVisitForConsult(null)}
                  className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-bold"
                >
                  Close
                </button>
                <button
                  onClick={handleCompleteConsult}
                  className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold shadow-md shadow-teal-600/20"
                >
                  Complete & Save Consultation
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

