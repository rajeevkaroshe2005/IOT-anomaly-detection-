import React from 'react';
import { AlertOctagon, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[ErrorBoundary caught error]:', error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    localStorage.removeItem('iot_audio_enabled');
    this.setState({ hasError: false, error: null, errorInfo: null });
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#F5F1E8] flex items-center justify-center p-6 font-mono-data">
          <div className="max-w-xl w-full bg-white border-2 border-[#B23A2F] rounded shadow-2xl p-6 text-[#242424]">
            <div className="flex items-center space-x-3 border-b border-[#E9E2D3] pb-4">
              <div className="p-3 bg-[#B23A2F]/15 rounded text-[#B23A2F]">
                <AlertOctagon className="w-8 h-8" />
              </div>
              <div>
                <h1 className="text-lg font-bold uppercase text-[#B23A2F]">
                  SCADA Telemetry View Diagnostic Fault
                </h1>
                <p className="text-xs text-[#686868]">
                  An unexpected render exception was trapped by the SCADA runtime guard.
                </p>
              </div>
            </div>

            <div className="mt-4 p-3 bg-[#F0EBE1] rounded border border-[#E9E2D3] text-xs space-y-1">
              <div className="font-bold text-[#B23A2F]">
                {this.state.error?.toString() || 'Unknown Runtime Exception'}
              </div>
              {this.state.errorInfo?.componentStack && (
                <pre className="text-[10px] text-[#686868] overflow-x-auto max-h-32 mt-2 whitespace-pre-wrap">
                  {this.state.errorInfo.componentStack}
                </pre>
              )}
            </div>

            <div className="mt-6 flex items-center justify-end space-x-3">
              <button
                onClick={this.handleReload}
                className="px-4 py-2 rounded bg-[#F0EBE1] border border-[#E9E2D3] text-xs font-bold hover:bg-[#E9E2D3] flex items-center space-x-2"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>RELOAD CLIENT</span>
              </button>
              <button
                onClick={this.handleReset}
                className="px-4 py-2 rounded bg-[#16423C] text-white text-xs font-bold hover:bg-[#1F5C54]"
              >
                RECOVER DASHBOARD
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
