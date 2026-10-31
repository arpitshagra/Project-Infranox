import { apiUrl } from './api';
import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Dashboard from './pages/Dashboard';
import DetectionStudio from './pages/DetectionStudio';
import RoadMap from './pages/RoadMap';
import RoadIntelligence from './pages/RoadIntelligence';
import ComplaintPortal from './pages/ComplaintPortal';
import Reports from './pages/Reports';
import Login from './pages/Login';
import SarvamChatbot from './components/SarvamChatbot';

export default function App() {
  const [activeTab, setActiveTab] = useState('home');
  const [stats, setStats] = useState(null);
  const [apiOnline, setApiOnline] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [isCopilotOpen, setIsCopilotOpen] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);

  useEffect(() => {
    // Check local storage for persistent user session
    const savedUser = localStorage.getItem('infranox_user');
    if (savedUser) {
      try {
        setCurrentUser(JSON.parse(savedUser));
      } catch (e) {
        console.error(e);
      }
    }

    // Fetch initial stats
    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  const fetchStats = () => {
    fetch(apiUrl('/api/stats'))
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setApiOnline(true);
      })
      .catch(() => setApiOnline(false));
  };

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    setShowLoginModal(false);
  };

  const handleLogout = () => {
    localStorage.removeItem('infranox_user');
    setCurrentUser(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans text-slate-900 selection:bg-slate-900 selection:text-white">
      {/* Top Navbar */}
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        apiOnline={apiOnline}
        currentUser={currentUser}
        onOpenAuth={() => setShowLoginModal(true)}
        onLogout={handleLogout}
        onOpenCopilot={() => setIsCopilotOpen(true)}
      />

      {/* Main Page Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8">
        {showLoginModal ? (
          <Login 
            onLoginSuccess={handleLoginSuccess}
            onCancel={() => setShowLoginModal(false)}
          />
        ) : (
          <>
            {activeTab === 'home' && (
              <Home 
                stats={stats} 
                setActiveTab={setActiveTab} 
                onOpenAuth={() => setShowLoginModal(true)}
                currentUser={currentUser}
              />
            )}
            {activeTab === 'dashboard' && (
              <Dashboard stats={stats} setActiveTab={setActiveTab} />
            )}
            {activeTab === 'studio' && (
              <DetectionStudio onSurveyComplete={fetchStats} />
            )}
            {activeTab === 'map' && (
              <RoadMap />
            )}
            {activeTab === 'leaderboard' && (
              <RoadIntelligence stats={stats} />
            )}
            {activeTab === 'complaints' && (
              <ComplaintPortal />
            )}
            {activeTab === 'reports' && (
              <Reports />
            )}
          </>
        )}
      </main>

      {/* Sarvam AI Copilot Drawer */}
      <SarvamChatbot 
        isOpen={isCopilotOpen} 
        onClose={() => setIsCopilotOpen(false)} 
      />

      {/* Floating Copilot Launcher Button */}
      {!isCopilotOpen && (
        <button
          onClick={() => setIsCopilotOpen(true)}
          className="fixed bottom-6 right-6 z-40 bg-slate-900 hover:bg-slate-800 text-white shadow-xl px-4 py-2.5 rounded-full text-xs font-semibold tracking-wide border border-slate-700 flex items-center gap-2 transition hover:scale-105"
        >
          <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" />
          Sarvam AI Copilot
        </button>
      )}

      {/* Clean Technical Footer */}
      <footer className="mt-20 border-t border-slate-200 bg-white py-6 text-xs text-slate-500 font-mono">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div>
            <span className="font-bold text-slate-900">INFRANOX</span> • National Highway Road Intelligence Platform
          </div>
          <div className="flex items-center gap-3 text-slate-400 text-[11px]">
            <span>YOLOv8 Engine</span>
            <span>•</span>
            <span>ASTM D6433 PCI</span>
            <span>•</span>
            <span>Sarvam-105B Indic LLM</span>
            <span>•</span>
            <span>OpenStreetMap OSRM</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
