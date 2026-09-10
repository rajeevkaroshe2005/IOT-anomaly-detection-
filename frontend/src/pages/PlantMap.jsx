import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Map,
  Cpu,
  AlertTriangle,
  CheckCircle2,
  Thermometer,
  Droplets,
  Gauge,
  Radio,
  RefreshCw,
  ExternalLink,
  Flame,
  Snowflake,
  Factory,
  Boxes,
  X
} from 'lucide-react';
import { sensorsAPI } from '../services/api';
import { useWebSocket } from '../context/WebSocketContext';

// Spatial layout metadata for the 5 industrial plant zones
const PLANT_ZONES = [
  {
    device_id: 'SENSOR-001',
    zoneName: 'Main Production Floor',
    code: 'ZONE-A',
    icon: Factory,
    type: 'Machining & Fabrication',
    gridArea: 'col-span-12 lg:col-span-8 row-span-2',
    description: 'High-speed automated CNC milling and robotic workcells.'
  },
  {
    device_id: 'SENSOR-002',
    zoneName: 'Cold Storage Warehouse',
    code: 'ZONE-B',
    icon: Snowflake,
    type: 'Refrigerated Storage',
    gridArea: 'col-span-12 sm:col-span-6 lg:col-span-4 row-span-1',
    description: 'Sub-ambient cooling for raw materials and sensitive components.'
  },
  {
    device_id: 'SENSOR-003',
    zoneName: 'Steam Boiler Reactor Room',
    code: 'ZONE-C',
    icon: Flame,
    type: 'High-Thermal Utility',
    gridArea: 'col-span-12 sm:col-span-6 lg:col-span-4 row-span-1',
    description: 'Pressurized steam boilers and continuous thermal exchangers.'
  },
  {
    device_id: 'SENSOR-004',
    zoneName: 'Packaging & Conveyor Line B',
    code: 'ZONE-D',
    icon: Boxes,
    type: 'Logistics Conveyance',
    gridArea: 'col-span-12 sm:col-span-6 lg:col-span-6 row-span-1',
    description: 'High-throughput sorting, optical inspection, and boxing conveyors.'
  },
  {
    device_id: 'SENSOR-005',
    zoneName: 'Raw Chemical Silo Storage',
    code: 'ZONE-E',
    icon: Radio,
    type: 'Pressurized Vessel',
    gridArea: 'col-span-12 sm:col-span-6 lg:col-span-6 row-span-1',
    description: 'Nitrogen-purged atmospheric storage vessels for reactant fluids.'
  }
];

export default function PlantMap() {
  const { addListener } = useWebSocket();

  const [sensors, setSensors] = useState([]);
  const [selectedSensor, setSelectedSensor] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchSensors = async () => {
    try {
      const res = await sensorsAPI.getAll();
      setSensors(res.data);
    } catch (e) {
      console.error('Failed to load sensors for plant map:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSensors();
  }, []);

  // Listen to live WebSocket stream to update rooms instantaneously
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

  const getSensorData = (deviceId) => {
    return sensors.find((s) => s.device_id === deviceId);
  };

  return (
    <div className="space-y-6 font-mono-data">
      {/* Top Header */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Map className="w-5 h-5 text-[#16423C]" />
            <h1 className="text-xl font-bold uppercase tracking-wider text-[#242424]">
              2D Digital Twin • Industrial Facility Spatial Map
            </h1>
          </div>
          <p className="text-xs text-[#686868] mt-1">
            Real-time physical facility telemetry overlay. Click any room to inspect node diagnostics and isolation scores.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchSensors}
            className="flex items-center space-x-1 px-3 py-1.5 rounded bg-[#F0EBE1] border border-[#E9E2D3] text-xs text-[#242424] hover:bg-[#E9E2D3]"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
            <span>SYNC MAP</span>
          </button>
        </div>
      </div>

      {/* Map Legend Banner */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] px-5 py-3 rounded shadow-industrial flex flex-wrap items-center justify-between text-xs text-[#686868] gap-4">
        <div className="flex items-center space-x-6 text-[11px]">
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-[#2E7D32]" />
            <span className="font-semibold text-[#242424]">Nominal Safe Zone</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-[#B23A2F] animate-ping" />
            <span className="font-bold text-[#B23A2F]">Emergency Anomaly Hazard</span>
          </div>
          <div className="flex items-center space-x-2">
            <span className="w-3 h-3 rounded-full bg-[#6B6B6B]" />
            <span>Standby Node</span>
          </div>
        </div>

        <div className="text-[11px] text-[#1F5C54] font-semibold">
          TOTAL MONITORED AREA: 48,000 SQ. FT.
        </div>
      </div>

      {/* Interactive 2D Plant Floor Plan Grid */}
      <div className="grid grid-cols-12 gap-4">
        {PLANT_ZONES.map((zone) => {
          const s = getSensorData(zone.device_id);
          const isAnomaly = s?.is_anomaly;
          const ZoneIcon = zone.icon;

          return (
            <div
              key={zone.device_id}
              onClick={() => s && setSelectedSensor({ ...s, zone })}
              className={`${zone.gridArea} border rounded p-5 cursor-pointer transition-all relative overflow-hidden flex flex-col justify-between min-h-[170px] ${
                isAnomaly
                  ? 'bg-[#B23A2F]/10 border-[#B23A2F] ring-2 ring-[#B23A2F] shadow-md animate-pulse'
                  : 'bg-[#FFFFFF] border-[#E9E2D3] hover:border-[#16423C] hover:shadow-industrial'
              }`}
            >
              {/* Emergency Hazard Corner Badge */}
              {isAnomaly && (
                <div className="absolute top-0 right-0 bg-[#B23A2F] text-white px-3 py-1 text-[10px] font-bold tracking-wider uppercase rounded-bl flex items-center space-x-1">
                  <AlertTriangle className="w-3 h-3 animate-bounce" />
                  <span>EMERGENCY HAZARD (Score: {s.anomaly_score?.toFixed(2)})</span>
                </div>
              )}

              {/* Room Header */}
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <div
                      className={`p-2 rounded ${
                        isAnomaly ? 'bg-[#B23A2F] text-white' : 'bg-[#16423C] text-[#D99A2B]'
                      }`}
                    >
                      <ZoneIcon className="w-4 h-4" />
                    </div>
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-xs text-[#242424]">{zone.zoneName}</span>
                        <span className="text-[10px] text-[#686868]">[{zone.code}]</span>
                      </div>
                      <div className="text-[10px] text-[#1F5C54] font-semibold">{zone.type}</div>
                    </div>
                  </div>

                  {!isAnomaly && (
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#2E7D32]/15 text-[#2E7D32]">
                      ● SAFE
                    </span>
                  )}
                </div>

                <p className="text-[11px] text-[#686868] mt-3">{zone.description}</p>
              </div>

              {/* Live Room Gauges */}
              <div className="mt-4 pt-3 border-t border-[#E9E2D3] grid grid-cols-3 gap-2">
                <div className="p-2 bg-[#F5F1E8] rounded border border-[#E9E2D3]">
                  <div className="text-[9px] text-[#686868] flex items-center space-x-1">
                    <Thermometer className="w-3 h-3 text-[#C96B32]" />
                    <span>TEMP</span>
                  </div>
                  <div className="text-xs font-bold text-[#C96B32] mt-0.5">
                    {s?.temperature != null ? `${Number(s.temperature).toFixed(1)} °C` : '—'}
                  </div>
                </div>

                <div className="p-2 bg-[#F5F1E8] rounded border border-[#E9E2D3]">
                  <div className="text-[9px] text-[#686868] flex items-center space-x-1">
                    <Droplets className="w-3 h-3 text-[#1F5C54]" />
                    <span>HUMIDITY</span>
                  </div>
                  <div className="text-xs font-bold text-[#1F5C54] mt-0.5">
                    {s?.humidity != null ? `${Number(s.humidity).toFixed(1)} %` : '—'}
                  </div>
                </div>

                <div className="p-2 bg-[#F5F1E8] rounded border border-[#E9E2D3]">
                  <div className="text-[9px] text-[#686868] flex items-center space-x-1">
                    <Gauge className="w-3 h-3 text-[#16423C]" />
                    <span>PRESSURE</span>
                  </div>
                  <div className="text-xs font-bold text-[#16423C] mt-0.5">
                    {s?.pressure != null ? `${Number(s.pressure).toFixed(1)} hPa` : '—'}
                  </div>
                </div>
              </div>

              {/* Device ID Marker */}
              <div className="mt-2 flex items-center justify-between text-[10px] text-[#686868]">
                <span>SENSOR: <strong className="text-[#16423C]">{zone.device_id}</strong></span>
                <span className="text-[#1F5C54] hover:underline font-semibold">Click to Inspect →</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Room Inspector Telemetry Modal */}
      {selectedSensor && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4 backdrop-blur-xs">
          <div className="bg-[#FFFFFF] border border-[#E9E2D3] rounded max-w-lg w-full p-6 shadow-industrial-md font-mono-data space-y-4">
            <div className="flex items-center justify-between border-b border-[#E9E2D3] pb-3">
              <div>
                <h2 className="text-sm font-bold text-[#16423C] uppercase">
                  Spatial Inspector: {selectedSensor.device_id}
                </h2>
                <div className="text-[11px] text-[#686868]">
                  {selectedSensor.name} • {selectedSensor.location}
                </div>
              </div>
              <button
                onClick={() => setSelectedSensor(null)}
                className="text-[#686868] hover:text-[#242424]"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Current Status */}
            <div
              className={`p-3 rounded border text-xs flex items-center justify-between ${
                selectedSensor.is_anomaly
                  ? 'bg-[#B23A2F]/10 border-[#B23A2F]/30 text-[#B23A2F] font-bold'
                  : 'bg-[#2E7D32]/10 border-[#2E7D32]/30 text-[#2E7D32] font-semibold'
              }`}
            >
              <div className="flex items-center space-x-2">
                {selectedSensor.is_anomaly ? (
                  <AlertTriangle className="w-4 h-4" />
                ) : (
                  <CheckCircle2 className="w-4 h-4" />
                )}
                <span>
                  {selectedSensor.is_anomaly
                    ? `CRITICAL ANOMALY: Score ${selectedSensor.anomaly_score?.toFixed(4)}`
                    : 'NOMINAL INDUSTRIAL EQUILIBRIUM'}
                </span>
              </div>
              <span>{selectedSensor.status}</span>
            </div>

            {/* Live Metrics Grid */}
            <div className="grid grid-cols-3 gap-3">
              <div className="p-3 rounded bg-[#F5F1E8] border border-[#E9E2D3]">
                <div className="text-[10px] text-[#686868] uppercase">Temperature</div>
                <div className="text-lg font-bold text-[#C96B32] mt-1">
                  {selectedSensor.temperature != null ? `${Number(selectedSensor.temperature).toFixed(1)} °C` : '—'}
                </div>
              </div>
              <div className="p-3 rounded bg-[#F5F1E8] border border-[#E9E2D3]">
                <div className="text-[10px] text-[#686868] uppercase">Humidity</div>
                <div className="text-lg font-bold text-[#1F5C54] mt-1">
                  {selectedSensor.humidity != null ? `${Number(selectedSensor.humidity).toFixed(1)} %` : '—'}
                </div>
              </div>
              <div className="p-3 rounded bg-[#F5F1E8] border border-[#E9E2D3]">
                <div className="text-[10px] text-[#686868] uppercase">Pressure</div>
                <div className="text-lg font-bold text-[#16423C] mt-1">
                  {selectedSensor.pressure != null ? `${Number(selectedSensor.pressure).toFixed(1)} hPa` : '—'}
                </div>
              </div>
            </div>

            <div className="pt-3 border-t border-[#E9E2D3] flex items-center justify-between">
              <span className="text-[11px] text-[#686868]">
                Last packet: {selectedSensor.last_seen ? selectedSensor.last_seen.substring(11, 19) : '—'}
              </span>
              <Link
                to={`/sensors/${selectedSensor.id}`}
                className="px-3 py-1.5 rounded bg-[#16423C] text-white text-xs font-bold hover:bg-[#1F5C54] flex items-center space-x-1"
              >
                <span>OPEN FULL TELEMETRY</span>
                <ExternalLink className="w-3 h-3" />
              </Link>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
