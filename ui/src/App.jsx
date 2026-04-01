import React, { useState, useEffect } from 'react';
import { 
  Car, 
  ShieldAlert, 
  Navigation, 
  Activity, 
  CheckCircle2, 
  AlertTriangle,
  Info,
  MapPin
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const App = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Poll for data every 5 seconds
  useEffect(() => {
    const fetchData = async () => {
      try {
        // In a real environment, this would hit the FastAPI endpoint
        // For development/demo, we return a mock scene if the backend isn't up
        const response = await fetch('/api/system/process', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            camera_id: "CAM-01",
            timestamp: Date.now() / 1000,
            slots: Array.from({ length: 10 }, (_, i) => ({
              id: i,
              status: Math.random() > 0.5 ? "occupied" : "free",
              distance: i * 5.2
            })),
            hazards: Math.random() > 0.8 ? ["Oil Leak (Simulated)"] : [],
            confidence: 0.98
          })
        });
        
        if (!response.ok) throw new Error('API not reachable');
        const json = await response.json();
        setData(json);
        setError(null);
      } catch (err) {
        // Fail-safe mock for UI development
        setData({
          guidance: {
            message: "Operating in simulation mode. Backend offline.",
            best_slot: 2,
            violations: []
          },
          status: "simulated"
        });
      } finally {
        setLoading(false);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center min-h-screen">
      <motion.div 
        animate={{ rotate: 360 }}
        transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
      >
        <Activity size={48} color="#6366f1" />
      </motion.div>
    </div>
  );

  const { guidance } = data || {};
  const mockSlots = Array.from({ length: 10 }, (_, i) => ({
    id: i,
    status: (i === 1 || i === 4 || i === 7) ? "occupied" : "free",
    distance: i * 5.2
  }));

  return (
    <div className="flex-1 overflow-auto p-8 max-w-7xl mx-auto w-full">
      {/* Header with AI guidance */}
      <header className="mb-12">
        <div className="flex items-center gap-4 mb-4">
          <ShieldAlert className="text-primary" size={40} />
          <h1>ParkSight AI <span style={{fontSize: '1rem', fontWeight: 400, opacity: 0.6}}>v1.0 (Production)</span></h1>
        </div>

        <motion.div 
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass p-6 flex flex-col md:flex-row items-center gap-6"
          style={{ borderLeft: '4px solid var(--primary)' }}
        >
          <div className="p-4 rounded-full bg-indigo-500/20">
            <Navigation className="text-primary animate-pulse" size={32} />
          </div>
          <div className="flex-1">
            <h2 className="mb-1">AI Guidance</h2>
            <p className="text-lg text-slate-200">{guidance?.message || "Analyzing lot occupancy..."}</p>
          </div>
          {guidance?.best_slot !== -1 && (
            <div className="px-6 py-3 rounded-lg bg-emerald-500/20 border border-emerald-500/30 text-emerald-400">
              Best Slot: <strong className="text-xl">#{guidance?.best_slot}</strong>
            </div>
          )}
        </motion.div>
      </header>

      {/* Main Dashboard Grid */}
      <main>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="glass p-6 text-center">
            <h3 className="text-slate-400 text-sm mb-2 uppercase tracking-wider">Utilization</h3>
            <p className="text-3xl font-bold text-primary">40%</p>
          </div>
          <div className="glass p-6 text-center">
            <h3 className="text-slate-400 text-sm mb-2 uppercase tracking-wider">Peak Hour Status</h3>
            <p className="text-3xl font-bold text-emerald-400">OPTIMAL</p>
          </div>
          <div className="glass p-6 text-center">
            <h3 className="text-slate-400 text-sm mb-2 uppercase tracking-wider">Alerts (24h)</h3>
            <p className="text-3xl font-bold text-rose-400">2</p>
          </div>
        </div>

        <div className="flex items-center justify-between mb-6">
          <h2 className="flex items-center gap-2">
            <MapPin size={20} className="text-slate-400" />
            Live Map & Guidance
          </h2>
          <div className="flex gap-2">
            <span className="px-3 py-1 glass text-xs rounded-full border border-emerald-500/30 text-emerald-400">
              ● All Slots Active
            </span>
          </div>
        </div>

        {/* 3D-Like Parking Map with Guidance Overlay */}
        <div className="relative glass h-[400px] mb-8 overflow-hidden rounded-2xl group">
          <div className="absolute inset-0 bg-slate-900/50 flex items-center justify-center">
            {/* Simulated Grid Slots */}
            <div className="flex gap-4 p-8 items-end h-full w-full justify-around">
              {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9].map(i => (
                <div key={i} className={`w-16 h-32 rounded-lg border-2 border-dashed transition-all duration-500 
                  ${i === 0 ? 'bg-emerald-500/10 border-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.2)]' : 'bg-slate-800/40 border-slate-700'}`}>
                  <div className="text-[10px] text-slate-500 text-center mt-2 uppercase">SLOT {i}</div>
                </div>
              ))}
            </div>
            
            {/* AR Guidance Path Overlay */}
            <svg className="absolute inset-0 w-full h-full pointer-events-none">
              <defs>
                <linearGradient id="guidanceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
                  <stop offset="0%" stopColor="#10b981" stopOpacity="0.8" />
                  <stop offset="100%" stopColor="#10b981" stopOpacity="0.1" />
                </linearGradient>
              </defs>
              <path d="M 500,400 Q 400,300 50,150" fill="none" stroke="url(#guidanceGradient)" strokeWidth="8" strokeLinecap="round" className="animate-pulse" />
              <circle cx="50" cy="150" r="10" fill="#10b981" className="animate-ping" />
            </svg>

            <div className="absolute bottom-8 left-1/2 -translate-x-1/2 glass px-6 py-3 border-emerald-500/50">
              <p className="text-emerald-400 font-medium flex items-center gap-3">
                <ChevronRight size={18} />
                GUIDANCE: TURN LEFT 45° INTO SLOT 0
              </p>
            </div>
          </div>
        </div>

        <div className="dashboard-grid">
          <AnimatePresence>
            {mockSlots.map((slot) => (
              <motion.div
                key={slot.id}
                layout
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                className="glass glass-hover slot-card"
              >
                <div className="flex justify-between items-center">
                  <span className="text-sm font-semibold text-slate-400">SLOT #{slot.id}</span>
                  <span className={`px-2 py-1 rounded text-xs font-bold ${
                    slot.status === 'occupied' ? 'bg-rose-500/20 text-rose-400' : 'bg-emerald-500/20 text-emerald-400'
                  }`}>
                    {slot.status.toUpperCase()}
                  </span>
                </div>

                <div className="slot-visual">
                  {slot.status === 'occupied' ? (
                    <Car className="car-icon text-rose-400" size={64} />
                  ) : (
                    <div className="text-emerald-500/20 font-bold text-4xl">FREE</div>
                  )}
                  {guidance?.best_slot === slot.id && slot.status === 'free' && (
                    <div className="absolute top-2 right-2 bg-primary text-white p-1 rounded-full">
                      <CheckCircle2 size={16} />
                    </div>
                  )}
                </div>

                <div className="flex justify-between text-xs text-slate-500">
                  <span>Distance: {slot.distance}m</span>
                  <span>Edge: {data?.status === 'simulated' ? 'MOCK' : 'YOLO26-N'}</span>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      </main>

      {/* Incident Panel */}
      {guidance?.violations?.length > 0 && (
        <section className="mt-12">
          <h2 className="mb-4 text-rose-400 flex items-center gap-2">
            <AlertTriangle size={24} />
            Security Alerts
          </h2>
          <div className="grid gap-4">
            {guidance.violations.map((v, i) => (
              <div key={i} className="glass p-4 border-l-4 border-rose-500 flex items-center gap-4">
                <ShieldAlert className="text-rose-500" />
                <div>
                  <h4 className="font-bold text-rose-300">{v.type}</h4>
                  <p className="text-sm">{v.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Footer Info */}
      <footer className="mt-20 pt-8 border-t border-slate-800 flex justify-between text-slate-500 text-sm">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-primary animate-pulse" />
          <span>Camera Stream: CAM-01 (ACTIVE)</span>
        </div>
        <div>
          LLM Engine: LangGraph + Groq (Llama3-70B)
        </div>
      </footer>
    </div>
  );
};

export default App;
