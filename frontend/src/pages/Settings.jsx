import React, { useState } from 'react';
import {
  Sliders,
  User,
  Shield,
  Radio,
  Brain,
  Database,
  Save,
  CheckCircle2
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
  const { user, isAdmin } = useAuth();
  const [saved, setSaved] = useState(false);

  const [thresholds, setThresholds] = useState({
    tempMin: 20.0,
    tempMax: 40.0,
    humMin: 30.0,
    humMax: 80.0,
    pressMin: 990.0,
    pressMax: 1030.0,
  });

  const handleSave = (e) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 font-mono-data">
      {/* Top Header */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial flex items-center justify-between">
        <div>
          <div className="flex items-center space-x-2">
            <Sliders className="w-5 h-5 text-[#16423C]" />
            <h1 className="text-xl font-bold uppercase tracking-wider text-[#242424]">
              System Configuration & Environmental Thresholds
            </h1>
          </div>
          <p className="text-xs text-[#686868] mt-1">
            Configure telemetry safety parameters, ML contamination rates, and review active credentials.
          </p>
        </div>
      </div>

      {saved && (
        <div className="p-3 bg-[#2E7D32]/10 border border-[#2E7D32]/30 text-[#2E7D32] text-xs rounded flex items-center space-x-2">
          <CheckCircle2 className="w-4 h-4" />
          <span>Operational parameters updated successfully.</span>
        </div>
      )}

      {/* Grid of Settings */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Identity & RBAC */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial space-y-4">
          <div className="flex items-center space-x-2 border-b border-[#E9E2D3] pb-2 text-xs font-bold text-[#16423C] uppercase">
            <User className="w-4 h-4" />
            <span>Active Session & RBAC Claims</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1 border-b border-[#F0EBE1]">
              <span className="text-[#686868]">Current Username:</span>
              <span className="font-bold text-[#242424]">{user?.username || 'admin'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F0EBE1]">
              <span className="text-[#686868]">Assigned Role:</span>
              <span className="font-bold text-[#D99A2B]">{user?.role || 'ADMIN'}</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F0EBE1]">
              <span className="text-[#686868]">Authentication Mode:</span>
              <span className="font-semibold text-[#1F5C54]">JWT Bearer Token (HS256)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F0EBE1]">
              <span className="text-[#686868]">Privilege Level:</span>
              <span className="font-semibold text-[#242424]">
                {isAdmin ? 'Full Administrative Control' : 'Read-Only Telemetry Viewer'}
              </span>
            </div>
          </div>
        </div>

        {/* MQTT Broker Configuration Info */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial space-y-4">
          <div className="flex items-center space-x-2 border-b border-[#E9E2D3] pb-2 text-xs font-bold text-[#16423C] uppercase">
            <Radio className="w-4 h-4" />
            <span>Message Broker Ingestion Config</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1 border-b border-[#F0EBE1]">
              <span className="text-[#686868]">MQTT Broker Host:</span>
              <span className="font-bold text-[#16423C]">localhost</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F0EBE1]">
              <span className="text-[#686868]">Standard Port:</span>
              <span className="font-bold text-[#242424]">1883 (TCP)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F0EBE1]">
              <span className="text-[#686868]">Topic Wildcard:</span>
              <span className="font-bold text-[#1F5C54]">iot/sensors/+</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F0EBE1]">
              <span className="text-[#686868]">Quality of Service (QoS):</span>
              <span className="font-bold text-[#242424]">Level 1 (At least once)</span>
            </div>
          </div>
        </div>

        {/* ML Hyperparameter Parameters */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial space-y-4">
          <div className="flex items-center space-x-2 border-b border-[#E9E2D3] pb-2 text-xs font-bold text-[#16423C] uppercase">
            <Brain className="w-4 h-4" />
            <span>Machine Learning Model Parameters</span>
          </div>

          <div className="space-y-3 text-xs">
            <div className="flex justify-between py-1 border-b border-[#F0EBE1]">
              <span className="text-[#686868]">Algorithm:</span>
              <span className="font-bold text-[#16423C]">Scikit-Learn Isolation Forest</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F0EBE1]">
              <span className="text-[#686868]">Contamination Factor:</span>
              <span className="font-bold text-[#B23A2F]">0.05 (5% Expected Outliers)</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F0EBE1]">
              <span className="text-[#686868]">Ensemble Estimators:</span>
              <span className="font-bold text-[#242424]">150 Isolation Trees</span>
            </div>
            <div className="flex justify-between py-1 border-b border-[#F0EBE1]">
              <span className="text-[#686868]">Random State Seed:</span>
              <span className="font-bold text-[#242424]">42 (Deterministic Reproducibility)</span>
            </div>
          </div>
        </div>

        {/* Environmental Bounds Form */}
        <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial space-y-4">
          <div className="flex items-center space-x-2 border-b border-[#E9E2D3] pb-2 text-xs font-bold text-[#16423C] uppercase">
            <Sliders className="w-4 h-4" />
            <span>Industrial Boundary Calibration</span>
          </div>

          <form onSubmit={handleSave} className="space-y-3 text-xs">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] text-[#686868] uppercase font-bold mb-1">
                  Temp Min (°C)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholds.tempMin}
                  onChange={(e) => setThresholds({ ...thresholds, tempMin: parseFloat(e.target.value) })}
                  className="w-full px-2.5 py-1.5 border border-[#E9E2D3] rounded bg-[#F5F1E8]"
                />
              </div>
              <div>
                <label className="block text-[10px] text-[#686868] uppercase font-bold mb-1">
                  Temp Max (°C)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholds.tempMax}
                  onChange={(e) => setThresholds({ ...thresholds, tempMax: parseFloat(e.target.value) })}
                  className="w-full px-2.5 py-1.5 border border-[#E9E2D3] rounded bg-[#F5F1E8]"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-[10px] text-[#686868] uppercase font-bold mb-1">
                  Humidity Min (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholds.humMin}
                  onChange={(e) => setThresholds({ ...thresholds, humMin: parseFloat(e.target.value) })}
                  className="w-full px-2.5 py-1.5 border border-[#E9E2D3] rounded bg-[#F5F1E8]"
                />
              </div>
              <div>
                <label className="block text-[10px] text-[#686868] uppercase font-bold mb-1">
                  Humidity Max (%)
                </label>
                <input
                  type="number"
                  step="0.1"
                  value={thresholds.humMax}
                  onChange={(e) => setThresholds({ ...thresholds, humMax: parseFloat(e.target.value) })}
                  className="w-full px-2.5 py-1.5 border border-[#E9E2D3] rounded bg-[#F5F1E8]"
                />
              </div>
            </div>

            <div className="pt-2 flex justify-end">
              <button
                type="submit"
                className="flex items-center space-x-1.5 px-3 py-1.5 rounded bg-[#16423C] text-white text-xs font-bold hover:bg-[#1F5C54]"
              >
                <Save className="w-3.5 h-3.5 text-[#D99A2B]" />
                <span>SAVE THRESHOLDS</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
