import React, { createContext, useContext, useState, useCallback } from 'react';
import { login as apiLogin, getDoctor, getPatient } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    try {
      const stored = localStorage.getItem('user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const login = useCallback(async (email, password, role) => {
    const data = await apiLogin(email, password, role);
    // Fetch user name from the correct endpoint
    let name = email.split('@')[0];
    try {
      if (role === 'doctor') {
        const doc = await getDoctor(data.user_id);
        name = doc.name;
      } else {
        const pat = await getPatient(data.user_id);
        name = pat.name;
      }
    } catch { /* fall back to email prefix */ }

    const userObj = { token: data.access_token, role: data.role, id: data.user_id, email, name };
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(userObj));
    setUser(userObj);
    return userObj;
  }, []);

  const logout = useCallback(() => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
