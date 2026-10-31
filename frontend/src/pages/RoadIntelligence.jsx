import { apiUrl } from '../api';
import React, { useState, useEffect } from 'react';
import { 
  Trophy, 
  ArrowUpDown, 
  Download, 
  AlertTriangle, 
  CheckCircle, 
  Flame, 
  Clock, 
  Layers 
} from 'lucide-react';

export default function RoadIntelligence({ stats }) {
  const [roads, setRoads] = useState([]);
  const [sortBy, setSortBy] = useState('urgent'); // 'urgent' | 'best' | 'potholes'

  useEffect(() => {
    fetch(apiUrl('/api/roads'))
      .then(res => res.json())
      .then(data => setRoads(data))
      .catch(err => console.log('Error loading roads:', err));
  }, []);

  const sortedRoads = [...roads].sort((a, b) => {
    if (sortBy === 'urgent') return (a.health_score || 0) - (b.health_score || 0);
    if (sortBy === 'best') return (b.health_score || 0) - (a.health_score || 0);
    if (sortBy === 'potholes') return (b.potholes?.length || 0) - (a.potholes?.length || 0);
    return 0;
  });

  return (
    <div className="space-y-8 py-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Road Intelligence & Maintenance Priority Leaderboard
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Civil engineering assessment ranking based on ASTM D6433 Pavement Condition Index (PCI) and physical hazard severity.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex bg-slate-100 p-1 rounded-xl text-xs font-bold text-slate-600">
            <button
              onClick={() => setSortBy('urgent')}
              className={`px-3 py-1.5 rounded-lg transition ${sortBy === 'urgent' ? 'bg-white text-slate-900 shadow-sm' : ''}`}
            >
              Most Urgent Repair
            </button>
            <button
              onClick={() => setSortBy('best')}
              className={`px-3 py-1.5 rounded-lg transition ${sortBy === 'best' ? 'bg-white text-slate-900 shadow-sm' : ''}`}
            >
              Best Condition
            </button>
            <button
              onClick={() => setSortBy('potholes')}
              className={`px-3 py-1.5 rounded-lg transition ${sortBy === 'potholes' ? 'bg-white text-slate-900 shadow-sm' : ''}`}
            >
              Most Potholes
            </button>
          </div>

          <a
            href={apiUrl('/api/reports/roads.csv')}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-sm"
          >
            <Download className="w-3.5 h-3.5" />
            Export Leaderboard CSV
          </a>
        </div>
      </div>

      {/* Priority Focus Podium */}
      {sortedRoads.length >= 3 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Gold / Top Urgent */}
          <div className="bg-gradient-to-br from-rose-50 to-rose-100/60 p-6 rounded-2xl border border-rose-200 shadow-sm relative overflow-hidden">
            <span className="text-xs font-black text-rose-700 uppercase tracking-wider block">Priority #1 Emergency Intervention</span>
            <h3 className="text-lg font-black text-slate-900 mt-1">{sortedRoads[0]?.road_name}</h3>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-black text-rose-600">{sortedRoads[0]?.health_score}/100</span>
              <span className="text-xs font-bold text-rose-700">{sortedRoads[0]?.rating}</span>
            </div>
            <p className="text-xs text-slate-600 mt-2">
              Action: {sortedRoads[0]?.urgency} • {sortedRoads[0]?.potholes?.length || 0} potholes reported
            </p>
          </div>

          {/* Silver / Second Urgent */}
          <div className="bg-gradient-to-br from-amber-50 to-amber-100/60 p-6 rounded-2xl border border-amber-200 shadow-sm relative overflow-hidden">
            <span className="text-xs font-black text-amber-700 uppercase tracking-wider block">Priority #2 Scheduled Repair</span>
            <h3 className="text-lg font-black text-slate-900 mt-1">{sortedRoads[1]?.road_name}</h3>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-black text-amber-600">{sortedRoads[1]?.health_score}/100</span>
              <span className="text-xs font-bold text-amber-700">{sortedRoads[1]?.rating}</span>
            </div>
            <p className="text-xs text-slate-600 mt-2">
              Action: {sortedRoads[1]?.urgency} • {sortedRoads[1]?.potholes?.length || 0} potholes reported
            </p>
          </div>

          {/* Bronze / Third */}
          <div className="bg-gradient-to-br from-blue-50 to-blue-100/60 p-6 rounded-2xl border border-blue-200 shadow-sm relative overflow-hidden">
            <span className="text-xs font-black text-blue-700 uppercase tracking-wider block">Priority #3 Routine Monitoring</span>
            <h3 className="text-lg font-black text-slate-900 mt-1">{sortedRoads[2]?.road_name}</h3>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-3xl font-black text-blue-600">{sortedRoads[2]?.health_score}/100</span>
              <span className="text-xs font-bold text-blue-700">{sortedRoads[2]?.rating}</span>
            </div>
            <p className="text-xs text-slate-600 mt-2">
              Action: {sortedRoads[2]?.urgency} • {sortedRoads[2]?.potholes?.length || 0} potholes reported
            </p>
          </div>
        </div>
      )}

      {/* Full Leaderboard Table */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                <th className="py-4 px-6">Rank</th>
                <th className="py-4 px-6">Corridor Name</th>
                <th className="py-4 px-6">Health Score (PCI)</th>
                <th className="py-4 px-6">Condition Rating</th>
                <th className="py-4 px-6">Maintenance Action</th>
                <th className="py-4 px-6">Potholes Logged</th>
                <th className="py-4 px-6">Survey Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-xs">
              {sortedRoads.map((road, idx) => (
                <tr key={idx} className="hover:bg-slate-50/80 transition">
                  <td className="py-4 px-6 font-bold text-slate-400">
                    #{idx + 1}
                  </td>
                  <td className="py-4 px-6">
                    <span className="font-bold text-slate-900 block">{road.road_name}</span>
                    <span className="text-[11px] text-slate-400 font-normal">
                      {road.start_point} ➔ {road.end_point}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center gap-2">
                      <span className="font-extrabold text-slate-900 text-sm">
                        {road.health_score}/100
                      </span>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <span 
                      className="inline-block px-2.5 py-1 rounded-md text-[11px] font-bold"
                      style={{
                        backgroundColor: `${road.color || '#22C55E'}15`,
                        color: road.color || '#22C55E'
                      }}
                    >
                      {road.rating}
                    </span>
                  </td>
                  <td className="py-4 px-6 font-medium text-slate-600">
                    {road.urgency}
                  </td>
                  <td className="py-4 px-6 font-bold text-slate-700">
                    {road.potholes?.length || 0} defects
                  </td>
                  <td className="py-4 px-6 text-slate-400">
                    {road.survey_date || 'Recent'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

