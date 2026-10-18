// File: frontend/src/pages/DoctorAttendance.jsx
// Description: Doctor & clinical staff biometric attendance, shift roster, and specialty coverage gap audits

import React, { useState, useEffect } from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../services/api';
import {
  Stethoscope,
  Fingerprint,
  AlertTriangle,
  CheckCircle,
  Clock,
  UserCheck,
  ShieldAlert,
  Search
} from 'lucide-react';

export default function DoctorAttendance({ facilities = [], selectedFacilityId }) {
  const { t } = useLanguage();
  const [staffList, setStaffList] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchStaff = async () => {
    try {
      const params = selectedFacilityId ? { facility_id: selectedFacilityId } : {};
      const data = await api.getStaff(params);
      setStaffList(data);
    } catch (err) {
      console.error("Error loading staff:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStaff();
    const interval = setInterval(fetchStaff, 12000);
    return () => clearInterval(interval);
  }, [selectedFacilityId]);

  const handlePunch = async (staffId, newStatus) => {
    try {
      await api.recordPunch({
        staff_id: staffId,
        status: newStatus
      });
      fetchStaff();
    } catch (err) {
      alert("Punch record failed: " + err.message);
    }
  };

  // Check for critical specialty absences (e.g., Gynecologist or Pediatrician)
  const missingSpecialties = staffList.filter(s =>
    (s.role.includes("Gynecologist") || s.role.includes("OBGYN") || s.role.includes("Pediatrician")) &&
    s.attendance_status !== "Present"
  );

  const filteredStaff = staffList.filter(s => {
    if (!searchQuery) return true;
    return s.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
           s.role.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const totalStaff = staffList.length;
  const presentStaff = staffList.filter(s => s.attendance_status === 'Present').length;
  const attendancePct = totalStaff > 0 ? Math.round((presentStaff / totalStaff) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Stethoscope className="w-5 h-5 text-teal-600" />
            {t('attTitle')}
          </h2>
          <p className="text-xs text-slate-500 mt-1">{t('attSubtitle')}</p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <div className="text-[11px] font-semibold text-slate-400">Duty Attendance</div>
            <div className="text-lg font-bold text-teal-700">{attendancePct}% Present ({presentStaff}/{totalStaff})</div>
          </div>
        </div>
      </div>

      {/* Specialty Gap Alert if OBGYN or Pediatrician absent */}
      {missingSpecialties.length > 0 && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-2xl flex items-start gap-3">
          <div className="p-2 bg-amber-100 rounded-xl text-amber-700">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-xs font-bold text-amber-900 uppercase tracking-wide">
              Specialist Coverage Audit Gap Detected
            </h4>
            <p className="text-xs text-amber-800 mt-0.5">
              Critical medical officers are currently absent or off-duty: {missingSpecialties.map(m => `${m.full_name} (${m.role})`).join(', ')}.
              District CMO notified for roving specialist dispatch.
            </p>
          </div>
        </div>
      )}

      {/* Staff Roster Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <div className="relative flex-1 max-w-sm">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            <input
              type="text"
              placeholder="Search staff or specialty..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 text-xs border border-slate-200 rounded-lg focus:outline-none focus:border-teal-500"
            />
          </div>
          <span className="text-xs font-semibold text-slate-500">
            {filteredStaff.length} Doctors & Staff Listed
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
              <tr>
                <th className="px-4 py-3">{t('thStaffName')}</th>
                <th className="px-4 py-3">{t('thRole')}</th>
                <th className="px-4 py-3">{t('thShift')}</th>
                <th className="px-4 py-3">{t('thPunchTime')}</th>
                <th className="px-4 py-3">{t('thAttStatus')}</th>
                <th className="px-4 py-3 text-right">Biometric Punch Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredStaff.length === 0 ? (
                <tr>
                  <td colSpan="6" className="py-8 text-center text-slate-400">
                    No clinical staff records found.
                  </td>
                </tr>
              ) : (
                filteredStaff.map((s) => {
                  const isPresent = s.attendance_status === 'Present';

                  return (
                    <tr key={s.id} className="hover:bg-slate-50 transition">
                      <td className="px-4 py-3 font-bold text-slate-900">
                        <div className="text-sm">{s.full_name}</div>
                        <div className="text-[11px] text-slate-400 font-normal">Reg: {s.registration_number}</div>
                      </td>

                      <td className="px-4 py-3 text-slate-700 font-semibold">
                        {s.role}
                      </td>

                      <td className="px-4 py-3 text-slate-600">
                        {s.shift_timing}
                      </td>

                      <td className="px-4 py-3 text-slate-500 font-mono text-[11px]">
                        {s.biometric_punch_in
                          ? new Date(s.biometric_punch_in).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                          : 'No punch recorded'}
                      </td>

                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full font-bold text-[11px] ${
                          isPresent
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-rose-100 text-rose-800 animate-pulse'
                        }`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${isPresent ? 'bg-emerald-600' : 'bg-rose-600'}`}></span>
                          {isPresent ? t('statusPresent') : t('statusAbsent')}
                        </span>
                      </td>

                      <td className="px-4 py-3 text-right">
                        <div className="inline-flex items-center gap-1.5">
                          {isPresent ? (
                            <button
                              onClick={() => handlePunch(s.id, 'Absent')}
                              className="px-2.5 py-1 rounded-lg bg-rose-50 hover:bg-rose-100 text-rose-700 font-bold text-[11px] transition"
                            >
                              Punch Out / Leave
                            </button>
                          ) : (
                            <button
                              onClick={() => handlePunch(s.id, 'Present')}
                              className="px-2.5 py-1 rounded-lg bg-emerald-50 hover:bg-emerald-100 text-emerald-700 font-bold text-[11px] transition flex items-center gap-1"
                            >
                              <Fingerprint className="w-3.5 h-3.5" />
                              <span>{t('btnPunchIn')}</span>
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

