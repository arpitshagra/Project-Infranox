import React, { useState, useEffect } from 'react';
import { 
  FileSpreadsheet, 
  Download, 
  Database, 
  Layers, 
  FileText, 
  CheckCircle2,
  Search
} from 'lucide-react';

export default function Reports() {
  const [roads, setRoads] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    fetch('/api/roads')
      .then(res => res.json())
      .then(data => setRoads(data))
      .catch(err => console.log('Error loading roads:', err));
  }, []);

  const filteredRoads = roads.filter(r => 
    r.road_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.start_point?.toLowerCase().includes(searchTerm.toLowerCase()) ||
    r.end_point?.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Inspection Reports & GIS Data Registry
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Export structured CSV audit datasets, download physical pothole coordinates, and inspect GIS geometry.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <a
            href="/api/reports/potholes.csv"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-sm"
          >
            <Download className="w-4 h-4" />
            Download Pothole Catalog CSV
          </a>
          <a
            href="/api/reports/roads.csv"
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-bold transition shadow-sm"
          >
            <Download className="w-4 h-4" />
            Download Road Assessment CSV
          </a>
        </div>
      </div>

      {/* Dataset Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase text-slate-500">Persistent Pothole Catalog</span>
            <FileSpreadsheet className="w-5 h-5 text-blue-600" />
          </div>
          <p className="text-sm font-bold text-slate-800">potholes_catalog.csv</p>
          <p className="text-xs text-slate-500">
            Full track ID, first/last video timestamp, bounding box area, severity classification, and hit confidence.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase text-slate-500">Civil Road Assessment</span>
            <FileText className="w-5 h-5 text-emerald-600" />
          </div>
          <p className="text-sm font-bold text-slate-800">road_assessment.csv</p>
          <p className="text-xs text-slate-500">
            ASTM D6433 PCI health indices (0–100), defect density per minute, maintenance urgency levels, and corridor metadata.
          </p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase text-slate-500">GIS Community Database</span>
            <Database className="w-5 h-5 text-cyan-600" />
          </div>
          <p className="text-sm font-bold text-slate-800">community_road_network.json</p>
          <p className="text-xs text-slate-500">
            GeoJSON polylines, geocoded endpoints, color ratings, and latitude/longitude pothole pins.
          </p>
        </div>
      </div>

      {/* Corridor Search & Explorer */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h3 className="text-base font-bold text-slate-900">
            GIS Monitored Corridors Explorer ({filteredRoads.length} Segments)
          </h3>
          <div className="relative">
            <Search className="w-3.5 h-3.5 absolute left-3 top-3 text-slate-400" />
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search by road or landmark..."
              className="text-xs pl-8 pr-3 py-2 border border-slate-200 rounded-lg bg-slate-50 w-64"
            />
          </div>
        </div>

        <div className="divide-y divide-slate-100">
          {filteredRoads.map((road, idx) => (
            <div key={idx} className="py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="space-y-1">
                <p className="font-bold text-slate-900 text-sm">{road.road_name}</p>
                <p className="text-xs text-slate-500">
                  {road.start_point} ➔ {road.end_point}
                </p>
                <div className="flex items-center gap-3 text-[11px] text-slate-400">
                  <span>Coordinates: {road.coordinates?.length || 0} GPS nodes</span>
                  <span>•</span>
                  <span>Defects: {road.potholes?.length || 0} pins</span>
                  <span>•</span>
                  <span>Survey Date: {road.survey_date || 'N/A'}</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span 
                  className="px-3 py-1 rounded-md text-xs font-bold"
                  style={{
                    backgroundColor: `${road.color || '#22C55E'}15`,
                    color: road.color || '#22C55E'
                  }}
                >
                  Score: {road.health_score}/100 • {road.rating}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

