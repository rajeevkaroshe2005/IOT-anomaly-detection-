import React, { useState, useEffect } from 'react';
import { Menu, Play, Square, Bell, User, LogOut, Clock, Activity, Volume2, VolumeX } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useWebSocket } from '../context/WebSocketContext';
import { simulatorAPI, dashboardAPI } from '../services/api';
import { scadaAudio } from '../utils/audioAlert';

export default function Header({ setIsSidebarOpen }) {
  const { user, logout, isAdmin } = useAuth();
  const { isConnected } = useWebSocket();
  const navigate = useNavigate();

  const [simRunning, setSimRunning] = useState(false);
  const [simLoading, setSimLoading] = useState(false);
  const [activeAlertCount, setActiveAlertCount] = useState(0);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [soundEnabled, setSoundEnabled] = useState(scadaAudio.isEnabled());

  // Clock ticker
  useEffect(() => {
    const timer = setInterval(() => setCurrentTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  // Poll simulator status and alerts
  const checkStatus = async () => {
    try {
      const statsRes = await dashboardAPI.getStats();
      setSimRunning(statsRes.data.simulator_running);
      setActiveAlertCount(statsRes.data.active_alerts);
    } catch (e) {
      // quiet
    }
  };

  useEffect(() => {
    checkStatus();
    const interval = setInterval(checkStatus, 4000);
    return () => clearInterval(interval);
  }, []);

  const handleToggleSimulator = async () => {
    setSimLoading(true);
    try {
      if (simRunning) {
        await simulatorAPI.stop();
        setSimRunning(false);
      } else {
        await simulatorAPI.start({ interval_seconds: 1.5, anomaly_probability: 0.12 });
        setSimRunning(true);
      }
    } catch (err) {
      console.error('Failed to toggle simulator:', err);
    } finally {
      setSimLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <header className="h-16 bg-[#FFFFFF] border-b border-[#E9E2D3] px-4 lg:px-8 flex items-center justify-between shadow-industrial sticky top-0 z-20">
      {/* Left: Mobile Toggle & Title */}
      <div className="flex items-center space-x-4">
        <button
          onClick={() => setIsSidebarOpen((prev) => !prev)}
          className="lg:hidden p-2 rounded text-[#242424] hover:bg-[#F0EBE1]"
        >
          <Menu className="w-5 h-5" />
        </button>

        {/* Live Stream Telemetry Indicator */}
        <div className="flex items-center space-x-2 text-xs font-mono-data">
          <div
            className={`w-2.5 h-2.5 rounded-full ${
              isConnected ? 'bg-[#2E7D32] scada-live-pulse' : 'bg-[#B23A2F]'
            }`}
          />
          <span className="font-semibold tracking-wider text-[#242424]">
            {isConnected ? 'LIVE WEBSOCKET STREAM' : 'DISCONNECTED'}
          </span>
        </div>
      </div>

      {/* Right: Quick Controls, Clock, Alerts & User */}
      <div className="flex items-center space-x-3 lg:space-x-5">
        {/* Simulator Quick Toggle Button (Prompt Requirement 33) */}
        <button
          onClick={handleToggleSimulator}
          disabled={simLoading}
          className={`flex items-center space-x-2 px-3.5 py-1.5 rounded text-xs font-mono-data font-bold transition-all shadow-sm border ${
            simRunning
              ? 'bg-[#B23A2F] text-white border-[#B23A2F] hover:bg-[#8B231B]'
              : 'bg-[#16423C] text-[#F5F1E8] border-[#16423C] hover:bg-[#1F5C54]'
          }`}
          title="Toggle Background IoT Sensor Simulator"
        >
          {simRunning ? (
            <>
              <Square className="w-3.5 h-3.5 fill-current animate-pulse" />
              <span>STOP SIMULATION</span>
            </>
          ) : (
            <>
              <Play className="w-3.5 h-3.5 fill-current text-[#D99A2B]" />
              <span>START SIMULATION</span>
            </>
          )}
        </button>

        {/* System Time Clock */}
        <div className="hidden md:flex items-center space-x-1.5 text-xs text-[#686868] font-mono-data border-l border-[#E9E2D3] pl-4">
          <Clock className="w-3.5 h-3.5 text-[#1F5C54]" />
          <span>{currentTime.toLocaleTimeString()}</span>
          <span className="text-[10px] text-[#686868]/70">UTC</span>
        </div>

        {/* Alerts Pill */}
        <Link
          to="/alerts"
          className={`flex items-center space-x-1.5 px-2.5 py-1 rounded text-xs font-mono-data border transition-colors ${
            activeAlertCount > 0
              ? 'bg-[#B23A2F]/10 text-[#B23A2F] border-[#B23A2F]/30 hover:bg-[#B23A2F]/20'
              : 'bg-[#F0EBE1] text-[#686868] border-[#E9E2D3]'
          }`}
        >
          <Bell className={`w-3.5 h-3.5 ${activeAlertCount > 0 ? 'animate-bounce' : ''}`} />
          <span className="font-bold">{activeAlertCount}</span>
          <span className="hidden sm:inline">ALERTS</span>
        </Link>

        {/* SCADA Industrial Audio Alarm Toggle */}
        <button
          onClick={() => setSoundEnabled(scadaAudio.toggleSound())}
          className={`flex items-center space-x-1 px-2.5 py-1 rounded text-xs font-mono-data border transition-colors ${
            soundEnabled
              ? 'bg-[#1F5C54]/10 text-[#1F5C54] border-[#1F5C54]/30 hover:bg-[#1F5C54]/20'
              : 'bg-[#F0EBE1] text-[#686868] border-[#E9E2D3] hover:bg-[#E9E2D3]'
          }`}
          title={soundEnabled ? 'SCADA Alarm Audio: Active (Click to Mute)' : 'SCADA Alarm Audio: Muted (Click to Enable)'}
        >
          {soundEnabled ? (
            <Volume2 className="w-3.5 h-3.5 text-[#1F5C54]" />
          ) : (
            <VolumeX className="w-3.5 h-3.5 text-[#686868]" />
          )}
          <span className="hidden xl:inline text-[10px] font-bold">
            {soundEnabled ? 'ALARM ON' : 'MUTED'}
          </span>
        </button>

        {/* User Session Profile Chip */}
        <div className="flex items-center space-x-2 border-l border-[#E9E2D3] pl-4">
          <div className="w-7 h-7 rounded bg-[#16423C] text-white flex items-center justify-center text-xs font-bold font-mono-data">
            {user?.username?.substring(0, 2).toUpperCase() || 'AD'}
          </div>
          <div className="hidden lg:block text-left text-xs font-mono-data leading-tight">
            <div className="font-bold text-[#242424]">{user?.username || 'admin'}</div>
            <div className="text-[10px] text-[#D99A2B] font-semibold">{user?.role || 'ADMIN'}</div>
          </div>
          <button
            onClick={handleLogout}
            title="Logout"
            className="p-1.5 text-[#686868] hover:text-[#B23A2F] rounded hover:bg-[#F0EBE1] transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </header>
  );
}
