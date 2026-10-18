// File: frontend/src/pages/LeaveManagementPage.jsx
// Description: Full staff leave management UI with tabbed navigation for My Requests,
// Pending Approvals, Team Calendar, Leave Balances (recharts BarChart), and Coverage Gaps.
// Multilingual via LanguageContext. Uses TailwindCSS throughout.

import React, { useState, useEffect, useCallback } from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { api } from '../services/api';
import {
  Calendar,
  ClipboardList,
  CheckCircle2,
  BarChart3,
  ShieldAlert,
  Plus,
  X,
  ChevronLeft,
  ChevronRight,
  User,
  Clock,
  AlertCircle,
  CheckCheck,
  Ban,
  Send,
  Loader2,
  FileText,
  Users
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, Cell, Legend
} from 'recharts';

// ─── Constants ───────────────────────────────────────────────────
const TABS = [
  { id: 'my-requests',       label: 'My Requests',       icon: ClipboardList },
  { id: 'pending-approvals', label: 'Pending Approvals',  icon: CheckCircle2  },
  { id: 'team-calendar',     label: 'Team Calendar',      icon: Calendar      },
  { id: 'leave-balances',    label: 'Leave Balances',     icon: BarChart3     },
  { id: 'coverage-gaps',     label: 'Coverage Gaps',      icon: ShieldAlert   },
];

const STATUS_BADGE = {
  PENDING:         'bg-yellow-100 text-yellow-800 border border-yellow-200',
  APPROVED_L1:     'bg-blue-100 text-blue-800 border border-blue-200',
  APPROVED_L2:     'bg-indigo-100 text-indigo-800 border border-indigo-200',
  FULLY_APPROVED:  'bg-emerald-100 text-emerald-800 border border-emerald-200',
  REJECTED:        'bg-red-100 text-red-800 border border-red-200',
  CANCELLED:       'bg-gray-100 text-gray-600 border border-gray-200',
};

const STATUS_ICON = {
  PENDING:         <Clock className="w-3 h-3" />,
  APPROVED_L1:     <CheckCheck className="w-3 h-3" />,
  APPROVED_L2:     <CheckCheck className="w-3 h-3" />,
  FULLY_APPROVED:  <CheckCircle2 className="w-3 h-3" />,
  REJECTED:        <Ban className="w-3 h-3" />,
  CANCELLED:       <X className="w-3 h-3" />,
};

// Role-based dot colours for the calendar
const ROLE_COLORS = {
  'Medical Officer':  '#6366f1',
  'Staff Nurse':      '#10b981',
  'Pharmacist':       '#f59e0b',
  'Lab Technician':   '#3b82f6',
  'AYUSH Doctor':     '#8b5cf6',
  default:            '#94a3b8',
};

// ─── Helpers ─────────────────────────────────────────────────────
function roleDotColor(role = '') {
  for (const key of Object.keys(ROLE_COLORS)) {
    if (key !== 'default' && role.toLowerCase().includes(key.toLowerCase())) {
      return ROLE_COLORS[key];
    }
  }
  return ROLE_COLORS.default;
}

function StatusBadge({ status }) {
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[11px] font-bold ${STATUS_BADGE[status] || STATUS_BADGE.CANCELLED}`}>
      {STATUS_ICON[status]}
      {status?.replace(/_/g, ' ')}
    </span>
  );
}

// ─── Submit Leave Modal ───────────────────────────────────────────
function SubmitLeaveModal({ leaveTypes, staffList, onClose, onSubmitted }) {
  const { t } = useLanguage();
  const [form, setForm] = useState({
    staff_id: '',
    leave_type_id: '',
    start_date: '',
    end_date: '',
    total_days: 1,
    reason: '',
    emergency_contact: '',
    cover_arrangement: '',
  });
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Auto-compute total_days when dates change
  useEffect(() => {
    if (form.start_date && form.end_date) {
      const diff = (new Date(form.end_date) - new Date(form.start_date)) / 86400000 + 1;
      if (diff > 0) setForm(f => ({ ...f, total_days: diff }));
    }
  }, [form.start_date, form.end_date]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await api.submitLeaveRequest(form);
      onSubmitted();
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const inputCls = 'w-full text-xs border border-slate-200 rounded-lg px-3 py-2 focus:outline-none focus:border-teal-500 bg-white';

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-lg border border-slate-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h3 className="font-bold text-slate-900 flex items-center gap-2">
            <FileText className="w-4 h-4 text-teal-600" />
            Submit Leave Request
          </h3>
          <button onClick={onClose} className="p-1.5 hover:bg-slate-100 rounded-lg transition">
            <X className="w-4 h-4 text-slate-500" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4 max-h-[80vh] overflow-y-auto">
          {/* Staff Select */}
          <div>
            <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1 block">
              Staff Member *
            </label>
            <select
              required
              value={form.staff_id}
              onChange={e => setForm(f => ({ ...f, staff_id: e.target.value }))}
              className={inputCls}
            >
              <option value="">Select staff...</option>
              {staffList.map(s => (
                <option key={s.id} value={s.id}>{s.full_name} — {s.role}</option>
              ))}
            </select>
          </div>

          {/* Leave Type */}
          <div>
            <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1 block">
              Leave Type *
            </label>
            <select
              required
              value={form.leave_type_id}
              onChange={e => setForm(f => ({ ...f, leave_type_id: e.target.value }))}
              className={inputCls}
            >
              <option value="">Select type...</option>
              {leaveTypes.map(lt => (
                <option key={lt.id} value={lt.id}>{lt.name} (max {lt.max_days_per_year} days/yr)</option>
              ))}
            </select>
          </div>

          {/* Date Range */}
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1 block">
                Start Date *
              </label>
              <input type="date" required value={form.start_date}
                onChange={e => setForm(f => ({ ...f, start_date: e.target.value }))}
                className={inputCls} />
            </div>
            <div>
              <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1 block">
                End Date *
              </label>
              <input type="date" required value={form.end_date} min={form.start_date}
                onChange={e => setForm(f => ({ ...f, end_date: e.target.value }))}
                className={inputCls} />
            </div>
          </div>

          {/* Total Days (computed) */}
          <div>
            <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1 block">
              Total Days
            </label>
            <input type="number" min="0.5" step="0.5" value={form.total_days}
              onChange={e => setForm(f => ({ ...f, total_days: parseFloat(e.target.value) }))}
              className={inputCls} />
          </div>

          {/* Reason */}
          <div>
            <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1 block">
              Reason *
            </label>
            <textarea required rows={3} value={form.reason}
              onChange={e => setForm(f => ({ ...f, reason: e.target.value }))}
              placeholder="Reason for leave..."
              className={inputCls + ' resize-none'} />
          </div>

          {/* Emergency Contact */}
          <div>
            <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1 block">
              Emergency Contact
            </label>
            <input type="text" value={form.emergency_contact}
              onChange={e => setForm(f => ({ ...f, emergency_contact: e.target.value }))}
              placeholder="+91 XXXXX XXXXX"
              className={inputCls} />
          </div>

          {/* Cover Arrangement */}
          <div>
            <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1 block">
              Cover Arrangement
            </label>
            <textarea rows={2} value={form.cover_arrangement}
              onChange={e => setForm(f => ({ ...f, cover_arrangement: e.target.value }))}
              placeholder="Who will cover your duties during absence..."
              className={inputCls + ' resize-none'} />
          </div>

          {error && (
            <div className="flex items-start gap-2 p-3 bg-red-50 border border-red-200 rounded-lg text-xs text-red-700">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              {error}
            </div>
          )}

          <div className="flex justify-end gap-3 pt-2">
            <button type="button" onClick={onClose}
              className="px-4 py-2 text-xs font-semibold text-slate-600 border border-slate-200 rounded-lg hover:bg-slate-50 transition">
              Cancel
            </button>
            <button type="submit" disabled={submitting}
              className="flex items-center gap-2 px-4 py-2 text-xs font-bold text-white bg-teal-600 hover:bg-teal-700 rounded-lg transition disabled:opacity-60">
              {submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
              Submit Request
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

// ─── My Requests Tab ─────────────────────────────────────────────
function MyRequestsTab({ facilities, selectedFacilityId }) {
  const [requests, setRequests] = useState([]);
  const [leaveTypes, setLeaveTypes] = useState([]);
  const [staffList, setStaffList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [statusFilter, setStatusFilter] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [reqs, types, staff] = await Promise.all([
        api.getLeaveRequests({ facility_id: selectedFacilityId, status: statusFilter }),
        api.getLeaveTypes(),
        api.getStaff(selectedFacilityId ? { facility_id: selectedFacilityId } : {}),
      ]);
      setRequests(reqs.items || []);
      setLeaveTypes(types);
      setStaffList(staff);
    } catch (err) {
      console.error('Error fetching leave requests:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedFacilityId, statusFilter]);

  useEffect(() => { fetchData(); }, [fetchData]);

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div className="flex items-center gap-2">
          <select value={statusFilter} onChange={e => setStatusFilter(e.target.value)}
            className="text-xs border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:border-teal-500">
            <option value="">All Statuses</option>
            {Object.keys(STATUS_BADGE).map(s => (
              <option key={s} value={s}>{s.replace(/_/g, ' ')}</option>
            ))}
          </select>
        </div>
        <button onClick={() => setShowModal(true)}
          className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg transition">
          <Plus className="w-4 h-4" />
          New Leave Request
        </button>
      </div>

      {/* Request Cards */}
      {loading ? (
        <div className="flex justify-center items-center py-16">
          <Loader2 className="w-6 h-6 text-teal-600 animate-spin" />
        </div>
      ) : requests.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 py-16 text-center">
          <ClipboardList className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <p className="text-sm text-slate-400">No leave requests found</p>
        </div>
      ) : (
        <div className="space-y-3">
          {requests.map(req => (
            <div key={req.id}
              className="bg-white border border-slate-200 rounded-2xl p-4 hover:shadow-sm transition">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-bold text-sm text-slate-900">
                      {req.staff_name || req.staff_id}
                    </span>
                    <span className="text-xs text-slate-400">·</span>
                    <span className="text-xs font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded-full">
                      {req.leave_type_name || '—'}
                    </span>
                    <StatusBadge status={req.status} />
                  </div>
                  <div className="mt-1 text-xs text-slate-500 flex flex-wrap gap-3">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {req.start_date} → {req.end_date}
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {req.total_days} day{req.total_days !== 1 ? 's' : ''}
                    </span>
                  </div>
                  {req.reason && (
                    <p className="mt-1.5 text-xs text-slate-600 line-clamp-1">
                      {req.reason}
                    </p>
                  )}
                </div>
                <div className="text-[10px] text-slate-400 font-mono shrink-0">
                  {new Date(req.created_at).toLocaleDateString()}
                </div>
              </div>

              {/* Cover arrangement chip */}
              {req.cover_arrangement && (
                <div className="mt-2 flex items-center gap-1.5 text-[11px] text-slate-500 bg-slate-50 rounded-lg px-3 py-1.5">
                  <Users className="w-3 h-3" />
                  Cover: {req.cover_arrangement}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Submit Modal */}
      {showModal && (
        <SubmitLeaveModal
          leaveTypes={leaveTypes}
          staffList={staffList}
          onClose={() => setShowModal(false)}
          onSubmitted={fetchData}
        />
      )}
    </div>
  );
}

// ─── Pending Approvals Tab ────────────────────────────────────────
function PendingApprovalsTab({ selectedFacilityId }) {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionState, setActionState] = useState({}); // { [reqId]: { comment, submitting } }

  const fetchPending = useCallback(async () => {
    setLoading(true);
    try {
      // Fetch all pending/L1/L2 requests
      const statuses = ['PENDING', 'APPROVED_L1', 'APPROVED_L2'];
      const all = await Promise.all(
        statuses.map(s => api.getLeaveRequests({ facility_id: selectedFacilityId, status: s }))
      );
      const merged = all.flatMap(r => r.items || []);
      setRequests(merged);
    } catch (err) {
      console.error('Error loading pending approvals:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedFacilityId]);

  useEffect(() => { fetchPending(); }, [fetchPending]);

  const handleAction = async (reqId, action) => {
    const state = actionState[reqId] || {};
    if (action === 'reject' && !state.comment?.trim()) {
      alert('A comment is required to reject a leave request.');
      return;
    }
    setActionState(prev => ({ ...prev, [reqId]: { ...prev[reqId], submitting: true } }));
    try {
      const payload = {
        approver_user_id: 'current-user',   // Replace with real auth user id
        approver_name: 'Supervisor',
        approver_role: 'Medical Officer',
        comments: state.comment || '',
      };
      if (action === 'approve') {
        await api.approveLeaveRequest(reqId, payload);
      } else {
        await api.rejectLeaveRequest(reqId, payload);
      }
      fetchPending();
    } catch (err) {
      alert('Action failed: ' + err.message);
    } finally {
      setActionState(prev => ({ ...prev, [reqId]: { ...prev[reqId], submitting: false } }));
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center py-16">
        <Loader2 className="w-6 h-6 text-teal-600 animate-spin" />
      </div>
    );
  }

  if (requests.length === 0) {
    return (
      <div className="bg-white rounded-2xl border border-slate-200 py-16 text-center">
        <CheckCircle2 className="w-8 h-8 text-emerald-300 mx-auto mb-2" />
        <p className="text-sm text-slate-400">No pending approvals</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {requests.map(req => {
        const state = actionState[req.id] || {};
        return (
          <div key={req.id} className="bg-white border border-slate-200 rounded-2xl p-5 space-y-4">
            {/* Header */}
            <div className="flex items-start justify-between gap-3">
              <div>
                <div className="flex items-center gap-2 flex-wrap">
                  <User className="w-4 h-4 text-teal-600" />
                  <span className="font-bold text-sm text-slate-900">{req.staff_name || req.staff_id}</span>
                  <StatusBadge status={req.status} />
                </div>
                <div className="mt-1 flex flex-wrap gap-3 text-xs text-slate-500">
                  <span className="font-semibold text-teal-700">{req.leave_type_name}</span>
                  <span>{req.start_date} → {req.end_date}</span>
                  <span>{req.total_days} day{req.total_days !== 1 ? 's' : ''}</span>
                </div>
              </div>
              <span className="text-[10px] text-slate-400 font-mono">
                {new Date(req.created_at).toLocaleDateString()}
              </span>
            </div>

            {/* Reason */}
            <div className="bg-slate-50 rounded-xl px-4 py-3 text-xs text-slate-700">
              <span className="font-semibold text-slate-500 uppercase tracking-wide text-[10px]">Reason: </span>
              {req.reason}
            </div>
            {req.cover_arrangement && (
              <div className="text-xs text-slate-600">
                <span className="font-semibold">Cover: </span>{req.cover_arrangement}
              </div>
            )}

            {/* Comment Box */}
            <textarea
              placeholder="Add comment (required for rejection)..."
              value={state.comment || ''}
              onChange={e => setActionState(prev => ({
                ...prev,
                [req.id]: { ...prev[req.id], comment: e.target.value }
              }))}
              rows={2}
              className="w-full text-xs border border-slate-200 rounded-lg px-3 py-2 resize-none focus:outline-none focus:border-teal-500"
            />

            {/* Action Buttons */}
            <div className="flex items-center gap-3 justify-end">
              <button
                onClick={() => handleAction(req.id, 'reject')}
                disabled={state.submitting}
                className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-red-700 bg-red-50 hover:bg-red-100 border border-red-200 rounded-lg transition disabled:opacity-50">
                {state.submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Ban className="w-3.5 h-3.5" />}
                Reject
              </button>
              <button
                onClick={() => handleAction(req.id, 'approve')}
                disabled={state.submitting}
                className="flex items-center gap-1.5 px-4 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-lg transition disabled:opacity-50">
                {state.submitting ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCheck className="w-3.5 h-3.5" />}
                Approve
              </button>
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ─── Team Calendar Tab ────────────────────────────────────────────
function TeamCalendarTab({ selectedFacilityId }) {
  const now = new Date();
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [year, setYear] = useState(now.getFullYear());
  const [calData, setCalData] = useState(null);
  const [loading, setLoading] = useState(true);

  const MONTH_NAMES = [
    'January','February','March','April','May','June',
    'July','August','September','October','November','December'
  ];

  const fetchCalendar = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getLeaveCalendar({ month, year, facility_id: selectedFacilityId });
      setCalData(data);
    } catch (err) {
      console.error('Error fetching calendar:', err);
    } finally {
      setLoading(false);
    }
  }, [month, year, selectedFacilityId]);

  useEffect(() => { fetchCalendar(); }, [fetchCalendar]);

  const prevMonth = () => {
    if (month === 1) { setMonth(12); setYear(y => y - 1); }
    else setMonth(m => m - 1);
  };
  const nextMonth = () => {
    if (month === 12) { setMonth(1); setYear(y => y + 1); }
    else setMonth(m => m + 1);
  };

  // Build 6-week grid
  const firstDow = new Date(year, month - 1, 1).getDay(); // 0=Sun
  const daysInMonth = new Date(year, month, 0).getDate();
  const cells = [];
  for (let i = 0; i < firstDow; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(d);

  const absenceMap = {};
  if (calData?.days) {
    calData.days.forEach(day => {
      if (day.absences.length > 0) {
        absenceMap[day.date] = day.absences;
      }
    });
  }

  return (
    <div className="space-y-4">
      {/* Month Navigator */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 flex items-center justify-between">
        <button onClick={prevMonth}
          className="p-2 hover:bg-slate-100 rounded-lg transition">
          <ChevronLeft className="w-4 h-4 text-slate-600" />
        </button>
        <h3 className="font-bold text-sm text-slate-900">
          {MONTH_NAMES[month - 1]} {year}
        </h3>
        <button onClick={nextMonth}
          className="p-2 hover:bg-slate-100 rounded-lg transition">
          <ChevronRight className="w-4 h-4 text-slate-600" />
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-16">
          <Loader2 className="w-6 h-6 text-teal-600 animate-spin" />
        </div>
      ) : (
        <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
          {/* Day headers */}
          <div className="grid grid-cols-7 bg-slate-50 border-b border-slate-200">
            {['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].map(d => (
              <div key={d} className="py-2 text-center text-[11px] font-bold text-slate-500 uppercase tracking-wide">
                {d}
              </div>
            ))}
          </div>

          {/* Calendar Grid */}
          <div className="grid grid-cols-7 divide-x divide-y divide-slate-100">
            {cells.map((day, idx) => {
              if (!day) return <div key={`empty-${idx}`} className="min-h-[80px] bg-slate-50/50" />;
              const dateStr = `${year}-${String(month).padStart(2,'0')}-${String(day).padStart(2,'0')}`;
              const absences = absenceMap[dateStr] || [];
              const isToday = dateStr === new Date().toISOString().slice(0, 10);

              return (
                <div key={dateStr} className={`min-h-[80px] p-1.5 ${isToday ? 'bg-teal-50' : 'hover:bg-slate-50'} transition`}>
                  <div className={`text-xs font-bold mb-1 w-6 h-6 flex items-center justify-center rounded-full
                    ${isToday ? 'bg-teal-600 text-white' : 'text-slate-700'}`}>
                    {day}
                  </div>
                  <div className="space-y-0.5">
                    {absences.slice(0, 3).map((a, i) => (
                      <div key={i} className="flex items-center gap-1 text-[10px] text-slate-700 bg-white border border-slate-100 rounded px-1 py-0.5 truncate"
                        title={`${a.staff_name} (${a.role}) — ${a.leave_type}`}>
                        <span className="w-2 h-2 rounded-full shrink-0"
                          style={{ backgroundColor: roleDotColor(a.role) }} />
                        <span className="truncate">{a.staff_name.split(' ')[0]}</span>
                      </div>
                    ))}
                    {absences.length > 3 && (
                      <div className="text-[9px] text-slate-400 pl-1">+{absences.length - 3} more</div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="flex flex-wrap gap-3">
        {Object.entries(ROLE_COLORS).filter(([k]) => k !== 'default').map(([role, color]) => (
          <div key={role} className="flex items-center gap-1.5 text-[11px] text-slate-600">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
            {role}
          </div>
        ))}
      </div>
    </div>
  );
}

// ─── Leave Balances Tab ───────────────────────────────────────────
function LeaveBalancesTab({ selectedFacilityId }) {
  const [staffList, setStaffList] = useState([]);
  const [selectedStaff, setSelectedStaff] = useState('');
  const [balances, setBalances] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    api.getStaff(selectedFacilityId ? { facility_id: selectedFacilityId } : {})
      .then(setStaffList)
      .catch(console.error);
  }, [selectedFacilityId]);

  const fetchBalances = async (staffId) => {
    if (!staffId) return;
    setLoading(true);
    try {
      const data = await api.getLeaveBalance(staffId);
      setBalances(data);
    } catch (err) {
      console.error('Error fetching balance:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleStaffChange = (e) => {
    setSelectedStaff(e.target.value);
    fetchBalances(e.target.value);
  };

  // Bar chart data
  const chartData = balances.map(b => ({
    name: b.leave_type_name || b.leave_type_id,
    Used: parseFloat(b.used.toFixed(1)),
    Pending: parseFloat(b.pending.toFixed(1)),
    Remaining: parseFloat(b.remaining.toFixed(1)),
  }));

  return (
    <div className="space-y-6">
      {/* Staff Picker */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4">
        <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-2 block">
          Select Staff Member
        </label>
        <select value={selectedStaff} onChange={handleStaffChange}
          className="w-full max-w-sm text-xs border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:border-teal-500">
          <option value="">Choose a staff member...</option>
          {staffList.map(s => (
            <option key={s.id} value={s.id}>{s.full_name} — {s.role}</option>
          ))}
        </select>
      </div>

      {loading && (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 text-teal-600 animate-spin" />
        </div>
      )}

      {!loading && selectedStaff && balances.length > 0 && (
        <>
          {/* Bar Chart */}
          <div className="bg-white rounded-2xl border border-slate-200 p-5">
            <h4 className="text-sm font-bold text-slate-800 mb-4">Leave Balance Overview — {new Date().getFullYear()}</h4>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={chartData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#64748b' }} />
                <YAxis tick={{ fontSize: 11, fill: '#64748b' }} />
                <Tooltip
                  contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}
                  formatter={(value, name) => [`${value} days`, name]}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="Used" fill="#f43f5e" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Pending" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Remaining" fill="#10b981" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Progress Bars */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {balances.map(b => {
              const total = b.total_allocated || 1;
              const usedPct = Math.round((b.used / total) * 100);
              const pendPct = Math.round((b.pending / total) * 100);
              const remPct = Math.round((b.remaining / total) * 100);

              return (
                <div key={b.id} className="bg-white rounded-2xl border border-slate-200 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-bold text-slate-800">{b.leave_type_name}</span>
                    <span className="text-xs text-slate-500">{b.total_allocated} days/yr</span>
                  </div>

                  {/* Stacked progress bar */}
                  <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex">
                    <div className="h-full bg-rose-500 transition-all duration-500"
                      style={{ width: `${usedPct}%` }} title={`Used: ${b.used}`} />
                    <div className="h-full bg-amber-400 transition-all duration-500"
                      style={{ width: `${pendPct}%` }} title={`Pending: ${b.pending}`} />
                    <div className="h-full bg-emerald-400 transition-all duration-500"
                      style={{ width: `${remPct}%` }} title={`Remaining: ${b.remaining}`} />
                  </div>

                  <div className="flex flex-wrap gap-3 text-[11px]">
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-rose-500" />
                      Used: <strong>{b.used}</strong>
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-amber-400" />
                      Pending: <strong>{b.pending}</strong>
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-400" />
                      Remaining: <strong>{b.remaining}</strong>
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </>
      )}

      {!loading && selectedStaff && balances.length === 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 py-12 text-center">
          <BarChart3 className="w-8 h-8 text-slate-300 mx-auto mb-2" />
          <p className="text-sm text-slate-400">No balance data found for this staff member</p>
        </div>
      )}
    </div>
  );
}

// ─── Coverage Gaps Tab ────────────────────────────────────────────
function CoverageGapsTab({ facilities, selectedFacilityId }) {
  const [gapData, setGapData] = useState(null);
  const [checkDate, setCheckDate] = useState(new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = useState(false);

  const fetchGaps = useCallback(async () => {
    setLoading(true);
    try {
      const data = await api.getCoverageGaps({
        facility_id: selectedFacilityId,
        check_date: checkDate,
      });
      setGapData(data);
    } catch (err) {
      console.error('Error fetching coverage gaps:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedFacilityId, checkDate]);

  useEffect(() => { fetchGaps(); }, [fetchGaps]);

  return (
    <div className="space-y-4">
      {/* Date Picker */}
      <div className="bg-white rounded-2xl border border-slate-200 p-4 flex flex-wrap items-end gap-4">
        <div>
          <label className="text-[11px] font-semibold text-slate-500 uppercase tracking-wide mb-1 block">
            Check Date
          </label>
          <input type="date" value={checkDate}
            onChange={e => setCheckDate(e.target.value)}
            className="text-xs border border-slate-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:border-teal-500" />
        </div>
        <button onClick={fetchGaps}
          className="flex items-center gap-2 px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white text-xs font-bold rounded-lg transition">
          Check Coverage
        </button>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <Loader2 className="w-6 h-6 text-teal-600 animate-spin" />
        </div>
      ) : gapData ? (
        gapData.gaps.length === 0 ? (
          <div className="bg-white rounded-2xl border border-slate-200 py-14 text-center">
            <CheckCircle2 className="w-10 h-10 text-emerald-400 mx-auto mb-3" />
            <p className="font-bold text-slate-700 text-sm">Full coverage on {checkDate}</p>
            <p className="text-xs text-slate-400 mt-1">All required roles have sufficient staffing</p>
          </div>
        ) : (
          <div className="space-y-3">
            {/* Critical warning banner */}
            <div className="flex items-start gap-3 p-4 bg-red-50 border border-red-200 rounded-2xl">
              <ShieldAlert className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-bold text-red-800">
                  {gapData.gaps.length} Coverage Gap{gapData.gaps.length > 1 ? 's' : ''} Detected on {checkDate}
                </p>
                <p className="text-xs text-red-600 mt-0.5">
                  Immediate attention required to ensure patient safety and service continuity.
                </p>
              </div>
            </div>

            {gapData.gaps.map((gap, idx) => (
              <div key={idx} className="bg-white border border-amber-200 rounded-2xl p-5 shadow-sm">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-amber-100 rounded-xl flex items-center justify-center">
                      <AlertCircle className="w-4 h-4 text-amber-600" />
                    </div>
                    <div>
                      <p className="font-bold text-sm text-slate-900">{gap.role}</p>
                      {gap.facility_name && (
                        <p className="text-xs text-slate-500">{gap.facility_name}</p>
                      )}
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-xs font-bold text-red-700 bg-red-50 border border-red-200 px-2 py-0.5 rounded-full">
                      −{gap.gap} staff short
                    </span>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-3 gap-3 text-center">
                  <div className="bg-slate-50 rounded-xl p-3">
                    <div className="text-lg font-bold text-slate-800">{gap.required_count}</div>
                    <div className="text-[10px] text-slate-500 uppercase tracking-wide">Required</div>
                  </div>
                  <div className="bg-emerald-50 rounded-xl p-3">
                    <div className="text-lg font-bold text-emerald-700">{gap.present_count}</div>
                    <div className="text-[10px] text-slate-500 uppercase tracking-wide">Available</div>
                  </div>
                  <div className="bg-amber-50 rounded-xl p-3">
                    <div className="text-lg font-bold text-amber-700">{gap.on_leave_count}</div>
                    <div className="text-[10px] text-slate-500 uppercase tracking-wide">On Leave</div>
                  </div>
                </div>

                <div className="mt-3 w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                  <div className="h-full bg-red-500 rounded-full transition-all"
                    style={{ width: `${Math.round((gap.present_count / gap.required_count) * 100)}%` }} />
                </div>
              </div>
            ))}
          </div>
        )
      ) : null}
    </div>
  );
}

// ─── Main Page Component ──────────────────────────────────────────
export default function LeaveManagementPage({ facilities = [], selectedFacilityId }) {
  const { t } = useLanguage();
  const [activeTab, setActiveTab] = useState('my-requests');

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white px-6 py-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Calendar className="w-5 h-5 text-teal-600" />
            Staff Leave Management
          </h2>
          <p className="text-xs text-slate-500 mt-1">
            Track requests, approvals, balances and coverage gaps across your health centre
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-500">
          <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
          Live sync enabled
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <div className="flex overflow-x-auto border-b border-slate-200">
          {TABS.map(tab => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-5 py-3.5 text-xs font-semibold whitespace-nowrap border-b-2 transition
                  ${active
                    ? 'border-teal-600 text-teal-700 bg-teal-50/60'
                    : 'border-transparent text-slate-500 hover:text-slate-700 hover:bg-slate-50'
                  }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* Tab Content */}
        <div className="p-5">
          {activeTab === 'my-requests' && (
            <MyRequestsTab facilities={facilities} selectedFacilityId={selectedFacilityId} />
          )}
          {activeTab === 'pending-approvals' && (
            <PendingApprovalsTab selectedFacilityId={selectedFacilityId} />
          )}
          {activeTab === 'team-calendar' && (
            <TeamCalendarTab selectedFacilityId={selectedFacilityId} />
          )}
          {activeTab === 'leave-balances' && (
            <LeaveBalancesTab selectedFacilityId={selectedFacilityId} />
          )}
          {activeTab === 'coverage-gaps' && (
            <CoverageGapsTab facilities={facilities} selectedFacilityId={selectedFacilityId} />
          )}
        </div>
      </div>
    </div>
  );
}
