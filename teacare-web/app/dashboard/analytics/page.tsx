'use client';
import { useEffect, useState } from 'react';
import { 
  LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  ComposedChart, Area, AreaChart, PieChart, Pie, Cell, Legend, ReferenceDot
} from 'recharts';
import { 
  TrendingUp, Activity, ArrowRight, TrendingDown, 
  MapPin, RefreshCw, FlaskConical, Globe, Percent, Layers, Download, AlertOctagon, Calendar
} from 'lucide-react';

const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

export default function TemporalAnalyticsPage() {
  // --- 1. State Management ---
  // Default: Last 30 Days
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  
  const [selectedCountry, setSelectedCountry] = useState('All');
  const [selectedRegion, setSelectedRegion] = useState('All');
  const [selectedDisease, setSelectedDisease] = useState('All');
  
  const [filterOptions, setFilterOptions] = useState<any>({ locations: {}, diseases: [] });
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  // --- 2. Initial Load: Filter Options ---
  useEffect(() => {
    async function loadFilters() {
        try {
            const res = await fetch('http://localhost:8000/api/analytics/filters');
            const json = await res.json();
            setFilterOptions(json);
        } catch (e) { console.error(e); }
    }
    loadFilters();
  }, []);

  // --- 3. Fetch Data (Triggered by any filter change) ---
  useEffect(() => {
    fetchData();
  }, [startDate, endDate, selectedCountry, selectedRegion, selectedDisease]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        country: selectedCountry,
        region: selectedRegion,
        disease: selectedDisease
      });
      const res = await fetch(`http://localhost:8000/api/analytics/temporal?${params.toString()}`);
      const json = await res.json();
      
      const mergedTimeline = json.timeline.map((item: any, index: number) => ({
        ...item,
        trend: json.trend_line[index]
      }));

      setData({ ...json, timeline: mergedTimeline });
    } catch (error) { console.error(error); } 
    finally { setLoading(false); }
  };

  const handleReset = () => {
      setSelectedCountry('All');
      setSelectedRegion('All');
      setSelectedDisease('All');
      // Reset to last 30 days
      setStartDate(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
      setEndDate(new Date().toISOString().split('T')[0]);
  };

  const downloadCSV = () => {
    // Construct the API URL with current filters
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate,
      country: selectedCountry,
      region: selectedRegion,
      disease: selectedDisease
    });

    // Trigger Browser Download directly from Backend
    const exportUrl = `http://localhost:8000/api/analytics/export?${params.toString()}`;
    window.open(exportUrl, '_blank');
  };

  const countries = ['All', ...Object.keys(filterOptions.locations)];
  const availableRegions = selectedCountry !== 'All' 
    ? ['All', ...(filterOptions.locations[selectedCountry] || [])]
    : ['All'];

  return (
    <div className="space-y-6 max-w-7xl mx-auto pb-10">
      
      {/* HEADER & CONTROLS */}
      <div className="flex flex-col gap-6">
        <div className="flex flex-col md:flex-row justify-between items-end gap-4">
            <div>
                <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                    <TrendingUp className="text-indigo-600" /> Temporal Analytics
                </h1>
                <p className="text-slate-500 text-sm mt-1">Data-driven insights from reported cases.</p>
            </div>
            
            <div className="flex flex-wrap gap-3 items-center">
                {/* NEW: Date Range Pickers */}
                <div className="flex items-center bg-white border border-slate-200 rounded-lg p-1 shadow-sm">
                    <input 
                        type="date" 
                        value={startDate} 
                        onChange={(e) => setStartDate(e.target.value)}
                        className="text-xs font-bold text-slate-600 bg-transparent border-none outline-none px-2 py-1"
                    />
                    <span className="text-slate-300 px-1">→</span>
                    <input 
                        type="date" 
                        value={endDate} 
                        onChange={(e) => setEndDate(e.target.value)}
                        className="text-xs font-bold text-slate-600 bg-transparent border-none outline-none px-2 py-1"
                    />
                </div>

                <button 
                    onClick={downloadCSV}
                    disabled={loading || !data}
                    className="flex items-center gap-2 px-4 py-2 text-xs font-bold bg-white border border-slate-200 text-slate-600 rounded-md hover:bg-slate-50 hover:text-indigo-600 transition-all shadow-sm disabled:opacity-50"
                >
                    <Download size={14} /> Export CSV
                </button>
            </div>
        </div>

        {/* FILTERS */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-4">
            <div className="flex-1">
                <label className="text-xs font-bold text-slate-500 uppercase mb-1 flex items-center gap-1"><Globe size={12}/> Country</label>
                <select value={selectedCountry} onChange={(e) => {setSelectedCountry(e.target.value); setSelectedRegion('All')}} className="w-full p-2 bg-slate-50 border rounded-lg text-sm outline-none">
                    {countries.map(c => <option key={c} value={c}>{c}</option>)}
                </select>
            </div>
            <div className="flex-1">
                <label className="text-xs font-bold text-slate-500 uppercase mb-1 flex items-center gap-1"><MapPin size={12}/> Region</label>
                <select value={selectedRegion} onChange={(e) => setSelectedRegion(e.target.value)} disabled={selectedCountry === 'All'} className={`w-full p-2 bg-slate-50 border rounded-lg text-sm outline-none ${selectedCountry === 'All' ? 'opacity-50':''}`}>
                    {availableRegions.map(r => <option key={r} value={r}>{r}</option>)}
                </select>
            </div>
            <div className="flex-1">
                <label className="text-xs font-bold text-slate-500 uppercase mb-1 flex items-center gap-1"><FlaskConical size={12}/> Pathogen</label>
                <select value={selectedDisease} onChange={(e) => setSelectedDisease(e.target.value)} className="w-full p-2 bg-slate-50 border rounded-lg text-sm outline-none">
                    <option value="All">All Pathogens</option>
                    {filterOptions.diseases.map((d: string) => <option key={d} value={d}>{d}</option>)}
                </select>
            </div>
            <button onClick={handleReset} className="p-2 mt-auto text-slate-400 hover:text-red-500 hover:bg-red-50 rounded-lg"><RefreshCw size={20}/></button>
        </div>
      </div>

      {loading || !data ? (
        <div className="flex h-96 items-center justify-center text-slate-400 animate-pulse bg-white rounded-2xl border border-slate-200">
          <Activity className="mr-2 animate-bounce" /> Processing Data...
        </div>
      ) : (
        <>
            {/* ROW 1: TRENDS */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm relative overflow-hidden">
                    <div className="flex justify-between items-center mb-6 relative z-10">
                        <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                            <Activity size={16} className="text-indigo-500" /> Disease Incidence Curve                         </h3>
                        {data.statistics.anomaly_count > 0 && (
                            <span className="flex items-center gap-1 text-xs font-bold text-red-600 bg-red-50 px-2 py-1 rounded-full border border-red-100">
                                <AlertOctagon size={12} /> {data.statistics.anomaly_count} Outliers
                            </span>
                        )}
                    </div>
                    <div className="h-64 w-full relative z-10">
                        <ResponsiveContainer width="100%" height="100%">
                            <ComposedChart data={data.timeline}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="date" tick={{fontSize: 10}} tickFormatter={(val) => val.slice(5)} />
                                <YAxis tick={{fontSize: 10}} allowDecimals={false} />
                                <Tooltip contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} />
                                <Bar dataKey="disease_count" fill="#6366f1" radius={[4, 4, 0, 0]} barSize={20} name="Reported Cases" />
                                <Line type="monotone" dataKey="trend" stroke="#f59e0b" strokeWidth={3} dot={false} name="Trend Line" />
                                {data.anomalies.map((anomaly: any, index: number) => (
                                    <ReferenceDot key={index} x={anomaly.date} y={anomaly.disease_count} r={5} fill="#ef4444" stroke="#fff" />
                                ))}
                            </ComposedChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 h-full flex flex-col justify-between">
                    <div>
                        <h3 className="text-xs font-bold text-slate-500 uppercase flex items-center gap-2 mb-4">
                            <Percent size={14} /> Growth Velocity
                        </h3>
                        <div className="flex items-end gap-3 mb-2">
                            <span className={`text-4xl font-black ${data.statistics.growth_rate > 0 ? 'text-red-500' : 'text-emerald-500'}`}>
                                {data.statistics.growth_rate > 0 ? '+' : ''}{data.statistics.growth_rate}%
                            </span>
                            <span className="text-sm font-bold text-slate-400 mb-1">vs period</span>
                        </div>
                        {data.statistics.growth_rate > 0 ? (
                            <TrendingUp className="text-red-400 w-full h-12 opacity-20" />
                        ) : (
                            <TrendingDown className="text-emerald-400 w-full h-12 opacity-20" />
                        )}
                    </div>
                    <div className="mt-4 pt-4 border-t border-slate-200">
                        <h4 className="text-[10px] font-bold text-slate-400 uppercase flex items-center gap-1 mb-2">
                            <Calendar size={10} /> Seasonal Profile (Yearly)
                        </h4>
                        <div className="h-20">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={data.seasonality || []}>
                                    <Bar dataKey="cases" fill="#cbd5e1" radius={[2, 2, 0, 0]}>
                                        {(data.seasonality || []).map((entry: any, index: number) => (
                                            <Cell key={`cell-${index}`} fill={entry.cases > 5 ? '#6366f1' : '#cbd5e1'} />
                                        ))}
                                    </Bar>
                                    <Tooltip cursor={{fill: 'transparent'}} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </div>
            </div>

            {/* ROW 2: COMPARISONS */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                            <Layers size={16} className="text-emerald-500" /> Pathogen Evolution                         </h3>
                    </div>
                    <div className="h-64 w-full">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={data.composition || []}>
                                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                                <XAxis dataKey="date" tick={{fontSize: 10}} tickFormatter={(val) => val.slice(5)} />
                                <YAxis tick={{fontSize: 10}} />
                                <Tooltip contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} />
                                <Legend iconType="circle" wrapperStyle={{fontSize: '10px', paddingTop: '10px'}} />
                                {filterOptions.diseases.map((d: string, index: number) => (
                                    <Area key={d} type="monotone" dataKey={d} stackId="1" stroke={COLORS[index % COLORS.length]} fill={COLORS[index % COLORS.length]} fillOpacity={0.6} />
                                ))}
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                    <div className="flex justify-between items-center mb-6">
                        <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                            <FlaskConical size={16} className="text-purple-500" /> Prevalence Distribution                         </h3>
                    </div>
                    <div className="h-64 w-full flex items-center justify-center">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie data={data.disease_breakdown || []} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value">
                                    {(data.disease_breakdown || []).map((entry: any, index: number) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} />
                                <Legend layout="vertical" verticalAlign="middle" align="right" wrapperStyle={{fontSize: '11px', fontWeight: 'bold'}} />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* ROW 3: FORECAST */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
                <div className="flex justify-between items-center mb-6">
                    <h3 className="text-sm font-bold text-slate-800 flex items-center gap-2">
                        <ArrowRight size={16} className="text-slate-500" /> 7-Day Linear Forecast                     </h3>
                    <span className="text-xs font-bold px-2 py-1 bg-slate-100 text-slate-600 rounded border border-slate-200">Method: ARIMA-Linear</span>
                </div>
                <div className="h-48 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <ComposedChart data={data.forecast || []}>
                            <defs>
                                <linearGradient id="colorConf" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.2}/>
                                    <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                                </linearGradient>
                            </defs>
                            <XAxis dataKey="date" tick={{fontSize: 10}} tickFormatter={(val) => val.slice(5)} />
                            <YAxis tick={{fontSize: 10}} />
                            <Tooltip contentStyle={{borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'}} />
                            <Area type="monotone" dataKey="confidence_high" stroke="none" fill="url(#colorConf)" name="Confidence Interval" />
                            <Line type="monotone" dataKey="predicted" stroke="#059669" strokeWidth={3} dot={{r: 4}} name="Predicted Cases" />
                        </ComposedChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </>
      )}
    </div>
  );
}