import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { WebSocketProvider } from './context/WebSocketContext';
import MainLayout from './layouts/MainLayout';

// Pages
import Dashboard from './pages/Dashboard';
import Sensors from './pages/Sensors';
import SensorDetail from './pages/SensorDetail';
import LiveMonitoring from './pages/LiveMonitoring';
import Anomalies from './pages/Anomalies';
import Alerts from './pages/Alerts';
import Architecture from './pages/Architecture';
import SystemHealth from './pages/SystemHealth';
import Admin from './pages/Admin';
import Settings from './pages/Settings';
import PlantMap from './pages/PlantMap';
import Login from './pages/Login';

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user } = useAuth();
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return children;
};

export default function App() {
  return (
    <AuthProvider>
      <WebSocketProvider>
        <Router>
          <Routes>
            <Route path="/login" element={<Login />} />

            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <MainLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<Dashboard />} />
              <Route path="plant-map" element={<PlantMap />} />
              <Route path="sensors" element={<Sensors />} />
              <Route path="sensors/:id" element={<SensorDetail />} />
              <Route path="monitoring" element={<LiveMonitoring />} />
              <Route path="anomalies" element={<Anomalies />} />
              <Route path="alerts" element={<Alerts />} />
              <Route path="architecture" element={<Architecture />} />
              <Route path="health" element={<SystemHealth />} />
              <Route path="admin" element={<Admin />} />
              <Route path="settings" element={<Settings />} />
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Router>
      </WebSocketProvider>
    </AuthProvider>
  );
}
