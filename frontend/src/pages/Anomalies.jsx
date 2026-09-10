import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  RefreshCw,
  Filter,
  CheckCircle2,
  Cpu,
  Clock,
  Thermometer,
  Droplets,
  Gauge,
  Download
} from 'lucide-react';
import { anomaliesAPI, sensorsAPI, exportAPI } from '../services/api';
import { useWebSocket } from '../context/WebSocketContext';
import { useAuth } from '../context/AuthContext';

export default function Anomalies() {
  const { addListener } = useWebSocket();
  const { isAdmin } = useAuth();

  const [anomalies, setAnomalies] = useState([]);
  const [sensors, setSensors] = useState([]);
  const [selectedSensorId, setSelectedSensorId] = useState('');
  const [selectedSeverity, setSelectedSeverity] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchAnomalies = async () => {
    try {
      const params = {};
      if (selectedSensorId) params.sensor_id = selectedSensorId;
      if (selectedSeverity) params.severity = selectedSeverity;

      const [anomRes, sensorRes] = await Promise.all([
        anomaliesAPI.getAll(params),
        sensorsAPI.getAll(),
      ]);
      setAnomalies(anomRes.data);
      setSensors(sensorRes.data);
    } catch (err) {
      console.error('Failed to fetch anomalies:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnomalies();
  }, [selectedSensorId, selectedSeverity]);

  // Live WebSocket update
  useEffect(() => {
    const removeListener = addListener((eventType, data) => {
      if (eventType === 'ANOMALY_DETECTED') {
        setAnomalies((prev) => [data, ...prev]);
      }
    });
    return removeListener;
  }, [addListener]);

  const handleAcknowledge = async (id) => {
    try {
      await anomaliesAPI.acknowledge(id);
      setAnomalies((prev) =>
        prev.map((a) => (a.id === id ? { ...a, acknowledged: true } : a))
      );
    } catch (e) {
      console.error('Acknowledge failed:', e);
    }
  };

  return (
    <div className="space-y-6 font-mono-data">
      {/* Top Header */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-5 h-5 text-[#B23A2F]" />
            <h1 className="text-xl font-bold uppercase tracking-wider text-[#242424]">
              Machine Learning Anomaly Audit Log
            </h1>
          </div>
          <p className="text-xs text-[#686868] mt-1">
            Multivariate outlier events flagged by Scikit-Learn Isolation Forest on multi-sensor telemetry.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <a
            href={exportAPI.getAnomaliesCsvUrl(selectedSensorId || null)}
            target="_blank"
            rel="noopener noreferrer"
            download="anomalies_export.csv"
            className="flex items-center space-x-1 px-3 py-1.5 rounded bg-[#16423C] text-[#F5F1E8] text-xs hover:bg-[#1F5C54] transition-colors"
          >
            <Download className="w-3.5 h-3.5 text-[#D99A2B]" />
            <span>EXPORT CSV</span>
          </a>
          <button
            onClick={fetchAnomalies}
            className="flex items-center space-x-1 px-3 py-1.5 rounded bg-[#F0EBE1] border border-[#E9E2D3] text-xs text-[#242424] hover:bg-[#E9E2D3]"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>REFRESH</span>
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial flex flex-wrap items-center gap-4 text-xs">
        <div className="flex items-center space-x-2">
          <Filter className="w-3.5 h-3.5 text-[#16423C]" />
          <span className="font-bold uppercase text-[#16423C]">FILTERS:</span>
        </div>

        {/* Sensor Filter */}
        <div className="flex items-center space-x-2 bg-[#F5F1E8] px-3 py-1.5 rounded border border-[#E9E2D3]">
          <Cpu className="w-3.5 h-3.5 text-[#686868]" />
          <select
            value={selectedSensorId}
            onChange={(e) => setSelectedSensorId(e.target.value)}
            className="bg-transparent text-xs text-[#242424] focus:outline-none"
          >
            <option value="">All Sensors</option>
            {sensors.map((s) => (
              <option key={s.id} value={s.id}>
                {s.device_id} ({s.location})
              </option>
            ))}
          </select>
        </div>

        {/* Severity Filter */}
        <div className="flex items-center space-x-2 bg-[#F5F1E8] px-3 py-1.5 rounded border border-[#E9E2D3]">
          <span className="text-[10px] text-[#686868] uppercase font-bold">Severity:</span>
          <select
            value={selectedSeverity}
            onChange={(e) => setSelectedSeverity(e.target.value)}
            className="bg-transparent text-xs text-[#242424] focus:outline-none"
          >
            <option value="">All Severities</option>
            <option value="CRITICAL">Critical</option>
            <option value="HIGH">High</option>
            <option value="MEDIUM">Medium</option>
            <option value="LOW">Low</option>
          </select>
        </div>

        <div className="ml-auto text-xs text-[#686868]">
          RECORD COUNT: <span className="font-bold text-[#16423C]">{anomalies.length}</span>
        </div>
      </div>

      {/* Anomalies Table (Prompt Requirement 7) */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] rounded shadow-industrial overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F0EBE1] text-[#686868] uppercase text-[10px] border-b border-[#E9E2D3]">
              <tr>
                <th className="py-3 px-4">SENSOR ID</th>
                <th className="py-3 px-4">LOCATION</th>
                <th className="py-3 px-4 text-right">TEMPERATURE</th>
                <th className="py-3 px-4 text-right">HUMIDITY</th>
                <th className="py-3 px-4 text-right">PRESSURE</th>
                <th className="py-3 px-4 text-center">ANOMALY SCORE</th>
                <th className="py-3 px-4 text-center">SEVERITY</th>
                <th className="py-3 px-4">TIMESTAMP</th>
                <th className="py-3 px-4">CLASSIFICATION REASON</th>
                {isAdmin && <th className="py-3 px-4 text-center">STATUS</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E9E2D3]">
              {anomalies.length > 0 ? (
                anomalies.map((a) => (
                  <tr
                    key={a.id}
                    className="hover:bg-[#F5F1E8]/70 transition-colors bg-[#B23A2F]/5"
                  >
                    <td className="py-3 px-4 font-bold text-[#16423C]">{a.device_id}</td>
                    <td className="py-3 px-4 text-[#686868]">{a.location || 'Plant Floor'}</td>
                    <td className="py-3 px-4 text-right font-bold text-[#C96B32]">
                      {a.temperature?.toFixed(1)} °C
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-[#1F5C54]">
                      {a.humidity?.toFixed(1)} %
                    </td>
                    <td className="py-3 px-4 text-right font-bold text-[#16423C]">
                      {a.pressure?.toFixed(1)} hPa
                    </td>
                    <td className="py-3 px-4 text-center font-bold text-[#B23A2F]">
                      {a.anomaly_score?.toFixed(4)}
                    </td>
                    <td className="py-3 px-4 text-center">
                      <span
                        className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                          a.severity === 'CRITICAL'
                            ? 'bg-[#B23A2F] text-white'
                            : a.severity === 'HIGH'
                            ? 'bg-[#D99A2B] text-white'
                            : 'bg-[#6B6B6B] text-white'
                        }`}
                      >
                        {a.severity}
                      </span>
                    </td>
                    <td className="py-3 px-4 text-[11px] text-[#686868]">
                      {a.timestamp?.replace('T', ' ').substring(0, 19)}
                    </td>
                    <td className="py-3 px-4 text-[11px] text-[#242424] max-w-xs truncate">
                      {a.reason || 'Isolation Forest multivariate decision split'}
                    </td>
                    {isAdmin && (
                      <td className="py-3 px-4 text-center">
                        {a.acknowledged ? (
                          <span className="text-[#2E7D32] text-[10px] font-semibold flex items-center justify-center space-x-1">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>ACK</span>
                          </span>
                        ) : (
                          <button
                            onClick={() => handleAcknowledge(a.id)}
                            className="px-2 py-0.5 rounded bg-[#16423C] text-white hover:bg-[#1F5C54] text-[10px] font-bold"
                          >
                            ACKNOWLEDGE
                          </button>
                        )}
                      </td>
                    )}
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={isAdmin ? 10 : 9} className="py-12 text-center text-xs text-[#686868]">
                    No anomaly records match the selected filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
