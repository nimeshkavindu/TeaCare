'use client';
import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Server, Database, Activity, AlertTriangle, CheckCircle2, Clock, RefreshCw, ArrowRight } from 'lucide-react';

interface SystemHealth {
  api_latency: string;
  services: {
    database: 'online' | 'offline';
    ai_engine: 'online' | 'offline' | 'degraded';
    api: 'online' | 'offline';
  };
}

interface LogEntry {
  id: number;
  level: string;
  source: string;
  message: string;
  timestamp: string;
}

export default function AdminDashboard() {
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [lastUpdated, setLastUpdated] = useState<string>('');

  const fetchData = async () => {
    try {
      // 1. Fetch Health
      const healthRes = await fetch('http://localhost:8000/api/health');
      if (healthRes.ok) setHealth(await healthRes.json());

      // 2. Fetch Logs (Limit 5 for dashboard)
      const logsRes = await fetch('http://localhost:8000/api/logs?limit=5');
      if (logsRes.ok) setLogs(await logsRes.json());

      setLastUpdated(new Date().toLocaleTimeString());
    } catch (error) {
      console.error("Fetch failed", error);
      // Fallback handled by UI state
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Update every 5s
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      {/* Header */}
      <header className="mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">System Overview</h1>
          <p className="text-slate-500 mt-1">Real-time infrastructure monitoring</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-400 bg-white px-3 py-1 rounded-full border border-slate-200 shadow-sm">
          <Clock size={14} />
          <span>Last updated: {lastUpdated || 'Never'}</span>
          <button onClick={fetchData} className="ml-2 hover:text-green-600 transition-colors">
            <RefreshCw size={14} />
          </button>
        </div>
      </header>

      {/* Status Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatusCard 
          title="FastAPI Backend" 
          status={health?.services.api || 'offline'} 
          ping={health?.api_latency || '---'} 
          icon={Server} 
        />
        <StatusCard 
          title="PostgreSQL Database" 
          status={health?.services.database || 'offline'} 
          ping={health?.services.database === 'online' ? 'Connected' : 'Failed'} 
          icon={Database} 
        />
        <StatusCard 
          title="AI Inference Engine" 
          status={health?.services.ai_engine || 'offline'} 
          ping={health?.services.ai_engine === 'online' ? 'Ready' : 'Not Loaded'} 
          icon={Activity} 
          details={health?.services.ai_engine === 'offline' ? "Model not loaded" : "Active"}
        />
      </div>

      {/* Logs Section */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
          <div className="flex items-center gap-3">
            <h2 className="font-semibold text-slate-800">Recent Activity</h2>
            <span className="text-xs font-medium px-2 py-1 bg-green-100 text-green-700 rounded-full animate-pulse">Live</span>
          </div>
          
          {/* View All Button */}
          <Link 
            href="/admin/logs" 
            className="text-sm text-green-600 hover:text-green-700 font-medium flex items-center gap-1 transition-colors"
          >
            View All Logs <ArrowRight size={16} />
          </Link>
        </div>
        
        <div className="divide-y divide-slate-100">
          {logs.length === 0 ? (
            <div className="p-8 text-center text-slate-400">No activity recorded yet.</div>
          ) : (
            logs.map((log) => (
              <LogItem 
                key={log.id} 
                type={log.level}
                source={log.source}
                message={log.message} 
                time={new Date(log.timestamp).toLocaleTimeString()} 
              />
            ))
          )}
        </div>
      </div>
    </div>
  );
}

// --- MISSING COMPONENTS ADDED BELOW ---

function StatusCard({ title, status, ping, icon: Icon, details }: any) {
  const isOnline = status === 'online';
  const isDegraded = status === 'degraded';
  
  // Dynamic Color Logic
  let statusColor = 'bg-red-100 text-red-700'; // Default Error
  let iconColor = 'bg-red-100 text-red-600';
  
  if (isOnline) {
    statusColor = 'bg-green-100 text-green-700';
    iconColor = 'bg-green-100 text-green-600';
  } else if (isDegraded) {
    statusColor = 'bg-amber-100 text-amber-700';
    iconColor = 'bg-amber-100 text-amber-600';
  }

  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className={`p-3 rounded-xl ${iconColor}`}>
          <Icon size={24} />
        </div>
        <span className={`px-2 py-1 rounded-full text-xs font-bold uppercase tracking-wide ${statusColor}`}>
          {status}
        </span>
      </div>
      
      <h3 className="font-bold text-slate-800 text-lg">{title}</h3>
      
      <div className="flex items-center gap-2 mt-2 text-sm text-slate-500 font-medium">
        <Activity size={14} />
        <span>Response: {ping}</span>
      </div>

      {details && (
        <div className="mt-4 pt-4 border-t border-slate-100 text-xs text-slate-400 flex items-center gap-2">
          {status === 'offline' ? <AlertTriangle size={12} /> : <CheckCircle2 size={12} />}
          {details}
        </div>
      )}
    </div>
  );
}

function LogItem({ type, source, message, time }: any) {
  const typeKey = type?.toLowerCase() || 'info';
  
  const styles: any = {
    error: { color: 'text-red-600', bg: 'bg-red-50', icon: AlertTriangle },
    warning: { color: 'text-amber-600', bg: 'bg-amber-50', icon: Clock },
    success: { color: 'text-green-600', bg: 'bg-green-50', icon: CheckCircle2 },
    info: { color: 'text-blue-600', bg: 'bg-blue-50', icon: Activity }
  };
  
  const style = styles[typeKey] || styles.info;
  const Icon = style.icon;

  return (
    <div className={`px-6 py-4 flex items-center justify-between hover:bg-slate-50 transition-colors`}>
      <div className="flex items-center gap-4">
        <div className={`p-2 rounded-lg ${style.bg} ${style.color}`}>
          <Icon size={18} />
        </div>
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <span className={`text-[10px] font-bold uppercase tracking-wider ${style.color}`}>{source}</span>
          </div>
          <p className="text-sm font-medium text-slate-700">{message}</p>
        </div>
      </div>
      <span className="text-xs text-slate-400 font-mono whitespace-nowrap">{time}</span>
    </div>
  );
}