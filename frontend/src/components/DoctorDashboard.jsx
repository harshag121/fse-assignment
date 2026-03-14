import React, { useEffect, useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { getAppointments, cancelAppointment, generateReport } from '../services/api';
import AppointmentCard from './AppointmentCard';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell,
} from 'recharts';
import styles from './DoctorDashboard.module.css';

const DATE_FILTERS = ['today', 'yesterday', 'this_week', 'last_week'];

const STATUS_COLORS = {
  confirmed: '#16a34a',
  pending:   '#d97706',
  cancelled: '#dc2626',
  completed: '#2563eb',
};

export default function DoctorDashboard() {
  const { user } = useAuth();
  const [appointments, setAppointments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [reportQuery, setReportQuery] = useState('');
  const [reportResult, setReportResult] = useState('');
  const [reportLoading, setReportLoading] = useState(false);
  const [dateFilter] = useState('today');

  useEffect(() => {
    if (!user?.id) return;
    fetchAppointments();
    // eslint-disable-next-line
  }, [user]);

  async function fetchAppointments() {
    try {
      setLoading(true);
      const data = await getAppointments({ doctor_id: user.id });
      setAppointments(data);
    } catch {
      /* silent */
    } finally {
      setLoading(false);
    }
  }

  async function handleCancel(id) {
    await cancelAppointment(id);
    setAppointments((prev) =>
      prev.map((a) => (a.id === id ? { ...a, status: 'cancelled' } : a))
    );
  }

  async function handleReport() {
    if (!reportQuery.trim()) return;
    setReportLoading(true);
    setReportResult('');
    try {
      const res = await generateReport(user.id, reportQuery);
      setReportResult(res.reply || JSON.stringify(res, null, 2));
    } catch {
      setReportResult('Failed to generate report. Please try again.');
    } finally {
      setReportLoading(false);
    }
  }

  // Chart data
  const statusData = Object.entries(
    appointments.reduce((acc, a) => {
      acc[a.status] = (acc[a.status] || 0) + 1;
      return acc;
    }, {})
  ).map(([name, count]) => ({ name, count }));

  const todayStr = new Date().toDateString();
  const todayAppts = appointments.filter(
    (a) => new Date(a.start_time).toDateString() === todayStr
  );

  return (
    <div className={styles.container}>
      <h1 className={styles.pageTitle}>Doctor Dashboard</h1>

      {/* Stats row */}
      <div className={styles.statsRow}>
        <StatCard label="Total" value={appointments.length} color="#2563eb" />
        <StatCard label="Today" value={todayAppts.length} color="#0891b2" />
        <StatCard
          label="Confirmed"
          value={appointments.filter((a) => a.status === 'confirmed').length}
          color="#16a34a"
        />
        <StatCard
          label="Cancelled"
          value={appointments.filter((a) => a.status === 'cancelled').length}
          color="#dc2626"
        />
      </div>

      <div className={styles.mainGrid}>
        {/* Appointments list */}
        <section className={styles.section}>
          <h2 className={styles.sectionTitle}>Appointments</h2>
          {loading ? (
            <p className={styles.loading}>Loading…</p>
          ) : appointments.length === 0 ? (
            <p className={styles.empty}>No appointments found.</p>
          ) : (
            <div className={styles.cardGrid}>
              {appointments.map((a) => (
                <AppointmentCard key={a.id} appointment={a} onCancel={handleCancel} />
              ))}
            </div>
          )}
        </section>

        <div className={styles.rightCol}>
          {/* Chart */}
          {statusData.length > 0 && (
            <section className={styles.section}>
              <h2 className={styles.sectionTitle}>Status Overview</h2>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={statusData}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                    {statusData.map((entry) => (
                      <Cell key={entry.name} fill={STATUS_COLORS[entry.name] || '#94a3b8'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </section>
          )}

          {/* Natural language report */}
          <section className={styles.section}>
            <h2 className={styles.sectionTitle}>AI Report Generator</h2>
            <p className={styles.reportHint}>
              Ask anything, e.g. "How many fever cases last week?" or "Send today's summary to Slack"
            </p>
            <textarea
              className={styles.reportInput}
              rows={3}
              value={reportQuery}
              onChange={(e) => setReportQuery(e.target.value)}
              placeholder="Type your query…"
            />
            <button
              className={styles.reportBtn}
              onClick={handleReport}
              disabled={reportLoading || !reportQuery.trim()}
            >
              {reportLoading ? 'Generating…' : 'Generate Report'}
            </button>
            {reportResult && (
              <div className={styles.reportResult}>
                <pre>{reportResult}</pre>
              </div>
            )}
          </section>
        </div>
      </div>
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div className={styles.statCard} style={{ borderTop: `3px solid ${color}` }}>
      <p className={styles.statValue} style={{ color }}>{value}</p>
      <p className={styles.statLabel}>{label}</p>
    </div>
  );
}
