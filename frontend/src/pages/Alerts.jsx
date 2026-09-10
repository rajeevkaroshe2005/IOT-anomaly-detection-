import React, { useState, useEffect } from 'react';
import {
  Bell,
  RefreshCw,
  CheckCircle2,
  Trash2,
  Filter,
  AlertCircle,
  Clock,
  Cpu
} from 'lucide-react';
import { alertsAPI } from '../services/api';
import { useWebSocket } from '../context/WebSocketContext';
import { useAuth } from '../context/AuthContext';

export default function Alerts() {
  const { addListener } = useWebSocket();
  const { isAdmin } = useAuth();

  const [alerts, setAlerts] = useState([]);
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchAlerts = async () => {
    try {
      const params = {};
      if (statusFilter) params.status = statusFilter;
      if (severityFilter) params.severity = severityFilter;

      const res = await alertsAPI.getAll(params);
      setAlerts(res.data);
    } catch (err) {
      console.error('Failed to load alerts:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [statusFilter, severityFilter]);

  // Live WebSocket update for alerts
  useEffect(() => {
    const removeListener = addListener((eventType, data) => {
      if (eventType === 'ALERT_GENERATED') {
        setAlerts((prev) => [data, ...prev]);
      } else if (eventType === 'ALERT_RESOLVED') {
        setAlerts((prev) =>
          prev.map((al) => (al.id === data.id ? { ...al, status: 'RESOLVED', resolved_at: data.resolved_at } : al))
        );
      }
    });
    return removeListener;
  }, [addListener]);

  const handleResolve = async (id) => {
    try {
      await alertsAPI.resolve(id);
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, status: 'RESOLVED' } : a))
      );
    } catch (err) {
      console.error('Failed to resolve alert:', err);
    }
  };

  const handleDelete = async (id) => {
    if (window.confirm('Confirm deletion of this alert record?')) {
      try {
        await alertsAPI.delete(id);
        setAlerts((prev) => prev.filter((a) => a.id !== id));
      } catch (err) {
        console.error('Failed to delete alert:', err);
      }
    }
  };

  return (
    <div className="space-y-6 font-mono-data">
      {/* Header */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] p-5 rounded shadow-industrial flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Bell className="w-5 h-5 text-[#B23A2F]" />
            <h1 className="text-xl font-bold uppercase tracking-wider text-[#242424]">
              Industrial Operational Alerts Console
            </h1>
          </div>
          <p className="text-xs text-[#686868] mt-1">
            Automated alerts dispatched when environmental metrics breach isolation thresholds or safe operational boundaries.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={fetchAlerts}
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

        <div className="flex items-center space-x-2 bg-[#F5F1E8] px-3 py-1.5 rounded border border-[#E9E2D3]">
          <span className="text-[10px] text-[#686868] uppercase font-bold">Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-transparent text-xs text-[#242424] focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="ACTIVE">Active Only</option>
            <option value="RESOLVED">Resolved Only</option>
          </select>
        </div>

        <div className="flex items-center space-x-2 bg-[#F5F1E8] px-3 py-1.5 rounded border border-[#E9E2D3]">
          <span className="text-[10px] text-[#686868] uppercase font-bold">Severity:</span>
          <select
            value={severityFilter}
            onChange={(e) => setSeverityFilter(e.target.value)}
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
          TOTAL ALERTS: <span className="font-bold text-[#16423C]">{alerts.length}</span>
        </div>
      </div>

      {/* Alerts Table (Prompt Requirement 8) */}
      <div className="bg-[#FFFFFF] border border-[#E9E2D3] rounded shadow-industrial overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#F0EBE1] text-[#686868] uppercase text-[10px] border-b border-[#E9E2D3]">
              <tr>
                <th className="py-3 px-4">ALERT ID</th>
                <th className="py-3 px-4">SENSOR ID</th>
                <th className="py-3 px-4">LOCATION</th>
                <th className="py-3 px-4">ALERT TYPE</th>
                <th className="py-3 px-4 text-center">SEVERITY</th>
                <th className="py-3 px-4">INCIDENT MESSAGE</th>
                <th className="py-3 px-4 text-center">STATUS</th>
                <th className="py-3 px-4">TIMESTAMP</th>
                {isAdmin && <th className="py-3 px-4 text-right">ADMIN ACTIONS</th>}
              </tr>
            </thead>
            <tbody className="divide-y divide-[#E9E2D3]">
              {alerts.length > 0 ? (
                alerts.map((al) => {
                  const isActive = al.status === 'ACTIVE';
                  return (
                    <tr
                      key={al.id}
                      className={`hover:bg-[#F5F1E8]/70 transition-colors ${
                        isActive ? 'bg-[#B23A2F]/5' : ''
                      }`}
                    >
                      <td className="py-3 px-4 font-bold text-[#686868]">
                        #{String(al.id).padStart(4, '0')}
                      </td>
                      <td className="py-3 px-4 font-bold text-[#16423C]">{al.device_id}</td>
                      <td className="py-3 px-4 text-[#686868]">{al.location || 'Facility Edge'}</td>
                      <td className="py-3 px-4 font-semibold text-[#242424]">{al.type}</td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                            al.severity === 'CRITICAL'
                              ? 'bg-[#B23A2F] text-white'
                              : al.severity === 'HIGH'
                              ? 'bg-[#D99A2B] text-white'
                              : al.severity === 'MEDIUM'
                              ? 'bg-[#1F5C54] text-white'
                              : 'bg-[#6B6B6B] text-white'
                          }`}
                        >
                          {al.severity}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-[11px] text-[#242424] max-w-sm leading-relaxed">
                        {al.message}
                      </td>
                      <td className="py-3 px-4 text-center">
                        <span
                          className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                            isActive
                              ? 'bg-[#B23A2F]/15 text-[#B23A2F]'
                              : 'bg-[#2E7D32]/15 text-[#2E7D32]'
                          }`}
                        >
                          {isActive ? '● ACTIVE' : '✓ RESOLVED'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-[11px] text-[#686868]">
                        {al.created_at?.replace('T', ' ').substring(0, 19)}
                      </td>
                      {isAdmin && (
                        <td className="py-3 px-4 text-right">
                          <div className="flex items-center justify-end space-x-2">
                            {isActive ? (
                              <button
                                onClick={() => handleResolve(al.id)}
                                className="px-2.5 py-1 rounded bg-[#2E7D32] text-white text-[10px] font-bold hover:bg-[#256327] transition-colors"
                              >
                                RESOLVE
                              </button>
                            ) : (
                              <span className="text-[10px] text-[#2E7D32] font-semibold">
                                Closed
                              </span>
                            )}
                            <button
                              onClick={() => handleDelete(al.id)}
                              className="p-1 rounded bg-[#F0EBE1] text-[#B23A2F] hover:bg-[#B23A2F]/20 transition-colors"
                              title="Delete Alert Record"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        </td>
                      )}
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={isAdmin ? 9 : 8} className="py-12 text-center text-xs text-[#686868]">
                    No alert records match the selected filter.
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
