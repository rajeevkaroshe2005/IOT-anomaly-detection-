import React, { useState, useEffect } from 'react';
import {
  Server,
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Cpu,
  Database,
  Radio,
  Brain,
  Zap,
  HardDrive,
  Activity,
  Clock
} from 'lucide-react';
import { systemAPI } from '../services/api';

const SUBSYSTEM_ICONS = {
  'FastAPI REST Server': Server,
  'Database Layer': Database,
  'MQTT Message Broker': Radio,
  'AWS IoT Core Broker': Radio,
  'ML Isolation Forest Engine': Brain,
  'WebSocket Broadcaster': Zap,
  'IoT Sensor Simulator': Cpu,
};

export default function SystemHealth() {
  const [healthData, setHealthData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchHealth = async () => {
    try {
      const res = await systemAPI.getHealth();
      setHealthData(res.data);
    } catch (err) {
      console.error('Failed to load system health:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const timer = setInterval(fetchHealth, 5000);
    return () => clearInterval(timer);
  }, []);

  const getStatusBadge = (status) => {
    if (status === 'ONLINE') {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-[#2E7D32]/15 text-[#2E7D32] font-bold text-xs">
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>ONLINE</span>
        </span>
      );
    }
    if (status === 'WARNING') {
      return (
        <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-[#D99A2B]/15 text-[#D99A2B] font-bold text-xs">
          <AlertTriangle className="w-3.5 h-3.5" />
          <span>WARNING</span>
        </span>
      );
    }
    return (
      <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded bg-[#B23A2F]/15 text-[#B23A2F] font-bold text-xs">
        <XCircle className="w-3.5 h-3.5" />
        <span>OFFLINE</span>
      </span>
    );
  };

  return (
    <div className="space-y-6 font-mono-data">
      {/* Top Header */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Server className="w-5 h-5 text-[#16423C]" />
            <h1 className="text-xl font-bold uppercase tracking-wider text-[#242424]">
              Subsystem Health & Infrastructure Telemetry
            </h1>
          </div>
          <p className="text-xs text-[#686868] mt-1">
            Real-time diagnostics and liveness probes for all 6 industrial microservices and core infrastructure layers.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchHealth}
            className="flex items-center space-x-1 px-3 py-1.5 rounded bg-[#F0EBE1] border border-[#E9E2D3] text-xs text-[#242424] hover:bg-[#E9E2D3]"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>PROBE SUBSYSTEMS</span>
          </button>
        </div>
      </div>

      {/* Host Metrics Bar */}
      {healthData && healthData.system_metrics && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
            <div className="text-[10px] uppercase text-[#686868] flex items-center space-x-1">
              <Cpu className="w-3 h-3 text-[#1F5C54]" />
              <span>CPU UTILIZATION</span>
            </div>
            <div className="text-2xl font-bold text-[#16423C] mt-1">
              {healthData.system_metrics.cpu_percent}%
            </div>
          </div>

          <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
            <div className="text-[10px] uppercase text-[#686868] flex items-center space-x-1">
              <Activity className="w-3 h-3 text-[#C96B32]" />
              <span>HOST MEMORY USED</span>
            </div>
            <div className="text-2xl font-bold text-[#242424] mt-1">
              {healthData.system_metrics.memory_used_mb} <span className="text-xs font-normal">MB</span>
            </div>
            <div className="text-[10px] text-[#686868]">
              {healthData.system_metrics.memory_percent}% of Total
            </div>
          </div>

          <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
            <div className="text-[10px] uppercase text-[#686868] flex items-center space-x-1">
              <HardDrive className="w-3 h-3 text-[#16423C]" />
              <span>STORAGE USAGE</span>
            </div>
            <div className="text-2xl font-bold text-[#242424] mt-1">
              {healthData.system_metrics.disk_percent}%
            </div>
          </div>

          <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
            <div className="text-[10px] uppercase text-[#686868] flex items-center space-x-1">
              <Clock className="w-3 h-3 text-[#2E7D32]" />
              <span>SERVER UPTIME</span>
            </div>
            <div className="text-2xl font-bold text-[#2E7D32] mt-1">
              {healthData.system_metrics.uptime_seconds} <span className="text-xs font-normal">SEC</span>
            </div>
          </div>
        </div>
      )}

      {/* Subsystem Health Cards (Prompt Requirement 16) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {healthData?.subsystems.map((sub) => {
          const Icon = SUBSYSTEM_ICONS[sub.name] || Server;
          return (
            <div
              key={sub.name}
              className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial flex flex-col justify-between space-y-4"
            >
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div className="p-2 rounded bg-[#F5F1E8] text-[#16423C]">
                      <Icon className="w-4 h-4" />
                    </div>
                    <span className="font-bold text-xs text-[#242424]">{sub.name}</span>
                  </div>
                  {getStatusBadge(sub.status)}
                </div>

                <p className="text-xs text-[#686868] mt-3 leading-relaxed">{sub.detail}</p>
              </div>

              <div className="pt-3 border-t border-[#E9E2D3] flex items-center justify-between text-[11px] text-[#686868]">
                <span>LATENCY:</span>
                <span className="font-bold text-[#1F5C54]">
                  {sub.latency_ms !== null ? `${sub.latency_ms} ms` : 'N/A'}
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
