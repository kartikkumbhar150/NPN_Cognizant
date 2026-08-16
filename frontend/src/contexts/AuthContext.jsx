import React, { createContext, useContext, useState, useCallback } from 'react';
import { login as apiLogin, logout as apiLogout, getToken, getEmployee } from '../services/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken]       = useState(() => getToken());
  const [employee, setEmployee] = useState(() => getEmployee());
  const [authError, setAuthError] = useState('');
  const [isLoggingIn, setIsLoggingIn] = useState(false);

  const login = useCallback(async (email, password) => {
    setIsLoggingIn(true);
    setAuthError('');
    try {
      const data = await apiLogin(email, password);
      setToken(data.access_token);
      setEmployee({
        name:  data.employee_name,
        role:  data.employee_role,
        email: data.employee_email,
      });
      return true;
    } catch (err) {
      setAuthError(err.message || 'Login failed. Please check your credentials.');
      return false;
    } finally {
      setIsLoggingIn(false);
    }
  }, []);

  const logout = useCallback(() => {
    apiLogout();
    setToken(null);
    setEmployee(null);
  }, []);

  const isAuthenticated = Boolean(token);

  return (
    <AuthContext.Provider value={{ token, employee, isAuthenticated, login, logout, authError, isLoggingIn }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
