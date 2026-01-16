'use client';
import { MapContainer, TileLayer, CircleMarker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useEffect, useState } from 'react';

// Define Interface for Location Data
interface LocationReport {
  report_id: number;
  latitude: number;
  longitude: number;
  disease_name: string;
  confidence: string;
  timestamp: string;
}

export default function DiseaseMap() {
  const [reports, setReports] = useState<LocationReport[]>([]);

  useEffect(() => {
    // Fetch real location data from your backend
    fetch('http://localhost:8000/reports/locations')
      .then(res => res.json())
      .then(data => setReports(data))
      .catch(err => console.error("Map data fetch failed:", err));
  }, []);

  // Center of the Map (Default: Sri Lanka). Adjust [Lat, Lng] to your area.
  const center: [number, number] = [6.9271, 79.8612]; 

  return (
    <div className="h-full w-full rounded-2xl overflow-hidden shadow-sm border border-slate-200 z-0 relative">
      <MapContainer center={center} zoom={8} style={{ height: '100%', width: '100%' }}>
        {/* Dark Mode Map Tiles (Optional - looks professional) */}
        {/* You can switch to standard OSM if you prefer light mode */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
          url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
        />
        
        {reports.map((r) => (
          <CircleMarker 
            key={r.report_id}
            center={[r.latitude, r.longitude]}
            pathOptions={{ 
                color: r.disease_name.includes('Healthy') ? '#10b981' : '#ef4444',
                fillColor: r.disease_name.includes('Healthy') ? '#10b981' : '#ef4444',
                fillOpacity: 0.6,
                weight: 2
            }}
            radius={8}
          >
            <Popup>
              <div className="text-sm p-1">
                <p className="font-bold text-slate-800">{r.disease_name}</p>
                <p className="text-slate-500 text-xs">{r.timestamp}</p>
                <div className="mt-1 inline-block px-2 py-0.5 bg-slate-100 rounded text-xs font-mono">
                    {r.confidence}
                </div>
              </div>
            </Popup>
          </CircleMarker>
        ))}
      </MapContainer>
    </div>
  );
}