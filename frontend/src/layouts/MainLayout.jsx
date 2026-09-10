import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';
import { useWebSocket } from '../context/WebSocketContext';
import { AlertCircle, X } from 'lucide-react';

export default function MainLayout() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const { notification, clearNotification } = useWebSocket();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-[#F5F1E8] text-[#242424] flex">
      {/* Sidebar */}
      <Sidebar isOpen={isSidebarOpen} setIsOpen={setIsSidebarOpen} />

      {/* Backdrop for mobile */}
      {isSidebarOpen && (
        <div
          onClick={() => setIsSidebarOpen(false)}
          className="fixed inset-0 bg-black/40 z-20 lg:hidden backdrop-blur-xs"
        />
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 lg:pl-64">
        <Header setIsSidebarOpen={setIsSidebarOpen} />

        {/* Global Urgent Anomaly Toast Notification */}
        {notification && (
          <div className="bg-[#B23A2F] text-white px-4 py-2.5 shadow-md flex items-center justify-between font-mono-data text-xs border-b border-[#8B231B] animate-pulse">
            <div className="flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 text-white" />
              <span className="font-bold uppercase tracking-wider">{notification.title}:</span>
              <span>{notification.message}</span>
              <span className="text-[10px] opacity-80">[{notification.timestamp}]</span>
            </div>
            <button
              onClick={clearNotification}
              className="p-1 hover:bg-black/20 rounded transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        )}

        {/* Page Viewport */}
        <main className="flex-1 p-4 lg:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
