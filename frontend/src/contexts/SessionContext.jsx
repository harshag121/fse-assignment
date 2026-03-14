import React, { createContext, useContext, useState, useCallback } from 'react';

const SessionContext = createContext(null);

function generateSessionId() {
  return 'sess-' + Math.random().toString(36).slice(2, 11) + '-' + Date.now();
}

export function SessionProvider({ children }) {
  const [sessionId, setSessionId] = useState(() => generateSessionId());
  const [messages, setMessages] = useState([]);

  const newSession = useCallback(() => {
    setSessionId(generateSessionId());
    setMessages([]);
  }, []);

  const addMessage = useCallback((msg) => {
    setMessages((prev) => [...prev, { ...msg, id: Date.now() + Math.random() }]);
  }, []);

  return (
    <SessionContext.Provider value={{ sessionId, messages, addMessage, newSession }}>
      {children}
    </SessionContext.Provider>
  );
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error('useSession must be used within SessionProvider');
  return ctx;
}
