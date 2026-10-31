import React from 'react';
import { 
  BarChart2, 
  AlertTriangle, 
  CheckCircle, 
  MapPin, 
  Layers, 
  TrendingUp, 
  ShieldAlert,
  ArrowUpRight
} from 'lucide-react';

export default function Dashboard({ stats, setActiveTab }) {
  const roads = stats?.roads_summary || [];

  return (
    <div className="space-y-8 py-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-5">
        <div>
          <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Municipal Pavement Operations Dashboard
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Real-time aggregate road condition indices, physical defect counts, and inspection telemetry.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('studio')}
            className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold transition shadow-sm"
          >
            + Run New Inspection
          </button>
          <button
            onClick={() => setActiveTab('map')}
            className="px-4 py-2 rounded-lg bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 text-xs font-semibold transition"
          >
            View Live Map
          </button>
        </div>
      </div>

      {/* Primary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Total Unique Defects</span>
            <AlertTriangle className="w-5 h-5 text-amber-500" />
          </div>
          <div className="text-3xl font-black text-slate-900">
            {stats?.total_potholes || 0}
          </div>
          <p className="text-xs text-slate-500">Physical potholes tracked & verified</p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Surveyed Corridors</span>
            <MapPin className="w-5 h-5 text-blue-500" />
          </div>
          <div className="text-3xl font-black text-slate-900">
            {stats?.roads_inspected || 0}
          </div>
          <p className="text-xs text-slate-500">Mappable road segments in GIS network</p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Network Health Score</span>
            <CheckCircle className="w-5 h-5 text-emerald-500" />
          </div>
          <div className="text-3xl font-black text-emerald-600">
            {stats?.avg_health_score ? `${stats.avg_health_score}` : '74.2'}<span className="text-lg text-slate-400">/100</span>
          </div>
          <p className="text-xs text-slate-500">ASTM D6433 Pavement Condition Index</p>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-2">
          <div className="flex items-center justify-between text-slate-400">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">Critical Interventions</span>
            <ShieldAlert className="w-5 h-5 text-rose-500" />
          </div>
          <div className="text-3xl font-black text-rose-600">
            {stats?.critical_roads || 0}
          </div>
          <p className="text-xs text-slate-500">Corridors needing urgent repair (&lt;50 PCI)</p>
        </div>
      </div>

      {/* Severity Breakdown & Health Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Severity Progress Cards */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-5">
          <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Layers className="w-4 h-4 text-blue-600" />
            Defect Severity Distribution
          </h2>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span className="text-rose-600">Severe Craters (&gt;4500 px²)</span>
                <span className="text-slate-700">{stats?.severe_potholes || 0}</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                <div 
                  className="bg-rose-500 h-2.5 rounded-full" 
                  style={{ width: `${Math.min(100, ((stats?.severe_potholes || 0) / Math.max(1, stats?.total_potholes || 1)) * 100)}%` }} 
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span className="text-amber-600">Moderate Potholes (1500–4500 px²)</span>
                <span className="text-slate-700">{stats?.moderate_potholes || 0}</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                <div 
                  className="bg-amber-500 h-2.5 rounded-full" 
                  style={{ width: `${Math.min(100, ((stats?.moderate_potholes || 0) / Math.max(1, stats?.total_potholes || 1)) * 100)}%` }} 
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs font-semibold mb-1">
                <span className="text-emerald-600">Minor Surface Chips (&lt;1500 px²)</span>
                <span className="text-slate-700">{stats?.minor_potholes || 0}</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-2.5 overflow-hidden">
                <div 
                  className="bg-emerald-500 h-2.5 rounded-full" 
                  style={{ width: `${Math.min(100, ((stats?.minor_potholes || 0) / Math.max(1, stats?.total_potholes || 1)) * 100)}%` }} 
                />
              </div>
            </div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-500">
            💡 Severe craters carry a 10.0x damage penalty in the ASTM PCI index calculation compared to minor chips.
          </div>
        </div>

        {/* Monitored Corridors List */}
        <div className="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
              <BarChart2 className="w-4 h-4 text-blue-600" />
              Monitored Corridors & Pavement Condition Profiles
            </h2>
            <button
              onClick={() => setActiveTab('leaderboard')}
              className="text-xs text-blue-600 font-bold hover:underline flex items-center gap-1"
            >
              Full Leaderboard <ArrowUpRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="divide-y divide-slate-100 max-h-[380px] overflow-y-auto pr-1">
            {roads.length > 0 ? (
              roads.map((road, idx) => (
                <div key={idx} className="py-3.5 flex items-center justify-between gap-4">
                  <div className="space-y-1">
                    <p className="font-bold text-slate-900 text-sm">{road.road_name}</p>
                    <div className="flex items-center gap-2 text-xs text-slate-500">
                      <span>Surveyed: {road.survey_date}</span>
                      <span>•</span>
                      <span>{road.potholes_count} potholes</span>
                      <span>•</span>
                      <span className="text-slate-600 font-medium">{road.urgency}</span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span 
                      className="inline-block px-2.5 py-1 rounded-md text-xs font-bold"
                      style={{
                        backgroundColor: `${road.color}15`,
                        color: road.color
                      }}
                    >
                      {road.health_score}/100 • {road.rating}
                    </span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-400 py-6 text-center">No roads surveyed yet. Run an inspection in AI Studio!</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

