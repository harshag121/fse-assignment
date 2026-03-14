import React, { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { SessionProvider } from './contexts/SessionContext';
import LandingPage from './components/LandingPage';
import ChatInterface from './components/ChatInterface';
import DoctorDashboard from './components/DoctorDashboard';
import { createPatient, createDoctor } from './services/api';

function LoginPage({ role, onBack }) {
  const { login } = useAuth();
  const [tab, setTab] = useState('login');
  const [form, setForm] = useState({ email: '', password: '', name: '', specialization: '', phone: '' });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

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

  const isDoctor = role === 'doctor';

  return (
    <div className="min-h-screen flex items-center justify-center bg-[#f6f8f8] font-display px-4">
      {/* Background decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-40 -right-40 w-96 h-96 bg-[#0d968b]/10 rounded-full blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-96 h-96 bg-[#0d968b]/5 rounded-full blur-3xl"></div>
      </div>

      <div className="relative bg-white rounded-2xl shadow-2xl shadow-slate-200 w-full max-w-md p-8 border border-slate-100">
        {/* Back button + Logo */}
        <button onClick={onBack} className="flex items-center gap-2 text-slate-500 hover:text-slate-700 mb-6 text-sm font-medium transition-colors">
          <span className="material-symbols-outlined text-[18px]">arrow_back</span>
          Back to home
        </button>

        <div className="flex items-center gap-3 mb-8">
          <div className="bg-[#0d968b] p-2 rounded-xl">
            <span className="material-symbols-outlined text-white">{isDoctor ? 'stethoscope' : 'patient_list'}</span>
          </div>
          <div>
            <h1 className="text-xl font-bold text-slate-900">
              {isDoctor ? 'Provider Portal' : 'Patient Portal'}
            </h1>
            <p className="text-xs text-slate-500">{isDoctor ? 'Analytics & Reports' : 'Book Appointments'}</p>
          </div>
        </div>

        {/* Tab switcher */}
        <div className="flex bg-slate-100 rounded-xl p-1 gap-1 mb-6">
          {['login', 'register'].map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`flex-1 py-2.5 text-sm font-semibold rounded-lg transition-all ${tab === t ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}
            >
              {t === 'login' ? 'Sign In' : 'Create Account'}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {tab === 'register' && (
            <>
              <div className="relative">
                <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-[18px]">person</span>
                <input className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-[#0d968b]/20 focus:border-[#0d968b] outline-none transition-all" placeholder="Full Name" value={form.name} onChange={update('name')} required />
              </div>
              {isDoctor && (
                <div className="relative">
                  <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-[18px]">medical_services</span>
                  <input className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-[#0d968b]/20 focus:border-[#0d968b] outline-none transition-all" placeholder="Specialization" value={form.specialization} onChange={update('specialization')} required />
                </div>
              )}
            </>
          )}
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-[18px]">mail</span>
            <input type="email" className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-[#0d968b]/20 focus:border-[#0d968b] outline-none transition-all" placeholder="Email address" value={form.email} onChange={update('email')} required />
          </div>
          <div className="relative">
            <span className="material-symbols-outlined absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-400 text-[18px]">lock</span>
            <input type="password" className="w-full pl-10 pr-4 py-3 border border-slate-200 rounded-xl text-sm focus:ring-2 focus:ring-[#0d968b]/20 focus:border-[#0d968b] outline-none transition-all" placeholder="Password" value={form.password} onChange={update('password')} required />
          </div>

          {error && (
            <div className="flex items-center gap-2 p-3 bg-red-50 border border-red-200 rounded-xl">
              <span className="material-symbols-outlined text-red-500 text-[18px]">error</span>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-[#0d968b] hover:bg-[#0b7a71] disabled:opacity-60 text-white font-bold rounded-xl text-sm transition-all shadow-lg shadow-[#0d968b]/20 flex items-center justify-center gap-2"
          >
            {loading ? (
              <><span className="material-symbols-outlined animate-spin text-[18px]">sync</span> Loading…</>
            ) : tab === 'login' ? 'Sign In' : 'Create Account'}
          </button>
        </form>

        {tab === 'login' && (
          <p className="text-center text-xs text-slate-400 mt-6">
            Demo: <span className="font-mono text-slate-600">gharshavardhan211@gmail.com</span> / <span className="font-mono text-slate-600">test123</span>
          </p>
        )}
      </div>
    </div>
  );
}

function AppContent() {
  const { user } = useAuth();
  const [selectedRole, setSelectedRole] = useState(null);

  if (!user && !selectedRole) {
    return <LandingPage onSelectRole={setSelectedRole} />;
  }
  if (!user) {
    return <LoginPage role={selectedRole} onBack={() => setSelectedRole(null)} />;
  }
  if (user.role === 'doctor') {
    return <DoctorDashboard />;
  }
  return (
    <SessionProvider>
      <ChatInterface />
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
