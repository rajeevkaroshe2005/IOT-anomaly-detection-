import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Radio, Lock, User, ShieldCheck, Eye, EyeOff, CheckCircle2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export default function Login() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();

  const [username, setUsername] = useState('admin');
  const [password, setPassword] = useState('admin123');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    const result = await login(username, password);
    if (result.success) {
      navigate('/');
    } else {
      setErrorMessage(result.error);
    }
  };

  const handleQuickLogin = async (userType) => {
    if (userType === 'admin') {
      setUsername('admin');
      setPassword('admin123');
      const res = await login('admin', 'admin123');
      if (res.success) navigate('/');
    } else {
      setUsername('viewer');
      setPassword('viewer123');
      const res = await login('viewer', 'viewer123');
      if (res.success) navigate('/');
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F1E8] flex flex-col justify-center items-center px-4 font-mono-data">
      <div className="max-w-md w-full bg-[#FFFFFF] border border-[#E9E2D3] rounded shadow-industrial-md p-8 space-y-6">
        {/* Brand Header */}
        <div className="text-center space-y-2">
          <div className="w-12 h-12 rounded bg-[#16423C] text-[#D99A2B] flex items-center justify-center mx-auto shadow-sm">
            <Radio className="w-6 h-6 animate-pulse" />
          </div>
          <h1 className="text-lg font-bold text-[#16423C] uppercase tracking-wider">
            Industrial SCADA Gateway
          </h1>
          <p className="text-xs text-[#686868]">
            Cloud-Based IoT Sensor Monitoring & Anomaly Detection System
          </p>
        </div>

        {/* Demo Roles Quick Pick Banner */}
        <div className="p-3 bg-[#F0EBE1] rounded border border-[#E9E2D3] text-xs space-y-2">
          <div className="text-[10px] uppercase font-bold text-[#16423C] tracking-wider">
            One-Click Evaluator Credentials:
          </div>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => handleQuickLogin('admin')}
              className="px-2.5 py-1.5 rounded bg-[#16423C] text-white font-bold text-[11px] hover:bg-[#1F5C54] transition-colors"
            >
              ADMIN (admin / admin123)
            </button>
            <button
              type="button"
              onClick={() => handleQuickLogin('viewer')}
              className="px-2.5 py-1.5 rounded bg-[#1F5C54] text-white font-bold text-[11px] hover:bg-[#16423C] transition-colors"
            >
              VIEWER (viewer / viewer123)
            </button>
          </div>
        </div>

        {errorMessage && (
          <div className="p-3 rounded bg-[#B23A2F]/10 border border-[#B23A2F]/30 text-[#B23A2F] text-xs">
            {errorMessage}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-4 text-xs">
          <div>
            <label className="block uppercase text-[11px] font-bold text-[#242424] mb-1">
              Operator Username
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-[#686868] absolute left-3 top-2.5" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="admin"
                className="w-full pl-9 pr-3 py-2 border border-[#E9E2D3] rounded bg-[#F5F1E8] text-[#242424] focus:outline-none focus:border-[#16423C]"
              />
            </div>
          </div>

          <div>
            <label className="block uppercase text-[11px] font-bold text-[#242424] mb-1">
              Access Password
            </label>
            <div className="relative">
              <Lock className="w-4 h-4 text-[#686868] absolute left-3 top-2.5" />
              <input
                type={showPassword ? 'text' : 'password'}
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-9 pr-10 py-2 border border-[#E9E2D3] rounded bg-[#F5F1E8] text-[#242424] focus:outline-none focus:border-[#16423C]"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-2.5 text-[#686868] hover:text-[#242424]"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-2.5 rounded bg-[#16423C] text-white font-bold text-xs uppercase tracking-wider hover:bg-[#1F5C54] transition-colors shadow-sm disabled:opacity-50"
          >
            {loading ? 'Authenticating...' : 'Authenticate & Enter Gateway'}
          </button>
        </form>

        <div className="text-[11px] text-[#686868] text-center pt-2 border-t border-[#E9E2D3]">
          Role-Based Access Control • PBKDF2 Password Hashing • Stateless JWT Token
        </div>
      </div>
    </div>
  );
}
