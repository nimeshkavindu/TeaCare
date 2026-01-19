'use client';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Props Definition
interface MapProps {
  data: any[];
  colorMap: { [key: string]: string }; // NEW: Receives dynamic colors
}

export default function EpidemiologyMap({ data, colorMap }: MapProps) {
  const center: [number, number] = [7.8731, 80.7718]; // Default Center (Sri Lanka)

  return (
    <MapContainer 
      center={center} 
      zoom={8} 
      style={{ height: '100%', width: '100%', borderRadius: '1rem', zIndex: 0 }}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
        url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
      />

      {data.map((point) => {
        // Fallback to grey if disease not in map
        const markerColor = colorMap[point.disease] || '#94a3b8'; 

        return (
          <CircleMarker
            key={point.id}
            center={[point.lat, point.lng]}
            pathOptions={{ 
              color: markerColor, 
              fillColor: markerColor, 
              fillOpacity: 0.7,
              weight: 1
            }}
            radius={6}
          >
            <Popup className="text-xs font-sans">
              <div className="p-1">
                <strong className="text-slate-700 block mb-1">{point.disease}</strong>
                <span className="text-slate-500 block">Conf: {(point.confidence * 100).toFixed(1)}%</span>
                <span className="text-slate-400 block text-[10px] mt-1">{point.date}</span>
                <span className="text-slate-400 block text-[10px]">{point.location}</span>
              </div>
            </Popup>
            <Tooltip direction="top" offset={[0, -5]} opacity={1}>
              <span className="font-bold text-xs">{point.disease}</span>
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}