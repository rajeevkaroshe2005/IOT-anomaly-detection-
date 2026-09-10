import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Cpu,
  CheckCircle2,
  AlertTriangle,
  HeartPulse,
  Activity,
  Layers,
  Thermometer,
  Droplets,
  Gauge,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  Bell
} from 'lucide-react';
import { dashboardAPI, sensorsAPI, alertsAPI } from '../services/api';
import { useWebSocket } from '../context/WebSocketContext';

export default function Dashboard() {
  const { latestReading, addListener } = useWebSocket();
  const [stats, setStats] = useState({
    total_sensors: 5,
    online_sensors: 5,
    offline_sensors: 0,
    total_readings: 150,
    total_anomalies: 2,
    active_alerts: 2,
    system_health_pct: 98.0,
    latest_reading: null,
    simulator_running: false,
  });
  const [sensors, setSensors] = useState([]);
  const [recentAlerts, setRecentAlerts] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, sensorsRes, alertsRes] = await Promise.all([
        dashboardAPI.getStats(),
        sensorsAPI.getAll(),
        alertsAPI.getAll({ limit: 5, status: 'ACTIVE' }),
      ]);
      setStats(statsRes.data);
      setSensors(sensorsRes.data);
      setRecentAlerts(alertsRes.data);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 8000);
    return () => clearInterval(interval);
  }, []);

  // Listen to live WebSocket stream to update stats and sensors dynamically without reloading
  useEffect(() => {
    const removeListener = addListener((eventType, data) => {
      if (eventType === 'NEW_READING') {
        setStats((prev) => ({
          ...prev,
          total_readings: prev.total_readings + 1,
          latest_reading: data,
        }));

        setSensors((prev) =>
          prev.map((s) => {
            if (s.device_id === data.device_id) {
              return {
                ...s,
                status: 'ONLINE',
                temperature: data.temperature,
                humidity: data.humidity,
                pressure: data.pressure,
                is_anomaly: data.is_anomaly,
                anomaly_score: data.anomaly_score,
                last_reading_time: data.timestamp,
              };
            }
            return s;
          })
        );
      } else if (eventType === 'ANOMALY_DETECTED') {
        setStats((prev) => ({
          ...prev,
          total_anomalies: prev.total_anomalies + 1,
        }));
      } else if (eventType === 'ALERT_GENERATED') {
        setStats((prev) => ({
          ...prev,
          active_alerts: prev.active_alerts + 1,
        }));
        setRecentAlerts((prev) => [data, ...prev.slice(0, 4)]);
      }
    });

    return removeListener;
  }, [addListener]);

  const latest = latestReading || stats.latest_reading;

  return (
    <div className="space-y-6">
      {/* Top Banner: Industrial SCADA Context */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <span className="w-2.5 h-2.5 rounded-full bg-[#2E7D32]"></span>
            <h1 className="text-xl font-bold uppercase tracking-wider text-[#242424] font-mono-data">
              Real-Time SCADA Telemetry & Anomaly Detection
            </h1>
          </div>
          <p className="text-xs text-[#686868] mt-1">
            Multivariate Stream Ingestion via MQTT • Isolation Forest Anomaly Inference • Live WebSocket Broadcast
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchDashboardData}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#F0EBE1] border border-[#E9E2D3] text-xs font-mono-data text-[#242424] hover:bg-[#E9E2D3] transition-colors"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>REFRESH</span>
          </button>
          <Link
            to="/architecture"
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#16423C] text-[#F5F1E8] text-xs font-mono-data font-semibold hover:bg-[#1F5C54] transition-colors"
          >
            <Layers className="w-3.5 h-3.5 text-[#D99A2B]" />
            <span>ARCHITECTURE</span>
          </Link>
        </div>
      </div>

      {/* KPI Cards Grid (Requirement 1 & 25) */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        {/* Total Sensors */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
          <div className="text-[10px] font-mono-data uppercase tracking-wider text-[#686868]">
            TOTAL SENSORS
          </div>
          <div className="text-2xl font-bold font-mono-data text-[#242424] mt-1">
            {String(stats.total_sensors).padStart(2, '0')}
          </div>
          <div className="text-[10px] font-mono-data text-[#16423C] mt-1 flex items-center space-x-1">
            <Cpu className="w-3 h-3" />
            <span>Industrial Fleet</span>
          </div>
        </div>

        {/* Online Sensors */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
          <div className="text-[10px] font-mono-data uppercase tracking-wider text-[#686868]">
            ONLINE SENSORS
          </div>
          <div className="text-2xl font-bold font-mono-data text-[#2E7D32] mt-1">
            {String(stats.online_sensors).padStart(2, '0')}
          </div>
          <div className="text-[10px] font-mono-data text-[#2E7D32] mt-1 flex items-center space-x-1">
            <CheckCircle2 className="w-3 h-3" />
            <span>Active MQTT Streams</span>
          </div>
        </div>

        {/* Offline Sensors */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
          <div className="text-[10px] font-mono-data uppercase tracking-wider text-[#686868]">
            OFFLINE SENSORS
          </div>
          <div className="text-2xl font-bold font-mono-data text-[#6B6B6B] mt-1">
            {String(stats.offline_sensors).padStart(2, '0')}
          </div>
          <div className="text-[10px] font-mono-data text-[#6B6B6B] mt-1">
            Standby / Maintenance
          </div>
        </div>

        {/* Total Readings */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
          <div className="text-[10px] font-mono-data uppercase tracking-wider text-[#686868]">
            TOTAL READINGS
          </div>
          <div className="text-2xl font-bold font-mono-data text-[#1F5C54] mt-1">
            {stats.total_readings.toLocaleString()}
          </div>
          <div className="text-[10px] font-mono-data text-[#1F5C54] mt-1 flex items-center space-x-1">
            <Activity className="w-3 h-3" />
            <span>Ingested & Validated</span>
          </div>
        </div>

        {/* Total Anomalies */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
          <div className="text-[10px] font-mono-data uppercase tracking-wider text-[#686868]">
            TOTAL ANOMALIES
          </div>
          <div className="text-2xl font-bold font-mono-data text-[#B23A2F] mt-1">
            {String(stats.total_anomalies).padStart(2, '0')}
          </div>
          <div className="text-[10px] font-mono-data text-[#B23A2F] mt-1 flex items-center space-x-1">
            <AlertTriangle className="w-3 h-3" />
            <span>ML Isolation Forest</span>
          </div>
        </div>

        {/* System Health */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
          <div className="text-[10px] font-mono-data uppercase tracking-wider text-[#686868]">
            SYSTEM HEALTH
          </div>
          <div className="text-2xl font-bold font-mono-data text-[#16423C] mt-1">
            {stats.system_health_pct}%
          </div>
          <div className="text-[10px] font-mono-data text-[#2E7D32] mt-1 flex items-center space-x-1">
            <HeartPulse className="w-3 h-3" />
            <span>Operational Target</span>
          </div>
        </div>
      </div>

      {/* Latest Telemetry Tele-gauge Bar (Prompt Requirement 1) */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
        <div className="flex flex-col md:flex-row md:items-center justify-between border-b border-[#E9E2D3] pb-3 mb-3 gap-2">
          <div className="flex items-center space-x-2">
            <span className="w-2 h-2 rounded-full bg-[#1F5C54] animate-ping" />
            <span className="text-xs font-mono-data uppercase font-bold text-[#16423C] tracking-wider">
              LATEST STREAM INGESTION TELEMETRY
            </span>
          </div>
          {latest && (
            <div className="text-xs font-mono-data text-[#686868]">
              TIMESTAMP: <span className="text-[#242424] font-semibold">{latest.timestamp}</span>
            </div>
          )}
        </div>

        {latest ? (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 font-mono-data">
            {/* Device ID */}
            <div className="p-3 bg-[#F0EBE1]/60 rounded border border-[#E9E2D3]">
              <div className="text-[10px] text-[#686868] uppercase">DEVICE ID / LOCATION</div>
              <div className="text-sm font-bold text-[#16423C] mt-0.5">{latest.device_id}</div>
              <div className="text-[11px] text-[#686868]">{latest.location || 'Facility Edge'}</div>
            </div>

            {/* Temperature */}
            <div className="p-3 bg-[#F0EBE1]/60 rounded border border-[#E9E2D3]">
              <div className="text-[10px] text-[#686868] uppercase flex items-center space-x-1">
                <Thermometer className="w-3 h-3 text-[#C96B32]" />
                <span>TEMPERATURE</span>
              </div>
              <div className="text-lg font-bold text-[#C96B32] mt-0.5">
                {latest.temperature?.toFixed(1)} °C
              </div>
              <div className="text-[10px] text-[#686868]">Norm: 20.0 - 40.0 °C</div>
            </div>

            {/* Humidity */}
            <div className="p-3 bg-[#F0EBE1]/60 rounded border border-[#E9E2D3]">
              <div className="text-[10px] text-[#686868] uppercase flex items-center space-x-1">
                <Droplets className="w-3 h-3 text-[#1F5C54]" />
                <span>HUMIDITY</span>
              </div>
              <div className="text-lg font-bold text-[#1F5C54] mt-0.5">
                {latest.humidity?.toFixed(1)} %
              </div>
              <div className="text-[10px] text-[#686868]">Norm: 30.0 - 80.0 %</div>
            </div>

            {/* Pressure */}
            <div className="p-3 bg-[#F0EBE1]/60 rounded border border-[#E9E2D3]">
              <div className="text-[10px] text-[#686868] uppercase flex items-center space-x-1">
                <Gauge className="w-3 h-3 text-[#16423C]" />
                <span>PRESSURE</span>
              </div>
              <div className="text-lg font-bold text-[#16423C] mt-0.5">
                {latest.pressure?.toFixed(1)} hPa
              </div>
              <div className="text-[10px] text-[#686868]">Norm: 990 - 1030 hPa</div>
            </div>
          </div>
        ) : (
          <div className="py-6 text-center text-xs font-mono-data text-[#686868]">
            Awaiting incoming telemetry packets... Start the simulator or publish via MQTT.
          </div>
        )}
      </div>

      {/* Main Split: Live Sensors Fleet & Active Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Real-Time Fleet Telemetry */}
        <div className="lg:col-span-2 bg-[#FFFFFF] border border-[#E9E2D3] rounded shadow-industrial overflow-hidden">
          <div className="p-4 border-b border-[#E9E2D3] flex items-center justify-between bg-[#F0EBE1]/30">
            <div className="flex items-center space-x-2">
              <Cpu className="w-4 h-4 text-[#16423C]" />
              <h2 className="text-xs font-bold uppercase tracking-wider font-mono-data text-[#16423C]">
                Active Sensor Telemetry Fleet (5 Nodes)
              </h2>
            </div>
            <Link
              to="/sensors"
              className="text-xs font-mono-data font-semibold text-[#1F5C54] hover:text-[#16423C] flex items-center space-x-1"
            >
              <span>MANAGE SENSORS</span>
              <ArrowRight className="w-3 h-3" />
            </Link>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono-data">
              <thead className="bg-[#F0EBE1] text-[#686868] uppercase text-[10px] border-b border-[#E9E2D3]">
                <tr>
                  <th className="py-2.5 px-4">SENSOR ID</th>
                  <th className="py-2.5 px-4">NAME & LOCATION</th>
                  <th className="py-2.5 px-4 text-right">TEMP (°C)</th>
                  <th className="py-2.5 px-4 text-right">HUMIDITY</th>
                  <th className="py-2.5 px-4 text-right">PRESSURE</th>
                  <th className="py-2.5 px-4 text-center">ANOMALY STATUS</th>
                  <th className="py-2.5 px-4 text-center">ACTION</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E9E2D3]">
                {sensors.map((s) => {
                  const isAnomaly = s.is_anomaly;
                  return (
                    <tr
                      key={s.id}
                      className={`hover:bg-[#F5F1E8]/60 transition-colors ${
                        isAnomaly ? 'bg-[#B23A2F]/5' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-bold text-[#16423C]">{s.device_id}</td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-[#242424]">{s.name}</div>
                        <div className="text-[10px] text-[#686868]">{s.location}</div>
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-[#C96B32]">
                        {s.temperature !== undefined && s.temperature !== null
                          ? `${s.temperature.toFixed(1)} °C`
                          : '—'}
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-[#1F5C54]">
                        {s.humidity !== undefined && s.humidity !== null
                          ? `${s.humidity.toFixed(1)} %`
                          : '—'}
                      </td>
                      <td className="py-3 px-4 text-right font-semibold text-[#16423C]">
                        {s.pressure !== undefined && s.pressure !== null
                          ? `${s.pressure.toFixed(1)} hPa`
                          : '—'}
                      </td>
                      <td className="py-3 px-4 text-center">
                        {isAnomaly ? (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-[#B23A2F] text-white">
                            ● ANOMALY
                          </span>
                        ) : (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-[#2E7D32]/15 text-[#2E7D32]">
                            ● NORMAL
                          </span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <Link
                          to={`/sensors/${s.id}`}
                          className="text-[#1F5C54] hover:underline font-semibold text-[11px]"
                        >
                          View Details
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* Right 1 Col: Active Alerts & Fast Action */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] rounded shadow-industrial flex flex-col justify-between">
          <div>
            <div className="p-4 border-b border-[#E9E2D3] flex items-center justify-between bg-[#F0EBE1]/30">
              <div className="flex items-center space-x-2">
                <Bell className="w-4 h-4 text-[#B23A2F]" />
                <h2 className="text-xs font-bold uppercase tracking-wider font-mono-data text-[#16423C]">
                  Active System Alerts
                </h2>
              </div>
              <Link
                to="/alerts"
                className="text-xs font-mono-data font-semibold text-[#1F5C54] hover:text-[#16423C]"
              >
                ALL ALERTS
              </Link>
            </div>

            <div className="p-3 space-y-2">
              {recentAlerts.length > 0 ? (
                recentAlerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="p-3 rounded border border-[#E9E2D3] bg-[#F5F1E8]/50 font-mono-data text-xs space-y-1"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-[#16423C]">{alert.device_id}</span>
                      <span
                        className={`px-1.5 py-0.5 rounded text-[9px] font-bold ${
                          alert.severity === 'CRITICAL'
                            ? 'bg-[#B23A2F] text-white'
                            : alert.severity === 'HIGH'
                            ? 'bg-[#D99A2B] text-white'
                            : 'bg-[#6B6B6B] text-white'
                        }`}
                      >
                        {alert.severity}
                      </span>
                    </div>
                    <div className="text-[11px] text-[#242424] leading-snug">{alert.message}</div>
                    <div className="text-[9px] text-[#686868]">{alert.created_at}</div>
                  </div>
                ))
              ) : (
                <div className="py-8 text-center text-xs font-mono-data text-[#2E7D32]">
                  <CheckCircle2 className="w-6 h-6 mx-auto mb-1 text-[#2E7D32]" />
                  <span>No active alert triggers. All systems nominal.</span>
                </div>
              )}
            </div>
          </div>

          <div className="p-3 border-t border-[#E9E2D3] bg-[#F0EBE1]/40">
            <Link
              to="/monitoring"
              className="w-full flex items-center justify-center space-x-2 py-2 px-3 rounded bg-[#16423C] text-white text-xs font-mono-data font-semibold hover:bg-[#1F5C54] transition-colors"
            >
              <Activity className="w-3.5 h-3.5 text-[#D99A2B]" />
              <span>OPEN REAL-TIME CHARTS</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
