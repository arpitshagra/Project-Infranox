import React from 'react';

export default function Navbar({ 
  activeTab, 
  setActiveTab, 
  apiOnline, 
  currentUser, 
  onOpenAuth, 
  onLogout,
  onOpenCopilot 
}) {
  const navItems = [
    { id: 'home', label: 'Overview' },
    { id: 'dashboard', label: 'Dashboard' },
    { id: 'studio', label: 'AI Studio' },
    { id: 'map', label: 'Live Map' },
    { id: 'leaderboard', label: 'Intelligence' },
    { id: 'complaints', label: 'Complaints' },
    { id: 'reports', label: 'Reports' },
  ];

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          {/* Logo & Platform Name */}
          <div 
            onClick={() => setActiveTab('home')}
            className="flex items-center gap-2.5 cursor-pointer"
          >
            <div className="w-7 h-7 rounded-lg bg-slate-900 flex items-center justify-center text-white font-mono font-bold text-xs">
              IN
            </div>
            <div>
              <span className="font-bold text-base tracking-tight text-slate-950 block leading-none">
                INFRANOX
              </span>
              <span className="text-[10px] text-slate-400 font-mono">Road Intelligence</span>
            </div>
          </div>

          {/* Clean Text-Only Desktop Navigation (Zero icon clutter) */}
          <nav className="hidden md:flex items-center gap-1">
            {navItems.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-slate-900 text-white'
                      : 'text-slate-600 hover:text-slate-950 hover:bg-slate-100'
                  }`}
                >
                  {item.label}
                </button>
              );
            })}
          </nav>

          {/* Right Action Utilities */}
          <div className="flex items-center gap-2.5">
            {/* Sarvam AI Copilot Launcher */}
            <button
              onClick={onOpenCopilot}
              className="flex items-center gap-1.5 text-xs font-semibold px-2.5 py-1.5 bg-blue-50 text-blue-800 border border-blue-200 rounded-md hover:bg-blue-100 transition"
              title="Open Sarvam Indic Highway Copilot"
            >
              <span className="w-1.5 h-1.5 rounded-full bg-blue-600" />
              Sarvam AI
            </button>

            {/* System Status Pill */}
            <div className="hidden sm:flex items-center gap-1.5 px-2 py-1 rounded bg-slate-50 border border-slate-200 text-[11px] font-mono text-slate-600">
              <span className={`w-1.5 h-1.5 rounded-full ${apiOnline ? 'bg-emerald-500' : 'bg-amber-500'}`} />
              {apiOnline ? 'YOLOv8 Online' : 'Connecting'}
            </div>

            {/* User Auth or Sign In */}
            {currentUser ? (
              <div className="flex items-center gap-2">
                <span className="text-xs font-medium text-slate-700 hidden lg:inline">
                  {currentUser.name}
                </span>
                <button
                  onClick={onLogout}
                  className="text-xs px-2.5 py-1 text-slate-500 hover:text-slate-800 border border-slate-200 rounded hover:bg-slate-50"
                >
                  Log Out
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenAuth}
                className="text-xs font-medium px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-md transition"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Mobile Horizontal Scroll Nav */}
      <div className="md:hidden flex overflow-x-auto border-t border-slate-100 px-2 py-1 gap-1 bg-slate-50">
        {navItems.map((item) => {
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              className={`px-3 py-1 rounded text-xs font-medium whitespace-nowrap ${
                isActive ? 'bg-slate-900 text-white' : 'text-slate-600'
              }`}
            >
              {item.label}
            </button>
          );
        })}
      </div>
    </header>
  );
}
