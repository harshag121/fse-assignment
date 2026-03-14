import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getAppointments, cancelAppointment } from '../services/api';
import NlReportGenerator from './NlReportGenerator';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from 'recharts';

const NAV_ITEMS = [
  { id: 'dashboard', icon: 'dashboard', label: 'Dashboard' },
  { id: 'appointments', icon: 'calendar_today', label: 'Appointments' },
  { id: 'reports', icon: 'description', label: 'Reports' },
];

function StatCard({ icon, iconBg, iconColor, badge, badgeColor, label, value }) {
  return (
    <div className="bg-white p-6 rounded-xl border border-[#0d968b]/5 shadow-sm">
      <div className="flex justify-between items-start mb-4">
        <span className={`p-2 ${iconBg} rounded-lg ${iconColor} material-symbols-outlined`}>{icon}</span>
        <span className={`text-xs font-bold ${badgeColor} px-2 py-1 rounded-full`}>{badge}</span>
      </div>
      <h3 className="text-slate-500 text-sm font-medium mb-1">{label}</h3>
      <p className="text-3xl font-bold">{value}</p>
    </div>
  );
}

const GREETING = () => {
  const h = new Date().getHours();
  if (h < 12) return 'Good morning';
  if (h < 17) return 'Good afternoon';
  return 'Good evening';
};

export default function DoctorDashboard() {
  const { user, logout } = useAuth();
  const [view, setView] = useState('dashboard');
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user?.id) return;
    getAppointments({ doctor_id: user.id })
      .then(setAppointments)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [user]);

  async function handleCancel(id) {
    await cancelAppointment(id);
    setAppointments((prev) => prev.map((a) => a.id === id ? { ...a, status: 'cancelled' } : a));
  }

  const todayStr = new Date().toDateString();
  const todayAppts = appointments.filter((a) => new Date(a.start_time).toDateString() === todayStr);
  const confirmed = appointments.filter((a) => a.status === 'confirmed').length;
  const pending = appointments.filter((a) => a.status === 'pending').length;
  const cancelled = appointments.filter((a) => a.status === 'cancelled').length;

  // Weekly chart data (last 7 days)
  const last7 = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(); d.setDate(d.getDate() - 6 + i);
    const dayStr = d.toDateString();
    const count = appointments.filter((a) => new Date(a.start_time).toDateString() === dayStr).length;
    return { day: d.toLocaleDateString('en', { weekday: 'short' }), count };
  });

  // Status distribution for pie
  const statusData = [
    { name: 'Confirmed', value: confirmed, color: '#0d968b' },
    { name: 'Pending', value: pending, color: '#f59e0b' },
    { name: 'Cancelled', value: cancelled, color: '#f43f5e' },
  ].filter((d) => d.value > 0);

  // Recent appointments for activity
  const recent = [...appointments]
    .sort((a, b) => new Date(b.start_time) - new Date(a.start_time))
    .slice(0, 4);

  const activityIcon = (status) => {
    if (status === 'confirmed') return { icon: 'check_circle', bg: 'bg-emerald-50', color: 'text-emerald-600' };
    if (status === 'pending') return { icon: 'schedule', bg: 'bg-amber-50', color: 'text-amber-600' };
    return { icon: 'cancel', bg: 'bg-rose-50', color: 'text-rose-600' };
  };

  if (view === 'reports') {
    return (
      <div className="flex h-screen overflow-hidden bg-[#f6f8f8] font-display">
        {/* Same sidebar */}
        <aside className="w-64 flex-shrink-0 border-r border-[#0d968b]/10 bg-white hidden lg:flex flex-col">
          <div className="p-6 flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#0d968b]/10 flex items-center justify-center text-[#0d968b]">
              <span className="material-symbols-outlined">health_and_safety</span>
            </div>
            <h2 className="font-bold text-lg tracking-tight">MedAnalytics</h2>
          </div>
          <nav className="flex-1 px-4 space-y-2 mt-4">
            {NAV_ITEMS.map((item) => (
              <button
                key={item.id}
                onClick={() => setView(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors text-left ${view === item.id ? 'bg-[#0d968b] text-white' : 'hover:bg-[#0d968b]/5 text-slate-700'}`}
              >
                <span className={`material-symbols-outlined ${view === item.id ? 'text-white' : 'text-slate-500'}`}>{item.icon}</span>
                <span className="font-medium">{item.label}</span>
              </button>
            ))}
          </nav>
          <div className="p-4 border-t border-[#0d968b]/10">
            <div className="flex items-center gap-3 p-2 bg-[#0d968b]/5 rounded-xl">
              <div className="w-10 h-10 rounded-full bg-[#0d968b]/20 flex items-center justify-center font-bold text-[#0d968b] text-sm">
                {user?.name?.charAt(0) || 'D'}
              </div>
              <div className="flex flex-col min-w-0 flex-1">
                <span className="text-sm font-bold truncate">{user?.name || 'Doctor'}</span>
                <span className="text-xs text-slate-500">General Practitioner</span>
              </div>
              <button onClick={logout} title="Sign out" className="text-slate-400 hover:text-slate-600">
                <span className="material-symbols-outlined text-[18px]">logout</span>
              </button>
            </div>
          </div>
        </aside>
        <main className="flex-1 overflow-y-auto">
          <NlReportGenerator user={user} />
        </main>
      </div>
    );
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#f6f8f8] font-display">
      {/* Sidebar */}
      <aside className="w-64 flex-shrink-0 border-r border-[#0d968b]/10 bg-white hidden lg:flex flex-col">
        <div className="p-6 flex items-center gap-3">
          <div className="w-10 h-10 rounded-full bg-[#0d968b]/10 flex items-center justify-center text-[#0d968b]">
            <span className="material-symbols-outlined">health_and_safety</span>
          </div>
          <h2 className="font-bold text-lg tracking-tight">MedAnalytics</h2>
        </div>
        <nav className="flex-1 px-4 space-y-2 mt-4">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.id}
              onClick={() => setView(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-colors text-left ${view === item.id ? 'bg-[#0d968b] text-white' : 'hover:bg-[#0d968b]/5 text-slate-700'}`}
            >
              <span className={`material-symbols-outlined ${view === item.id ? 'text-white' : 'text-slate-500'}`}>{item.icon}</span>
              <span className="font-medium">{item.label}</span>
            </button>
          ))}
        </nav>
        <div className="p-4 border-t border-[#0d968b]/10">
          <div className="flex items-center gap-3 p-2 bg-[#0d968b]/5 rounded-xl">
            <div className="w-10 h-10 rounded-full bg-[#0d968b]/20 flex items-center justify-center font-bold text-[#0d968b] text-sm">
              {user?.name?.charAt(0) || 'D'}
            </div>
            <div className="flex flex-col min-w-0 flex-1">
              <span className="text-sm font-bold truncate">{user?.name || 'Doctor'}</span>
              <span className="text-xs text-slate-500">General Practitioner</span>
            </div>
            <button onClick={logout} title="Sign out" className="text-slate-400 hover:text-slate-600">
              <span className="material-symbols-outlined text-[18px]">logout</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 overflow-y-auto scroll-smooth">
        {/* Header */}
        <header className="sticky top-0 z-10 bg-[#f6f8f8]/80 backdrop-blur-md px-8 py-6 flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-200/60">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{GREETING()}, {user?.name || 'Doctor'}</h1>
            <p className="text-slate-500">Here is what's happening with your practice today.</p>
          </div>
          <div className="flex items-center gap-4">
            <button
              onClick={() => setView('reports')}
              className="bg-[#0d968b] hover:bg-[#0b7a71] text-white px-6 py-2 rounded-xl font-bold transition-all shadow-lg shadow-[#0d968b]/20 flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-sm">magic_button</span>
              Generate Report
            </button>
          </div>
        </header>

        <div className="p-8 space-y-8">
          {/* Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard icon="event_available" iconBg="bg-[#0d968b]/10" iconColor="text-[#0d968b]" badge={`${todayAppts.length} today`} badgeColor="text-emerald-600 bg-emerald-50" label="Total Appointments" value={appointments.length} />
            <StatCard icon="pending_actions" iconBg="bg-amber-100" iconColor="text-amber-600" badge={pending > 0 ? 'Needs review' : 'All clear'} badgeColor="text-slate-400 bg-slate-50" label="Pending Confirmations" value={pending} />
            <StatCard icon="check_circle" iconBg="bg-indigo-100" iconColor="text-indigo-600" badge={`${appointments.length > 0 ? Math.round(confirmed / appointments.length * 100) : 0}%`} badgeColor="text-emerald-600 bg-emerald-50" label="Confirmed" value={confirmed} />
            <StatCard icon="cancel" iconBg="bg-rose-100" iconColor="text-rose-600" badge={cancelled > 0 ? '↑ review' : '0 today'} badgeColor="text-rose-600 bg-rose-50" label="Cancelled" value={cancelled} />
          </div>

          {/* Charts + Lists */}
          {view === 'appointments' ? (
            /* Appointments list view */
            <div className="bg-white rounded-xl border border-[#0d968b]/5 shadow-sm p-8">
              <h3 className="font-bold text-lg mb-6">All Appointments</h3>
              {loading ? (
                <div className="flex items-center justify-center h-32 text-slate-400">
                  <span className="material-symbols-outlined animate-spin mr-2">sync</span> Loading…
                </div>
              ) : appointments.length === 0 ? (
                <p className="text-slate-500 text-center py-8">No appointments found.</p>
              ) : (
                <div className="space-y-3">
                  {appointments.map((a) => {
                    const i = activityIcon(a.status);
                    return (
                      <div key={a.id} className="flex items-center gap-4 p-4 rounded-xl border border-slate-100 hover:border-[#0d968b]/20 transition-colors">
                        <div className={`w-10 h-10 rounded-full ${i.bg} ${i.color} flex items-center justify-center flex-shrink-0`}>
                          <span className="material-symbols-outlined text-sm">{i.icon}</span>
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-sm text-slate-800">
                            {a.patient?.name || `Patient #${a.patient_id}`}
                          </p>
                          <p className="text-xs text-slate-400">{new Date(a.start_time).toLocaleString()} · {a.symptoms || 'No symptoms noted'}</p>
                        </div>
                        <span className={`px-2 py-1 rounded-full text-xs font-bold ${a.status === 'confirmed' ? 'bg-emerald-50 text-emerald-700' : a.status === 'pending' ? 'bg-amber-50 text-amber-700' : 'bg-rose-50 text-rose-700'}`}>
                          {a.status}
                        </span>
                        {a.status !== 'cancelled' && (
                          <button onClick={() => handleCancel(a.id)} className="text-rose-500 hover:text-rose-700 text-xs font-medium ml-2">Cancel</button>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ) : (
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
              {/* Line Chart */}
              <div className="xl:col-span-2 bg-white p-8 rounded-xl border border-[#0d968b]/5 shadow-sm">
                <div className="flex justify-between items-center mb-8">
                  <h3 className="font-bold text-lg">Appointment Volume</h3>
                  <span className="text-sm font-medium text-slate-500">Last 7 Days</span>
                </div>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={last7}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                      <XAxis dataKey="day" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                      <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} allowDecimals={false} />
                      <Tooltip contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 20px rgba(0,0,0,.1)' }} />
                      <Line type="monotone" dataKey="count" stroke="#0d968b" strokeWidth={2.5} dot={{ fill: '#0d968b', r: 4 }} activeDot={{ r: 6 }} />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              {/* Donut / Pie Chart */}
              <div className="bg-white p-8 rounded-xl border border-[#0d968b]/5 shadow-sm">
                <h3 className="font-bold text-lg mb-6">Status Distribution</h3>
                {statusData.length > 0 ? (
                  <>
                    <div className="h-48">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie data={statusData} cx="50%" cy="50%" innerRadius={50} outerRadius={80} paddingAngle={3} dataKey="value">
                            {statusData.map((entry) => <Cell key={entry.name} fill={entry.color} />)}
                          </Pie>
                          <Tooltip />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                    <div className="space-y-3 mt-4">
                      {statusData.map((s) => (
                        <div key={s.name} className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <div className="w-3 h-3 rounded-full" style={{ background: s.color }}></div>
                            <span className="text-slate-500">{s.name}</span>
                          </div>
                          <span className="font-bold">{s.value}</span>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <p className="text-slate-400 text-sm text-center py-8">No data yet</p>
                )}
              </div>
            </div>
          )}

          {/* Recent Activity + Quick Actions */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 pb-12">
            {/* Recent Activity */}
            <div className="bg-white p-8 rounded-xl border border-[#0d968b]/5 shadow-sm">
              <div className="flex justify-between items-center mb-6">
                <h3 className="font-bold text-lg">Recent Activity</h3>
                <button onClick={() => setView('appointments')} className="text-[#0d968b] text-sm font-semibold hover:underline">View All</button>
              </div>
              {loading ? (
                <div className="flex items-center text-slate-400 text-sm"><span className="material-symbols-outlined animate-spin mr-2 text-[18px]">sync</span>Loading…</div>
              ) : recent.length === 0 ? (
                <p className="text-slate-400 text-sm">No recent activity.</p>
              ) : (
                <div className="space-y-6">
                  {recent.map((a) => {
                    const i = activityIcon(a.status);
                    return (
                      <div key={a.id} className="flex gap-4">
                        <div className={`w-10 h-10 rounded-full ${i.bg} ${i.color} flex items-center justify-center shrink-0`}>
                          <span className="material-symbols-outlined text-sm">{i.icon}</span>
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium">
                            Appointment {a.status} – <span className="font-bold">{a.patient?.name || `Patient #${a.patient_id}`}</span>
                          </p>
                          <p className="text-xs text-slate-400 mt-1">{new Date(a.start_time).toLocaleDateString()}{a.symptoms ? ` · ${a.symptoms}` : ''}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            {/* Quick Actions */}
            <div className="bg-white p-8 rounded-xl border border-[#0d968b]/5 shadow-sm">
              <h3 className="font-bold text-lg mb-6">Quick Actions</h3>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { icon: 'analytics', label: 'Generate Report', action: () => setView('reports') },
                  { icon: 'calendar_today', label: 'All Appointments', action: () => setView('appointments') },
                  { icon: 'send', label: 'Send to Slack', action: () => setView('reports') },
                  { icon: 'refresh', label: 'Refresh Data', action: () => { setLoading(true); getAppointments({ doctor_id: user.id }).then(setAppointments).finally(() => setLoading(false)); } },
                ].map((qa) => (
                  <button
                    key={qa.label}
                    onClick={qa.action}
                    className="flex flex-col items-center justify-center gap-3 p-6 rounded-xl border border-[#0d968b]/10 hover:bg-[#0d968b]/5 transition-all group"
                  >
                    <span className="material-symbols-outlined text-[#0d968b] group-hover:scale-110 transition-transform">{qa.icon}</span>
                    <span className="text-sm font-medium text-center">{qa.label}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
