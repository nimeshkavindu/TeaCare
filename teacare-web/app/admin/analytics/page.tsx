'use client';
import { useEffect, useState } from 'react';
import dynamic from 'next/dynamic';
import { 
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, 
  PieChart, Pie, Cell, LineChart, Line, CartesianGrid 
} from 'recharts';
import { Users, FileText, Activity, AlertTriangle, Target, Calendar, Filter } from 'lucide-react';

// Dynamically Import Map
const DiseaseMap = dynamic(() => import('../components/DiseaseMap'), { 
  ssr: false,
  loading: () => <div className="h-96 bg-slate-100 animate-pulse rounded-2xl flex items-center justify-center text-slate-400">Loading Geospatial Data...</div>
});

const COLORS = ['#059669', '#0891b2', '#7c3aed', '#ea580c', '#db2777'];

export default function AnalyticsPage() {
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [range, setRange] = useState("7d"); // Default Filter

  useEffect(() => {
    setLoading(true);
    // Fetch data whenever 'range' changes
    fetch(`http://localhost:8000/api/admin/stats?time_range=${range}`)
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => setLoading(false));
  }, [range]);

  if (loading && !stats) return (
    <div className="flex h-screen items-center justify-center text-slate-400 gap-2">
        <Activity className="animate-spin" /> Loading System Analytics...
    </div>
  );

  if (!stats) return <div className="p-8 text-red-500">Failed to load analytics. Check backend connection.</div>;

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8">
      
      {/* 1. HEADER */}
      <div>
          <h1 className="text-3xl font-bold text-slate-900">System Analytics</h1>
          <p className="text-slate-500">Real-time agricultural insights & AI performance.</p>
      </div>

      {/* 2. STAT CARDS (Global Stats) */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          icon={<Users size={24} className="text-blue-600"/>}
          label="Total Users" 
          value={stats.total_users}
          color="bg-blue-50 border-blue-100"
          breakdown={stats.role_breakdown} 
        />
        <StatCard 
          icon={<FileText size={24} className="text-emerald-600"/>}
          label="Total Reports"
          value={stats.total_reports}
          color="bg-emerald-50 border-emerald-100"
        />
        <StatCard 
          icon={<AlertTriangle size={24} className="text-amber-600"/>}
          label="Pending Reviews"
          value={stats.pending_reviews}
          color="bg-amber-50 border-amber-100"
        />
        
        {/* AI Accuracy Card */}
        <div className={`p-6 rounded-2xl border flex items-center gap-4 transition-transform hover:scale-105 ${
            stats.ai_accuracy > 80 ? 'bg-green-50 border-green-200' : 
            stats.ai_accuracy > 60 ? 'bg-yellow-50 border-yellow-200' : 'bg-red-50 border-red-200'
        }`}>
            <div className={`p-3 rounded-xl shadow-sm ${
                stats.ai_accuracy > 80 ? 'bg-green-100 text-green-700' : 'bg-white text-slate-600'
            }`}>
                <Target size={24} />
            </div>
            <div>
                <p className="text-slate-500 text-sm font-medium uppercase tracking-wider">AI Accuracy</p>
                <div className="flex items-end gap-2">
                    <h3 className={`text-3xl font-bold ${
                        stats.ai_accuracy > 80 ? 'text-green-700' : 
                        stats.ai_accuracy > 60 ? 'text-yellow-700' : 'text-red-700'
                    }`}>
                        {stats.ai_accuracy}%
                    </h3>
                    <span className="text-xs text-slate-400 mb-1">({range})</span>
                </div>
            </div>
        </div>
      </div>

      {/* 3. CHARTS HEADER & FILTERS */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-slate-200 pb-4">
        <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
                <Activity size={20} className="text-indigo-600"/>
                Detailed Analytics
            </h2>
            <p className="text-sm text-slate-500">Trends and distributions based on selected period.</p>
        </div>

        {/* --- FILTER BUTTONS --- */}
        <div className="bg-white p-1 rounded-lg border border-slate-200 shadow-sm flex items-center">
            <span className="px-3 text-slate-400 flex items-center gap-2 text-xs font-bold uppercase border-r border-slate-100 mr-1">
                <Filter size={12} /> Range:
            </span>
            {['7d', '30d', '6m', '1y'].map((r) => (
                <button
                    key={r}
                    onClick={() => setRange(r)}
                    className={`px-3 py-1.5 text-xs font-bold rounded-md transition-all ${
                        range === r 
                        ? 'bg-indigo-600 text-white shadow-md' 
                        : 'text-slate-500 hover:bg-slate-50 hover:text-slate-700'
                    }`}
                >
                    {r === '7d' && '7 Days'}
                    {r === '30d' && '30 Days'}
                    {r === '6m' && '6 Months'}
                    {r === '1y' && '1 Year'}
                </button>
            ))}
        </div>
      </div>

      {/* 4. CHARTS ROW */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        
        {/* CHART A: Trends */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-slate-800 mb-6">
            {range === '1y' || range === '6m' ? 'Monthly Trends' : 'Daily Trends'}
          </h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={stats.trends}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis 
                    dataKey="date" 
                    tick={{fontSize: 11, fill: '#64748b'}} 
                    axisLine={false} 
                    tickLine={false} 
                    tickFormatter={(val) => {
                        if(range === '1y' || range === '6m') return val; // YYYY-MM
                        return val.slice(5); // MM-DD
                    }}
                />
                <YAxis allowDecimals={false} tick={{fontSize: 12, fill: '#64748b'}} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{borderRadius: '12px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'}} />
                <Line 
                    type="monotone" 
                    dataKey="reports" 
                    stroke="#4f46e5" 
                    strokeWidth={3} 
                    dot={{r: 4, fill: '#4f46e5', strokeWidth: 2, stroke: '#fff'}} 
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* CHART B: Distribution */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <h3 className="text-lg font-bold text-slate-800 mb-6">Top Detected Diseases</h3>
          <div className="h-64 flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={stats.distribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {stats.distribution.map((entry: any, index: number) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="flex flex-wrap gap-3 justify-center mt-2">
            {stats.distribution.map((entry: any, index: number) => (
                <div key={index} className="flex items-center gap-2 text-xs font-bold text-slate-600">
                    <div className="w-3 h-3 rounded-full" style={{backgroundColor: COLORS[index % COLORS.length]}}></div>
                    {entry.name} ({entry.value})
                </div>
            ))}
          </div>
        </div>
      </div>

      {/* 5. MAP SECTION (Now placed after charts) */}
      <div className="bg-white p-1 rounded-2xl border border-slate-200 shadow-sm">
        <div className="p-6 pb-2 flex justify-between items-center">
            <h3 className="text-lg font-bold text-slate-800 flex items-center gap-2">
                <span className="w-2 h-8 bg-indigo-500 rounded-full"></span>
                Disease Outbreak Map
            </h3>
            <span className="text-xs font-bold text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">Live Data</span>
        </div>
        <div className="h-96 w-full p-6 pt-2"> 
            <DiseaseMap />
        </div>
      </div>

    </div>
  );
}

// Helper for Stat Cards
function StatCard({ icon, label, value, color, breakdown }: any) {
    return (
        <div className={`p-6 rounded-2xl border ${color} flex flex-col justify-between transition-transform hover:scale-105 bg-white h-full`}>
            {/* Top Section: Icon and Big Number */}
            <div className="flex items-center gap-4 mb-2">
                <div className="p-3 bg-white rounded-xl shadow-sm border border-slate-100">{icon}</div>
                <div>
                    <p className="text-slate-500 text-sm font-medium uppercase tracking-wider">{label}</p>
                    <h3 className="text-3xl font-bold text-slate-900">{value}</h3>
                </div>
            </div>
            
            {/* Bottom Section: Role Breakdown Badges */}
            {/* This part was missing in your code! */}
            {breakdown && (
                <div className="mt-3 pt-3 border-t border-slate-100 flex flex-wrap gap-2">
                    {Object.entries(breakdown).map(([role, count]: any) => (
                        <span key={role} className="text-[10px] font-bold px-2 py-1 rounded-full bg-slate-50 text-slate-600 border border-slate-200 uppercase">
                            {count} {role}
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}