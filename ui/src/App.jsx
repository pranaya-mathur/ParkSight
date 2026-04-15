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
  Wallet,
  FileText,
  CreditCard,
  Cpu,
  Zap,
  Globe,
  Crosshair
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
  const [billingSummary, setBillingSummary] = useState(null);
  const [invoices, setInvoices] = useState([]);
  const [invoiceDetail, setInvoiceDetail] = useState(null);
  const [activeSessions, setActiveSessions] = useState([]);
  const [ticketIdsInput, setTicketIdsInput] = useState('');
  const [payAmount, setPayAmount] = useState('');
  const [payMethod, setPayMethod] = useState('UPI');
  const [payRef, setPayRef] = useState('');
  const [sessionVehicle, setSessionVehicle] = useState('VEH-DEMO');
  const [sessionSlot, setSessionSlot] = useState('1');
  const [billingMsg, setBillingMsg] = useState('');
  const [loading, setLoading] = useState(true);
  const [authToken, setAuthToken] = useState(() => localStorage.getItem('parksight_token') || '');
  const [loginEmail, setLoginEmail] = useState('admin@parksight.local');
  const [loginPassword, setLoginPassword] = useState('');
  const [loginMsg, setLoginMsg] = useState('');
  const [calImageUrl, setCalImageUrl] = useState('');
  const [calSlots, setCalSlots] = useState([]);
  const [calDraft, setCalDraft] = useState([]);
  const [calHomography, setCalHomography] = useState([[1, 0, 0], [0, 1, 0], [0, 0, 1]]);
  const [calCameraId, setCalCameraId] = useState('CAM-01');
  const [calMsg, setCalMsg] = useState('');

  // Signage Ticker Component
  const AnnouncementTicker = ({ message }) => (
    <div className="glass px-6 py-3 mb-8 flex items-center gap-6 border-primary/20 overflow-hidden relative">
      <div className="flex items-center gap-2 text-primary font-black text-[10px] uppercase tracking-[0.2em] whitespace-nowrap border-r border-primary/20 pr-6">
        <Zap size={14} className="animate-pulse" />
        Live Broadcast
      </div>
      <div className="flex-1 overflow-hidden whitespace-nowrap">
        <motion.div 
          animate={{ x: [1000, -1000] }}
          transition={{ repeat: Infinity, duration: 25, ease: "linear" }}
          className="inline-block"
        >
          <span className="text-xs font-bold tracking-wider text-slate-300 uppercase mr-20">
            {message || "System Neural Link Active - Optimal Guidance Pathfinding Operational"}
          </span>
          <span className="text-xs font-black tracking-widest text-primary uppercase mr-20">
            PROCEED TO HIGHLIGHTED ZONE: {data.guidance?.best_slot !== undefined ? `SLOT #${data.guidance.best_slot}` : "INITIALIZING SEARCH"}
          </span>
        </motion.div>
      </div>
      <div className="absolute right-0 top-0 bottom-0 w-20 bg-gradient-to-l from-[#0f172a] to-transparent z-10" />
    </div>
  );

  // Spatial AR Overlay Component
  const SpatialView = ({ slots, guidance }) => (
    <div className="spatial-container mb-10 aspect-video overflow-hidden group relative">
      {/* Neural Matrix Background Layers */}
      <div className="absolute inset-0 bg-[#020617]" />
      <div className="grid-overlay opacity-20" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,rgba(99,102,241,0.1)_0%,transparent_70%)]" />
      
      {/* Dynamic Digital Twin Texture */}
      <div className="absolute inset-0 opacity-[0.03] pointer-events-none" style={{ backgroundImage: 'url("data:image/svg+xml,%3Csvg viewBox=\'0 0 200 200\' xmlns=\'http://www.w3.org/2000/svg\'%3E%3Cfilter id=\'noiseFilter\'%3E%3CfeTurbulence type=\'fractalNoise\' baseFrequency=\'0.65\' numOctaves=\'3\' stitchTiles=\'stitch\'/%3E%3C/filter%3E%3Crect width=\'100%25\' height=\'100%25\' filter=\'url(%23noiseFilter)\' /%3E%3C/svg%3E")' }} />
      
      <div className="scan-line" />
      
      {/* Viewport Meta */}
      <div className="absolute top-6 left-6 z-20 flex flex-col gap-1">
        <div className="flex items-center gap-2 bg-slate-950/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-primary/30">
          <div className="w-1.5 h-1.5 rounded-full bg-primary animate-ping" />
          <span className="text-[9px] font-black tracking-[0.15em] uppercase text-white">Spatial Matrix v4.0</span>
        </div>
        <span className="text-[8px] text-slate-500 font-bold uppercase tracking-widest ml-1">Node: {selectedCamera} // Neural Sync: Active</span>
      </div>

      <svg viewBox="0 280 1920 600" className="absolute inset-0 w-full h-full drop-shadow-[0_0_20px_rgba(99,102,241,0.15)]">
        <defs>
          <filter id="neon-glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="8" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
          <linearGradient id="pathGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--primary)" />
            <stop offset="100%" stopColor="var(--secondary)" />
          </linearGradient>
        </defs>

        {/* Render Slot Geometries */}
        {slots?.map(slot => (
           <motion.polygon
             key={slot.id}
             points={slot.polygon_points?.map(p => `${p[0]},${p[1]}`).join(' ')}
             initial={{ opacity: 0, scale: 0.95 }}
             animate={{ opacity: 1, scale: 1 }}
             fill={slot.id === guidance?.best_slot ? 'rgba(99, 102, 241, 0.4)' : 
                   slot.status === 'occupied' ? 'rgba(244, 63, 94, 0.25)' : 'rgba(6, 182, 212, 0.08)'}
             stroke={slot.id === guidance?.best_slot ? 'var(--primary)' : 
                     slot.status === 'occupied' ? 'var(--danger)' : 'var(--accent)'}
             strokeWidth={slot.id === guidance?.best_slot ? '6' : '3'}
             strokeDasharray={slot.status === 'free' ? '10 5' : 'none'}
             className={slot.id === guidance?.best_slot || slot.status === 'occupied' ? 'neon-path' : ''}
             style={{ transition: 'all 0.8s cubic-bezier(0.16, 1, 0.3, 1)' }}
           />
        ))}

        {/* Render Guidance Path */}
        {guidance?.path_points && (
          <motion.path
            d={`M ${guidance.path_points.map(p => `${p.x} ${p.y}`).join(' L ')}`}
            fill="none"
            stroke="url(#pathGradient)"
            strokeWidth="4"
            strokeLinecap="round"
            strokeDasharray="12 8"
            initial={{ strokeDashoffset: 200 }}
            animate={{ strokeDashoffset: 0 }}
            transition={{ repeat: Infinity, duration: 8, ease: "linear" }}
            filter="url(#neon-glow)"
          />
        )}
      </svg>
      
      <div className="absolute bottom-6 right-6 flex items-center gap-4">
        <div className="flex items-center gap-2 glass px-3 py-1.5 border-primary/20">
          <Globe size={12} className="text-primary" />
          <span className="text-[9px] font-bold text-slate-400">GEODESIC SYNC 1:1</span>
        </div>
      </div>
    </div>
  );

  // Filter slots based on search query
  const filteredSlots = data.slots?.filter(slot => 
    !searchQuery || 
    slot.license_plate?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    slot.vehicle_id?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getAuthHeaders = () => {
    const t = authToken || localStorage.getItem('parksight_token');
    return t ? { Authorization: `Bearer ${t}` } : {};
  };
  const apiFetch = (url, opts = {}) =>
    fetch(url, { ...opts, headers: { ...getAuthHeaders(), ...(opts.headers || {}) } });

  // Fetch all data for the selected camera
  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [telRes, heatRes, violRes, revRes, tickRes] = await Promise.all([
          apiFetch(`/api/telemetry/summary?camera_id=${selectedCamera}`).then(r => r.json()),
          apiFetch(`/api/analytics/heatmap?camera_id=${selectedCamera}`).then(r => r.json()),
          apiFetch(`/api/analytics/violations?camera_id=${selectedCamera}`).then(r => r.json()),
          apiFetch(`/api/revenue/summary`).then(r => r.json()),
          apiFetch(`/api/revenue/tickets`).then(r => r.json())
        ]);

        if (telRes.length > 0) {
          setData(telRes[0].data);
        }
        setStats(heatRes);
        setViolations(violRes);
        setRevenueSummary(revRes);
        setTickets(tickRes);
        if (revRes.billing_payments_total !== undefined) {
          setBillingSummary({
            payments_completed_total: revRes.billing_payments_total,
            accounts_receivable_open: revRes.billing_ar_open,
            invoice_paid_total: revRes.billing_invoice_paid_total,
            invoice_counts: revRes.billing_invoice_counts,
          });
        }
      } catch (err) {
        console.error("Fetch error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
    const interval = setInterval(fetchAll, 3000);
    return () => clearInterval(interval);
  }, [selectedCamera, authToken]);

  const refreshBilling = async () => {
    try {
      const [sum, inv, sess] = await Promise.all([
        apiFetch('/api/billing/summary').then(r => r.json()),
        apiFetch('/api/billing/invoices').then(r => r.json()),
        apiFetch('/api/billing/sessions').then(r => r.json()),
      ]);
      setBillingSummary(sum);
      setInvoices(inv);
      setActiveSessions(sess);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (view !== 'billing') return;
    refreshBilling();
    const t = setInterval(refreshBilling, 4000);
    return () => clearInterval(t);
  }, [view]);

  const loadInvoiceDetail = async (id) => {
    const r = await apiFetch(`/api/billing/invoices/${id}`);
    if (r.ok) setInvoiceDetail(await r.json());
  };

  const submitPayment = async () => {
    if (!invoiceDetail || !payAmount) return;
    setBillingMsg('');
    const r = await apiFetch(`/api/billing/invoices/${invoiceDetail.id}/payments`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        amount: parseFloat(payAmount),
        method: payMethod,
        reference: payRef || null,
      }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
      setBillingMsg(j.detail || 'Payment failed');
      return;
    }
    setInvoiceDetail(j.invoice);
    setPayAmount('');
    setPayRef('');
    refreshBilling();
  };

  const createInvoiceFromTickets = async () => {
    setBillingMsg('');
    const ids = ticketIdsInput.split(/[\s,]+/).map((x) => parseInt(x, 10)).filter((n) => !Number.isNaN(n));
    if (!ids.length) {
      setBillingMsg('Enter ticket IDs (comma-separated)');
      return;
    }
    const r = await apiFetch('/api/billing/invoices/from-tickets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ticket_ids: ids }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
      setBillingMsg(typeof j.detail === 'string' ? j.detail : JSON.stringify(j.detail || j));
      return;
    }
    setTicketIdsInput('');
    setInvoiceDetail(j);
    refreshBilling();
  };

  const startParkingSession = async () => {
    setBillingMsg('');
    const r = await apiFetch('/api/billing/sessions/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        vehicle_id: sessionVehicle,
        slot_id: parseInt(sessionSlot, 10) || 0,
      }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
      setBillingMsg(j.detail || 'Failed');
      return;
    }
    setBillingMsg(`Session #${j.id} started`);
    refreshBilling();
  };

  const closeParkingSession = async (sessionId) => {
    setBillingMsg('');
    const r = await apiFetch(`/api/billing/sessions/${sessionId}/close`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({}),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
      setBillingMsg(typeof j.detail === 'string' ? j.detail : 'Close failed');
      return;
    }
    setInvoiceDetail(j);
    refreshBilling();
  };

  const submitLogin = async () => {
    setLoginMsg('');
    const r = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: loginEmail, password: loginPassword }),
    });
    const j = await r.json().catch(() => ({}));
    if (!r.ok) {
      setLoginMsg(typeof j.detail === 'string' ? j.detail : 'Login failed');
      return;
    }
    localStorage.setItem('parksight_token', j.access_token);
    setAuthToken(j.access_token);
    setLoginMsg('Signed in');
  };

  const logout = () => {
    localStorage.removeItem('parksight_token');
    setAuthToken('');
    setLoginMsg('');
  };

  const onCalImgClick = (e) => {
    const el = e.currentTarget;
    const rect = el.getBoundingClientRect();
    const scaleX = el.naturalWidth / rect.width || 1;
    const scaleY = el.naturalHeight / rect.height || 1;
    const x = Math.round((e.clientX - rect.left) * scaleX);
    const y = Math.round((e.clientY - rect.top) * scaleY);
    setCalDraft((d) => [...d, [x, y]]);
  };

  const saveCalibration = async () => {
    setCalMsg('');
    const body = {
      camera_id: calCameraId,
      homography: calHomography,
      slots: calSlots.map((s) => ({
        id: s.id,
        polygon: s.polygon,
        distance: s.distance ?? s.id + 1,
      })),
    };
    const r = await apiFetch('/api/calibration/slot-config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const j = await r.json().catch(() => ({}));
    setCalMsg(!r.ok ? (typeof j.detail === 'string' ? j.detail : 'Save failed') : `Saved (${j.path || 'ok'})`);
  };

  const NavItem = ({ id, icon: Icon, label }) => (
    <div 
      onClick={() => setView(id)}
      className={`nav-item ${view === id ? 'active' : ''}`}
    >
      <Icon size={18} />
      <span>{label}</span>
      {view === id && <motion.div layoutId="nav-pill" className="ml-auto w-1 h-5 bg-primary rounded-full shadow-[0_0_8px_var(--primary)]" />}
    </div>
  );

  return (
    <>
      <aside className="sidebar">
        <div className="flex items-center gap-3 px-3 mb-10">
          <div className="p-2 bg-primary/10 rounded-xl border border-primary/20">
            <ShieldAlert className="text-primary" size={24} />
          </div>
          <div>
            <h1 className="text-lg">ParkSight</h1>
            <p className="text-[10px] font-black uppercase tracking-widest text-slate-500">Spatial Intelligence</p>
          </div>
        </div>

        <nav className="flex-1">
          <NavItem id="live" icon={LayoutDashboard} label="Neural Live Map" />
          <NavItem id="analytics" icon={BarChart3} label="Space Analytics" />
          <NavItem id="revenue" icon={Banknote} label="Revenue Hub" />
          <NavItem id="billing" icon={FileText} label="Billing & AR" />
          <NavItem id="violations" icon={History} label="Enforcement Log" />
          <NavItem id="calibration" icon={Crosshair} label="Calibration" />
        </nav>

        <div className="pt-6 border-t border-white/5">
          <NavItem id="settings" icon={Settings} label="Global Config" />
          <div className="mt-4 glass p-4 border-primary/10">
            <div className="flex items-center gap-2 mb-2">
              <Cpu size={12} className="text-accent" />
              <span className="text-[10px] font-black uppercase text-slate-300">Edge Processing</span>
            </div>
            <div className="h-1 bg-slate-900 rounded-full overflow-hidden">
              <motion.div 
                animate={{ width: ['20%', '65%', '40%'] }}
                transition={{ repeat: Infinity, duration: 5 }}
                className="h-full bg-accent" 
              />
            </div>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="flex justify-between items-center mb-10">
          <div>
            <div className="flex items-center gap-2 text-[10px] font-black uppercase tracking-[0.2em] text-primary mb-1">
              <Navigation size={12} />
              Enterprise Console / {view}
            </div>
            <h2 className="text-3xl font-black">{view === 'live' ? 'Spatial Viewport' : view.replace(/-/g, ' ').toUpperCase()}</h2>
          </div>

          <div className="flex items-center gap-6">
            <div className="relative">
               <input 
                 type="text" 
                 placeholder="Search Vehicle ID..." 
                 value={searchQuery}
                 onChange={(e) => setSearchQuery(e.target.value)}
                 className="bg-slate-950/50 border border-white/10 rounded-xl px-4 py-2 text-xs focus:border-primary outline-none transition-all w-64 backdrop-blur-md"
               />
            </div>
            <div className="flex bg-slate-950/50 p-1 rounded-xl border border-white/10 backdrop-blur-md">
              {['CAM-01', 'CAM-02'].map(cam => (
                <button
                  key={cam}
                  onClick={() => setSelectedCamera(cam)}
                  className={`px-6 py-2 rounded-lg text-xs font-bold transition-all ${
                    selectedCamera === cam ? 'bg-primary text-white shadow-lg shadow-primary/20' : 'text-slate-500 hover:text-slate-300'
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
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
            >
              <AnnouncementTicker message={data.broadcast} />
              
              <SpatialView slots={data.slots} guidance={data.guidance} />

              {/* Metrics Panel */}
              <div className="grid grid-cols-4 gap-4 mb-10">
                <div className="glass p-4 border-primary/20 flex flex-col justify-center items-center relative overflow-hidden group">
                  <div className="absolute inset-0 bg-primary/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1 z-10">Total Sectors</span>
                  <span className="text-3xl font-black text-white z-10">{data.slots?.length || 0}</span>
                </div>
                <div className="glass p-4 border-danger/20 flex flex-col justify-center items-center relative overflow-hidden group">
                   <div className="absolute inset-0 bg-danger/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-danger mb-1 z-10">Occupied</span>
                  <span className="text-3xl font-black text-white z-10">{data.slots?.filter(s => s.status === 'occupied').length || 0}</span>
                </div>
                <div className="glass p-4 border-success/20 flex flex-col justify-center items-center relative overflow-hidden group">
                  <div className="absolute inset-0 bg-success/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-success mb-1 z-10">Available Flux</span>
                  <span className="text-3xl font-black text-white z-10">{data.slots?.filter(s => s.status === 'free').length || 0}</span>
                </div>
                <div className="glass p-4 border-warning/20 flex flex-col justify-center items-center relative overflow-hidden group">
                   <div className="absolute inset-0 bg-warning/10 opacity-0 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-warning mb-1 z-10">Reserved Priority</span>
                  <span className="text-3xl font-black text-white z-10">{data.slots?.filter(s => s.status === 'reserved').length || 0}</span>
                </div>
              </div>

              <div className="dashboard-grid">
                {filteredSlots?.length === 0 ? (
                  <div className="col-span-full py-24 text-center glass border-dashed border-white/5">
                    <AlertTriangle size={32} className="mx-auto text-slate-700 mb-4" />
                    <p className="text-slate-500 italic text-sm">No spatial signatures matching "{searchQuery}" detected.</p>
                  </div>
                ) : (
                  filteredSlots?.map(slot => (
                    <motion.div 
                      layout
                      key={slot.id} 
                      className={`glass glass-hover slot-card ${slot.id === data.guidance?.best_slot ? 'border-primary/50 bg-primary/5' : ''}`}
                    >
                      <div className="flex justify-between items-start mb-4">
                         <div>
                           <span className="text-[9px] font-black text-slate-500 uppercase tracking-[0.2em]">Matrix Sector</span>
                           <h4 className="text-xl font-black text-white">#SLOT-{slot.id}</h4>
                         </div>
                         <div className={`px-3 py-1 rounded-full text-[8px] font-black uppercase tracking-widest ${
                           slot.status === 'occupied' ? 'bg-danger/10 text-danger border border-danger/20' : 'bg-success/10 text-success border border-success/20'
                         }`}>
                           {slot.status}
                         </div>
                      </div>
                      
                      <div className="slot-visual relative overflow-hidden group">
                        {slot.status === 'occupied' ? (
                          <>
                            <div className="duration-badge bg-slate-950/80 backdrop-blur-sm">
                              <Timer size={10} className="inline mr-1" /> {Math.round(slot.occupancy_duration)}s
                            </div>
                            <Car className="text-white/5 group-hover:text-white/10 transition-colors" size={80} />
                            
                            {/* License Plate Identity Card */}
                            {slot.license_plate && (
                              <motion.div 
                                initial={{ y: 30 }} animate={{ y: 0 }}
                                className="absolute bottom-3 left-3 right-3 bg-white text-black p-2 rounded-lg shadow-2xl flex items-center justify-between"
                              >
                                <span className="text-[10px] font-black tracking-tight">{slot.license_plate}</span>
                                <div className="px-1.5 py-0.5 bg-black/10 rounded text-[7px] font-black">RE-ID VERIFIED</div>
                              </motion.div>
                            )}
                            {!slot.license_plate && (
                              <div className="absolute bottom-3 flex items-center gap-2">
                                <div className="w-2 h-2 rounded-full bg-warning animate-pulse" />
                                <span className="text-[9px] font-bold text-warning">SCANNING IDENTITY...</span>
                              </div>
                            )}
                          </>
                        ) : (
                          <div className="flex flex-col items-center gap-2 opacity-30 group-hover:opacity-60 transition-opacity">
                            <Zap size={32} />
                            <span className="text-[8px] font-black uppercase tracking-widest">Available Flux</span>
                          </div>
                        )}
                        
                        {slot.id === data.guidance?.best_slot && slot.status === 'free' && (
                          <motion.div 
                            animate={{ scale: [1, 1.1, 1], opacity: [0.7, 1, 0.7] }}
                            transition={{ repeat: Infinity, duration: 3 }}
                            className="absolute inset-0 bg-primary/10 flex flex-col items-center justify-center gap-2 border-2 border-primary/40 rounded-xl"
                          >
                            <div className="p-2 bg-primary rounded-full shadow-[0_0_20px_var(--primary)]">
                              <CheckCircle2 size={24} className="text-white" />
                            </div>
                            <span className="text-[10px] font-black text-primary tracking-widest">RECOMMENDED</span>
                          </motion.div>
                        )}
                      </div>
                      
                      <div className="flex justify-between items-center text-[10px] font-bold mt-4 pt-4 border-t border-white/5">
                        <div className="flex flex-col">
                           <span className="text-slate-600 uppercase text-[8px]">Distance</span>
                           <span className="text-slate-300">{slot.distance}m</span>
                        </div>
                        <div className="flex flex-col items-end">
                           <span className="text-slate-600 uppercase text-[8px]">Vehicle Hash</span>
                           <span className="text-primary font-mono">{slot.vehicle_id ? slot.vehicle_id.substring(0,8) : 'N/A'}</span>
                        </div>
                      </div>
                    </motion.div>
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
              <div className="glass p-10">
                <div className="flex items-center justify-between mb-10">
                   <h3 className="flex items-center gap-3 font-bold uppercase tracking-widest text-sm">
                     <Activity size={20} className="text-primary" /> Sector Load Heatmap
                   </h3>
                   <span className="text-[10px] font-black text-slate-500">REALTIME TELEMETRY</span>
                </div>
                <div className="space-y-6">
                  {stats?.slots?.map(s => (
                    <div key={s.slot_id} className="group">
                      <div className="flex justify-between mb-2">
                        <span className="text-xs font-black text-slate-400 group-hover:text-primary transition-colors">MATRIX SECTOR #{s.slot_id}</span>
                        <span className="text-xs font-mono text-slate-200">{s.utilization_percent}%</span>
                      </div>
                      <div className="h-2 bg-slate-950 rounded-full overflow-hidden border border-white/5">
                        <motion.div 
                          initial={{ width: 0 }}
                          animate={{ width: `${s.utilization_percent}%` }}
                          transition={{ duration: 1.5, ease: "easeOut" }}
                          className={`h-full relative ${
                            s.utilization_percent > 75 ? 'bg-danger' : 
                            s.utilization_percent > 35 ? 'bg-primary' : 'bg-slate-700'
                          }`}
                        >
                           <div className="absolute inset-0 bg-white/20 animate-pulse" />
                        </motion.div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="glass p-10 flex flex-col justify-between relative overflow-hidden">
                <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 blur-[100px] -mr-32 -mt-32" />
                <div>
                   <h3 className="mb-10 flex items-center gap-3 font-bold uppercase tracking-widest text-sm">
                     <Timer size={20} className="text-primary" /> Peak Prediction Engine
                   </h3>
                   {stats?.error ? (
                     <div className="py-20 text-center opacity-30 italic">Syncing neural data...</div>
                   ) : (
                     <div className="space-y-8">
                       <div className="flex justify-between items-center p-6 rounded-2xl bg-slate-950/60 border border-white/5">
                         <div>
                           <p className="text-[10px] font-black text-slate-500 uppercase mb-1">Average Matrix Load</p>
                           <p className="text-sm font-bold">Current System Saturation</p>
                         </div>
                         <span className="text-5xl font-black text-primary drop-shadow-[0_0_15px_var(--primary-glow)]">
                           {Math.round((stats?.slots?.reduce((a,b)=>a+b.utilization_percent,0)/10) || 0)}%
                         </span>
                       </div>
                       <div className="p-6 border-l-4 border-primary bg-primary/5 rounded-r-2xl">
                         <p className="text-[10px] text-primary uppercase font-black mb-2 tracking-[0.2em]">Neural Recommendation</p>
                         <p className="text-sm leading-relaxed text-slate-300">
                           High spatial saturation detected in central sectors. Recommend dynamic slot reservation premiums and priority routing for EV fleet.
                         </p>
                       </div>
                     </div>
                   )}
                </div>
                <div className="mt-10 flex items-center justify-between text-[10px] font-black text-slate-500 uppercase tracking-widest">
                  <span>Logic Processor: ACTIVE</span>
                  <span>v1.0.4-STABLE</span>
                </div>
              </div>
            </motion.div>
          )}

          {view === 'revenue' && (
            <motion.div 
              key="revenue"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              className="space-y-8"
            >
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {[
                  { label: 'Settled Capital', val: `₹${revenueSummary.total_revenue}`, icon: Wallet, color: 'text-success', bg: 'bg-success/5', border: 'border-success/20' },
                  { label: 'Floating Assets', val: `₹${revenueSummary.pending_revenue}`, icon: Receipt, color: 'text-primary', bg: 'bg-primary/5', border: 'border-primary/20' },
                  { label: 'Risk Enforcement', val: revenueSummary.active_tickets, icon: ShieldAlert, color: 'text-danger', bg: 'bg-danger/5', border: 'border-danger/20' }
                ].map((card, i) => (
                  <div key={i} className={`glass p-8 ${card.bg} ${card.border} group hover:border-white/20 transition-all`}>
                    <div className="flex justify-between items-start mb-6">
                      <div className={`p-4 rounded-2xl ${card.bg.replace('/5', '/10')} ${card.color}`}>
                        <card.icon size={28} />
                      </div>
                      <span className={`text-[10px] font-black uppercase tracking-widest ${card.color}`}>{card.label}</span>
                    </div>
                    <h3 className="text-5xl font-black text-white group-hover:scale-105 transition-transform origin-left">{card.val}</h3>
                    <p className="text-[10px] text-slate-500 mt-4 italic font-bold uppercase tracking-widest">Global Settle: OK</p>
                  </div>
                ))}
              </div>

              {billingSummary && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-[10px] font-bold uppercase tracking-widest text-slate-500">
                  <div className="glass p-4 border border-white/5">
                    Collected (payments ledger):{' '}
                    <span className="text-success">₹{Number(billingSummary.payments_completed_total || 0).toFixed(2)}</span>
                  </div>
                  <div className="glass p-4 border border-white/5">
                    Open AR (invoices):{' '}
                    <span className="text-primary">₹{Number(billingSummary.accounts_receivable_open || 0).toFixed(2)}</span>
                  </div>
                  <div className="glass p-4 border border-white/5">
                    Invoices paid (face):{' '}
                    <span className="text-slate-200">₹{Number(billingSummary.invoice_paid_total || 0).toFixed(2)}</span>
                  </div>
                </div>
              )}

              <div className="glass p-10">
                <div className="flex items-center justify-between mb-10">
                  <h3 className="text-sm font-black tracking-[0.25em] uppercase flex items-center gap-3">
                    <Receipt className="text-primary" size={20} /> Automated Ledger Enforcement
                  </h3>
                  <button className="px-5 py-2 rounded-full glass border-primary/20 text-[10px] font-black text-primary uppercase hover:bg-primary/10 transition-all">Export Report .PDF</button>
                </div>
                
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead>
                      <tr className="text-[10px] font-black text-slate-600 uppercase border-b border-white/5">
                        <th className="pb-6">Ledger ID</th>
                        <th className="pb-6">Signature</th>
                        <th className="pb-6">Incident Type</th>
                        <th className="pb-6">Global Sync</th>
                        <th className="pb-6">Quantum Fine</th>
                        <th className="pb-6 text-right">Settlement</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {tickets.length === 0 ? (
                        <tr>
                          <td colSpan="6" className="py-24 text-center text-slate-600 italic">No automated enforcement incidents logged.</td>
                        </tr>
                      ) : (
                        tickets.map(ticket => (
                          <tr key={ticket.id} className="text-xs group hover:bg-white/5 transition-all">
                            <td className="py-5 font-mono text-slate-500">TX-{ticket.id}</td>
                            <td className="py-5 font-black text-slate-200">{ticket.vehicle_id}</td>
                            <td className="py-5">
                               <span className="px-2 py-1 rounded bg-danger/10 text-danger text-[9px] font-black uppercase tracking-tight">
                                 {ticket.violation}
                               </span>
                            </td>
                            <td className="py-5 text-slate-500 font-medium">{new Date(ticket.timestamp).toLocaleString()}</td>
                            <td className="py-5 font-black text-success">₹{ticket.amount}</td>
                            <td className="py-5 text-right">
                              <span className={`px-3 py-1.5 rounded-lg text-[9px] font-black tracking-widest ${
                                ticket.status === 'PAID' ? 'bg-success/20 text-success' : 'bg-danger/20 text-danger'
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

          {view === 'billing' && (
            <motion.div
              key="billing"
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-8 max-w-6xl mx-auto"
            >
              <div className="flex flex-wrap gap-4 justify-between items-end">
                <div>
                  <h3 className="text-sm font-black tracking-[0.25em] uppercase flex items-center gap-3 text-primary">
                    <FileText size={20} /> Billing & accounts receivable
                  </h3>
                  <p className="text-xs text-slate-500 mt-2 font-bold uppercase tracking-widest">
                    GST invoices (9% CGST + 9% SGST), payments, metered parking
                  </p>
                </div>
                <button
                  type="button"
                  onClick={refreshBilling}
                  className="px-5 py-2 rounded-full glass border-primary/30 text-[10px] font-black text-primary uppercase"
                >
                  Refresh
                </button>
              </div>

              {billingMsg && (
                <div className="text-xs text-danger font-bold bg-danger/10 border border-danger/30 rounded-xl px-4 py-3">
                  {billingMsg}
                </div>
              )}

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass p-8 space-y-4">
                  <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-500">Parking session</h4>
                  <div className="flex flex-wrap gap-3">
                    <input
                      className="flex-1 min-w-[140px] bg-slate-950/80 border border-white/10 rounded-lg px-3 py-2 text-sm"
                      value={sessionVehicle}
                      onChange={(e) => setSessionVehicle(e.target.value)}
                      placeholder="vehicle_id"
                    />
                    <input
                      className="w-24 bg-slate-950/80 border border-white/10 rounded-lg px-3 py-2 text-sm"
                      value={sessionSlot}
                      onChange={(e) => setSessionSlot(e.target.value)}
                      placeholder="slot"
                    />
                    <button
                      type="button"
                      onClick={startParkingSession}
                      className="px-4 py-2 rounded-lg bg-primary text-white text-[10px] font-black uppercase"
                    >
                      Start
                    </button>
                  </div>
                  <div className="space-y-2 max-h-40 overflow-y-auto">
                    {activeSessions.length === 0 ? (
                      <p className="text-xs text-slate-600 italic">No active sessions</p>
                    ) : (
                      activeSessions.map((s) => (
                        <div key={s.id} className="flex justify-between items-center text-xs border border-white/5 rounded-lg px-3 py-2">
                          <span className="font-mono text-slate-400">#{s.id}</span>
                          <span className="text-slate-200">{s.vehicle_id}</span>
                          <span className="text-slate-500">slot {s.slot_id}</span>
                          <button
                            type="button"
                            onClick={() => closeParkingSession(s.id)}
                            className="text-[10px] font-black uppercase text-accent"
                          >
                            Close & bill
                          </button>
                        </div>
                      ))
                    )}
                  </div>
                </div>

                <div className="glass p-8 space-y-4">
                  <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-500">Invoice from tickets</h4>
                  <p className="text-[10px] text-slate-600">Same vehicle only. Unpaid tickets only.</p>
                  <input
                    className="w-full bg-slate-950/80 border border-white/10 rounded-lg px-3 py-2 text-sm font-mono"
                    value={ticketIdsInput}
                    onChange={(e) => setTicketIdsInput(e.target.value)}
                    placeholder="e.g. 1, 2, 3"
                  />
                  <button
                    type="button"
                    onClick={createInvoiceFromTickets}
                    className="px-4 py-2 rounded-lg border border-primary/40 text-primary text-[10px] font-black uppercase"
                  >
                    Create invoice
                  </button>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="glass p-8 overflow-x-auto">
                  <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-4">Invoices</h4>
                  <table className="w-full text-left text-xs">
                    <thead>
                      <tr className="text-[10px] text-slate-600 uppercase border-b border-white/5">
                        <th className="pb-3">#</th>
                        <th className="pb-3">Vehicle</th>
                        <th className="pb-3">Status</th>
                        <th className="pb-3 text-right">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                      {invoices.length === 0 ? (
                        <tr>
                          <td colSpan={4} className="py-8 text-center text-slate-600 italic">
                            No invoices yet
                          </td>
                        </tr>
                      ) : (
                        invoices.map((inv) => (
                          <tr
                            key={inv.id}
                            className={`cursor-pointer hover:bg-white/5 ${invoiceDetail?.id === inv.id ? 'bg-primary/10' : ''}`}
                            onClick={() => loadInvoiceDetail(inv.id)}
                          >
                            <td className="py-3 font-mono text-slate-500">{inv.number}</td>
                            <td className="py-3 font-bold text-slate-200">{inv.vehicle_id}</td>
                            <td className="py-3">
                              <span className="px-2 py-0.5 rounded bg-white/5 text-[9px] font-black">{inv.status}</span>
                            </td>
                            <td className="py-3 text-right font-mono">₹{inv.total?.toFixed(2)}</td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>

                <div className="glass p-8 space-y-4">
                  <h4 className="text-[10px] font-black uppercase tracking-widest text-slate-500 flex items-center gap-2">
                    <CreditCard size={14} /> Invoice detail & payment
                  </h4>
                  {!invoiceDetail ? (
                    <p className="text-xs text-slate-600 italic">Select an invoice</p>
                  ) : (
                    <>
                      <div className="text-sm font-black text-white">{invoiceDetail.number}</div>
                      <div className="text-[10px] text-slate-500 space-y-1">
                        <div>
                          Subtotal ₹{invoiceDetail.subtotal?.toFixed(2)} + CGST ₹{invoiceDetail.cgst_amount?.toFixed(2)} + SGST ₹
                          {invoiceDetail.sgst_amount?.toFixed(2)}
                        </div>
                        <div className="text-slate-300">
                          Total ₹{invoiceDetail.total?.toFixed(2)} · Paid ₹{invoiceDetail.amount_paid?.toFixed(2)} · Balance ₹
                          {invoiceDetail.balance?.toFixed(2)}
                        </div>
                      </div>
                      <ul className="text-[10px] text-slate-400 space-y-1 max-h-28 overflow-y-auto border border-white/5 rounded-lg p-3">
                        {invoiceDetail.lines?.map((ln) => (
                          <li key={ln.id}>
                            {ln.description} — ₹{ln.amount?.toFixed(2)}
                          </li>
                        ))}
                      </ul>
                      {invoiceDetail.status !== 'PAID' && invoiceDetail.status !== 'VOID' && (
                        <div className="flex flex-wrap gap-2 items-end pt-2">
                          <input
                            type="number"
                            className="w-28 bg-slate-950/80 border border-white/10 rounded-lg px-2 py-2 text-sm"
                            placeholder="Amount"
                            value={payAmount}
                            onChange={(e) => setPayAmount(e.target.value)}
                          />
                          <select
                            className="bg-slate-950/80 border border-white/10 rounded-lg px-2 py-2 text-xs"
                            value={payMethod}
                            onChange={(e) => setPayMethod(e.target.value)}
                          >
                            <option value="UPI">UPI</option>
                            <option value="CARD">Card</option>
                            <option value="CASH">Cash</option>
                            <option value="BANK_TRANSFER">Bank</option>
                          </select>
                          <input
                            className="flex-1 min-w-[120px] bg-slate-950/80 border border-white/10 rounded-lg px-2 py-2 text-xs"
                            placeholder="Reference / UTR"
                            value={payRef}
                            onChange={(e) => setPayRef(e.target.value)}
                          />
                          <button
                            type="button"
                            onClick={submitPayment}
                            className="px-4 py-2 rounded-lg bg-success text-slate-950 text-[10px] font-black uppercase"
                          >
                            Record payment
                          </button>
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </motion.div>
          )}

          {view === 'settings' && (
            <motion.div key="settings" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-xl mx-auto glass p-8 border border-white/10">
              <h3 className="text-sm font-black uppercase tracking-widest text-primary mb-6">API sign-in</h3>
              <p className="text-xs text-slate-500 mb-6">When <code className="text-primary">PARKSIGHT_REQUIRE_AUTH=1</code>, paste a JWT here or sign in as the seeded admin (defaults in README).</p>
              <div className="space-y-4">
                <input className="w-full bg-slate-950/80 border border-white/10 rounded-lg px-3 py-2 text-sm" placeholder="Email" value={loginEmail} onChange={(e) => setLoginEmail(e.target.value)} />
                <input type="password" className="w-full bg-slate-950/80 border border-white/10 rounded-lg px-3 py-2 text-sm" placeholder="Password" value={loginPassword} onChange={(e) => setLoginPassword(e.target.value)} />
                <div className="flex gap-3">
                  <button type="button" onClick={submitLogin} className="px-4 py-2 rounded-lg bg-primary text-white text-xs font-black uppercase">Sign in</button>
                  <button type="button" onClick={logout} className="px-4 py-2 rounded-lg border border-white/10 text-xs font-bold">Clear token</button>
                </div>
                {loginMsg && <p className="text-xs text-slate-400">{loginMsg}</p>}
                {authToken && <p className="text-[10px] text-slate-600 break-all">Bearer stored ({authToken.slice(0, 24)}…)</p>}
              </div>
            </motion.div>
          )}

          {view === 'calibration' && (
            <motion.div key="calibration" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="max-w-4xl mx-auto space-y-8">
              <div className="glass p-6 border border-white/10">
                <h3 className="text-sm font-black uppercase tracking-widest text-primary mb-2">Slot calibration wizard</h3>
                <p className="text-xs text-slate-500 mb-4">Upload a reference frame, click to trace each slot polygon, then add the slot. Requires admin JWT when auth is enabled.</p>
                <input type="file" accept="image/*" className="text-xs mb-4" onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) setCalImageUrl(URL.createObjectURL(f));
                }} />
                <div className="relative inline-block max-w-full border border-white/10 rounded-lg overflow-hidden bg-slate-950">
                  {calImageUrl && (
                    <img src={calImageUrl} alt="calibration" className="max-h-[480px] w-auto cursor-crosshair" onClick={onCalImgClick} />
                  )}
                </div>
                <p className="text-[10px] text-slate-500 mt-2">Draft points: {calDraft.length} — click image to add corners along one slot outline.</p>
                <div className="flex flex-wrap gap-2 mt-4">
                  <button type="button" className="px-3 py-2 rounded-lg bg-slate-800 text-xs font-bold" onClick={() => setCalDraft([])}>Clear draft</button>
                  <button type="button" className="px-3 py-2 rounded-lg bg-primary text-white text-xs font-black uppercase" onClick={() => {
                    if (calDraft.length < 3) { setCalMsg('Need at least 3 points'); return; }
                    const id = calSlots.length;
                    setCalSlots((s) => [...s, { id, polygon: [...calDraft], distance: id + 1 }]);
                    setCalDraft([]);
                    setCalMsg(`Slot ${id} added`);
                  }}>Add slot from draft</button>
                </div>
                <div className="mt-6 grid gap-3 md:grid-cols-2">
                  <label className="text-xs font-bold text-slate-400">Camera ID
                    <input className="mt-1 w-full bg-slate-950/80 border border-white/10 rounded-lg px-3 py-2 text-sm" value={calCameraId} onChange={(e) => setCalCameraId(e.target.value)} />
                  </label>
                </div>
                <p className="text-[10px] text-slate-500 mt-4">Homography defaults to identity; use API <code className="text-primary">POST /calibration/homography</code> for four-point warp then paste JSON here if needed.</p>
                <pre className="text-[10px] bg-slate-950 p-3 rounded-lg overflow-auto max-h-32 mt-2">{JSON.stringify(calHomography)}</pre>
                <div className="flex gap-2 mt-4">
                  <button type="button" onClick={saveCalibration} className="px-4 py-2 rounded-lg bg-success text-slate-950 text-xs font-black uppercase">Save to edge config</button>
                </div>
                {calMsg && <p className="text-xs mt-3 text-slate-400">{calMsg}</p>}
                <p className="text-[10px] text-slate-600 mt-4">Slots queued: {calSlots.length}</p>
              </div>
            </motion.div>
          )}

          {view === 'violations' && (
            <motion.div 
              key="violations"
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              className="max-w-5xl mx-auto"
            >
              <div className="flex items-center justify-between mb-12">
                <div>
                  <h3 className="flex items-center gap-3 text-danger font-black uppercase tracking-[0.3em] text-sm mb-1">
                    <AlertTriangle size={20} /> Neural Safety Core
                  </h3>
                  <p className="text-xs text-slate-500 font-bold uppercase tracking-widest">Active Incident Suppression Log</p>
                </div>
                <div className="glass px-5 py-2 border-danger/30 text-danger text-[10px] font-black uppercase tracking-widest bg-danger/5">
                  Critical Monitoring Active
                </div>
              </div>
              
              <div className="space-y-6">
                {violations?.total_incidents === 0 ? (
                  <div className="glass p-32 text-center flex flex-col items-center gap-6 border-dashed border-white/10">
                    <div className="relative">
                       <CheckCircle2 size={64} className="text-success opacity-20" />
                       <motion.div animate={{ scale: [1, 1.5, 1], opacity: [0, 0.5, 0] }} transition={{ repeat: Infinity, duration: 2 }} className="absolute inset-0 bg-success rounded-full blur-2xl" />
                    </div>
                    <p className="text-slate-500 font-bold uppercase tracking-widest text-sm">System Safety Integrity: 100%</p>
                  </div>
                ) : (
                  Object.entries(violations?.breakdown || {}).map(([type, count], i) => (
                    <motion.div 
                      initial={{ opacity: 0, x: -20 }}
                      whileInView={{ opacity: 1, x: 0 }}
                      key={i} 
                      className="glass p-8 flex items-center gap-8 border-l-8 border-danger group hover:bg-danger/5 transition-all"
                    >
                      <div className="p-4 bg-danger/20 rounded-2xl text-danger shadow-[0_0_20px_rgba(244,63,94,0.3)]">
                        <AlertTriangle className="animate-pulse" size={32} />
                      </div>
                      <div className="flex-1">
                        <div className="text-[10px] font-black text-danger uppercase tracking-[0.2em] mb-1">Risk Signature</div>
                        <h4 className="text-xl font-black text-slate-100">{type}</h4>
                        <p className="text-xs text-slate-500 font-bold uppercase tracking-widest mt-1">Telemetry Occurrences: {count}</p>
                      </div>
                      <div className="flex gap-4">
                        <button className="px-6 py-3 rounded-xl bg-danger text-white text-[10px] font-black tracking-widest shadow-xl shadow-danger/20 hover:scale-105 active:scale-95 transition-all">RESOLVE CORE</button>
                        <button className="px-6 py-3 rounded-xl glass border-white/10 text-[10px] font-black tracking-widest hover:bg-white/5">ARCHIVE</button>
                      </div>
                    </motion.div>
                  ))
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        <footer className="mt-20 py-10 border-t border-white/5 flex justify-between items-center text-[9px] text-slate-600 font-black uppercase tracking-[0.3em]">
           <div className="flex items-center gap-4">
             <div className="flex items-center gap-2">
               <div className="w-2 h-2 rounded-full bg-primary shadow-[0_0_10px_var(--primary)]" />
               <span>Telemetry Link: {selectedCamera} // 115200 BAUD</span>
             </div>
             <div className="w-1 h-3 bg-white/10" />
             <div className="flex items-center gap-2">
               <span className="text-success">ENCRYPTED</span>
               <Globe size={10} />
             </div>
           </div>
           <div className="flex items-center gap-6">
             <div>Neural Core v4.0.12</div>
             <div className="text-slate-800">|</div>
             <div>PERSISTENCE BLOCK: ACTIVE</div>
           </div>
        </footer>
      </main>
    </>
  );
};

export default App;
