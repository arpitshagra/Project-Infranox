import React from 'react';

export default function Home({ stats, setActiveTab, onOpenAuth, currentUser }) {
  return (
    <div className="space-y-16 py-8">
      {/* Editorial Hero Section */}
      <section className="border-b border-slate-200 pb-16">
        <div className="max-w-4xl space-y-6">
          <div className="flex items-center gap-3">
            <span className="font-mono text-xs font-semibold text-slate-700 uppercase tracking-widest bg-slate-100 px-2.5 py-1 rounded">
              GovTech • ASTM D6433 Pavement Standard
            </span>
            <span className="text-xs text-slate-400 font-mono">Ver. 2.4.0 (Production)</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-bold tracking-tight text-slate-950 leading-[1.12]">
            Automated civil road defect surveillance and spatial hazard intelligence.
          </h1>

          <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl font-normal">
            INFRANOX processes moving vehicle dashcam video streams using fine-tuned YOLOv8 neural vision and multi-frame motion trackers to identify unique physical craters, score pavement condition, and warn highway commuters via live OpenStreetMap routing.
          </p>

          <div className="flex flex-wrap items-center gap-3 pt-2">
            <button
              onClick={() => setActiveTab('studio')}
              className="px-5 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-xs font-semibold tracking-wide transition shadow-sm"
            >
              Launch AI Detection Studio
            </button>
            <button
              onClick={() => setActiveTab('map')}
              className="px-5 py-2.5 bg-white border border-slate-200 hover:border-slate-400 text-slate-800 rounded-lg text-xs font-semibold transition"
            >
              Open Interactive GIS Map
            </button>
            {!currentUser && (
              <button
                onClick={onOpenAuth}
                className="px-5 py-2.5 text-slate-600 hover:text-slate-950 text-xs font-semibold hover:underline"
              >
                Officer Sign In &rarr;
              </button>
            )}
          </div>
        </div>

        {/* Live Network Metrics Row (Clean Technical Layout) */}
        <div className="mt-14 grid grid-cols-2 md:grid-cols-4 gap-6 pt-8 border-t border-slate-200">
          <div>
            <span className="font-mono text-[11px] uppercase text-slate-400 tracking-wider block">Logged Craters</span>
            <p className="text-3xl font-extrabold text-slate-950 mt-1 font-mono">
              {stats?.total_potholes || 0}
            </p>
            <span className="text-xs text-slate-500 mt-0.5 block">Unique verified coordinates</span>
          </div>

          <div>
            <span className="font-mono text-[11px] uppercase text-slate-400 tracking-wider block">Inspected Network</span>
            <p className="text-3xl font-extrabold text-slate-950 mt-1 font-mono">
              {stats?.roads_inspected || 0}
            </p>
            <span className="text-xs text-slate-500 mt-0.5 block">Monitored urban corridors</span>
          </div>

          <div>
            <span className="font-mono text-[11px] uppercase text-slate-400 tracking-wider block">Mean Pavement PCI</span>
            <p className="text-3xl font-extrabold text-emerald-700 mt-1 font-mono">
              {stats?.avg_health_score ? `${stats.avg_health_score}` : '74.2'}<span className="text-sm font-normal text-slate-400">/100</span>
            </p>
            <span className="text-xs text-slate-500 mt-0.5 block">ASTM D6433 Civil Health Index</span>
          </div>

          <div>
            <span className="font-mono text-[11px] uppercase text-slate-400 tracking-wider block">Hazard Priority</span>
            <p className="text-3xl font-extrabold text-rose-600 mt-1 font-mono">
              {stats?.critical_roads || 0}
            </p>
            <span className="text-xs text-slate-500 mt-0.5 block">Corridors requiring emergency intervention</span>
          </div>
        </div>
      </section>

      {/* Comparative Overview: Traditional vs INFRANOX */}
      <section className="space-y-6">
        <div>
          <span className="font-mono text-xs text-slate-400 uppercase tracking-widest block">System Comparison</span>
          <h2 className="text-2xl font-bold text-slate-950 tracking-tight mt-1">
            Reinventing municipal road quality audits
          </h2>
        </div>

        <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-2 divide-y md:divide-y-0 md:divide-x divide-slate-200">
            <div className="p-8 space-y-4 bg-slate-50/50">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider block font-mono">Legacy Methodology</span>
              <h3 className="text-base font-bold text-slate-900">Manual Walking & Eyeball Audits</h3>
              <ul className="space-y-2.5 text-xs text-slate-600 leading-relaxed">
                <li>• Subjective visual surveys take 4–6 weeks per municipal sector.</li>
                <li>• Duplicate reporting of the same pothole by multiple agencies.</li>
                <li>• Zero spatial routing or citizen alert capabilities.</li>
                <li>• Expensive specialized sensor vehicles ($80k+ hardware cost).</li>
              </ul>
            </div>

            <div className="p-8 space-y-4 bg-white">
              <span className="text-xs font-semibold text-emerald-700 uppercase tracking-wider block font-mono">INFRANOX Solution</span>
              <h3 className="text-base font-bold text-slate-900">Autonomous Neural Vision & GIS Pipeline</h3>
              <ul className="space-y-2.5 text-xs text-slate-700 leading-relaxed">
                <li>• <b>YOLOv8 Real-time Inference:</b> Processes standard 30–60 FPS dashcam footage at 120+ FPS.</li>
                <li>• <b>RoadPotholeTracker Algorithm:</b> Suppresses intra-frame duplicate bounding boxes and vehicle hood reflections.</li>
                <li>• <b>ASTM D6433 PCI Calculation:</b> Automatic scoring based on defect density and surface damage area (px²).</li>
                <li>• <b>Live OpenStreetMap Sync:</b> Synchronizes survey data to route commuters away from severe corridors.</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Structured Technical Specifications */}
      <section className="space-y-6">
        <div>
          <span className="font-mono text-xs text-slate-400 uppercase tracking-widest block">Architectural Matrix</span>
          <h2 className="text-2xl font-bold text-slate-950 tracking-tight mt-1">
            Engineered modular components
          </h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          <div className="p-6 rounded-xl border border-slate-200 bg-white space-y-2">
            <span className="text-xs font-mono font-semibold text-slate-500 uppercase">Module 01</span>
            <h3 className="font-bold text-slate-900 text-sm">Fine-Tuned YOLOv8 Core</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              11.1M parameter convolutional neural network trained on Indian highway surface fissures, rain puddles, and deep asphalt depressions.
            </p>
          </div>

          <div className="p-6 rounded-xl border border-slate-200 bg-white space-y-2">
            <span className="text-xs font-mono font-semibold text-slate-500 uppercase">Module 02</span>
            <h3 className="font-bold text-slate-900 text-sm">Spatial Tracking Engine</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Associates consecutive frame detections with forward vehicle velocity vectors. Closes tracks after hood exit and records confirmed physical hits.
            </p>
          </div>

          <div className="p-6 rounded-xl border border-slate-200 bg-white space-y-2">
            <span className="text-xs font-mono font-semibold text-slate-500 uppercase">Module 03</span>
            <h3 className="font-bold text-slate-900 text-sm">Sarvam AI Highway Copilot</h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              Integrated with Sarvam-105B Indic LLM to give commuters and engineers natural language query access to road telemetry in English and Hindi.
            </p>
          </div>
        </div>
      </section>

      {/* Call to Action Bar */}
      <section className="p-8 rounded-xl bg-slate-950 text-white flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
        <div>
          <h3 className="text-lg font-bold tracking-tight text-white">Ready to inspect municipal highway corridors?</h3>
          <p className="text-xs text-slate-400 mt-1">Upload road survey video or view the real-time live network map.</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setActiveTab('studio')}
            className="px-4 py-2 bg-white text-slate-950 rounded-lg text-xs font-bold hover:bg-slate-100 transition"
          >
            Start Video Survey
          </button>
          <button
            onClick={() => setActiveTab('complaints')}
            className="px-4 py-2 bg-slate-800 text-slate-200 rounded-lg text-xs font-medium hover:bg-slate-700 transition"
          >
            Citizen Grievance Portal
          </button>
        </div>
      </section>
    </div>
  );
}
