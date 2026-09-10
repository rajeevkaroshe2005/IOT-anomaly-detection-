import React, { createContext, useContext, useState, useEffect } from 'react';
import { authAPI } from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('iot_user');
    return saved ? JSON.parse(saved) : { username: 'admin', role: 'ADMIN' }; // Default pre-authenticated admin for smooth testing
  });
  const [token, setToken] = useState(() => localStorage.getItem('iot_token') || 'demo_token');
  const [loading, setLoading] = useState(false);

  const login = async (username, password) => {
    setLoading(true);
    try {
      const res = await authAPI.login(username, password);
      const { access_token, role, username: authUser } = res.data;
      const userData = { username: authUser, role };
      
      localStorage.setItem('iot_token', access_token);
      localStorage.setItem('iot_user', JSON.stringify(userData));
      
      setToken(access_token);
      setUser(userData);
      return { success: true };
    } catch (err) {
      return {
        success: false,
        error: err.response?.data?.detail || 'Authentication failed. Please check credentials.'
      };
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    localStorage.removeItem('iot_token');
    localStorage.removeItem('iot_user');
    setUser(null);
    setToken(null);
  };

  const isAdmin = user?.role === 'ADMIN';
  const isViewer = user?.role === 'VIEWER';

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAdmin, isViewer, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
