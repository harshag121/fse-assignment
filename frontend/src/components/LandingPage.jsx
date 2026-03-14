import React from 'react';

export default function LandingPage({ onSelectRole }) {
  return (
    <div className="relative min-h-screen flex flex-col font-display bg-background-light">
      {/* Top Navigation */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-[#0d968b]/10">
        <div className="max-w-7xl mx-auto px-6 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="bg-[#0d968b] p-1.5 rounded-lg flex items-center justify-center">
              <span className="material-symbols-outlined text-white text-xl">smart_toy</span>
            </div>
            <span className="text-xl font-bold tracking-tight text-slate-900">MedSched <span className="text-[#0d968b]">AI</span></span>
          </div>
          <nav className="hidden md:flex items-center gap-8">
            <a href="#" className="text-sm font-semibold text-slate-600 hover:text-[#0d968b] transition-colors">Features</a>
            <a href="#" className="text-sm font-semibold text-slate-600 hover:text-[#0d968b] transition-colors">Security</a>
            <a href="#" className="text-sm font-semibold text-slate-600 hover:text-[#0d968b] transition-colors">Pricing</a>
          </nav>
          <div className="flex items-center gap-4">
            <button className="hidden sm:block text-sm font-bold text-slate-700" onClick={() => onSelectRole('patient')}>Log in</button>
            <button
              className="bg-[#0d968b] text-white px-5 py-2 rounded-lg text-sm font-bold shadow-lg hover:bg-[#0b7a71] transition-all"
              onClick={() => onSelectRole('patient')}
            >
              Get Started
            </button>
          </div>
        </div>
      </header>

      {/* Hero */}
      <main className="flex-grow pt-24 pb-16 flex items-center justify-center" style={{
        background: 'radial-gradient(at 0% 0%, #0d968b 0px, transparent 50%), radial-gradient(at 100% 0%, #ccfbf1 0px, transparent 50%), radial-gradient(at 100% 100%, #14b8a6 0px, transparent 50%), radial-gradient(at 0% 100%, #f0fdfa 0px, transparent 50%), #0d968b'
      }}>
        <div className="max-w-5xl w-full px-6 flex flex-col items-center">
          {/* Badge */}
          <div className="mb-6 inline-flex items-center gap-2 bg-white/30 backdrop-blur-sm px-4 py-1.5 rounded-full border border-white/40">
            <span className="material-symbols-outlined text-[#0d968b] text-lg">verified</span>
            <span className="text-xs font-bold uppercase tracking-widest text-[#0d968b]">Next-Gen Patient Management</span>
          </div>
          <h1 className="text-4xl md:text-6xl font-black text-slate-900 leading-[1.1] mb-6 tracking-tight text-center">
            AI-Powered <br/>Medical Scheduling
          </h1>
          <p className="text-lg md:text-xl text-slate-700 max-w-2xl mx-auto leading-relaxed text-center mb-12">
            Natural language appointment booking with MCP-powered intelligence. Seamlessly bridging the gap between healthcare providers and patients.
          </p>

          {/* Role Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">
            {/* Patient Card */}
            <button
              onClick={() => onSelectRole('patient')}
              className="group relative bg-white backdrop-blur-xl p-8 rounded-xl border border-white/50 shadow-2xl hover:shadow-[#0d968b]/10 transition-all duration-300 cursor-pointer overflow-hidden text-left"
            >
              <div className="absolute -top-12 -right-12 w-32 h-32 bg-[#0d968b]/10 rounded-full group-hover:scale-150 transition-transform duration-500"></div>
              <div className="relative z-10">
                <div className="w-14 h-14 bg-[#0d968b]/10 rounded-xl flex items-center justify-center mb-6 group-hover:bg-[#0d968b] transition-colors">
                  <span className="material-symbols-outlined text-3xl text-[#0d968b] group-hover:text-white transition-colors">patient_list</span>
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-3">I'm a Patient</h3>
                <p className="text-slate-600 mb-8 leading-relaxed">Book appointments using natural language. Speak or type to find the best slot with your specialist instantly.</p>
                <div className="flex items-center gap-2 text-[#0d968b] font-bold group-hover:gap-3 transition-all">
                  <span>Book an Appointment</span>
                  <span className="material-symbols-outlined">arrow_forward</span>
                </div>
              </div>
            </button>

            {/* Doctor Card */}
            <button
              onClick={() => onSelectRole('doctor')}
              className="group relative bg-white backdrop-blur-xl p-8 rounded-xl border border-white/50 shadow-2xl hover:shadow-[#0d968b]/10 transition-all duration-300 cursor-pointer overflow-hidden text-left"
            >
              <div className="absolute -top-12 -right-12 w-32 h-32 bg-[#0d968b]/10 rounded-full group-hover:scale-150 transition-transform duration-500"></div>
              <div className="relative z-10">
                <div className="w-14 h-14 bg-[#0d968b]/10 rounded-xl flex items-center justify-center mb-6 group-hover:bg-[#0d968b] transition-colors">
                  <span className="material-symbols-outlined text-3xl text-[#0d968b] group-hover:text-white transition-colors">stethoscope</span>
                </div>
                <h3 className="text-2xl font-bold text-slate-900 mb-3">I'm a Doctor</h3>
                <p className="text-slate-600 mb-8 leading-relaxed">View detailed patient reports and practice analytics. Optimize your schedule with AI-driven workload balance.</p>
                <div className="flex items-center gap-2 text-[#0d968b] font-bold group-hover:gap-3 transition-all">
                  <span>Access Provider Portal</span>
                  <span className="material-symbols-outlined">arrow_forward</span>
                </div>
              </div>
            </button>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white py-12 border-t border-[#0d968b]/5">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex flex-col md:flex-row justify-between items-center gap-8">
            <div className="flex items-center gap-2.5 opacity-60 grayscale">
              <div className="bg-slate-400 p-1 rounded-md">
                <span className="material-symbols-outlined text-white text-sm">smart_toy</span>
              </div>
              <span className="text-lg font-bold text-slate-900">MedSched AI</span>
            </div>
            <div className="flex flex-wrap justify-center gap-8">
              <a href="#" className="text-sm text-slate-500 hover:text-[#0d968b] transition-colors">Privacy Policy</a>
              <a href="#" className="text-sm text-slate-500 hover:text-[#0d968b] transition-colors">Terms of Service</a>
              <a href="#" className="text-sm text-slate-500 hover:text-[#0d968b] transition-colors">HIPAA Compliance</a>
              <a href="#" className="text-sm text-slate-500 hover:text-[#0d968b] transition-colors">Contact Support</a>
            </div>
            <p className="text-sm text-slate-400">© 2024 MedSched AI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
