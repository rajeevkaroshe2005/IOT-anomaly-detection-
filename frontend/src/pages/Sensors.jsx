import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Cpu,
  Plus,
  Edit2,
  Trash2,
  Power,
  RefreshCw,
  ExternalLink,
  MapPin,
  Clock,
  Thermometer,
  Droplets,
  Gauge,
  X,
  Check
} from 'lucide-react';
import { sensorsAPI } from '../services/api';
import { useWebSocket } from '../context/WebSocketContext';
import { useAuth } from '../context/AuthContext';

export default function Sensors() {
  const { addListener } = useWebSocket();
  const { isAdmin } = useAuth();

  const [sensors, setSensors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [modalType, setModalType] = useState(null); // 'ADD' | 'EDIT' | null
  const [selectedSensor, setSelectedSensor] = useState(null);
  const [formData, setFormData] = useState({
    device_id: '',
    name: '',
    location: 'Production Floor',
    status: 'ONLINE',
    is_enabled: true
  });
  const [errorMsg, setErrorMsg] = useState('');

  const fetchSensors = async () => {
    try {
      const res = await sensorsAPI.getAll();
      setSensors(res.data);
    } catch (err) {
      console.error('Error fetching sensors:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSensors();
  }, []);

  // Live WebSocket update for sensors
  useEffect(() => {
    const removeListener = addListener((eventType, data) => {
      if (eventType === 'NEW_READING') {
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
                last_seen: data.timestamp,
              };
            }
            return s;
          })
        );
      }
    });
    return removeListener;
  }, [addListener]);

  const handleOpenAdd = () => {
    const nextId = `SENSOR-${String(sensors.length + 1).padStart(3, '0')}`;
    setFormData({
      device_id: nextId,
      name: `Industrial Node ${nextId}`,
      location: 'Production Floor',
      status: 'ONLINE',
      is_enabled: true
    });
    setErrorMsg('');
    setModalType('ADD');
  };

  const handleOpenEdit = (sensor) => {
    setSelectedSensor(sensor);
    setFormData({
      device_id: sensor.device_id,
      name: sensor.name,
      location: sensor.location,
      status: sensor.status,
      is_enabled: sensor.is_enabled
    });
    setErrorMsg('');
    setModalType('EDIT');
  };

  const handleSaveSensor = async (e) => {
    e.preventDefault();
    setErrorMsg('');
    try {
      if (modalType === 'ADD') {
        await sensorsAPI.create(formData);
      } else if (modalType === 'EDIT') {
        await sensorsAPI.update(selectedSensor.id, formData);
      }
      setModalType(null);
      fetchSensors();
    } catch (err) {
      setErrorMsg(err.response?.data?.detail || 'Operation failed.');
    }
  };

  const handleToggle = async (sensorId) => {
    try {
      await sensorsAPI.toggle(sensorId);
      fetchSensors();
    } catch (err) {
      console.error('Toggle failed:', err);
    }
  };

  const handleDelete = async (sensorId, devId) => {
    if (window.confirm(`Confirm permanent deletion of sensor ${devId}?`)) {
      try {
        await sensorsAPI.delete(sensorId);
        fetchSensors();
      } catch (err) {
        console.error('Delete failed:', err);
      }
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Cpu className="w-5 h-5 text-[#16423C]" />
            <h1 className="text-xl font-bold uppercase tracking-wider font-mono-data text-[#242424]">
              Sensor Fleet Inventory & Management
            </h1>
          </div>
          <p className="text-xs text-[#686868] mt-1 font-mono-data">
            Manage physical IoT sensors, locations, operational state, and view live telemetry.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchSensors}
            className="flex items-center space-x-1 px-3 py-1.5 rounded bg-[#F0EBE1] border border-[#E9E2D3] text-xs font-mono-data text-[#242424] hover:bg-[#E9E2D3]"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>REFRESH</span>
          </button>

          {isAdmin && (
            <button
              onClick={handleOpenAdd}
              className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded bg-[#16423C] text-white text-xs font-mono-data font-bold hover:bg-[#1F5C54] shadow-sm transition-colors"
            >
              <Plus className="w-4 h-4 text-[#D99A2B]" />
              <span>ADD SENSOR</span>
            </button>
          )}
        </div>
      </div>

      {/* Sensors Table */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] rounded shadow-industrial overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-mono-data">
            <thead className="bg-[#F0EBE1] text-[#686868] uppercase text-[10px] border-b border-[#E9E2D3]">
              <tr>
                <th className="py-3 px-4">SENSOR ID</th>
                <th className="py-3 px-4">SENSOR NAME</th>
                <th className="py-3 px-4">LOCATION</th>
                <th className="py-3 px-4 text-right">TEMPERATURE</th>
                <th className="py-3 px-4 text-right">HUMIDITY</th>
                <th className="py-3 px-4 text-right">PRESSURE</th>
                <th className="py-3 px-4 text-center">STATUS</th>
                <th className="py-3 px-4 text-center">ANOMALY</th>
                <th className="py-3 px-4 text-center">LAST SEEN</th>
                <th className="py-3 px-4 text-right">ACTIONS</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E9E2D3]">
              {sensors.map((s) => {
                const isOnline = s.status === 'ONLINE' && s.is_enabled;
                const isAnomaly = s.is_anomaly;

                return (
                  <tr key={s.id} className="hover:bg-[#F5F1E8]/70 transition-colors">
                    <td className="py-3.5 px-4 font-bold text-[#16423C]">
                      <Link
                        to={`/sensors/${s.id}`}
                        className="hover:underline flex items-center space-x-1"
                      >
                        <span>{s.device_id}</span>
                        <ExternalLink className="w-3 h-3 text-[#1F5C54] opacity-70" />
                      </Link>
                    </td>
                    <td className="py-3.5 px-4 font-semibold text-[#242424]">{s.name}</td>
                    <td className="py-3.5 px-4 text-[#686868]">
                      <div className="flex items-center space-x-1">
                        <MapPin className="w-3 h-3 text-[#1F5C54]" />
                        <span>{s.location}</span>
                      </div>
                    </td>
                    <td className="py-3.5 px-4 text-right font-bold text-[#C96B32]">
                      {s.temperature !== undefined && s.temperature !== null
                        ? `${s.temperature.toFixed(1)} °C`
                        : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right font-bold text-[#1F5C54]">
                      {s.humidity !== undefined && s.humidity !== null
                        ? `${s.humidity.toFixed(1)} %`
                        : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right font-bold text-[#16423C]">
                      {s.pressure !== undefined && s.pressure !== null
                        ? `${s.pressure.toFixed(1)} hPa`
                        : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-center">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold ${
                          isOnline
                            ? 'bg-[#2E7D32]/15 text-[#2E7D32]'
                            : 'bg-[#6B6B6B]/15 text-[#6B6B6B]'
                        }`}
                      >
                        {isOnline ? '● ONLINE' : '○ OFFLINE'}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-center">
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
                    <td className="py-3.5 px-4 text-center text-[11px] text-[#686868]">
                      {s.last_seen ? s.last_seen.substring(11, 19) : '—'}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <div className="flex items-center justify-end space-x-1.5">
                        <Link
                          to={`/sensors/${s.id}`}
                          title="Detailed Telemetry"
                          className="p-1 rounded bg-[#F0EBE1] text-[#16423C] hover:bg-[#E9E2D3]"
                        >
                          <ExternalLink className="w-3.5 h-3.5" />
                        </Link>

                        {isAdmin && (
                          <>
                            <button
                              onClick={() => handleToggle(s.id)}
                              title={s.is_enabled ? 'Disable Sensor' : 'Enable Sensor'}
                              className={`p-1 rounded transition-colors ${
                                s.is_enabled
                                  ? 'bg-[#2E7D32]/10 text-[#2E7D32] hover:bg-[#2E7D32]/20'
                                  : 'bg-[#6B6B6B]/10 text-[#6B6B6B] hover:bg-[#6B6B6B]/20'
                              }`}
                            >
                              <Power className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleOpenEdit(s)}
                              title="Edit Sensor"
                              className="p-1 rounded bg-[#F0EBE1] text-[#242424] hover:bg-[#E9E2D3]"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>
                            <button
                              onClick={() => handleDelete(s.id, s.device_id)}
                              title="Delete Sensor"
                              className="p-1 rounded bg-[#B23A2F]/10 text-[#B23A2F] hover:bg-[#B23A2F]/20"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Add / Edit Sensor Modal */}
      {modalType && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-[#FFFFFF] border border-[#E9E2D3] rounded max-w-md w-full p-6 shadow-industrial-md font-mono-data">
            <div className="flex items-center justify-between border-b border-[#E9E2D3] pb-3 mb-4">
              <h2 className="text-sm font-bold uppercase text-[#16423C]">
                {modalType === 'ADD' ? 'REGISTER NEW SENSOR' : `EDIT SENSOR: ${formData.device_id}`}
              </h2>
              <button
                onClick={() => setModalType(null)}
                className="text-[#686868] hover:text-[#242424]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {errorMsg && (
              <div className="mb-4 p-2.5 bg-[#B23A2F]/10 border border-[#B23A2F]/30 text-[#B23A2F] text-xs rounded">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleSaveSensor} className="space-y-4 text-xs">
              <div>
                <label className="block text-[11px] font-bold text-[#242424] uppercase mb-1">
                  Device ID
                </label>
                <input
                  type="text"
                  required
                  disabled={modalType === 'EDIT'}
                  value={formData.device_id}
                  onChange={(e) => setFormData({ ...formData, device_id: e.target.value })}
                  placeholder="e.g. SENSOR-006"
                  className="w-full px-3 py-2 border border-[#E9E2D3] rounded bg-[#F5F1E8] text-[#242424] focus:outline-none focus:border-[#16423C]"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#242424] uppercase mb-1">
                  Sensor Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="e.g. Secondary Chiller Unit"
                  className="w-full px-3 py-2 border border-[#E9E2D3] rounded bg-[#F5F1E8] text-[#242424] focus:outline-none focus:border-[#16423C]"
                />
              </div>

              <div>
                <label className="block text-[11px] font-bold text-[#242424] uppercase mb-1">
                  Industrial Location
                </label>
                <select
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="w-full px-3 py-2 border border-[#E9E2D3] rounded bg-[#F5F1E8] text-[#242424] focus:outline-none focus:border-[#16423C]"
                >
                  <option value="Production Floor">Production Floor</option>
                  <option value="Warehouse">Warehouse</option>
                  <option value="Boiler Room">Boiler Room</option>
                  <option value="Assembly Line">Assembly Line</option>
                  <option value="Storage Area">Storage Area</option>
                  <option value="HVAC Plant">HVAC Plant</option>
                </select>
              </div>

              <div className="flex items-center space-x-2 pt-2">
                <input
                  type="checkbox"
                  id="sensor_enabled"
                  checked={formData.is_enabled}
                  onChange={(e) => setFormData({ ...formData, is_enabled: e.target.checked })}
                  className="rounded text-[#16423C] focus:ring-0"
                />
                <label htmlFor="sensor_enabled" className="text-xs font-semibold text-[#242424]">
                  Enable Sensor Data Stream
                </label>
              </div>

              <div className="flex items-center justify-end space-x-3 pt-4 border-t border-[#E9E2D3]">
                <button
                  type="button"
                  onClick={() => setModalType(null)}
                  className="px-4 py-2 border border-[#E9E2D3] rounded text-[#686868] hover:bg-[#F0EBE1]"
                >
                  CANCEL
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded bg-[#16423C] text-white font-bold hover:bg-[#1F5C54]"
                >
                  {modalType === 'ADD' ? 'CREATE SENSOR' : 'SAVE CHANGES'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
