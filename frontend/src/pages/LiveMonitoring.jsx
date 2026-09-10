import React, { useState, useEffect } from 'react';
import {
  Activity,
  Cpu,
  Clock,
  Thermometer,
  Droplets,
  Gauge,
  AlertTriangle,
  RefreshCw,
  Radio
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceDot
} from 'recharts';
import { sensorsAPI, readingsAPI } from '../services/api';
import { useWebSocket } from '../context/WebSocketContext';

export default function LiveMonitoring() {
  const { addListener } = useWebSocket();

  const [sensors, setSensors] = useState([]);
  const [selectedSensorId, setSelectedSensorId] = useState(null);
  const [timeframe, setTimeframe] = useState('30m');
  const [readings, setReadings] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch sensor list on mount
  useEffect(() => {
    const init = async () => {
      try {
        const res = await sensorsAPI.getAll();
        setSensors(res.data);
        if (res.data.length > 0) {
          setSelectedSensorId(res.data[0].id);
        }
      } catch (e) {
        console.error('Failed to fetch sensors for monitoring:', e);
      }
    };
    init();
  }, []);

  // Fetch readings when sensor or timeframe changes
  const fetchTelemetry = async () => {
    if (!selectedSensorId) return;
    try {
      const res = await readingsAPI.getBySensorId(selectedSensorId, timeframe, 150);
      setReadings(res.data);
    } catch (e) {
      console.error('Failed to fetch readings:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
  }, [selectedSensorId, timeframe]);

  // Handle incoming live WebSocket readings for the selected sensor
  useEffect(() => {
    const removeListener = addListener((eventType, data) => {
      if (eventType === 'NEW_READING') {
        const currentSensor = sensors.find((s) => s.id === selectedSensorId);
        if (currentSensor && data.device_id === currentSensor.device_id) {
          setReadings((prev) => {
            const next = [...prev, data];
            // Keep window size manageable (last 100 points)
            return next.length > 100 ? next.slice(-100) : next;
          });
        }
      }
    });
    return removeListener;
  }, [addListener, selectedSensorId, sensors]);

  const activeSensor = sensors.find((s) => s.id === selectedSensorId);

  // Format data for Recharts
  const chartData = readings.map((r) => ({
    ...r,
    time: r.timestamp ? r.timestamp.substring(11, 19) : '',
    // If anomaly, flag for dot rendering
    anomalyTemp: r.is_anomaly ? r.temperature : null,
    anomalyHum: r.is_anomaly ? r.humidity : null,
    anomalyPress: r.is_anomaly ? r.pressure : null,
  }));

  const anomalyPoints = chartData.filter((d) => d.is_anomaly);

  return (
    <div className="space-y-6 font-mono-data">
      {/* Top SCADA Control Header */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Radio className="w-5 h-5 text-[#C96B32] animate-pulse" />
            <h1 className="text-xl font-bold uppercase tracking-wider text-[#242424]">
              Live Multi-Stream Telemetry Oscilloscope
            </h1>
          </div>
          <p className="text-xs text-[#686868] mt-1">
            Real-time sensory telemetry streaming via WebSocket. Outliers detected by Scikit-Learn Isolation Forest.
          </p>
        </div>

        {/* Controls: Sensor Selector & Time Filters */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Sensor Dropdown */}
          <div className="flex items-center space-x-2 bg-[#F5F1E8] px-3 py-1.5 rounded border border-[#E9E2D3]">
            <Cpu className="w-4 h-4 text-[#16423C]" />
            <select
              value={selectedSensorId || ''}
              onChange={(e) => setSelectedSensorId(Number(e.target.value))}
              className="bg-transparent text-xs font-bold text-[#16423C] focus:outline-none cursor-pointer"
            >
              {sensors.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.device_id} — {s.name} ({s.location})
                </option>
              ))}
            </select>
          </div>

          {/* Timeframe Filters (Prompt Requirement 9) */}
          <div className="flex items-center space-x-1 bg-[#F0EBE1] p-1 rounded border border-[#E9E2D3]">
            {[
              { id: '1m', label: '1 MIN' },
              { id: '5m', label: '5 MIN' },
              { id: '30m', label: '30 MIN' },
              { id: '1h', label: '1 HOUR' },
            ].map((tf) => (
              <button
                key={tf.id}
                onClick={() => setTimeframe(tf.id)}
                className={`px-2.5 py-1 rounded text-[11px] font-bold transition-colors ${
                  timeframe === tf.id
                    ? 'bg-[#16423C] text-white shadow-xs'
                    : 'text-[#686868] hover:text-[#242424]'
                }`}
              >
                {tf.label}
              </button>
            ))}
          </div>

          <button
            onClick={fetchTelemetry}
            className="p-1.5 rounded bg-[#F0EBE1] border border-[#E9E2D3] text-[#242424] hover:bg-[#E9E2D3]"
            title="Refresh View"
          >
            <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {/* Sensor Baseline Banner */}
      {activeSensor && (
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] px-5 py-3 rounded shadow-industrial flex flex-wrap items-center justify-between text-xs text-[#686868] gap-4">
          <div className="flex items-center space-x-4">
            <div>
              NODE: <span className="font-bold text-[#16423C]">{activeSensor.device_id}</span>
            </div>
            <div>
              LOCATION: <span className="font-semibold text-[#242424]">{activeSensor.location}</span>
            </div>
            <div>
              BUFFER: <span className="font-semibold text-[#1F5C54]">{readings.length} data points</span>
            </div>
          </div>

          {/* Chart Color Legend (Prompt Requirement 9 & 26) */}
          <div className="flex items-center space-x-4 text-[11px]">
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-[#C96B32]" />
              <span className="font-semibold text-[#242424]">Temp (Burnt Orange)</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-[#1F5C54]" />
              <span className="font-semibold text-[#242424]">Humidity (Deep Teal)</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-[#16423C]" />
              <span className="font-semibold text-[#242424]">Pressure (Forest Green)</span>
            </div>
            <div className="flex items-center space-x-1.5">
              <span className="w-3 h-3 rounded-full bg-[#B23A2F]" />
              <span className="font-bold text-[#B23A2F]">Anomaly (Dark Red)</span>
            </div>
          </div>
        </div>
      )}

      {/* 3 Real-Time Charts Grid (Requirement 9) */}
      <div className="space-y-5">
        {/* 1. TEMPERATURE CHART (Burnt Orange: #C96B32, Anomaly: #B23A2F) */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial space-y-3">
          <div className="flex items-center justify-between border-b border-[#E9E2D3] pb-2">
            <div className="flex items-center space-x-2 text-xs font-bold text-[#C96B32] uppercase">
              <Thermometer className="w-4 h-4" />
              <span>Real-Time Temperature Stream (°C)</span>
            </div>
            <div className="text-[10px] text-[#686868]">
              Operating Safe Range: 20.0 °C – 40.0 °C
            </div>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F0EBE1" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#686868' }} stroke="#E9E2D3" />
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#686868' }} stroke="#E9E2D3" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E9E2D3',
                    fontSize: '11px',
                    fontFamily: 'IBM Plex Mono'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="temperature"
                  name="Temperature (°C)"
                  stroke="#C96B32"
                  strokeWidth={2.2}
                  isAnimationActive={false}
                  dot={(props) => {
                    const { cx, cy, payload } = props;
                    if (payload.is_anomaly) {
                      return (
                        <circle
                          key={`dot-${payload.id}`}
                          cx={cx}
                          cy={cy}
                          r={6}
                          fill="#B23A2F"
                          stroke="#FFFFFF"
                          strokeWidth={2}
                        />
                      );
                    }
                    return null;
                  }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 2. HUMIDITY CHART (Deep Teal: #1F5C54, Anomaly: #B23A2F) */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial space-y-3">
          <div className="flex items-center justify-between border-b border-[#E9E2D3] pb-2">
            <div className="flex items-center space-x-2 text-xs font-bold text-[#1F5C54] uppercase">
              <Droplets className="w-4 h-4" />
              <span>Real-Time Humidity Stream (%)</span>
            </div>
            <div className="text-[10px] text-[#686868]">
              Operating Safe Range: 30.0 % – 80.0 %
            </div>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F0EBE1" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#686868' }} stroke="#E9E2D3" />
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#686868' }} stroke="#E9E2D3" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E9E2D3',
                    fontSize: '11px',
                    fontFamily: 'IBM Plex Mono'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="humidity"
                  name="Humidity (%)"
                  stroke="#1F5C54"
                  strokeWidth={2.2}
                  isAnimationActive={false}
                  dot={(props) => {
                    const { cx, cy, payload } = props;
                    if (payload.is_anomaly) {
                      return (
                        <circle
                          key={`dot-h-${payload.id}`}
                          cx={cx}
                          cy={cy}
                          r={6}
                          fill="#B23A2F"
                          stroke="#FFFFFF"
                          strokeWidth={2}
                        />
                      );
                    }
                    return null;
                  }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* 3. PRESSURE CHART (Forest Green: #16423C, Anomaly: #B23A2F) */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial space-y-3">
          <div className="flex items-center justify-between border-b border-[#E9E2D3] pb-2">
            <div className="flex items-center space-x-2 text-xs font-bold text-[#16423C] uppercase">
              <Gauge className="w-4 h-4" />
              <span>Real-Time Atmospheric Pressure Stream (hPa)</span>
            </div>
            <div className="text-[10px] text-[#686868]">
              Operating Safe Range: 990.0 hPa – 1030.0 hPa
            </div>
          </div>

          <div className="h-60 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F0EBE1" />
                <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#686868' }} stroke="#E9E2D3" />
                <YAxis domain={['auto', 'auto']} tick={{ fontSize: 10, fill: '#686868' }} stroke="#E9E2D3" />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#FFFFFF',
                    borderColor: '#E9E2D3',
                    fontSize: '11px',
                    fontFamily: 'IBM Plex Mono'
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="pressure"
                  name="Pressure (hPa)"
                  stroke="#16423C"
                  strokeWidth={2.2}
                  isAnimationActive={false}
                  dot={(props) => {
                    const { cx, cy, payload } = props;
                    if (payload.is_anomaly) {
                      return (
                        <circle
                          key={`dot-p-${payload.id}`}
                          cx={cx}
                          cy={cy}
                          r={6}
                          fill="#B23A2F"
                          stroke="#FFFFFF"
                          strokeWidth={2}
                        />
                      );
                    }
                    return null;
                  }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* Live Ingest Telemetry Stream Ticker */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] rounded shadow-industrial p-4 space-y-3">
        <div className="flex items-center justify-between border-b border-[#E9E2D3] pb-2">
          <div className="flex items-center space-x-2 text-xs font-bold text-[#16423C] uppercase">
            <Activity className="w-4 h-4 text-[#D99A2B]" />
            <span>Incoming Raw Telemetry Packets Buffer</span>
          </div>
          <span className="text-[10px] text-[#686868]">Autoscrolling stream</span>
        </div>

        <div className="max-h-48 overflow-y-auto space-y-1 text-[11px]">
          {readings.slice(-10).reverse().map((r, i) => (
            <div
              key={r.id || i}
              className={`p-2 rounded border flex items-center justify-between ${
                r.is_anomaly
                  ? 'bg-[#B23A2F]/10 border-[#B23A2F]/30 text-[#B23A2F] font-bold'
                  : 'bg-[#F5F1E8]/60 border-[#E9E2D3] text-[#242424]'
              }`}
            >
              <div className="flex items-center space-x-3">
                <span className="font-semibold">{r.timestamp?.substring(11, 19)}</span>
                <span>{r.device_id}</span>
                <span>T: {r.temperature?.toFixed(1)}°C</span>
                <span>H: {r.humidity?.toFixed(1)}%</span>
                <span>P: {r.pressure?.toFixed(1)}hPa</span>
              </div>
              <div>
                {r.is_anomaly ? (
                  <span className="bg-[#B23A2F] text-white px-2 py-0.5 rounded text-[10px]">
                    ANOMALY (Score: {r.anomaly_score?.toFixed(2)})
                  </span>
                ) : (
                  <span className="text-[#2E7D32] text-[10px]">NORMAL</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
