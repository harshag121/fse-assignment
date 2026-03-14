import axios from 'axios';

const api = axios.create({
  baseURL: (process.env.REACT_APP_API_URL || '') + '/api',
  headers: { 'Content-Type': 'application/json' },
});

// Attach JWT token to every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = (email, password, role) =>
  api.post('/auth/token', { email, password, role }).then((r) => r.data);

// ── Doctors ───────────────────────────────────────────────────────────────────
export const getDoctors = () => api.get('/doctors').then((r) => r.data);
export const getDoctor  = (id) => api.get(`/doctors/${id}`).then((r) => r.data);
export const createDoctor = (data) => api.post('/doctors', data).then((r) => r.data);
export const getDoctorAvailability = (id) =>
  api.get(`/doctors/${id}/availability`).then((r) => r.data);

// ── Patients ──────────────────────────────────────────────────────────────────
export const createPatient = (data) => api.post('/patients', data).then((r) => r.data);
export const getPatient    = (id)   => api.get(`/patients/${id}`).then((r) => r.data);

// ── Appointments ──────────────────────────────────────────────────────────────
export const getAppointments = (params) =>
  api.get('/appointments', { params }).then((r) => r.data);
export const cancelAppointment = (id) =>
  api.patch(`/appointments/${id}/cancel`).then((r) => r.data);

// ── Chat ──────────────────────────────────────────────────────────────────────
export const sendMessage = (sessionId, message, role, userId) =>
  api.post('/chat', { session_id: sessionId, message, role, user_id: userId }).then((r) => r.data);
export const getChatHistory = (sessionId) =>
  api.get(`/chat/${sessionId}/history`).then((r) => r.data);

// ── Reports ───────────────────────────────────────────────────────────────────
export const generateReport = (doctorId, query, sessionId) =>
  api.post('/reports/generate', { doctor_id: doctorId, query, session_id: sessionId }).then((r) => r.data);

export default api;
