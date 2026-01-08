'use client';
import { useState, useEffect } from 'react';
import { ScrollText, Search, Filter } from 'lucide-react';

export default function AllLogsPage() {
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        // Fetch 50 logs for the full view
        const res = await fetch('http://localhost:8000/api/logs?limit=50');
        if (res.ok) setLogs(await res.json());
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, []);

  return (
    <div className="p-8 max-w-7xl mx-auto">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 flex items-center gap-3">
          <div className="p-2 bg-slate-100 rounded-lg"><ScrollText size={32} /></div>
          System Activity Logs
        </h1>
        <p className="text-slate-500 mt-2 ml-14">Full history of system events, errors, and user actions.</p>
      </header>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        {/* Simple Toolbar */}
        <div className="px-6 py-4 border-b border-slate-100 flex gap-4 bg-slate-50/50">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input 
              type="text" 
              placeholder="Search logs..." 
              className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 text-sm focus:outline-none focus:ring-2 focus:ring-green-500/20 focus:border-green-500"
            />
          </div>
          <button className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-medium text-slate-600 flex items-center gap-2 hover:bg-white hover:shadow-sm transition-all">
            <Filter size={16} /> Filter
          </button>
        </div>

        {/* Logs Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-600">
            <thead className="bg-slate-50 border-b border-slate-100 text-xs uppercase font-semibold text-slate-500">
              <tr>
                <th className="px-6 py-4">Timestamp</th>
                <th className="px-6 py-4">Level</th>
                <th className="px-6 py-4">Source</th>
                <th className="px-6 py-4">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-slate-50/50 transition-colors">
                  <td className="px-6 py-4 font-mono text-xs text-slate-400">
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-[10px] font-bold border ${
                      log.level === 'ERROR' ? 'bg-red-50 text-red-600 border-red-100' :
                      log.level === 'WARNING' ? 'bg-amber-50 text-amber-600 border-amber-100' :
                      log.level === 'SUCCESS' ? 'bg-green-50 text-green-600 border-green-100' :
                      'bg-blue-50 text-blue-600 border-blue-100'
                    }`}>
                      {log.level}
                    </span>
                  </td>
                  <td className="px-6 py-4 font-medium text-slate-700">{log.source}</td>
                  <td className="px-6 py-4 text-slate-600">{log.message}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}