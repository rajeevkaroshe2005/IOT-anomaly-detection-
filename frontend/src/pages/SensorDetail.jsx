import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  Cpu,
  Thermometer,
  Droplets,
  Gauge,
  Clock,
  MapPin,
  AlertTriangle,
  Bell,
  RefreshCw,
  CheckCircle2
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
import { sensorsAPI, readingsAPI, anomaliesAPI, alertsAPI } from '../services/api';
import { useWebSocket } from '../context/WebSocketContext';

export default function SensorDetail() {
  const { id } = useParams();
  const { addListener } = useWebSocket();

  const [sensor, setSensor] = useState(null);
  const [readings, setReadings] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [timeframe, setTimeframe] = useState('30m');
  const [loading, setLoading] = useState(true);

  const fetchSensorData = async () => {
    try {
      const [sRes, rRes, anomRes, alertRes] = await Promise.all([
        sensorsAPI.getById(id),
        readingsAPI.getBySensorId(id, timeframe, 150),
        anomaliesAPI.getAll({ sensor_id: id, limit: 10 }),
        alertsAPI.getAll({ sensor_id: id, limit: 5 })
      ]);
      setSensor(sRes.data);
      setReadings(rRes.data);
      setAnomalies(anomRes.data);
      setAlerts(alertRes.data);
    } catch (err) {
      console.error('Failed to load sensor detail:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSensorData();
  }, [id, timeframe]);

  // Live WebSocket update
  useEffect(() => {
    const removeListener = addListener((eventType, data) => {
      if (sensor && data.device_id === sensor.device_id) {
        if (eventType === 'NEW_READING') {
          setSensor((prev) => ({
            ...prev,
            temperature: data.temperature,
            humidity: data.humidity,
            pressure: data.pressure,
            is_anomaly: data.is_anomaly,
            anomaly_score: data.anomaly_score,
            last_seen: data.timestamp
          }));
          setReadings((prev) => [...prev.slice(-149), data]);
        } else if (eventType === 'ANOMALY_DETECTED') {
          setAnomalies((prev) => [data, ...prev.slice(0, 9)]);
        } else if (eventType === 'ALERT_GENERATED') {
          setAlerts((prev) => [data, ...prev.slice(0, 4)]);
        }
      }
    });
    return removeListener;
  }, [addListener, sensor]);

  if (loading && !sensor) {
    return (
      <div className="py-20 text-center font-mono-data text-xs text-[#686868]">
        Loading sensor telemetry specification...
      </div>
    );
  }

  if (!sensor) {
    return (
      <div className="py-20 text-center font-mono-data text-xs text-[#B23A2F]">
        Sensor node not found.
      </div>
    );
  }

  // Format chart data timestamps
  const chartData = readings.map((r) => ({
    ...r,
    time: r.timestamp ? r.timestamp.substring(11, 19) : ''
  }));

  return (
    <div className="space-y-6 font-mono-data">
      {/* Back and Title */}
      <div className="flex items-center justify-between">
        <Link
          to="/sensors"
          className="flex items-center space-x-1.5 text-xs text-[#1F5C54] hover:text-[#16423C] font-semibold"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>BACK TO SENSORS INVENTORY</span>
        </Link>
        <button
          onClick={fetchSensorData}
          className="flex items-center space-x-1 px-3 py-1 rounded bg-[#F0EBE1] border border-[#E9E2D3] text-xs hover:bg-[#E9E2D3]"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
          <span>REFRESH</span>
        </button>
      </div>

      {/* Sensor Info Banner */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-3">
            <div className="p-2 rounded bg-[#16423C] text-white">
              <Cpu className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-lg font-bold text-[#242424]">{sensor.device_id}</h1>
                <span className="text-xs text-[#686868]">({sensor.name})</span>
                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                    sensor.status === 'ONLINE'
                      ? 'bg-[#2E7D32]/15 text-[#2E7D32]'
                      : 'bg-[#6B6B6B]/15 text-[#6B6B6B]'
                  }`}
                >
                  {sensor.status}
                </span>
              </div>
              <div className="flex items-center space-x-4 text-xs text-[#686868] mt-1">
                <div className="flex items-center space-x-1">
                  <MapPin className="w-3.5 h-3.5 text-[#1F5C54]" />
                  <span>{sensor.location}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <Clock className="w-3.5 h-3.5 text-[#1F5C54]" />
                  <span>Last Seen: {sensor.last_seen ? sensor.last_seen.substring(11, 19) : '—'}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Current Anomaly State */}
        <div>
          {sensor.is_anomaly ? (
            <div className="px-3 py-1.5 rounded bg-[#B23A2F] text-white text-xs font-bold flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4" />
              <span>ACTIVE ANOMALY FLAGGED (Score: {sensor.anomaly_score?.toFixed(2)})</span>
            </div>
          ) : (
            <div className="px-3 py-1.5 rounded bg-[#2E7D32]/15 text-[#2E7D32] text-xs font-bold flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4" />
              <span>NOMINAL OPERATIONAL BASELINE</span>
            </div>
          )}
        </div>
      </div>

      {/* 3 Telemetry Live Gauge Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Temperature */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
          <div className="flex items-center justify-between text-[#686868] text-xs">
            <div className="flex items-center space-x-1">
              <Thermometer className="w-4 h-4 text-[#C96B32]" />
              <span className="font-bold uppercase">Temperature</span>
            </div>
            <span className="text-[10px]">Normal: 20–40 °C</span>
          </div>
          <div className="text-3xl font-bold text-[#C96B32] mt-2">
            {sensor.temperature !== undefined ? `${sensor.temperature.toFixed(1)} °C` : '—'}
          </div>
        </div>

        {/* Humidity */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
          <div className="flex items-center justify-between text-[#686868] text-xs">
            <div className="flex items-center space-x-1">
              <Droplets className="w-4 h-4 text-[#1F5C54]" />
              <span className="font-bold uppercase">Humidity</span>
            </div>
            <span className="text-[10px]">Normal: 30–80 %</span>
          </div>
          <div className="text-3xl font-bold text-[#1F5C54] mt-2">
            {sensor.humidity !== undefined ? `${sensor.humidity.toFixed(1)} %` : '—'}
          </div>
        </div>

        {/* Pressure */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-4 rounded shadow-industrial">
          <div className="flex items-center justify-between text-[#686868] text-xs">
            <div className="flex items-center space-x-1">
              <Gauge className="w-4 h-4 text-[#16423C]" />
              <span className="font-bold uppercase">Pressure</span>
            </div>
            <span className="text-[10px]">Normal: 990–1030 hPa</span>
          </div>
          <div className="text-3xl font-bold text-[#16423C] mt-2">
            {sensor.pressure !== undefined ? `${sensor.pressure.toFixed(1)} hPa` : '—'}
          </div>
        </div>
      </div>

      {/* Historical Telemetry Chart */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-[#E9E2D3] gap-2">
          <div className="text-xs font-bold text-[#16423C] uppercase">
            Multi-Metric Telemetry Trend ({sensor.device_id})
          </div>

          <div className="flex items-center space-x-1">
            {['5m', '30m', '1h', '24h'].map((tf) => (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors ${
                  timeframe === tf
                    ? 'bg-[#16423C] text-white'
                    : 'bg-[#F0EBE1] text-[#686868] hover:bg-[#E9E2D3]'
                }`}
              >
                {tf}
              </button>
            ))}
          </div>
        </div>

        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData} margin={{ top: 10, right: 20, left: -10, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#E9E2D3" />
              <XAxis dataKey="time" tick={{ fontSize: 10, fill: '#686868' }} stroke="#E9E2D3" />
              <YAxis tick={{ fontSize: 10, fill: '#686868' }} stroke="#E9E2D3" />
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
                name="Temp (°C)"
                stroke="#C96B32"
                strokeWidth={2}
                dot={false}
              />
              <Line
                type="monotone"
                dataKey="humidity"
                name="Humidity (%)"
                stroke="#1F5C54"
                strokeWidth={1.5}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Split: Anomalies and Recent Alerts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Anomalies */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] rounded shadow-industrial p-4 space-y-3">
          <div className="text-xs font-bold text-[#16423C] uppercase flex items-center space-x-1.5 border-b border-[#E9E2D3] pb-2">
            <AlertTriangle className="w-3.5 h-3.5 text-[#B23A2F]" />
            <span>Detected Outliers on {sensor.device_id}</span>
          </div>

          <div className="space-y-2 max-h-60 overflow-y-auto">
            {anomalies.length > 0 ? (
              anomalies.map((anom) => (
                <div
                  key={anom.id}
                  className="p-2.5 rounded bg-[#F5F1E8] border border-[#E9E2D3] text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#B23A2F]">SCORE: {anom.anomaly_score}</span>
                    <span className="text-[10px] bg-[#B23A2F] text-white px-1.5 py-0.5 rounded font-bold">
                      {anom.severity}
                    </span>
                  </div>
                  <div className="text-[11px] text-[#242424]">{anom.reason}</div>
                  <div className="text-[10px] text-[#686868]">{anom.timestamp}</div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-[#2E7D32]">
                Zero anomalies detected on this sensor node.
              </div>
            )}
          </div>
        </div>

        {/* Alerts */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] rounded shadow-industrial p-4 space-y-3">
          <div className="text-xs font-bold text-[#16423C] uppercase flex items-center space-x-1.5 border-b border-[#E9E2D3] pb-2">
            <Bell className="w-3.5 h-3.5 text-[#D99A2B]" />
            <span>Generated Alerts ({sensor.device_id})</span>
          </div>

          <div className="space-y-2 max-h-60 overflow-y-auto">
            {alerts.length > 0 ? (
              alerts.map((al) => (
                <div
                  key={al.id}
                  className="p-2.5 rounded bg-[#F5F1E8] border border-[#E9E2D3] text-xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[#16423C]">{al.type}</span>
                    <span className="text-[10px] text-[#686868]">{al.status}</span>
                  </div>
                  <div className="text-[11px] text-[#242424]">{al.message}</div>
                  <div className="text-[10px] text-[#686868]">{al.created_at}</div>
                </div>
              ))
            ) : (
              <div className="py-8 text-center text-xs text-[#2E7D32]">
                No alert records generated for this node.
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
