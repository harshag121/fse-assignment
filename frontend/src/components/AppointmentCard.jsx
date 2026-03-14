import React from 'react';
import styles from './AppointmentCard.module.css';

const STATUS_COLORS = {
  confirmed: '#16a34a',
  pending:   '#d97706',
  cancelled: '#dc2626',
  completed: '#2563eb',
  rescheduled: '#7c3aed',
};

export default function AppointmentCard({ appointment, onCancel }) {
  const { id, doctor, patient, start_time, end_time, status, symptoms } = appointment;
  const start = new Date(start_time);
  const end   = new Date(end_time);

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <span className={styles.badge} style={{ background: STATUS_COLORS[status] || '#6b7280' }}>
          {status}
        </span>
        <span className={styles.apptId}>#{id}</span>
      </div>

      <div className={styles.body}>
        {doctor && (
          <p><strong>Doctor:</strong> Dr. {doctor.name} <span className={styles.spec}>({doctor.specialization})</span></p>
        )}
        {patient && (
          <p><strong>Patient:</strong> {patient.name}</p>
        )}
        <p><strong>Date:</strong> {start.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })}</p>
        <p><strong>Time:</strong> {start.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} – {end.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</p>
        {symptoms && <p><strong>Symptoms:</strong> {symptoms}</p>}
      </div>

      {status !== 'cancelled' && onCancel && (
        <div className={styles.footer}>
          <button className={styles.cancelBtn} onClick={() => onCancel(id)}>
            Cancel Appointment
          </button>
        </div>
      )}
    </div>
  );
}
