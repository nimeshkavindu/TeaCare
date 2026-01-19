'use client';
import { useEffect, useState, useMemo } from 'react';
import dynamic from 'next/dynamic'; 
import { Map as MapIcon, Filter, Globe, MapPin, FlaskConical, RefreshCw, Calendar, Download } from 'lucide-react';

// Dynamic Import
const EpidemiologyMap = dynamic(() => import('@/components/EpidemiologyMap'), { 
  ssr: false,
  loading: () => <div className="h-full w-full bg-slate-100 animate-pulse rounded-2xl flex items-center justify-center text-slate-400">Loading Cartography...</div>
});

// Scientific Color Palette
const COLORS = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

export default function MapPage() {
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedCountry, setSelectedCountry] = useState('All');
  const [selectedRegion, setSelectedRegion] = useState('All');
  const [selectedDisease, setSelectedDisease] = useState('All');
  
  const [filterOptions, setFilterOptions] = useState<any>({ locations: {}, diseases: [] });
  const [mapData, setMapData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  // 1. Load Filters
  useEffect(() => {
    fetch('http://localhost:8000/api/analytics/filters')
      .then(res => res.json())
      .then(json => setFilterOptions(json))
      .catch(console.error);
  }, []);

  // 2. Load Map Data
  useEffect(() => {
    setLoading(true);
    const params = new URLSearchParams({
        start_date: startDate,
        end_date: endDate,
        country: selectedCountry,
        region: selectedRegion,
        disease: selectedDisease
    });

    fetch(`http://localhost:8000/api/analytics/map?${params.toString()}`)
      .then(res => res.json())
      .then(data => {
          setMapData(data);
          setLoading(false);
      })
      .catch(e => {
          console.error(e);
          setLoading(false);
      });
  }, [startDate, endDate, selectedCountry, selectedRegion, selectedDisease]);

  // 3. Generate Color Map (Ensures consistency between Legend and Map)
  const diseaseColorMap = useMemo(() => {
    const map: { [key: string]: string } = {};
    filterOptions.diseases.forEach((d: string, index: number) => {
        map[d] = COLORS[index % COLORS.length];
    });
    return map;
  }, [filterOptions.diseases]);

  const countries = ['All', ...Object.keys(filterOptions.locations)];
  const availableRegions = selectedCountry !== 'All' 
    ? ['All', ...(filterOptions.locations[selectedCountry] || [])]
    : ['All'];

  return (
    <div className="flex flex-col h-[calc(100vh-100px)] gap-6 pb-6">
      
      {/* Header & Controls */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 shrink-0">
        <div>
            <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
                <MapIcon className="text-emerald-600" /> Epidemiology Map
            </h1>
            <p className="text-slate-500 text-sm mt-1">Geospatial distribution of pathogen vectors.</p>
        </div>

        <div className="flex items-center bg-white border border-slate-200 rounded-lg p-1 shadow-sm">
            <Calendar size={14} className="ml-2 text-slate-400" />
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
      </div>

      {/* Filter Bar */}
      <div className="bg-white p-3 rounded-xl border border-slate-200 shadow-sm flex flex-col md:flex-row gap-3 shrink-0">
            <div className="flex-1">
                <select value={selectedCountry} onChange={(e) => {setSelectedCountry(e.target.value); setSelectedRegion('All')}} className="w-full p-2 bg-slate-50 border rounded-lg text-xs font-semibold outline-none">
                    <option value="All">All Countries</option>
                    {countries.filter(c => c !== 'All').map(c => <option key={c} value={c}>{c}</option>)}
                </select>
            </div>
            <div className="flex-1">
                <select value={selectedRegion} onChange={(e) => setSelectedRegion(e.target.value)} disabled={selectedCountry === 'All'} className={`w-full p-2 bg-slate-50 border rounded-lg text-xs font-semibold outline-none ${selectedCountry === 'All' ? 'opacity-50':''}`}>
                    <option value="All">All Regions</option>
                    {availableRegions.filter(r => r !== 'All').map(r => <option key={r} value={r}>{r}</option>)}
                </select>
            </div>
            <div className="flex-1">
                <select value={selectedDisease} onChange={(e) => setSelectedDisease(e.target.value)} className="w-full p-2 bg-slate-50 border rounded-lg text-xs font-semibold outline-none">
                    <option value="All">All Pathogens</option>
                    {filterOptions.diseases.map((d: string) => <option key={d} value={d}>{d}</option>)}
                </select>
            </div>
      </div>

      {/* Map Container */}
      <div className="flex-1 bg-white rounded-2xl border border-slate-200 shadow-inner relative overflow-hidden">
        {/* Pass the dynamic color map to the component */}
        <EpidemiologyMap data={mapData} colorMap={diseaseColorMap} />
        
        {/* Dynamic Legend Overlay */}
        <div className="absolute bottom-6 left-6 bg-white/90 backdrop-blur-sm p-4 rounded-xl border border-slate-200 shadow-lg z-[1000] text-xs max-h-48 overflow-y-auto">
            <h4 className="font-bold text-slate-700 mb-2 flex items-center gap-2">
                <FlaskConical size={12} className="text-slate-400" /> Pathogen Key
            </h4>
            
            <div className="space-y-2">
                {/* Dynamically Map over available diseases */}
                {filterOptions.diseases.map((d: string) => (
                    <div key={d} className="flex items-center gap-2">
                        <span 
                            className="w-2.5 h-2.5 rounded-full shadow-sm" 
                            style={{ backgroundColor: diseaseColorMap[d] || '#ccc' }}
                        ></span> 
                        <span className="text-slate-600 font-medium">{d}</span>
                    </div>
                ))}
            </div>

            <div className="mt-3 pt-3 border-t border-slate-200 text-[10px] text-slate-400">
                Total Markers: <strong>{mapData.length}</strong>
            </div>
        </div>
      </div>

    </div>
  );
}