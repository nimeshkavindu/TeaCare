'use client';
import { MapContainer, TileLayer, CircleMarker, Popup, Tooltip, LayersControl } from 'react-leaflet';
import MarkerClusterGroup from 'react-leaflet-cluster';
import L from 'leaflet'; // <--- Import Leaflet for custom icons
import 'leaflet/dist/leaflet.css';

interface MapProps {
  data: any[];
  colorMap: { [key: string]: string };
  onSelectReport: (report: any) => void;
}

// --- CUSTOM CLUSTER ICON FUNCTION ---
// This creates a high-contrast "Dark Mode" circle for clusters
const createClusterCustomIcon = (cluster: any) => {
  return L.divIcon({
    html: `
      <div class="flex items-center justify-center w-full h-full bg-slate-900 text-white font-bold text-sm rounded-full border-2 border-white shadow-lg">
        ${cluster.getChildCount()}
      </div>
    `,
    className: 'custom-cluster-icon', // Leaflet requires a class name
    iconSize: L.point(40, 40, true),  // Size of the cluster icon (40x40px)
  });
};

export default function EpidemiologyMap({ data, colorMap, onSelectReport }: MapProps) {
  const center: [number, number] = [7.8731, 80.7718];

  return (
    <MapContainer 
      center={center} 
      zoom={8} 
      style={{ height: '100%', width: '100%', borderRadius: '1rem', zIndex: 0 }}
      scrollWheelZoom={true}
    >
      <LayersControl position="topright">
        <LayersControl.BaseLayer checked name="Voyager (Clean)">
          <TileLayer attribution='&copy; CartoDB' url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Satellite">
          <TileLayer attribution='&copy; Esri' url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}" />
        </LayersControl.BaseLayer>
        <LayersControl.BaseLayer name="Dark Matter">
          <TileLayer attribution='&copy; CartoDB' url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
        </LayersControl.BaseLayer>
      </LayersControl>

      {/* CLUSTER GROUP with Custom Icon */}
      <MarkerClusterGroup 
        chunkedLoading 
        spiderfyOnMaxZoom={true} 
        showCoverageOnHover={false} 
        maxClusterRadius={60}
        iconCreateFunction={createClusterCustomIcon} // <--- APPLY CUSTOM ICON HERE
      >
        {data.map((point) => {
          const markerColor = colorMap[point.disease] || '#94a3b8'; 

          return (
            <CircleMarker
              key={point.id}
              center={[point.lat, point.lng]}
              pathOptions={{ color: '#fff', weight: 1.5, fillColor: markerColor, fillOpacity: 0.8 }}
              radius={8}
              eventHandlers={{
                click: () => onSelectReport(point),
              }}
            >
              <Popup className="text-xs font-sans">
                <div className="p-1 min-w-[120px]">
                  <span className="inline-block px-2 py-0.5 rounded-full text-[10px] text-white font-bold mb-2" style={{ backgroundColor: markerColor }}>
                    {point.disease}
                  </span>
                  <div className="text-[10px] text-slate-600">
                    <p><strong>Conf:</strong> {(point.confidence * 100).toFixed(1)}%</p>
                    <p><strong>Loc:</strong> {point.location}</p>
                  </div>
                </div>
              </Popup>
              <Tooltip direction="top" offset={[0, -8]} opacity={1}>
                <span className="font-bold text-xs">{point.disease}</span>
              </Tooltip>
            </CircleMarker>
          );
        })}
      </MarkerClusterGroup>
    </MapContainer>
  );
}