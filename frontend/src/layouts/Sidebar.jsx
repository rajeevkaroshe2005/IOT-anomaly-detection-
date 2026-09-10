import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Cpu,
  Activity,
  AlertTriangle,
  Bell,
  Layers,
  Server,
  ShieldCheck,
  Sliders,
  Radio,
  ChevronRight
} from 'lucide-react';

const NAV_ITEMS = [
  { name: 'Dashboard', path: '/', icon: LayoutDashboard },
  { name: 'Sensors', path: '/sensors', icon: Cpu },
  { name: 'Live Monitoring', path: '/monitoring', icon: Activity },
  { name: 'Anomalies', path: '/anomalies', icon: AlertTriangle },
  { name: 'Alerts', path: '/alerts', icon: Bell },
  { name: 'Architecture', path: '/architecture', icon: Layers },
  { name: 'System Health', path: '/health', icon: Server },
  { name: 'Admin', path: '/admin', icon: ShieldCheck },
  { name: 'Settings', path: '/settings', icon: Sliders },
];

export default function Sidebar({ isOpen, setIsOpen }) {
  return (
    <aside
      className={`fixed inset-y-0 left-0 z-30 w-64 bg-[#16423C] text-[#F5F1E8] border-r border-[#1F5C54] transition-transform duration-200 ease-in-out lg:translate-x-0 ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } flex flex-col justify-between`}
    >
      {/* Brand Header */}
      <div>
        <div className="h-16 flex items-center px-6 border-b border-[#1F5C54] bg-[#0F2F2B]/50">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded bg-[#D99A2B] flex items-center justify-center text-[#16423C] font-bold">
              <Radio className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="font-bold text-sm tracking-wide uppercase text-white font-mono-data">
                IoT TELEMETRY
              </div>
              <div className="text-[10px] text-[#E9E2D3]/70 uppercase tracking-wider">
                Industrial SCADA v1.0
              </div>
            </div>
          </div>
        </div>

        {/* Industrial Mode Badge */}
        <div className="px-4 py-3 border-b border-[#1F5C54]/60 bg-[#16423C]">
          <div className="flex items-center justify-between text-[11px] font-mono-data text-[#E9E2D3]/80">
            <span>PIPELINE:</span>
            <span className="text-[#D99A2B] font-semibold">MQTT + ISOLATION FOREST</span>
          </div>
        </div>

        {/* Navigation Menu */}
        <nav className="p-3 space-y-1 mt-2">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => setIsOpen(false)}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3 py-2.5 rounded text-xs font-medium tracking-wide transition-colors ${
                    isActive
                      ? 'bg-[#1F5C54] text-white font-semibold border-l-4 border-[#D99A2B]'
                      : 'text-[#E9E2D3]/80 hover:bg-[#1F5C54]/40 hover:text-white'
                  }`
                }
              >
                <div className="flex items-center space-x-3">
                  <Icon className="w-4 h-4 text-[#D99A2B]" />
                  <span>{item.name}</span>
                </div>
                <ChevronRight className="w-3.5 h-3.5 opacity-40" />
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Industrial Footer Info */}
      <div className="p-4 border-t border-[#1F5C54] bg-[#0F2F2B]/60 text-[11px] text-[#E9E2D3]/70 font-mono-data">
        <div className="flex items-center justify-between">
          <span>EDGE NODES:</span>
          <span className="text-white font-bold">05 ACTIVE</span>
        </div>
        <div className="flex items-center justify-between mt-1">
          <span>BROKER:</span>
          <span className="text-[#2E7D32] font-semibold">MOSQUITTO :1883</span>
        </div>
      </div>
    </aside>
  );
}
