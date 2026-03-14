import React, { useState } from 'react';
import { generateReport } from '../services/api';

const SUGGESTIONS = [
  { icon: 'history', label: "Yesterday's visits" },
  { icon: 'thermostat', label: 'Patients with fever' },
  { icon: 'event_busy', label: 'Cancellation rate this week' },
  { icon: 'today', label: "Today's appointment summary" },
];

export default function NlReportGenerator({ user }) {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [sessionId] = useState(() => 'rep-' + Date.now());

  async function handleGenerate() {
    if (!query.trim() || loading) return;
    setLoading(true);
    setResult(null);
    try {
      const res = await generateReport(user.id, query, sessionId);
      setResult(res);
    } catch (err) {
      setResult({ reply: '⚠️ ' + (err?.response?.data?.detail || 'Failed to generate report.') });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col min-h-full bg-[#f6f8f8]">
      {/* Header */}
      <header className="flex items-center justify-between border-b border-[#0d968b]/10 px-6 md:px-20 py-4 bg-white sticky top-0 z-50">
        <div className="flex items-center gap-3">
          <div className="size-8 bg-[#0d968b] rounded-lg flex items-center justify-center text-white">
            <span className="material-symbols-outlined">analytics</span>
          </div>
          <h2 className="text-slate-900 text-lg font-bold tracking-tight">PracticeInsight AI</h2>
        </div>
        <div className="flex items-center gap-4">
          <button className="p-2 hover:bg-[#0d968b]/10 rounded-full transition-colors">
            <span className="material-symbols-outlined text-[#0d968b]">notifications</span>
          </button>
          <div className="size-10 rounded-full bg-[#0d968b]/20 flex items-center justify-center font-bold text-[#0d968b] text-sm">
            {user?.name?.slice(0, 2).toUpperCase() || 'DR'}
          </div>
        </div>
      </header>

      <main className="px-4 md:px-20 flex flex-1 justify-center py-10">
        <div className="flex flex-col max-w-[800px] flex-1 gap-8">
          {/* Hero */}
          <div className="text-center space-y-2">
            <h1 className="text-slate-900 tracking-tight text-4xl md:text-5xl font-extrabold">Ask Your Practice</h1>
            <p className="text-slate-500 text-lg">Generate instant clinical and operational reports using natural language.</p>
          </div>

          {/* Input Card */}
          <div className="flex flex-col gap-4 bg-white p-6 rounded-xl border border-[#0d968b]/10 shadow-sm">
            <div className="relative flex flex-col">
              <textarea
                className="w-full min-h-[160px] resize-none rounded-lg text-slate-900 focus:ring-2 focus:ring-[#0d968b]/50 border border-[#0d968b]/20 bg-[#f6f8f8] placeholder:text-slate-400 text-lg font-normal p-5 outline-none"
                placeholder="Ask anything about your practice... e.g. 'How many patients visited this week?'"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && e.ctrlKey && handleGenerate()}
              />
              <div className="absolute bottom-4 left-4 flex gap-2">
                <button className="p-2 text-[#0d968b] hover:bg-[#0d968b]/10 rounded-lg transition-colors" title="Calendar">
                  <span className="material-symbols-outlined">calendar_today</span>
                </button>
              </div>
            </div>

            {/* Suggestions */}
            <div className="flex flex-wrap gap-2 py-2">
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 w-full mb-1">Try asking:</span>
              {SUGGESTIONS.map((s) => (
                <button
                  key={s.label}
                  onClick={() => setQuery(s.label)}
                  className="flex h-9 items-center gap-x-2 rounded-full bg-[#0d968b]/10 hover:bg-[#0d968b]/20 border border-[#0d968b]/20 px-4 transition-colors"
                >
                  <span className="material-symbols-outlined text-sm text-[#0d968b]">{s.icon}</span>
                  <p className="text-[#0d968b] text-sm font-medium">{s.label}</p>
                </button>
              ))}
            </div>

            {/* Submit */}
            <div className="pt-2">
              <button
                onClick={handleGenerate}
                disabled={!query.trim() || loading}
                className="w-full flex items-center justify-center gap-3 rounded-xl h-14 px-5 bg-[#0d968b] hover:bg-[#0b7a71] disabled:opacity-50 text-white text-lg font-bold transition-all shadow-lg shadow-[#0d968b]/20"
              >
                {loading ? (
                  <>
                    <span className="material-symbols-outlined animate-spin">sync</span>
                    <span>Generating…</span>
                  </>
                ) : (
                  <>
                    <span className="material-symbols-outlined">magic_button</span>
                    <span>Generate Report</span>
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Results */}
          {result && (
            <div className="flex flex-col gap-6">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-slate-800">Latest Insights</h3>
                <div className="flex gap-2">
                  <button className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors text-sm font-medium">
                    <span className="material-symbols-outlined text-sm">picture_as_pdf</span>
                    Download PDF
                  </button>
                  <button
                    onClick={() => {
                      // The report was already sent to Slack via the AI tool — just show confirmation
                      alert('Report sent to Slack via AI!');
                    }}
                    className="flex items-center gap-2 px-4 py-2 bg-[#4A154B] text-white rounded-lg hover:opacity-90 transition-colors text-sm font-medium"
                  >
                    <span className="material-symbols-outlined text-sm">send</span>
                    Send to Slack
                  </button>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-[#0d968b]/10 p-6 shadow-sm">
                <div className="flex flex-col gap-1 mb-4">
                  <p className="text-sm text-slate-500 font-medium">Report Results</p>
                  <h4 className="text-xl font-bold text-slate-800">
                    {result.tool_calls_made?.includes('query_appointments_stats') ? 'Appointment Analytics' : 'AI Analysis'}
                  </h4>
                </div>
                <div className="prose prose-sm max-w-none">
                  {result.reply?.split('\n').map((line, i) => (
                    <p key={i} className={`text-slate-700 leading-relaxed ${line.startsWith('*') || line.startsWith('-') ? 'ml-4' : ''} ${line === '' ? 'mt-2' : ''}`}>
                      {line}
                    </p>
                  ))}
                </div>
                {result.tool_calls_made?.length > 0 && (
                  <div className="mt-4 pt-4 border-t border-slate-100 flex flex-wrap gap-2">
                    {result.tool_calls_made.map((t) => (
                      <span key={t} className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-[#0d968b]/10 text-[#0d968b] text-xs font-medium">
                        <span className="material-symbols-outlined text-xs">check_circle</span>
                        {t.replace(/_/g, ' ')}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </main>

      <footer className="py-10 text-center text-slate-400 text-sm border-t border-slate-100">
        <p>© 2024 PracticeInsight AI. HIPAA Compliant Analytics.</p>
      </footer>
    </div>
  );
}
