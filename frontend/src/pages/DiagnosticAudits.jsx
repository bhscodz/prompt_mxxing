// File: frontend/src/pages/DiagnosticAudits.jsx
// Description: Diagnostic test availability audits, reagent inventory checks, and laboratory equipment compliance

import React, { useState, useEffect } from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../services/api';
import {
  FlaskConical,
  CheckCircle2,
  AlertCircle,
  Wrench,
  Clock,
  Edit2,
  X
} from 'lucide-react';

export default function DiagnosticAudits({ facilities = [], selectedFacilityId }) {
  const { t } = useLanguage();
  const [tests, setTests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingTest, setEditingTest] = useState(null);
  const [editReagentsStock, setEditReagentsStock] = useState(100);
  const [editEquipmentFunctional, setEditEquipmentFunctional] = useState(true);

  const fetchAudits = async () => {
    try {
      const params = selectedFacilityId ? { facility_id: selectedFacilityId } : {};
      const data = await api.getDiagnosticAudits(params);
      setTests(data);
    } catch (err) {
      console.error("Error loading diagnostic tests:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAudits();
    const interval = setInterval(fetchAudits, 12000);
    return () => clearInterval(interval);
  }, [selectedFacilityId]);

  const handleUpdateAudit = async (e) => {
    e.preventDefault();
    if (!editingTest) return;

    try {
      await api.updateDiagnosticAudit(editingTest.id, {
        reagents_stock_units: parseInt(editReagentsStock) || 0,
        reagents_available: editReagentsStock > 0,
        equipment_functional: editEquipmentFunctional
      });
      setEditingTest(null);
      fetchAudits();
    } catch (err) {
      alert("Audit update failed: " + err.message);
    }
  };

  const compliantCount = tests.filter(t => t.audit_compliance_status === 'compliant').length;
  const deficitCount = tests.filter(t => t.audit_compliance_status !== 'compliant').length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <FlaskConical className="w-5 h-5 text-teal-600" />
            {t('diagTitle')}
          </h2>
          <p className="text-xs text-slate-500 mt-1">{t('diagSubtitle')}</p>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs font-bold px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-700 border border-emerald-200">
            {compliantCount} Fully Available
          </span>
          {deficitCount > 0 && (
            <span className="text-xs font-bold px-3 py-1.5 rounded-xl bg-rose-50 text-rose-700 border border-rose-200 animate-pulse">
              {deficitCount} Service Bottlenecks
            </span>
          )}
        </div>
      </div>

      {/* Tests Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">{t('thTestName')}</th>
                <th className="px-4 py-3">{t('thTestCategory')}</th>
                <th className="px-4 py-3">{t('thReagents')}</th>
                <th className="px-4 py-3">{t('thEquipment')}</th>
                <th className="px-4 py-3">{t('thTestsToday')}</th>
                <th className="px-4 py-3">{t('thTurnaround')}</th>
                <th className="px-4 py-3">{t('thCompliance')}</th>
                <th className="px-4 py-3 text-right">Audit Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {tests.length === 0 ? (
                <tr>
                  <td colSpan="8" className="py-8 text-center text-slate-400">
                    No diagnostic tests listed for this facility.
                  </td>
                </tr>
              ) : (
                tests.map((test) => {
                  const isCompliant = test.audit_compliance_status === 'compliant';
                  const isReagentDeficit = test.audit_compliance_status === 'reagent_deficit';

                  return (
                    <tr key={test.id} className="hover:bg-slate-50 transition">
                      <td className="px-4 py-3 font-bold text-slate-900">
                        {test.test_name}
                      </td>

                      <td className="px-4 py-3 text-slate-600 font-medium">
                        {test.category}
                      </td>

                      <td className="px-4 py-3">
                        <span className={`font-mono text-xs font-bold ${test.reagents_stock_units < 20 ? 'text-rose-600' : 'text-slate-700'}`}>
                          {test.reagents_stock_units} kits
                        </span>
                      </td>

                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 font-semibold text-[11px] ${
                          test.equipment_functional ? 'text-emerald-700' : 'text-rose-600'
                        }`}>
                          {test.equipment_functional ? (
                            <>
                              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500" />
                              Operational
                            </>
                          ) : (
                            <>
                              <Wrench className="w-3.5 h-3.5 text-rose-500" />
                              Breakdown
                            </>
                          )}
                        </span>
                      </td>

                      <td className="px-4 py-3 font-bold text-slate-900">
                        {test.tests_conducted_today}
                      </td>

                      <td className="px-4 py-3 text-slate-600">
                        ~{test.average_turnaround_mins} mins
                      </td>

                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-bold text-[11px] ${
                          isCompliant
                            ? 'bg-emerald-100 text-emerald-800'
                            : isReagentDeficit
                            ? 'bg-rose-100 text-rose-800 animate-pulse'
                            : 'bg-amber-100 text-amber-800'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${isCompliant ? 'bg-emerald-600' : 'bg-rose-600'}`}></span>
                          {isCompliant ? t('compliant') : isReagentDeficit ? t('reagentDeficit') : t('equipmentBreakdown')}
                        </span>
                      </td>

                      <td className="px-4 py-3 text-right">
                        <button
                          onClick={() => {
                            setEditingTest(test);
                            setEditReagentsStock(test.reagents_stock_units);
                            setEditEquipmentFunctional(test.equipment_functional);
                          }}
                          className="px-2.5 py-1 rounded-lg bg-teal-50 hover:bg-teal-100 text-teal-700 font-bold text-[11px] transition inline-flex items-center gap-1"
                        >
                          <Edit2 className="w-3 h-3" />
                          <span>Audit</span>
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

      {/* Edit Audit Modal */}
      {editingTest && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-sm w-full p-6 shadow-2xl border border-slate-100 animate-in fade-in zoom-in-95">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <FlaskConical className="w-4 h-4 text-teal-600" />
                Audit: {editingTest.test_name}
              </h3>
              <button onClick={() => setEditingTest(null)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleUpdateAudit} className="space-y-4 mt-4 text-xs">
              <div>
                <label className="block text-slate-700 font-bold mb-1">Reagent Units in Stock</label>
                <input
                  type="number"
                  min="0"
                  value={editReagentsStock}
                  onChange={(e) => setEditReagentsStock(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-xs"
                />
              </div>

              <div>
                <label className="block text-slate-700 font-bold mb-1">Diagnostic Equipment Status</label>
                <div className="flex items-center gap-3">
                  <label className="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                    <input
                      type="radio"
                      name="equipment_functional"
                      checked={editEquipmentFunctional === true}
                      onChange={() => setEditEquipmentFunctional(true)}
                      className="text-teal-600"
                    />
                    Operational
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer font-medium text-slate-700">
                    <input
                      type="radio"
                      name="equipment_functional"
                      checked={editEquipmentFunctional === false}
                      onChange={() => setEditEquipmentFunctional(false)}
                      className="text-teal-600"
                    />
                    Breakdown / Needs Repair
                  </label>
                </div>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setEditingTest(null)}
                  className="px-4 py-2 rounded-xl text-slate-600 hover:bg-slate-100 font-bold"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-xl bg-teal-600 hover:bg-teal-700 text-white font-bold shadow-md shadow-teal-600/20"
                >
                  Save Audit Record
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

