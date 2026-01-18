'use client';
import { useEffect, useState } from 'react';
import { 
  Activity, 
  Droplets, 
  Wind, 
  AlertTriangle, 
  ArrowUpRight, 
  Calendar,
  FileText,
  Map as MapIcon,
  Microscope,
  CheckCircle2,
  Clock,
  Dna // <--- Import DNA icon for "Strain"
} from 'lucide-react';
import Link from 'next/link';

export default function ResearcherDashboard() {
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<any>(null); // Researcher Stats
  const [recentReports, setRecentReports] = useState<any[]>([]);
  const [weather, setWeather] = useState<any>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        // 1. Fetch RESEARCHER Stats (Updated Endpoint)
        const statsRes = await fetch('http://localhost:8000/api/researcher/stats');
        const statsData = await statsRes.json();
        setStats(statsData);

        // 2. Fetch Recent Reports
        const reportsRes = await fetch('http://localhost:8000/api/admin/reports_triage?filter_by=all');
        const reportsData = await reportsRes.json();
        setRecentReports(reportsData.slice(0, 5));

        // 3. Fetch Weather
        const weatherRes = await fetch('http://localhost:8000/weather?lat=6.97&lng=80.78');
        const weatherData = await weatherRes.json();
        setWeather(weatherData);

        setLoading(false);
      } catch (error) {
        console.error("Dashboard Fetch Error:", error);
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="flex h-96 items-center justify-center text-green-800 animate-pulse">
        <Microscope className="mr-2 animate-bounce" /> Loading Research Data...
      </div>
    );
  }

  return (
    <div className="space-y-8">
      
      {/* 1. Header */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-slate-800 tracking-tight">Research Laboratory</h1>
          <p className="text-slate-500 mt-1">Real-time analysis of agronomic data streams & pathogen detection.</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-600 bg-white px-4 py-2 rounded-xl border border-slate-200 shadow-sm">
          <Calendar size={16} className="text-green-600" />
          <span className="font-medium">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </span>
        </div>
      </div>

      {/* 2. Key Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          label="Total Samples Analyzed" 
          value={stats?.total_samples || 0} 
          icon={FileText} 
          color="bg-blue-50 text-blue-700"
          trend="Dataset Size"
        />
        <StatCard 
          label="Pending Validations" 
          value={stats?.pending_validations || 0} 
          icon={Microscope} 
          color="bg-amber-50 text-amber-700"
          trend="Needs Review"
          trendColor="text-amber-600"
        />
        <StatCard 
          label="Uncertainty Flags" 
          value={stats?.uncertainty_flags || 0} 
          icon={Activity} 
          color="bg-red-50 text-red-700"
          trend="Low Confidence (<75%)"
          trendColor="text-red-600"
        />
        
        {/* REPLACED CARD: Dominant Strain */}
        <StatCard 
          label="Dominant Strain" 
          value={stats?.dominant_disease || "None"} 
          icon={Dna} 
          color="bg-purple-50 text-purple-700"
          trend="Most Detected"
          trendColor="text-purple-600"
        />
      </div>

      {/* 3. Main Split: Incoming Data & Environment */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Recent Samples Feed */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-6 border-b border-slate-100 flex justify-between items-center bg-slate-50/50">
            <div className="flex items-center gap-2">
                <Activity size={18} className="text-green-600" />
                <h3 className="font-bold text-slate-800 text-lg">Incoming Sample Stream</h3>
            </div>
            <Link href="/dashboard/lab" className="text-sm text-green-700 font-bold hover:underline flex items-center gap-1">
                View Lab Queue <ArrowUpRight size={14} />
            </Link>
          </div>
          
          <div className="divide-y divide-slate-100">
            {recentReports.length === 0 ? (
                <div className="p-8 text-center text-slate-400">No recent reports found.</div>
            ) : (
                recentReports.map((report) => (
                <div key={report.report_id} className="p-5 flex items-center justify-between hover:bg-slate-50 transition-colors group">
                    <div className="flex items-center gap-4">
                    <div className="relative w-14 h-14 rounded-xl bg-slate-200 overflow-hidden flex-shrink-0 border border-slate-200">
                        <img 
                            src={`http://localhost:8000/${report.image_url}`} 
                            alt="Leaf" 
                            className="w-full h-full object-cover"
                            onError={(e) => (e.currentTarget.src = 'https://via.placeholder.com/150?text=No+Img')} 
                        />
                        <div className={`absolute bottom-0 w-full h-1 ${
                            report.disease_name === 'Healthy' ? 'bg-green-500' : 'bg-red-500'
                        }`} />
                    </div>
                    
                    <div>
                        <h4 className="font-bold text-slate-800 group-hover:text-green-700 transition-colors">
                            {report.disease_name}
                        </h4>
                        <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                            <span className="flex items-center gap-1">
                                <Clock size={12} /> {report.timestamp}
                            </span>
                            <span className="flex items-center gap-1">
                                <MapIcon size={12} /> ID: #{report.report_id}
                            </span>
                        </div>
                    </div>
                    </div>
                    
                    <div className="text-right">
                        <div className={`text-xs font-bold px-3 py-1 rounded-full mb-1 inline-flex items-center gap-1 ${
                            report.verification_status === 'Pending' ? 'bg-amber-100 text-amber-700' : 
                            report.verification_status === 'Auto-Verified' ? 'bg-blue-100 text-blue-700' : 
                            'bg-green-100 text-green-700'
                        }`}>
                            {report.verification_status === 'Pending' && <AlertTriangle size={10} />}
                            {report.verification_status}
                        </div>
                        <p className="text-xs font-mono text-slate-400 font-medium">
                            {report.confidence} Conf.
                        </p>
                    </div>
                </div>
                ))
            )}
          </div>
        </div>

        {/* Right Column: Environmental Monitor */}
        {weather ? (
        <div className="bg-gradient-to-br from-green-800 to-green-950 rounded-2xl text-white p-1 shadow-xl">
            <div className="h-full bg-white/5 rounded-xl p-6 flex flex-col justify-between relative overflow-hidden backdrop-blur-sm border border-white/10">
                <div className="absolute -top-10 -right-10 w-40 h-40 bg-green-500 opacity-20 rounded-full blur-3xl" />
                
                <div>
                    <div className="flex items-center gap-2 mb-8 opacity-80">
                        <MapIcon size={16} />
                        <span className="text-xs font-bold tracking-[0.2em] uppercase">Field Conditions</span>
                        <span className="ml-auto text-xs bg-white/20 px-2 py-0.5 rounded text-white">{weather.location}</span>
                    </div>
                    
                    <div className="flex items-center justify-between mb-8 relative z-10">
                        <div>
                        <h2 className="text-6xl font-bold tracking-tighter">{weather.temperature}°</h2>
                        <p className="text-green-200 mt-1 font-medium text-lg flex items-center gap-2">
                            {weather.condition}
                        </p>
                        </div>
                        <div className="p-4 bg-white/10 rounded-full">
                            <Wind size={40} className="text-green-200" />
                        </div>
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-3 relative z-10">
                    <WeatherMetric 
                        label="Humidity" 
                        value={`${weather.humidity}%`} 
                        icon={Droplets} 
                        warning={weather.humidity > 80} 
                    />
                    <WeatherMetric 
                        label="Risk Level" 
                        value={weather.risk_level} 
                        icon={AlertTriangle} 
                        warning={weather.risk_level === 'High'}
                    />
                </div>

                <div className="mt-6 pt-6 border-t border-white/10">
                    <p className="text-xs text-green-300 uppercase font-bold mb-1">AI Recommendation</p>
                    <p className="text-sm text-white leading-relaxed opacity-90">
                        {weather.advice}
                    </p>
                </div>
            </div>
        </div>
        ) : (
            <div className="bg-slate-100 rounded-2xl animate-pulse h-full flex items-center justify-center text-slate-400">
                Loading Weather Data...
            </div>
        )}

      </div>
    </div>
  );
}

// --- Sub Components ---

function StatCard({ label, value, icon: Icon, color, trend, trendColor = "text-slate-500" }: any) {
  return (
    <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className={`p-3 rounded-xl ${color}`}>
          <Icon size={22} />
        </div>
        {trend && (
            <span className={`text-[10px] font-bold px-2 py-1 rounded-full bg-slate-50 ${trendColor}`}>
                {trend}
            </span>
        )}
      </div>
      <h3 className="text-3xl font-bold text-slate-800 tracking-tight">{value}</h3>
      <p className="text-sm text-slate-500 font-medium mt-1">{label}</p>
    </div>
  );
}

function WeatherMetric({ label, value, icon: Icon, warning }: any) {
    return (
        <div className={`p-3 rounded-xl border backdrop-blur-md transition-colors ${
            warning ? 'bg-red-500/20 border-red-500/30' : 'bg-white/5 border-white/10'
        }`}>
            <div className="flex items-center gap-2 mb-1 text-green-100 text-[10px] uppercase font-bold tracking-wider">
                <Icon size={12} /> {label}
            </div>
            <p className={`text-lg font-bold ${warning ? 'text-red-200' : 'text-white'}`}>
                {value}
            </p>
        </div>
    );
}