import React, { useState, useRef, useEffect } from 'react';
import { useSession } from '../contexts/SessionContext';
import { useAuth } from '../contexts/AuthContext';
import { sendMessage } from '../services/api';

const QUICK_ACTIONS = [
  { icon: 'event_available', label: 'Check Availability', msg: "Check Dr. Ahuja's availability for tomorrow" },
  { icon: 'calendar_month', label: 'My Appointments', msg: 'Show my upcoming appointments' },
  { icon: 'medical_services', label: 'Book with Dr. Smith', msg: 'Book appointment with Dr. Smith for this week' },
];

function ToolPill({ tools }) {
  if (!tools?.length) return null;
  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {tools.map((t) => (
        <span key={t} className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-[#0d968b]/10 text-[#0d968b] text-[11px] font-medium">
          <span className="material-symbols-outlined text-[12px]">check</span>
          {t.replace(/_/g, ' ')}
        </span>
      ))}
    </div>
  );
}

function Message({ msg }) {
  const isUser = msg.role === 'user';
  if (isUser) {
    return (
      <div className="flex gap-4 max-w-2xl ml-auto flex-row-reverse">
        <div className="size-8 rounded-full bg-[#0d968b] flex items-center justify-center flex-shrink-0 mt-1">
          <span className="material-symbols-outlined text-white text-[18px]">person</span>
        </div>
        <div className="space-y-1 flex flex-col items-end">
          <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest mr-1">You</p>
          <div className="bg-[#0d968b] text-white rounded-2xl rounded-tr-none p-4 shadow-sm">
            <p className="text-sm leading-relaxed">{msg.content}</p>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="flex gap-4 max-w-2xl">
      <div className="size-8 rounded-full bg-[#0d968b]/20 flex items-center justify-center flex-shrink-0 mt-1">
        <span className="material-symbols-outlined text-[#0d968b] text-[18px]">smart_toy</span>
      </div>
      <div className="space-y-1">
        <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest ml-1">Assistant</p>
        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none p-4 shadow-sm">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
          <ToolPill tools={msg.tools_called} />
        </div>
      </div>
    </div>
  );
}

function TypingIndicator() {
  return (
    <div className="flex gap-4 max-w-2xl">
      <div className="size-8 rounded-full bg-[#0d968b]/20 flex items-center justify-center flex-shrink-0 mt-1">
        <span className="material-symbols-outlined text-[#0d968b] text-[18px]">smart_toy</span>
      </div>
      <div className="space-y-2">
        <p className="text-[11px] font-bold text-slate-400 uppercase tracking-widest ml-1">Assistant</p>
        <div className="bg-white border border-slate-200 rounded-2xl rounded-tl-none p-4 shadow-sm">
          <div className="flex gap-1">
            <div className="size-2 rounded-full bg-slate-300 animate-bounce" style={{ animationDelay: '0ms' }}></div>
            <div className="size-2 rounded-full bg-slate-300 animate-bounce" style={{ animationDelay: '150ms' }}></div>
            <div className="size-2 rounded-full bg-slate-300 animate-bounce" style={{ animationDelay: '300ms' }}></div>
          </div>
        </div>
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-slate-100 border border-slate-200">
          <span className="material-symbols-outlined text-[16px] animate-spin text-[#0d968b]">sync</span>
          <span className="text-xs font-medium text-slate-600">Processing with AI…</span>
        </div>
      </div>
    </div>
  );
}

export default function ChatInterface() {
  const { user, logout } = useAuth();
  const { sessionId, messages, addMessage, newSession } = useSession();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function handleSend(text) {
    const msg = (text || input).trim();
    if (!msg || loading) return;
    setInput('');
    addMessage({ role: 'user', content: msg });
    setLoading(true);
    try {
      const res = await sendMessage(sessionId, msg, 'patient', user?.id);
      addMessage({ role: 'assistant', content: res.reply, tools_called: res.tool_calls_made });
    } catch (err) {
      const detail = err?.response?.data?.detail || 'Something went wrong. Please try again.';
      addMessage({ role: 'assistant', content: `⚠️ ${detail}` });
    } finally {
      setLoading(false);
    }
  }

  // Sidebar recent chats = past sessions (just current for now)
  const recentChats = [
    { id: sessionId, label: messages[0]?.content?.slice(0, 28) || 'New Conversation', active: true },
  ];

  return (
    <div className="flex h-screen overflow-hidden bg-[#f6f8f8] font-display">
      {/* Sidebar */}
      <aside className="w-[280px] flex-shrink-0 bg-white border-r border-slate-200 flex flex-col">
        <div className="p-6">
          <div className="flex items-center gap-3 mb-8">
            <div className="size-10 rounded-full bg-[#0d968b] flex items-center justify-center text-white">
              <span className="material-symbols-outlined">medical_services</span>
            </div>
            <div>
              <h1 className="text-base font-bold leading-tight">MediSchedule MCP</h1>
              <p className="text-xs text-slate-500">Healthcare Assistant</p>
            </div>
          </div>

          <button
            onClick={newSession}
            className="w-full flex items-center justify-center gap-2 bg-[#0d968b] hover:bg-[#0b7a71] text-white font-semibold py-3 px-4 rounded-xl transition-colors mb-6 shadow-sm"
          >
            <span className="material-symbols-outlined text-[20px]">add_box</span>
            <span>New Chat</span>
          </button>

          <nav className="space-y-1">
            <p className="px-3 text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2">Recent Chats</p>
            {recentChats.map((chat) => (
              <div
                key={chat.id}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-lg ${chat.active ? 'bg-[#0d968b]/10 text-[#0d968b] font-medium' : 'text-slate-600 hover:bg-slate-50'} cursor-default`}
              >
                <span className="material-symbols-outlined text-[18px]">chat_bubble</span>
                <span className="truncate text-sm">{chat.label}</span>
              </div>
            ))}
          </nav>
        </div>

        {/* User profile */}
        <div className="mt-auto p-6 border-t border-slate-100">
          <div className="flex items-center gap-3">
            <div className="size-9 rounded-full bg-[#0d968b]/20 flex items-center justify-center font-bold text-[#0d968b] text-sm flex-shrink-0">
              {user?.name?.charAt(0).toUpperCase() || 'P'}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold truncate">{user?.name || user?.email}</p>
              <p className="text-xs text-slate-500 truncate capitalize">{user?.role} · Patient</p>
            </div>
            <button onClick={logout} title="Sign out" className="text-slate-400 hover:text-slate-600 transition-colors">
              <span className="material-symbols-outlined text-[20px]">logout</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col relative overflow-hidden">
        {/* Header */}
        <header className="h-16 flex-shrink-0 flex items-center justify-between px-6 bg-white/80 backdrop-blur-md border-b border-slate-200 z-10">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#0d968b]/10 text-[#0d968b] border border-[#0d968b]/20">
              <span className="material-symbols-outlined text-[16px]">calendar_today</span>
              <span className="text-sm font-semibold tracking-tight">
                {messages.length > 0 ? 'Active Session' : 'Ready to Book'}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <div className="text-xs text-slate-400 font-mono">{sessionId.slice(0, 14)}…</div>
          </div>
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <div className="size-16 rounded-full bg-[#0d968b]/10 flex items-center justify-center mb-6">
                <span className="material-symbols-outlined text-[#0d968b] text-3xl">medical_services</span>
              </div>
              <h3 className="text-xl font-bold text-slate-800 mb-2">How can I help you today?</h3>
              <p className="text-slate-500 max-w-md mb-8">I can check doctor availability, book appointments, and handle rescheduling — all through conversation.</p>
              <div className="flex flex-col gap-2 w-full max-w-sm">
                {QUICK_ACTIONS.map((qa) => (
                  <button
                    key={qa.label}
                    onClick={() => handleSend(qa.msg)}
                    className="flex items-center gap-3 px-4 py-3 rounded-xl bg-white border border-slate-200 hover:border-[#0d968b]/40 hover:text-[#0d968b] transition-all text-left text-sm font-medium text-slate-700 shadow-sm"
                  >
                    <span className="material-symbols-outlined text-[#0d968b] text-[20px]">{qa.icon}</span>
                    {qa.label}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg) => (
            <Message key={msg.id} msg={msg} />
          ))}

          {loading && <TypingIndicator />}
          <div ref={bottomRef} />
        </div>

        {/* Bottom Input Area */}
        <div className="p-6 bg-gradient-to-t from-[#f6f8f8] via-[#f6f8f8]/90 to-transparent">
          {/* Quick Actions row */}
          {messages.length > 0 && (
            <div className="flex gap-2 mb-4 flex-wrap">
              {QUICK_ACTIONS.slice(0, 2).map((qa) => (
                <button
                  key={qa.label}
                  onClick={() => handleSend(qa.msg)}
                  className="flex items-center gap-2 px-4 py-2 rounded-full bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:border-[#0d968b]/40 hover:text-[#0d968b] transition-all shadow-sm"
                >
                  <span className="material-symbols-outlined text-[14px]">{qa.icon}</span>
                  {qa.label}
                </button>
              ))}
            </div>
          )}

          {/* Input */}
          <div className="relative flex items-center gap-3">
            <div className="flex-1 relative">
              <input
                ref={inputRef}
                className="w-full bg-white border border-slate-200 rounded-full py-4 pl-6 pr-14 text-sm focus:ring-2 focus:ring-[#0d968b]/20 focus:border-[#0d968b] transition-all shadow-sm outline-none"
                placeholder="Type your message…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
                disabled={loading}
              />
            </div>
            <button
              onClick={() => handleSend()}
              disabled={loading || !input.trim()}
              className="size-12 rounded-full bg-[#0d968b] text-white flex items-center justify-center hover:bg-[#0b7a71] disabled:opacity-50 transition-all shadow-lg shadow-[#0d968b]/30 flex-shrink-0"
            >
              <span className="material-symbols-outlined">{loading ? 'hourglass_empty' : 'send'}</span>
            </button>
          </div>
          <p className="text-center text-[10px] text-slate-400 mt-3">
            MediSchedule MCP may provide information that should be verified with your healthcare provider.
          </p>
        </div>
      </main>
    </div>
  );
}
