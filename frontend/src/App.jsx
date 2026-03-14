import React, { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SessionProvider } from './contexts/SessionContext';
import ChatInterface from './components/ChatInterface';
import DoctorDashboard from './components/DoctorDashboard';
import { login as apiLogin, createPatient, createDoctor } from './services/api';
import './App.css';

// ── Login Page ────────────────────────────────────────────────────────────────
function LoginPage() {
  const { login } = useAuth();
  const [tab, setTab] = useState('login');  // 'login' | 'register'
  const [role, setRole] = useState('patient');
  const [form, setForm] = useState({ email: '', password: '', name: '', specialization: '', phone: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  function update(field) {
    return (e) => setForm((f) => ({ ...f, [field]: e.target.value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      if (tab === 'login') {
        await login(form.email, form.password, role);
      } else {
        if (role === 'patient') {
          await createPatient({ name: form.name, email: form.email, password: form.password, phone: form.phone });
        } else {
          await createDoctor({ name: form.name, email: form.email, password: form.password, specialization: form.specialization, phone: form.phone });
        }
        await login(form.email, form.password, role);
      }
    } catch (err) {
      setError(err?.response?.data?.detail || 'Something went wrong');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      <div className="login-card">
        <h1 className="login-title">🏥 MedAssist</h1>
        <p className="login-sub">Smart Doctor Appointment System</p>

        <div className="tab-row">
          {['login', 'register'].map((t) => (
            <button key={t} className={`tab-btn ${tab === t ? 'tab-active' : ''}`} onClick={() => setTab(t)}>
              {t === 'login' ? 'Sign In' : 'Register'}
            </button>
          ))}
        </div>

        <div className="role-row">
          {['patient', 'doctor'].map((r) => (
            <button key={r} className={`role-btn ${role === r ? 'role-active' : ''}`} onClick={() => setRole(r)}>
              {r === 'patient' ? '👤 Patient' : '👨‍⚕️ Doctor'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {tab === 'register' && (
            <>
              <input className="input-field" placeholder="Full Name" value={form.name} onChange={update('name')} required />
              {role === 'doctor' && (
                <input className="input-field" placeholder="Specialization" value={form.specialization} onChange={update('specialization')} required />
              )}
              <input className="input-field" type="tel" placeholder="Phone (optional)" value={form.phone} onChange={update('phone')} />
            </>
          )}
          <input className="input-field" type="email" placeholder="Email" value={form.email} onChange={update('email')} required />
          <input className="input-field" type="password" placeholder="Password" value={form.password} onChange={update('password')} required />
          {error && <p className="error-msg">{error}</p>}
          <button className="submit-btn" type="submit" disabled={loading}>
            {loading ? 'Loading…' : tab === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>
      </div>
    </div>
  );
}

// ── Main App ──────────────────────────────────────────────────────────────────
function AppContent() {
  const { user, logout } = useAuth();
  const [view, setView] = useState('chat');  // 'chat' | 'dashboard'

  if (!user) return <LoginPage />;

  return (
    <SessionProvider>
      <div className="app-layout">
        {/* Sidebar */}
        <aside className="sidebar">
          <div className="sidebar-brand">🏥 MedAssist</div>
          <nav className="sidebar-nav">
            <button
              className={`nav-item ${view === 'chat' ? 'nav-active' : ''}`}
              onClick={() => setView('chat')}
            >
              💬 Chat
            </button>
            {user.role === 'doctor' && (
              <button
                className={`nav-item ${view === 'dashboard' ? 'nav-active' : ''}`}
                onClick={() => setView('dashboard')}
              >
                📊 Dashboard
              </button>
            )}
          </nav>
          <div className="sidebar-footer">
            <p className="user-info">{user.email}</p>
            <p className="user-role">{user.role}</p>
            <button className="logout-btn" onClick={logout}>Sign Out</button>
          </div>
        </aside>

        {/* Main content */}
        <main className="main-content">
          {view === 'chat'      && <ChatInterface />}
          {view === 'dashboard' && <DoctorDashboard />}
        </main>
      </div>
    </SessionProvider>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}
