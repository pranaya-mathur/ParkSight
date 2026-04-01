import React, { useState, useEffect } from 'react';
import { 
  Car, 
  ShieldAlert, 
  Navigation, 
  Activity, 
  CheckCircle2, 
  AlertTriangle,
  LayoutDashboard,
  BarChart3,
  History,
  Settings,
  ChevronRight,
  Camera,
  Timer
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const App = () => {
  const [view, setView] = useState('live');
  const [selectedCamera, setSelectedCamera] = useState('CAM-01');
  const [data, setData] = useState({ slots: [], hazards: [], summary: {} });
  const [stats, setStats] = useState(null);
  const [violations, setViolations] = useState([]);
  const [loading, setLoading] = useState(true);

  // Fetch all data for the selected camera
  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [telRes, heatRes, violRes] = await Promise.all([
          fetch(`/api/telemetry/summary?camera_id=${selectedCamera}`).then(r => r.json()),
          fetch(`/api/analytics/heatmap?camera_id=${selectedCamera}`).then(r => r.json()),
          fetch(`/api/analytics/violations?camera_id=${selectedCamera}`).then(r => r.json())
        ]);

        if (telRes.length > 0) {
          setData(telRes[0].data);
        }
        setStats(heatRes);
        setViolations(violRes);
      } catch (err) {
        console.error("Fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
    const interval = setInterval(fetchAll, 5000);
    return () => clearInterval(interval);
  }, [selectedCamera]);

  const NavItem = ({ id, icon: Icon, label }) => (
    <div 
      onClick={() => setView(id)}
      className={`nav-item ${view === id ? 'active' : ''}`}
    >
      <Icon size={20} />
      <span>{label}</span>
      {view === id && <motion.div layoutId="nav-pill" className="ml-auto w-1 h-4 bg-primary rounded-full" />}
    </div>
  );

  return (
    <>
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="flex items-center gap-3 px-2 mb-4">
          <ShieldAlert className="text-primary" size={32} />
          <h1 className="text-xl">ParkSight <span className="text-sm font-normal opacity-50">v1.1</span></h1>
        </div>

        <nav className="flex-1">
          <NavItem id="live" icon={LayoutDashboard} label="Live Map" />
          <NavItem id="analytics" icon={BarChart3} label="Analytics" />
          <NavItem id="violations" icon={History} label="Violation Log" />
        </nav>

        <div className="pt-4 border-t border-slate-800">
          <NavItem id="settings" icon={Settings} label="System Config" />
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header className="flex justify-between items-center mb-10">
          <div>
            <h2 className="text-2xl font-bold">{view === 'live' ? 'Real-time Guidance' : view.toUpperCase()}</h2>
            <p className="text-slate italic">Precision occupancy & safety orchestration</p>
          </div>

          <div className="flex items-center gap-4">
            <div className="flex bg-slate-900/50 p-1 rounded-xl border border-slate-800">
              {['CAM-01', 'CAM-02'].map(cam => (
                <button
                  key={cam}
                  onClick={() => setSelectedCamera(cam)}
                  className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                    selectedCamera === cam ? 'bg-indigo-600 text-white shadow-lg' : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  {cam}
                </button>
              ))}
            </div>
            <div className="glass px-4 py-2 flex items-center gap-3 border-emerald-500/20">
              <div className="status-indicator status-active" />
              <span className="text-xs font-bold text-emerald-400 uppercase tracking-tighter">System Health: Optimal</span>
            </div>
          </div>
        </header>

        <AnimatePresence mode="wait">
          {view === 'live' && (
            <motion.div 
              key="live"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              {/* Guidance Banner */}
              <div className="glass p-6 mb-8 flex items-center gap-6 border-l-4 border-indigo-500">
                <div className="p-3 bg-indigo-500/10 rounded-xl text-primary">
                  <Navigation className="animate-pulse" size={28} />
                </div>
                <div className="flex-1">
                  <span className="text-[10px] uppercase tracking-[0.2em] text-slate-500 font-bold">AI Orchestrator</span>
                  <p className="text-lg font-medium">
                    {data.guidance?.instruction || "Scanning parking geometry for optimal paths..."}
                  </p>
                </div>
                {data.occupancy_duration > 0 && (
                  <div className="flex flex-col items-end">
                    <span className="text-[10px] text-slate-500 font-bold uppercase">Time in Scene</span>
                    <span className="text-xl font-mono text-primary">{Math.floor(data.occupancy_duration)}s</span>
                  </div>
                )}
              </div>

              {/* Live Grid */}
              <div className="dashboard-grid">
                {data.slots?.map(slot => (
                  <div key={slot.id} className={`glass glass-hover slot-card ${slot.id === data.guidance?.best_slot ? 'glass-active' : ''}`}>
                    <div className="flex justify-between items-center mb-2">
                       <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Slot #{slot.id}</span>
                       <div className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase ${
                         slot.status === 'occupied' ? 'bg-danger/20 text-danger' : 'bg-accent/20 text-accent'
                       }`}>
                         {slot.status}
                       </div>
                    </div>
                    
                    <div className="slot-visual">
                      {slot.status === 'occupied' && (
                        <>
                          <div className="duration-badge"><Timer size={10} className="inline mr-1" /> {Math.round(slot.occupancy_duration)}s</div>
                          <Car className="text-white/20" size={64} />
                        </>
                      )}
                      {slot.id === data.guidance?.best_slot && slot.status === 'free' && (
                        <motion.div 
                          animate={{ scale: [1, 1.2, 1] }}
                          transition={{ repeat: Infinity, duration: 2 }}
                          className="text-primary flex flex-col items-center gap-1"
                        >
                          <CheckCircle2 size={32} />
                          <span className="text-[10px] font-bold">RECOMMENDED</span>
                        </motion.div>
                      )}
                    </div>
                    
                    <div className="flex justify-between text-[10px] font-bold text-slate-600 mt-2">
                      <span>DIST: {slot.distance}m</span>
                      <span>PERSPECTIVE: VALID</span>
                    </div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {view === 'analytics' && (
            <motion.div 
              key="analytics"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="grid grid-cols-1 md:grid-cols-2 gap-8"
            >
              <div className="glass p-8">
                <h3 className="mb-6 flex items-center gap-2"><Activity size={20} className="text-primary" /> Occupancy Heatmap</h3>
                <div className="flex flex-col gap-4">
                  {stats?.slots?.map(s => (
                    <div key={s.slot_id} className="flex items-center gap-4">
                      <span className="w-12 text-xs font-bold text-slate-500">#{s.slot_id}</span>
                      <div className="flex-1 h-3 bg-slate-900 rounded-full overflow-hidden">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${s.utilization_percent}%` }}
                          className={`h-full ${s.utilization_percent > 70 ? 'bg-danger' : s.utilization_percent > 30 ? 'bg-primary' : 'bg-slate-700'}`}
                        />
                      </div>
                      <span className="text-xs font-mono">{s.utilization_percent}%</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="glass p-8 bg-gradient-to-br from-slate-900/50 to-indigo-900/10">
                <h3 className="mb-6 flex items-center gap-2"><Timer size={20} className="text-primary" /> Peak Hour Insights</h3>
                {stats?.error ? (
                  <p className="text-slate">No telemetry data found for {selectedCamera}</p>
                ) : (
                  <div className="space-y-6">
                    <div className="flex justify-between items-center p-4 rounded-xl bg-slate-900/40">
                      <span className="text-slate italic font-medium">Average Load</span>
                      <span className="text-2xl font-black text-primary">{Math.round((stats?.slots?.reduce((a,b)=>a+b.utilization_percent,0)/10) || 0)}%</span>
                    </div>
                    <div className="p-4 border-l-2 border-primary/20">
                      <p className="text-xs text-slate uppercase font-bold mb-1 tracking-widest text-primary">Recommendation</p>
                      <p className="text-sm">High utilization detected on center slots. Consider dynamic pricing or EV priority shifts.</p>
                    </div>
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {view === 'violations' && (
            <motion.div 
              key="violations"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
            >
              <div className="flex items-center justify-between mb-8">
                <h3 className="flex items-center gap-2 text-rose-400 font-bold uppercase tracking-widest text-sm">
                  <AlertTriangle size={18} /> Safety & Policy Incident Log
                </h3>
                <span className="glass px-3 py-1 text-[10px] font-bold border-rose-500/20 text-rose-400 uppercase">
                  Reporting Node: {selectedCamera}
                </span>
              </div>
              
              <div className="space-y-4">
                {violations?.total_incidents === 0 ? (
                  <div className="glass p-20 text-center flex flex-col items-center gap-4">
                    <CheckCircle2 size={48} className="text-accent opacity-20" />
                    <p className="text-slate italic">All clear. No safety violations or overstays detected.</p>
                  </div>
                ) : (
                  Object.entries(violations?.breakdown || {}).map(([type, count], i) => (
                    <div key={i} className="glass p-6 flex items-center gap-6 border-l-4 border-danger">
                      <div className="p-3 bg-danger/10 rounded-xl text-danger">
                        <AlertTriangle className="animate-pulse" size={24} />
                      </div>
                      <div className="flex-1">
                        <h4 className="font-bold text-slate-200">{type}</h4>
                        <p className="text-xs text-slate italic">Frequency detected: {count} instance(s) in last 500 samples</p>
                      </div>
                      <div className="flex gap-2">
                        <button className="px-3 py-1.5 rounded-lg bg-danger text-white text-[10px] font-bold shadow-lg shadow-danger/20">RESOLVE</button>
                        <button className="px-3 py-1.5 rounded-lg glass text-[10px] font-bold">DISMISS</button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Footer Persistence Indicator */}
        <footer className="mt-auto pt-10 flex justify-between items-center text-[10px] text-slate-600 font-bold uppercase tracking-widest">
           <div className="flex items-center gap-2">
             <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_8px_var(--primary)]" />
             <span>Telemetry Tunnel: {selectedCamera} @ REST v1.1</span>
           </div>
           <div>SQL Persistence: ACTIVE (parksight.db)</div>
        </footer>
      </main>
    </>
  );
};

export default App;
