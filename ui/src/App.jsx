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
  Timer,
  Banknote,
  Receipt,
  Wallet
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const App = () => {
  const [view, setView] = useState('live');
  const [selectedCamera, setSelectedCamera] = useState('CAM-01');
  const [searchQuery, setSearchQuery] = useState('');
  const [data, setData] = useState({ slots: [], hazards: [], summary: {} });
  const [stats, setStats] = useState(null);
  const [violations, setViolations] = useState([]);
  const [revenueSummary, setRevenueSummary] = useState({ total_revenue: 0, pending_revenue: 0, active_tickets: 0 });
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);

  // Signage Ticker Component
  const AnnouncementTicker = ({ message }) => (
    <div className="bg-primary/10 border-y border-primary/20 py-2 overflow-hidden whitespace-nowrap mb-6">
      <motion.div 
        animate={{ x: [1000, -1000] }}
        transition={{ repeat: Infinity, duration: 20, ease: "linear" }}
        className="inline-block"
      >
        <span className="text-xs font-black tracking-widest text-primary uppercase mr-20">
          广播 BROADCAST: {message || "System Operational - Optimal Guidance Active"}
        </span>
        <span className="text-xs font-black tracking-widest text-primary uppercase mr-20">
          PROCEED TO HIGHLIGHTED ZONE: {data.guidance?.best_slot !== undefined ? `SLOT #${data.guidance.best_slot}` : "SCANNING"}
        </span>
      </motion.div>
    </div>
  );

  // Spatial AR Overlay Component
  const SpatialView = ({ slots, guidance }) => (
    <div className="relative glass mb-8 aspect-video overflow-hidden border-indigo-500/30">
      <div className="absolute inset-0 bg-slate-900/40 backdrop-blur-[2px]" />
      <svg viewBox="0 0 1920 1080" className="absolute inset-0 w-full h-full drop-shadow-[0_0_15px_rgba(99,102,241,0.2)]">
        {/* Render Slot Geometries */}
        {slots?.map(slot => (
           <polygon
             key={slot.id}
             points={slot.polygon_points?.map(p => `${p[0]},${p[1]}`).join(' ')}
             fill={slot.id === guidance?.best_slot ? 'rgba(99,102,241,0.5)' : 
                   slot.status === 'occupied' ? 'rgba(239,68,68,0.3)' : 'rgba(99,102,241,0.15)'}
             stroke={slot.id === guidance?.best_slot ? '#6366f1' : 
                     slot.status === 'occupied' ? '#ef4444' : '#6366f1'}
             strokeWidth={slot.id === guidance?.best_slot ? '3' : '1.5'}
             style={{transition: 'all 0.7s ease'}}
           />
        ))}

        {/* Render Guidance Path */}
        {guidance?.path_points && (
          <motion.path
            d={`M ${guidance.path_points.map(p => `${p.x} ${p.y}`).join(' L ')}`}
            fill="none"
            stroke="url(#pathGradient)"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeDasharray="4 2"
            initial={{ strokeDashoffset: 100 }}
            animate={{ strokeDashoffset: 0 }}
            transition={{ repeat: Infinity, duration: 10, ease: "linear" }}
            className="drop-shadow-[0_0_8px_#6366f1]"
          />
        )}
        
        <defs>
          <linearGradient id="pathGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#6366f1" />
            <stop offset="100%" stopColor="#a855f7" />
          </linearGradient>
        </defs>
      </svg>
      
      <div className="absolute top-4 left-4 glass px-3 py-1.5 border-primary/20 flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
        <span className="text-[10px] font-black tracking-tighter uppercase">Spatial Perspective Active</span>
      </div>
    </div>
  );

  // Filter slots based on search query
  const filteredSlots = data.slots?.filter(slot => 
    !searchQuery || 
    slot.license_plate?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    slot.vehicle_id?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Fetch all data for the selected camera
  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [telRes, heatRes, violRes, revRes, tickRes] = await Promise.all([
          fetch(`/api/telemetry/summary?camera_id=${selectedCamera}`).then(r => r.json()),
          fetch(`/api/analytics/heatmap?camera_id=${selectedCamera}`).then(r => r.json()),
          fetch(`/api/analytics/violations?camera_id=${selectedCamera}`).then(r => r.json()),
          fetch(`/api/revenue/summary`).then(r => r.json()),
          fetch(`/api/revenue/tickets`).then(r => r.json())
        ]);

        if (telRes.length > 0) {
          setData(telRes[0].data);
        }
        setStats(heatRes);
        setViolations(violRes);
        setRevenueSummary(revRes);
        setTickets(tickRes);
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
          <h1 className="text-xl">ParkSight <span className="text-sm font-normal opacity-50">v2.0</span></h1>
        </div>

        <nav className="flex-1">
          <NavItem id="live" icon={LayoutDashboard} label="Live Map" />
          <NavItem id="analytics" icon={BarChart3} label="Analytics" />
          <NavItem id="revenue" icon={Banknote} label="Revenue Control" />
          <NavItem id="violations" icon={History} label="Violation Log" />
        </nav>

        <div className="pt-4 border-t border-slate-800">
          <NavItem id="settings" icon={Settings} label="System Config" />
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        <header className="flex justify-between items-center mb-10">
          <div className="flex-1">
            <h2 className="text-2xl font-bold">{view === 'live' ? 'Identity Control' : view.toUpperCase()}</h2>
            <div className="flex items-center gap-4 mt-1">
               <p className="text-slate italic">AI-driven license plate & identity orchestration</p>
               {view === 'live' && (
                 <div className="relative group">
                   <input 
                     type="text" 
                     placeholder="Search Plate / ID..." 
                     value={searchQuery}
                     onChange={(e) => setSearchQuery(e.target.value)}
                     className="bg-slate-900/80 border border-slate-700 rounded-lg px-3 py-1 text-xs focus:border-primary outline-none transition-all w-48"
                   />
                 </div>
               )}
            </div>
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
              {/* Spatial & Signage Layer */}
              <AnnouncementTicker message={data.broadcast} />
              
              <div className="mb-10">
                <SpatialView slots={data.slots} guidance={data.guidance} />
              </div>

              {/* Live Grid */}
              <div className="dashboard-grid">
                {filteredSlots?.length === 0 ? (
                  <div className="col-span-full py-20 text-center glass opacity-50">
                    <p className="italic">No vehicles matching "{searchQuery}" found on this camera.</p>
                  </div>
                ) : (
                  filteredSlots?.map(slot => (
                    <div key={slot.id} className={`glass glass-hover slot-card ${slot.id === data.guidance?.best_slot ? 'glass-active' : ''}`}>
                      <div className="flex justify-between items-center mb-2">
                         <div className="flex flex-col">
                           <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">Slot #{slot.id}</span>
                           {slot.vehicle_id && (
                             <motion.span 
                               initial={{ opacity: 0 }} animate={{ opacity: 1 }}
                               className="text-[9px] text-primary font-mono font-bold"
                             >
                               {slot.vehicle_id}
                             </motion.span>
                           )}
                         </div>
                         <div className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase ${
                           slot.status === 'occupied' ? 'bg-danger/20 text-danger' : 'bg-accent/20 text-accent'
                         }`}>
                           {slot.status}
                         </div>
                      </div>
                      
                      <div className="slot-visual relative overflow-hidden">
                        {slot.status === 'occupied' && (
                          <>
                            <div className="duration-badge"><Timer size={10} className="inline mr-1" /> {Math.round(slot.occupancy_duration)}s</div>
                            <Car className="text-white/10" size={64} />
                            
                            {/* License Plate Tag */}
                            {slot.license_plate && (
                              <motion.div 
                                initial={{ y: 20 }} animate={{ y: 0 }}
                                className="absolute bottom-2 left-1/2 -translate-x-1/2 bg-white text-black px-2 py-0.5 rounded border-b-2 border-slate-400 shadow-xl"
                              >
                                <span className="text-[10px] font-black tracking-tight">{slot.license_plate}</span>
                              </motion.div>
                            )}
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
                        <span>IDENTITY: {slot.license_plate ? 'VERIFIED' : 'SCANNING'}</span>
                      </div>
                    </div>
                  ))
                )}
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

          {view === 'revenue' && (
            <motion.div 
              key="revenue"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="space-y-8"
            >
              {/* Financial Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="glass p-6 bg-gradient-to-br from-emerald-500/10 to-slate-900/50 border-emerald-500/20">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-2 bg-emerald-500/20 rounded-lg text-emerald-400">
                      <Wallet size={24} />
                    </div>
                    <span className="text-[10px] font-black text-emerald-400 uppercase">Live Earnings</span>
                  </div>
                  <h3 className="text-4xl font-black text-white">₹{revenueSummary.total_revenue}</h3>
                  <p className="text-xs text-slate-500 mt-2 italic font-medium">Settled electronic transactions</p>
                </div>
                
                <div className="glass p-6 bg-gradient-to-br from-indigo-500/10 to-slate-900/50 border-indigo-500/20">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-2 bg-indigo-500/20 rounded-lg text-indigo-400">
                      <Receipt size={24} />
                    </div>
                    <span className="text-[10px] font-black text-indigo-400 uppercase">Pending Collection</span>
                  </div>
                  <h3 className="text-4xl font-black text-white">₹{revenueSummary.pending_revenue}</h3>
                  <p className="text-xs text-slate-500 mt-2 italic font-medium">Active sessions & unpaid tickets</p>
                </div>

                <div className="glass p-6 bg-gradient-to-br from-danger/10 to-slate-900/50 border-danger/20">
                  <div className="flex justify-between items-start mb-4">
                    <div className="p-2 bg-danger/20 rounded-lg text-danger">
                      <ShieldAlert size={24} />
                    </div>
                    <span className="text-[10px] font-black text-danger uppercase">Enforcement</span>
                  </div>
                  <h3 className="text-4xl font-black text-white">{revenueSummary.active_tickets}</h3>
                  <p className="text-xs text-slate-500 mt-2 italic font-medium">Active un-resolved tickets</p>
                </div>
              </div>

              {/* Ticket Registry */}
              <div className="glass p-8">
                <h3 className="text-sm font-black tracking-widest uppercase mb-8 flex items-center gap-3">
                  <Receipt className="text-primary" size={18} />
                  Automated Enforcement Registry (E-Challans)
                </h3>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="text-[10px] font-black text-slate-500 uppercase border-b border-white/5">
                        <th className="pb-4">Ticket ID</th>
                        <th className="pb-4">Vehicle ID</th>
                        <th className="pb-4">Violation Type</th>
                        <th className="pb-4">Timestamp</th>
                        <th className="pb-4">Fine Amount</th>
                        <th className="pb-4 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {tickets.length === 0 ? (
                        <tr>
                          <td colSpan="6" className="py-20 text-center text-slate-500 italic">No tickets generated in the current billing cycle.</td>
                        </tr>
                      ) : (
                        tickets.map(ticket => (
                          <tr key={ticket.id} className="text-xs group hover:bg-white/5 transition-all">
                            <td className="py-4 font-mono text-slate-400">#TK-{ticket.id}</td>
                            <td className="py-4 font-black">{ticket.vehicle_id}</td>
                            <td className="py-4 text-danger font-bold uppercase tracking-tighter">{ticket.violation}</td>
                            <td className="py-4 text-slate-500">{new Date(ticket.timestamp).toLocaleString()}</td>
                            <td className="py-4 font-mono text-emerald-400">₹{ticket.amount}</td>
                            <td className="py-4 text-right">
                              <span className={`px-2 py-1 rounded text-[9px] font-black ${
                                ticket.status === 'PAID' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-danger/20 text-danger'
                              }`}>
                                {ticket.status}
                              </span>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
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
