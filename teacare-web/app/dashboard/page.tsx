'use client';
import { 
  Activity, 
  Droplets, 
  Wind, 
  AlertTriangle, 
  ArrowUpRight, 
  Calendar,
  FileText,
  Map as MapIcon // <--- Fixed: Import Map as MapIcon to avoid conflicts
} from 'lucide-react';

export default function DashboardHome() {
  // Mock Data
  const stats = [
    { label: "Total Samples", value: "1,240", change: "+12%", icon: FileText, color: "text-blue-600 bg-blue-50" },
    { label: "Disease Detection Rate", value: "8.4%", change: "-2.1%", icon: Activity, color: "text-purple-600 bg-purple-50" },
    { label: "Active Outbreaks", value: "3", change: "+1", icon: AlertTriangle, color: "text-red-600 bg-red-50" },
    { label: "Estates Monitored", value: "12", change: "0%", icon: MapIcon, color: "text-green-600 bg-green-50" }, // <--- Fixed: Use MapIcon here
  ];

  const recentDetections = [
    { id: 1, disease: "Blister Blight", confidence: "92%", location: "Badulla Estate", time: "10 mins ago", status: "High Risk" },
    { id: 2, disease: "Healthy", confidence: "99%", location: "Nuwara Eliya", time: "45 mins ago", status: "Safe" },
    { id: 3, disease: "Red Rust", confidence: "78%", location: "Kandy Region", time: "2 hours ago", status: "Medium Risk" },
    { id: 4, disease: "Blister Blight", confidence: "88%", location: "Badulla Estate", time: "3 hours ago", status: "High Risk" },
  ];

  return (
    <div className="space-y-8">
      
      {/* Header */}
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-slate-800">Research Overview</h1>
          <p className="text-slate-500 mt-1">Real-time analysis of agronomic data streams.</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-500 bg-white px-4 py-2 rounded-lg border border-slate-200 shadow-sm">
          <Calendar size={16} />
          <span>{new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}</span>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, i) => (
          <div key={i} className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition">
            <div className="flex justify-between items-start mb-4">
              <div className={`p-3 rounded-xl ${stat.color}`}>
                <stat.icon size={22} />
              </div>
              <span className={`flex items-center text-xs font-bold px-2 py-1 rounded-full ${stat.change.includes('+') ? 'text-green-700 bg-green-50' : 'text-slate-600 bg-slate-100'}`}>
                {stat.change} <ArrowUpRight size={12} className="ml-1" />
              </span>
            </div>
            <h3 className="text-2xl font-bold text-slate-800">{stat.value}</h3>
            <p className="text-sm text-slate-500 font-medium">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Main Content Split: Weather & Recent Feed */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Recent Incoming Data */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="p-6 border-b border-slate-100 flex justify-between items-center">
            <h3 className="font-bold text-slate-800 text-lg">Live Detection Feed</h3>
            <button className="text-sm text-green-600 font-medium hover:underline">View All Reports</button>
          </div>
          <div className="divide-y divide-slate-50">
            {recentDetections.map((item) => (
              <div key={item.id} className="p-5 flex items-center justify-between hover:bg-slate-50 transition">
                <div className="flex items-center gap-4">
                  {/* Mock Image Thumbnail */}
                  <div className="w-12 h-12 rounded-lg bg-slate-200 flex-shrink-0 overflow-hidden relative">
                    <div className={`absolute inset-0 opacity-20 ${item.disease === 'Healthy' ? 'bg-green-500' : 'bg-red-500'}`} />
                  </div>
                  <div>
                    <h4 className="font-semibold text-slate-800">{item.disease}</h4>
                    <p className="text-xs text-slate-500">{item.location} • {item.time}</p>
                  </div>
                </div>
                
                <div className="text-right">
                  <div className={`text-xs font-bold px-3 py-1 rounded-full mb-1 inline-block ${
                    item.status === 'High Risk' ? 'bg-red-100 text-red-700' : 
                    item.status === 'Safe' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'
                  }`}>
                    {item.confidence} Conf.
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Environmental Status (Mock) */}
        <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-2xl text-white p-6 shadow-lg flex flex-col justify-between relative overflow-hidden">
          {/* Decorative Background */}
          <div className="absolute top-0 right-0 w-32 h-32 bg-white opacity-10 rounded-full blur-2xl -mr-10 -mt-10" />
          
          <div>
            <div className="flex items-center gap-2 mb-6 opacity-90">
              <MapIcon size={18} />
              <span className="text-sm font-medium tracking-wide">REGIONAL WEATHER (BADULLA)</span>
            </div>
            
            <div className="flex items-center justify-between mb-8">
              <div>
                <h2 className="text-5xl font-bold">24°C</h2>
                <p className="text-blue-100 mt-1">Partly Cloudy</p>
              </div>
              <Wind size={48} className="text-blue-200 opacity-50" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-white/10 backdrop-blur-sm p-4 rounded-xl">
              <div className="flex items-center gap-2 mb-1 text-blue-100 text-xs uppercase font-bold">
                <Droplets size={14} /> Humidity
              </div>
              <p className="text-xl font-semibold">82%</p>
            </div>
            <div className="bg-white/10 backdrop-blur-sm p-4 rounded-xl">
              <div className="flex items-center gap-2 mb-1 text-blue-100 text-xs uppercase font-bold">
                <AlertTriangle size={14} /> Risk
              </div>
              <p className="text-xl font-semibold text-amber-300">High</p>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}