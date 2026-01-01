'use client';
import { Server, Database, Activity, AlertTriangle, CheckCircle2, Clock } from 'lucide-react';

export default function AdminDashboard() {
  return (
    <div>
      {/* Page Header */}
      <header className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">System Overview</h1>
        <p className="text-slate-500">Real-time monitoring of TeaCare infrastructure.</p>
      </header>

      {/* Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatusCard 
          title="FastAPI Backend" 
          status="online" 
          ping="45ms" 
          icon={Server} 
        />
        <StatusCard 
          title="PostgreSQL Database" 
          status="online" 
          ping="12ms" 
          icon={Database} 
        />
        <StatusCard 
          title="AI Inference Engine" 
          status="degraded" 
          ping="820ms" 
          icon={Activity} 
          details="High Latency on Qwen-0.5B"
        />
      </div>

      {/* Recent Alerts Section */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50 flex justify-between items-center">
          <h3 className="font-semibold text-slate-800">System Logs & Alerts</h3>
          <span className="text-xs font-medium bg-slate-200 text-slate-600 px-2 py-1 rounded">Last 24 Hours</span>
        </div>
        
        <div className="divide-y divide-slate-100">
          <LogItem 
            type="error" 
            message="Connection Timeout: Open-Meteo API failed to respond." 
            time="10:42 AM" 
          />
          <LogItem 
            type="warning" 
            message="High Memory Usage: Vector DB index rebuild took 4s." 
            time="09:15 AM" 
          />
          <LogItem 
            type="success" 
            message="System Backup: Daily snapshot completed successfully." 
            time="04:00 AM" 
          />
        </div>
      </div>
    </div>
  );
}

// --- Local Components (Keep code clean) ---

function StatusCard({ title, status, ping, icon: Icon, details }: any) {
  const isOnline = status === 'online';
  
  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className={`p-3 rounded-xl ${isOnline ? 'bg-green-100 text-green-600' : 'bg-amber-100 text-amber-600'}`}>
          <Icon size={24} />
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-bold uppercase ${isOnline ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'}`}>
          {status}
        </span>
      </div>
      
      <h3 className="font-bold text-slate-800 text-lg">{title}</h3>
      
      <div className="flex items-center gap-2 mt-2 text-sm text-slate-500">
        <Activity size={14} />
        <span>Latency: {ping}</span>
      </div>

      {details && (
        <div className="mt-4 pt-4 border-t border-slate-100 text-xs text-amber-600 font-medium flex items-center gap-2">
          <AlertTriangle size={12} />
          {details}
        </div>
      )}
    </div>
  );
}

function LogItem({ type, message, time }: any) {
  const colors = {
    error: 'text-red-600 bg-red-50',
    warning: 'text-amber-600 bg-amber-50',
    success: 'text-green-600 bg-green-50'
  };
  
  const icons = {
    error: AlertTriangle,
    warning: Clock, 
    success: CheckCircle2
  };

  const Icon = icons[type as keyof typeof icons];

  return (
    <div className="px-6 py-4 flex items-center gap-4 hover:bg-slate-50 transition-colors">
      <div className={`p-2 rounded-lg ${(colors as any)[type]}`}>
        <Icon size={18} />
      </div>
      <div className="flex-1">
        <p className="text-sm font-medium text-slate-700">{message}</p>
      </div>
      <span className="text-xs text-slate-400 font-mono">{time}</span>
    </div>
  );
}