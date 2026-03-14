import React, { useState, useRef, useEffect } from 'react';
import { useSession } from '../contexts/SessionContext';
import { useAuth } from '../contexts/AuthContext';
import { sendMessage } from '../services/api';
import styles from './ChatInterface.module.css';

function ToolBadge({ tools }) {
  if (!tools?.length) return null;
  return (
    <div className={styles.toolBadges}>
      {tools.map((t) => (
        <span key={t} className={styles.toolBadge}>{t}</span>
      ))}
    </div>
  );
}

function Message({ msg }) {
  const isUser = msg.role === 'user';
  return (
    <div className={`${styles.msgRow} ${isUser ? styles.userRow : styles.assistantRow}`}>
      <div className={`${styles.bubble} ${isUser ? styles.userBubble : styles.assistantBubble}`}>
        <p className={styles.msgText}>{msg.content}</p>
        {msg.tools_called?.length > 0 && <ToolBadge tools={msg.tools_called} />}
      </div>
    </div>
  );
}

const SUGGESTIONS = {
  patient: [
    "Check Dr. Ahuja's availability for tomorrow",
    "Book an appointment with Dr. Smith for fever",
    "Reschedule my 3PM slot to 4PM",
  ],
  doctor: [
    "How many patients visited yesterday?",
    "Send me a summary of today's appointments",
    "How many patients came with fever this week?",
  ],
};

export default function ChatInterface() {
  const { user } = useAuth();
  const { sessionId, messages, addMessage, newSession } = useSession();
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);
  const role = user?.role || 'patient';

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function handleSend(text) {
    const msg = text || input.trim();
    if (!msg || loading) return;
    setInput('');

    addMessage({ role: 'user', content: msg });
    setLoading(true);

    try {
      const res = await sendMessage(sessionId, msg, role, user?.id);
      addMessage({
        role: 'assistant',
        content: res.reply,
        tools_called: res.tool_calls_made,
      });
    } catch (err) {
      addMessage({
        role: 'assistant',
        content: '⚠️ Sorry, something went wrong. Please try again.',
      });
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h2 className={styles.title}>
            {role === 'doctor' ? '📊 Doctor Assistant' : '🏥 Book Appointment'}
          </h2>
          <p className={styles.subtitle}>Session: {sessionId.slice(0, 16)}…</p>
        </div>
        <button className={styles.newSessionBtn} onClick={newSession}>New Session</button>
      </div>

      <div className={styles.messagesArea}>
        {messages.length === 0 && (
          <div className={styles.emptyState}>
            <p className={styles.emptyTitle}>
              {role === 'doctor' ? 'Ask me about your patients' : 'How can I help you today?'}
            </p>
            <div className={styles.suggestions}>
              {SUGGESTIONS[role]?.map((s) => (
                <button key={s} className={styles.suggestionBtn} onClick={() => handleSend(s)}>{s}</button>
              ))}
            </div>
          </div>
        )}

        {messages.map((msg) => (
          <Message key={msg.id} msg={msg} />
        ))}

        {loading && (
          <div className={`${styles.msgRow} ${styles.assistantRow}`}>
            <div className={`${styles.bubble} ${styles.assistantBubble} ${styles.typingBubble}`}>
              <span className={styles.dot} /><span className={styles.dot} /><span className={styles.dot} />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className={styles.inputArea}>
        <input
          className={styles.input}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
          placeholder={role === 'doctor' ? 'Ask about appointments or reports…' : 'Type your request…'}
          disabled={loading}
        />
        <button className={styles.sendBtn} onClick={() => handleSend()} disabled={loading || !input.trim()}>
          Send
        </button>
      </div>
    </div>
  );
}
