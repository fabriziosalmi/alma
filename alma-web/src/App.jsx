import React from 'react';
import ChatInterface from './components/ChatInterface';
import BlueprintVisualizer from './components/BlueprintVisualizer';
import { Activity, Cpu, HardDrive, Shield } from 'lucide-react';

function App() {
  return (
    <div className="min-h-screen bg-slate-950 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black text-slate-200 p-4 md:p-8 font-sans selection:bg-cyan-500/30">

      {/* Background Glows */}
      <div className="fixed top-0 left-1/4 w-96 h-96 bg-purple-600/20 rounded-full blur-[128px] pointer-events-none" />
      <div className="fixed bottom-0 right-1/4 w-96 h-96 bg-cyan-600/10 rounded-full blur-[128px] pointer-events-none" />

      <div className="max-w-7xl mx-auto h-[calc(100vh-4rem)] flex flex-col gap-6">

        {/* Header */}
        <header className="flex justify-between items-center bg-slate-900/40 backdrop-blur-md p-4 rounded-2xl border border-slate-800/50">
          <div className="flex items-center gap-4">
            <h1 className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-purple-500 bg-clip-text text-transparent">
              ALMA
            </h1>
            <span className="px-2 py-0.5 bg-slate-800 text-slate-400 text-xs rounded-full border border-slate-700">
              BETA
            </span>
          </div>

          <div className="flex items-center gap-6">
            {/* Minimal Status Metrics */}
            <div className="flex items-center gap-6 text-xs font-medium text-slate-400 border-r border-slate-700 pr-6 mr-2">
              <div className="flex items-center gap-2 hover:text-emerald-400 transition-colors cursor-help" title="CPU Usage">
                <Cpu size={14} className="text-emerald-500" />
                <span>24%</span>
              </div>
              <div className="flex items-center gap-2 hover:text-blue-400 transition-colors cursor-help" title="Memory Usage">
                <HardDrive size={14} className="text-blue-500" />
                <span>4.2 GB</span>
              </div>
              <div className="flex items-center gap-2 hover:text-purple-400 transition-colors cursor-help" title="System Latency">
                <Activity size={14} className="text-purple-500" />
                <span>45ms</span>
              </div>
              <div className="flex items-center gap-2 hover:text-cyan-400 transition-colors cursor-help" title="Active Threats">
                <Shield size={14} className="text-cyan-500" />
                <span>0 Active</span>
              </div>
            </div>

            <div className="text-sm text-slate-400 flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Connected to <span className="text-emerald-400 font-semibold">Local Brain</span>
            </div>
          </div>
        </header>

        {/* Main Grid */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">

          {/* Left Column: Chat (4 cols) */}
          <div className="lg:col-span-4 flex flex-col h-full min-h-0">
            <ChatInterface />
          </div>

          {/* Right Column: Visualization (8 cols) */}
          <div className="lg:col-span-8 h-full min-h-0">
            <BlueprintVisualizer />
          </div>

        </div>
      </div>
    </div>
  );
}

export default App;
