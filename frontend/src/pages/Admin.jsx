import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  Play,
  Square,
  Zap,
  Sliders,
  Terminal,
  RefreshCw,
  RotateCcw,
  CheckCircle2,
  AlertTriangle,
  Cpu,
  Bell
} from 'lucide-react';
import { simulatorAPI, systemAPI, dashboardAPI } from '../services/api';
import { useAuth } from '../context/AuthContext';

export default function Admin() {
  const { isAdmin } = useAuth();

  const [simStatus, setSimStatus] = useState({
    is_running: false,
    interval_seconds: 1.5,
    anomaly_probability: 0.10,
    total_published: 0,
  });
  const [intervalSetting, setIntervalSetting] = useState(1.5);
  const [anomalyRateSetting, setAnomalyRateSetting] = useState(0.10);
  const [systemLogs, setSystemLogs] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [actionMsg, setActionMsg] = useState('');

  const refreshData = async () => {
    try {
      const [simRes, logsRes, statsRes] = await Promise.all([
        simulatorAPI.getStatus(),
        systemAPI.getLogs({ limit: 40 }),
        dashboardAPI.getStats(),
      ]);
      setSimStatus(simRes.data);
      setIntervalSetting(simRes.data.interval_seconds);
      setAnomalyRateSetting(simRes.data.anomaly_probability);
      setSystemLogs(logsRes.data);
      setStats(statsRes.data);
    } catch (e) {
      console.error('Admin refresh failed:', e);
    }
  };

  useEffect(() => {
    refreshData();
  }, []);

  const handleStartSim = async () => {
    setLoading(true);
    try {
      await simulatorAPI.start({
        interval_seconds: Number(intervalSetting),
        anomaly_probability: Number(anomalyRateSetting),
      });
      setActionMsg('Simulator successfully initiated.');
      refreshData();
    } catch (e) {
      setActionMsg('Failed to start simulator.');
    } finally {
      setLoading(false);
    }
  };

  const handleStopSim = async () => {
    setLoading(true);
    try {
      await simulatorAPI.stop();
      setActionMsg('Simulator halted.');
      refreshData();
    } catch (e) {
      setActionMsg('Failed to stop simulator.');
    } finally {
      setLoading(false);
    }
  };

  const handleForceAnomaly = async () => {
    try {
      const res = await simulatorAPI.forceAnomaly();
      setActionMsg(`Instant anomaly injected: ${res.data.reading?.device_id} (Score: ${res.data.reading?.anomaly_score})`);
      refreshData();
    } catch (e) {
      setActionMsg('Failed to inject anomaly.');
    }
  };

  const handleResetDatabase = async () => {
    if (window.confirm('Reset database back to clean initial demo state? (All 5 sensors & fresh baseline will be re-seeded)')) {
      try {
        await systemAPI.resetDemo();
        setActionMsg('Database wiped and re-seeded to initial clean demo state.');
        refreshData();
      } catch (e) {
        setActionMsg('Reset failed.');
      }
    }
  };

  if (!isAdmin) {
    return (
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-8 rounded text-center font-mono-data">
        <AlertTriangle className="w-8 h-8 text-[#D99A2B] mx-auto mb-2" />
        <h2 className="text-sm font-bold text-[#242424] uppercase">Administrative Access Restricted</h2>
        <p className="text-xs text-[#686868] mt-1">
          You are currently logged in with VIEWER permissions. Switch to the ADMIN account (admin / admin123) to manage the simulator and system logs.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6 font-mono-data">
      {/* Header */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <ShieldCheck className="w-5 h-5 text-[#16423C]" />
            <h1 className="text-xl font-bold uppercase tracking-wider text-[#242424]">
              Industrial Operations Control Deck
            </h1>
          </div>
          <p className="text-xs text-[#686868] mt-1">
            Orchestrate background telemetry simulation, calibrate injection probabilities, and review audit trails.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={refreshData}
            className="flex items-center space-x-1 px-3 py-1.5 rounded bg-[#F0EBE1] border border-[#E9E2D3] text-xs text-[#242424] hover:bg-[#E9E2D3]"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>REFRESH</span>
          </button>
        </div>
      </div>

      {actionMsg && (
        <div className="p-3 bg-[#1F5C54]/10 border border-[#1F5C54]/30 text-[#1F5C54] text-xs rounded flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{actionMsg}</span>
          </div>
          <button onClick={() => setActionMsg('')} className="text-xs font-bold">×</button>
        </div>
      )}

      {/* Simulator Control Panel (Prompt Requirement 15 & 33) */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-6 rounded shadow-industrial space-y-6">
        <div className="flex items-center justify-between border-b border-[#E9E2D3] pb-3">
          <div className="flex items-center space-x-2">
            <Sliders className="w-4 h-4 text-[#16423C]" />
            <h2 className="text-xs font-bold text-[#16423C] uppercase tracking-wider">
              IoT Telemetry Fleet Simulator Controller
            </h2>
          </div>
          <span
            className={`px-2.5 py-0.5 rounded text-[10px] font-bold ${
              simStatus.is_running
                ? 'bg-[#2E7D32] text-white animate-pulse'
                : 'bg-[#6B6B6B] text-white'
            }`}
          >
            {simStatus.is_running ? '● SIMULATOR ACTIVE' : '○ SIMULATOR STOPPED'}
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Sliders */}
          <div className="space-y-4">
            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-bold text-[#242424]">Publish Interval (Seconds):</span>
                <span className="text-[#1F5C54] font-bold">{intervalSetting}s</span>
              </div>
              <input
                type="range"
                min="0.5"
                max="5.0"
                step="0.5"
                value={intervalSetting}
                onChange={(e) => setIntervalSetting(parseFloat(e.target.value))}
                className="w-full accent-[#16423C]"
              />
              <div className="flex justify-between text-[10px] text-[#686868]">
                <span>0.5s (High Frequency)</span>
                <span>5.0s (Relaxed)</span>
              </div>
            </div>

            <div>
              <div className="flex items-center justify-between text-xs mb-1">
                <span className="font-bold text-[#242424]">Anomaly Injection Probability:</span>
                <span className="text-[#B23A2F] font-bold">{(anomalyRateSetting * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="0.5"
                step="0.05"
                value={anomalyRateSetting}
                onChange={(e) => setAnomalyRateSetting(parseFloat(e.target.value))}
                className="w-full accent-[#B23A2F]"
              />
              <div className="flex justify-between text-[10px] text-[#686868]">
                <span>0% (Zero Outliers)</span>
                <span>50% (High Stress)</span>
              </div>
            </div>
          </div>

          {/* Buttons and Triggers */}
          <div className="flex flex-col justify-between space-y-3 bg-[#F5F1E8] p-4 rounded border border-[#E9E2D3]">
            <div className="text-xs text-[#686868] leading-relaxed">
              Start background thread emulating all 5 edge sensors. Ingests via MQTT, triggers Isolation Forest evaluation, and pushes live packets to WebSocket.
            </div>

            <div className="flex flex-wrap items-center gap-3">
              {simStatus.is_running ? (
                <button
                  onClick={handleStopSim}
                  disabled={loading}
                  className="flex items-center space-x-2 px-4 py-2 rounded bg-[#B23A2F] text-white text-xs font-bold hover:bg-[#8B231B] transition-colors"
                >
                  <Square className="w-4 h-4 fill-current" />
                  <span>STOP SIMULATION</span>
                </button>
              ) : (
                <button
                  onClick={handleStartSim}
                  disabled={loading}
                  className="flex items-center space-x-2 px-4 py-2 rounded bg-[#16423C] text-white text-xs font-bold hover:bg-[#1F5C54] transition-colors"
                >
                  <Play className="w-4 h-4 fill-current text-[#D99A2B]" />
                  <span>START SIMULATION</span>
                </button>
              )}

              <button
                onClick={handleForceAnomaly}
                className="flex items-center space-x-1.5 px-3 py-2 rounded bg-[#D99A2B] text-white text-xs font-bold hover:bg-[#B87D1B] transition-colors"
                title="Immediately triggers a critical spike to test Isolation Forest & Alert engine"
              >
                <Zap className="w-3.5 h-3.5 fill-current" />
                <span>FORCE ANOMALY INJECTION</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Audit System Logs (Prompt Requirement 20) */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] rounded shadow-industrial p-5 space-y-4">
        <div className="flex items-center justify-between border-b border-[#E9E2D3] pb-2">
          <div className="flex items-center space-x-2 text-xs font-bold text-[#16423C] uppercase">
            <Terminal className="w-4 h-4 text-[#16423C]" />
            <span>Backend System Audit Trail</span>
          </div>

          <button
            onClick={handleResetDatabase}
            className="flex items-center space-x-1 px-2.5 py-1 rounded bg-[#B23A2F]/10 text-[#B23A2F] hover:bg-[#B23A2F]/20 text-[11px] font-bold"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>RESET DEMO DATA</span>
          </button>
        </div>

        <div className="bg-[#0F2F2B] text-[#F5F1E8] p-4 rounded font-mono text-[11px] max-h-72 overflow-y-auto space-y-1">
          {systemLogs.map((log) => {
            const isError = log.level === 'ERROR' || log.level === 'CRITICAL';
            const isWarning = log.level === 'WARNING';
            return (
              <div key={log.id} className="flex items-start space-x-2 leading-relaxed">
                <span className="text-[#E9E2D3]/60">{log.timestamp?.substring(11, 19)}</span>
                <span
                  className={`font-bold ${
                    isError
                      ? 'text-[#B23A2F]'
                      : isWarning
                      ? 'text-[#D99A2B]'
                      : 'text-[#2E7D32]'
                  }`}
                >
                  [{log.level}]
                </span>
                <span className="text-[#D99A2B]/80 font-semibold">[{log.source}]</span>
                <span className="text-[#F5F1E8]">{log.message}</span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
