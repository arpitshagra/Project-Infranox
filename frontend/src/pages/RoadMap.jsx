import { apiUrl } from '../api';
import React, { useState, useEffect } from 'react';
import { 
  MapContainer, 
  TileLayer, 
  Polyline, 
  Marker, 
  Popup, 
  useMapEvents,
  useMap
} from 'react-leaflet';
import L from 'leaflet';

// Modern clean minimal pin generators (pure HTML/CSS, zero generic icon clutter)
const createMarkerIcon = (bg, text, pulse = false) => L.divIcon({
  className: 'custom-leaflet-marker',
  html: `
    <div style="position: relative; display: flex; align-items: center; justify-content: center;">
      ${pulse ? `<div style="position: absolute; width: 34px; height: 34px; border-radius: 50%; background: ${bg}33; animation: ping 1.8s cubic-bezier(0, 0, 0.2, 1) infinite;"></div>` : ''}
      <div style="
        background: ${bg}; 
        color: white; 
        font-family: monospace; 
        font-weight: 700; 
        font-size: 11px; 
        width: 24px; 
        height: 24px; 
        border-radius: 50%; 
        display: flex; 
        align-items: center; 
        justify-content: center; 
        border: 2px solid white; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.25);
        cursor: pointer;
      ">${text}</div>
    </div>
  `,
  iconSize: [24, 24],
  iconAnchor: [12, 12]
});

const originMarker = createMarkerIcon('#059669', 'A', true);
const destMarker = createMarkerIcon('#dc2626', 'B', true);

const createPotholeMarker = (sev, id) => {
  const color = sev === 'Severe' ? '#ef4444' : (sev === 'Moderate' ? '#d97706' : '#10b981');
  return L.divIcon({
    className: 'pothole-hazard-marker',
    html: `
      <div style="
        background: ${color}; 
        color: white; 
        font-family: monospace; 
        font-weight: 700; 
        font-size: 10px; 
        padding: 2px 6px; 
        border-radius: 4px; 
        border: 1.5px solid white; 
        box-shadow: 0 2px 8px rgba(0,0,0,0.2); 
        white-space: nowrap;
      ">#${id}</div>
    `,
    iconSize: [28, 16],
    iconAnchor: [14, 8]
  });
};

function MapEventsHandler({ onMapClick }) {
  useMapEvents({
    click: (e) => {
      onMapClick(e.latlng.lat, e.latlng.lng);
    }
  });
  return null;
}

function MapViewController({ center, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, zoom || map.getZoom(), { duration: 1.2 });
    }
  }, [center, zoom, map]);
  return null;
}

export default function RoadMap() {
  const [roads, setRoads] = useState([]);
  const [clickOrigin, setClickOrigin] = useState(null);
  const [clickDest, setClickDest] = useState(null);
  const [clickStep, setClickStep] = useState('origin'); // 'origin' | 'dest' | 'done'
  const [routeResult, setRouteResult] = useState(null);
  const [isRouting, setIsRouting] = useState(false);
  const [mapStyle, setMapStyle] = useState('carto'); // 'carto' | 'osm' | 'satellite'
  const [searchQuery, setSearchQuery] = useState('');
  const [isGeocoding, setIsGeocoding] = useState(false);
  const [mapCenter, setMapCenter] = useState([28.6328, 77.2250]);
  const [showAddRoad, setShowAddRoad] = useState(false);

  // New corridor form
  const [roadName, setRoadName] = useState('');
  const [startAddr, setStartAddr] = useState('');
  const [endAddr, setEndAddr] = useState('');
  const [healthScore, setHealthScore] = useState(78);

  const fetchRoads = () => {
    fetch(apiUrl('/api/roads'))
      .then(r => r.json())
      .then(d => setRoads(d))
      .catch(err => console.log('Error fetching roads:', err));
  };

  useEffect(() => {
    fetchRoads();
  }, []);

  const handleMapClick = async (lat, lng) => {
    if (clickStep === 'origin') {
      try {
        const rev = await fetch(apiUrl(`/api/reverse-geocode?lat=${lat}&lon=${lng}`)).then(r => r.json());
        setClickOrigin({ lat, lon: lng, address: rev.address });
        setClickStep('dest');
      } catch {
        setClickOrigin({ lat, lon: lng, address: `${lat.toFixed(4)}, ${lng.toFixed(4)}` });
        setClickStep('dest');
      }
    } else if (clickStep === 'dest') {
      setIsRouting(true);
      try {
        const rev = await fetch(apiUrl(`/api/reverse-geocode?lat=${lat}&lon=${lng}`)).then(r => r.json());
        const dest = { lat, lon: lng, address: rev.address };
        setClickDest(dest);

        const res = await fetch(apiUrl(`/api/route?start_lat=${clickOrigin.lat}&start_lon=${clickOrigin.lon}&end_lat=${lat}&end_lon=${lng}`));
        const data = await res.json();
        setRouteResult(data);
        setClickStep('done');
      } catch (e) {
        console.error('Route calculation error:', e);
      } finally {
        setIsRouting(false);
      }
    } else if (clickStep === 'done') {
      setRouteResult(null);
      setClickDest(null);
      setClickOrigin({ lat, lon: lng, address: `${lat.toFixed(4)}, ${lng.toFixed(4)}` });
      setClickStep('dest');
    }
  };

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;
    setIsGeocoding(true);
    try {
      const res = await fetch(apiUrl(`/api/geocode?q=${encodeURIComponent(searchQuery)}`));
      const data = await res.json();
      if (res.ok && data.lat) {
        setMapCenter([data.lat, data.lon]);
        if (clickStep === 'origin') {
          setClickOrigin({ lat: data.lat, lon: data.lon, address: data.address });
          setClickStep('dest');
        } else if (clickStep === 'dest') {
          handleMapClick(data.lat, data.lon);
        }
      } else {
        alert('Could not locate address on OpenStreetMap.');
      }
    } catch {
      alert('Geocoding request failed.');
    } finally {
      setIsGeocoding(false);
    }
  };

  const handleQuickPreset = (origQuery, destQuery) => {
    setIsRouting(true);
    Promise.all([
      fetch(apiUrl(`/api/geocode?q=${encodeURIComponent(origQuery)}`)).then(r => r.json()),
      fetch(apiUrl(`/api/geocode?q=${encodeURIComponent(destQuery)}`)).then(r => r.json())
    ]).then(([orig, dest]) => {
      setClickOrigin(orig);
      setClickDest(dest);
      setMapCenter([orig.lat, orig.lon]);
      return fetch(apiUrl(`/api/route?start_lat=${orig.lat}&start_lon=${orig.lon}&end_lat=${dest.lat}&end_lon=${dest.lon}`))
        .then(r => r.json())
        .then(data => {
          setRouteResult(data);
          setClickStep('done');
        });
    }).catch(err => {
      console.error(err);
    }).finally(() => {
      setIsRouting(false);
    });
  };

  const handleReset = () => {
    setClickOrigin(null);
    setClickDest(null);
    setRouteResult(null);
    setClickStep('origin');
  };

  const handleCreateRoad = async (e) => {
    e.preventDefault();
    try {
      const res = await fetch('/api/roads', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          road_name: roadName,
          start_point: startAddr,
          end_point: endAddr,
          health_score: parseFloat(healthScore)
        })
      });
      if (res.ok) {
        setShowAddRoad(false);
        setRoadName('');
        setStartAddr('');
        setEndAddr('');
        fetchRoads();
      }
    } catch {
      alert('Failed to register road corridor.');
    }
  };

  const tilesMap = {
    carto: {
      url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
      attribution: '&copy; CartoDB &copy; OpenStreetMap'
    },
    osm: {
      url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
      attribution: '&copy; OpenStreetMap'
    },
    satellite: {
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      attribution: '&copy; Esri &copy; Earthstar Geographics'
    }
  };

  return (
    <div className="space-y-4 py-4">
      {/* Header & Controls Bar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-3 border-b border-slate-200 pb-4">
        <div>
          <h1 className="text-xl font-bold text-slate-900 tracking-tight">
            Pavement Quality GIS & Safe Navigation Matrix
          </h1>
          <p className="text-xs text-slate-500 mt-0.5">
            Color-coded highway condition inspection network with dynamic OSRM safe corridor navigation.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Basemap Switcher */}
          <div className="flex border border-slate-200 rounded-lg p-0.5 bg-white text-xs font-medium text-slate-600">
            <button
              onClick={() => setMapStyle('carto')}
              className={`px-2.5 py-1 rounded transition ${mapStyle === 'carto' ? 'bg-slate-900 text-white' : 'hover:text-slate-900'}`}
            >
              Voyager
            </button>
            <button
              onClick={() => setMapStyle('osm')}
              className={`px-2.5 py-1 rounded transition ${mapStyle === 'osm' ? 'bg-slate-900 text-white' : 'hover:text-slate-900'}`}
            >
              OSM Standard
            </button>
            <button
              onClick={() => setMapStyle('satellite')}
              className={`px-2.5 py-1 rounded transition ${mapStyle === 'satellite' ? 'bg-slate-900 text-white' : 'hover:text-slate-900'}`}
            >
              Satellite
            </button>
          </div>

          <button
            onClick={handleReset}
            className="text-xs px-3 py-1.5 border border-slate-200 bg-white hover:bg-slate-50 rounded-lg font-medium text-slate-700 transition"
          >
            Clear Pins
          </button>
          <button
            onClick={() => setShowAddRoad(true)}
            className="text-xs px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-medium transition"
          >
            + Register Corridor
          </button>
        </div>
      </div>

      {/* Main Map Canvas with Floating Interactive Overlays */}
      <div className="relative h-[680px] w-full rounded-xl overflow-hidden border border-slate-200 bg-slate-100 shadow-sm">
        {/* Floating Top Left Control Panel */}
        <div className="absolute top-4 left-4 z-[1000] w-80 max-w-[calc(100%-2rem)] bg-white/95 backdrop-blur border border-slate-200/90 rounded-xl p-3.5 shadow-lg space-y-3">
          {/* Geocoding Search */}
          <form onSubmit={handleSearch} className="flex gap-1.5">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search city, sector, or landmark..."
              className="flex-1 text-xs border border-slate-200 rounded px-2.5 py-1.5 bg-white focus:outline-none focus:ring-1 focus:ring-slate-900"
            />
            <button
              type="submit"
              disabled={isGeocoding}
              className="text-xs px-3 py-1.5 bg-slate-900 text-white rounded font-medium disabled:opacity-50"
            >
              {isGeocoding ? '...' : 'Find'}
            </button>
          </form>

          {/* Quick Presets */}
          <div className="space-y-1">
            <span className="text-[10px] font-mono text-slate-400 uppercase tracking-wider block">Sample Test Corridors:</span>
            <div className="flex flex-wrap gap-1">
              <button
                onClick={() => handleQuickPreset('Connaught Place, New Delhi', 'India Gate, New Delhi')}
                className="text-[11px] px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-slate-700"
              >
                Connaught Pl ➔ India Gate
              </button>
              <button
                onClick={() => handleQuickPreset('Sector 18 Noida', 'Akshardham Temple')}
                className="text-[11px] px-2 py-1 bg-slate-100 hover:bg-slate-200 rounded text-slate-700"
              >
                Noida ➔ Akshardham
              </button>
            </div>
          </div>

          {/* Pin Instruction Banner */}
          <div className="p-2.5 rounded-lg border bg-slate-50 text-[11px] text-slate-600 leading-tight space-y-1">
            {clickStep === 'origin' && (
              <p className="text-emerald-700 font-semibold">
                Click map to place <b>Point A (Origin)</b>
              </p>
            )}
            {clickStep === 'dest' && (
              <p className="text-rose-700 font-semibold">
                Origin set. Click map for <b>Point B (Destination)</b>
              </p>
            )}
            {clickStep === 'done' && (
              <p className="text-slate-800 font-semibold">
                Route calculated. Click anywhere to reset.
              </p>
            )}
            <p className="text-[10px] text-slate-400">
              Or use the search box above to pin landmarks directly.
            </p>
          </div>

          {/* Pavement Rating Color Legend */}
          <div className="pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-500 font-medium">
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-emerald-500" /> PCI &ge;70</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-amber-500" /> PCI 50-69</span>
            <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded-sm bg-rose-500" /> PCI &lt;50</span>
          </div>
        </div>

        {/* Floating Bottom Route Advisory (when calculated) */}
        {routeResult && (
          <div className="absolute bottom-4 left-4 right-4 z-[1000] bg-slate-900/95 backdrop-blur text-white border border-slate-800 rounded-xl p-4 shadow-2xl flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-left">
              <div>
                <span className="text-[10px] font-mono text-slate-400 block uppercase">Traverse Distance</span>
                <span className="text-base font-bold text-white">{routeResult.route?.distance_km} km</span>
              </div>
              <div>
                <span className="text-[10px] font-mono text-slate-400 block uppercase">Estimated Drive</span>
                <span className="text-base font-bold text-white">~{routeResult.route?.duration_min} mins</span>
              </div>
              <div>
                <span className="text-[10px] font-mono text-slate-400 block uppercase">Pavement Index (PCI)</span>
                <span className="text-base font-bold text-emerald-400">{routeResult.advisory?.route_pci}/100</span>
              </div>
              <div>
                <span className="text-[10px] font-mono text-slate-400 block uppercase">Hazard Assessment</span>
                <span className="text-xs font-bold text-amber-300 block mt-0.5">{routeResult.advisory?.safety_status}</span>
              </div>
            </div>

            <div className="max-w-md text-right border-t md:border-t-0 md:border-l border-slate-800 pt-2 md:pt-0 md:pl-4 text-xs text-slate-300">
              <span className="font-semibold text-white block mb-0.5">Civil Safety Notice:</span>
              <p className="text-[11px] text-slate-300 leading-snug">{routeResult.advisory?.advice}</p>
            </div>
          </div>
        )}

        {/* Leaflet Canvas */}
        <MapContainer
          center={mapCenter}
          zoom={12}
          scrollWheelZoom={true}
          className="h-full w-full"
        >
          <TileLayer
            attribution={tilesMap[mapStyle].attribution}
            url={tilesMap[mapStyle].url}
          />

          <MapViewController center={mapCenter} />
          <MapEventsHandler onMapClick={handleMapClick} />

          {/* Surveyed Road Corridors */}
          {roads.map((road, idx) => (
            <React.Fragment key={idx}>
              {road.coordinates && road.coordinates.length > 0 && (
                <Polyline
                  positions={road.coordinates}
                  pathOptions={{
                    color: road.color || '#10b981',
                    weight: 5,
                    opacity: 0.85
                  }}
                >
                  <Popup>
                    <div className="p-1 font-sans text-xs space-y-1">
                      <p className="font-bold text-slate-900 text-sm">{road.road_name}</p>
                      <p className="text-slate-600">From: {road.start_point}</p>
                      <p className="text-slate-600">To: {road.end_point}</p>
                      <div className="pt-1 border-t border-slate-100 flex justify-between">
                        <span>Pavement Health: <b>{road.health_score}/100</b></span>
                        <span className="font-semibold text-slate-700">{road.rating}</span>
                      </div>
                      <p className="text-slate-500">Urgency: {road.urgency}</p>
                      <p className="text-slate-500">Defects Logged: {road.potholes?.length || 0}</p>
                    </div>
                  </Popup>
                </Polyline>
              )}

              {/* Pothole Pins */}
              {road.potholes?.map((p, pIdx) => (
                <Marker
                  key={pIdx}
                  position={[p.lat, p.lon]}
                  icon={createPotholeMarker(p.severity, p.id)}
                >
                  <Popup>
                    <div className="p-1 font-sans text-xs space-y-1">
                      <p className="font-bold text-slate-900">Pothole #{p.id} [{p.severity}]</p>
                      <p className="text-slate-600">Road: {road.road_name}</p>
                      <p className="text-slate-600">Confidence: {p.conf}</p>
                      <p className="text-slate-600">Surface Area: {p.area} px²</p>
                      <p className="text-slate-400 text-[10px]">Lat: {p.lat.toFixed(5)}, Lon: {p.lon.toFixed(5)}</p>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </React.Fragment>
          ))}

          {/* Planned Driving Route */}
          {routeResult?.route?.coordinates && (
            <Polyline
              positions={routeResult.route.coordinates}
              pathOptions={{
                color: '#2563eb',
                weight: 5,
                dashArray: '6, 6',
                opacity: 0.95
              }}
            />
          )}

          {/* Origin Marker */}
          {clickOrigin && (
            <Marker position={[clickOrigin.lat, clickOrigin.lon]} icon={originMarker}>
              <Popup>
                <div className="text-xs p-1">
                  <b className="text-emerald-700">Point A (Origin)</b>
                  <p className="text-slate-600 mt-0.5">{clickOrigin.address}</p>
                </div>
              </Popup>
            </Marker>
          )}

          {/* Destination Marker */}
          {clickDest && (
            <Marker position={[clickDest.lat, clickDest.lon]} icon={destMarker}>
              <Popup>
                <div className="text-xs p-1">
                  <b className="text-rose-700">Point B (Destination)</b>
                  <p className="text-slate-600 mt-0.5">{clickDest.address}</p>
                </div>
              </Popup>
            </Marker>
          )}
        </MapContainer>
      </div>

      {/* Corridor Registration Modal */}
      {showAddRoad && (
        <div className="fixed inset-0 z-[2000] bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full p-6 shadow-xl border border-slate-200 space-y-4">
            <h3 className="text-base font-bold text-slate-900">Plot New Evaluated Corridor</h3>
            <form onSubmit={handleCreateRoad} className="space-y-3">
              <div>
                <label className="text-xs font-semibold text-slate-700">Corridor Title</label>
                <input
                  type="text"
                  required
                  value={roadName}
                  onChange={(e) => setRoadName(e.target.value)}
                  placeholder="e.g. Ring Road Bypass Corridor"
                  className="w-full text-xs border border-slate-200 rounded p-2 mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700">Start Address or Coordinates</label>
                <input
                  type="text"
                  required
                  value={startAddr}
                  onChange={(e) => setStartAddr(e.target.value)}
                  placeholder="e.g. Connaught Place, New Delhi"
                  className="w-full text-xs border border-slate-200 rounded p-2 mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700">End Address or Coordinates</label>
                <input
                  type="text"
                  required
                  value={endAddr}
                  onChange={(e) => setEndAddr(e.target.value)}
                  placeholder="e.g. India Gate, New Delhi"
                  className="w-full text-xs border border-slate-200 rounded p-2 mt-1"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700">
                  Pavement Health Score: {healthScore}/100
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={healthScore}
                  onChange={(e) => setHealthScore(e.target.value)}
                  className="w-full mt-1 accent-slate-900"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddRoad(false)}
                  className="px-3 py-1.5 text-xs text-slate-600 hover:bg-slate-100 rounded"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 text-xs font-semibold bg-slate-900 text-white rounded hover:bg-slate-800"
                >
                  Save to Network
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
