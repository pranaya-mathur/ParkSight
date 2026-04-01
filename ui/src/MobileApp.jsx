import React, { useState, useEffect } from 'react';
import { 
  Car, 
  MapPin, 
  Navigation, 
  Clock, 
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const MobileApp = ({ vehicleId }) => {
  const [guidance, setGuidance] = useState(null);
  const [loading, setLoading] = useState(true);

  // Fetch personalized guidance for this vehicle
  useEffect(() => {
    const fetchGuidance = async () => {
      try {
        const res = await fetch(`/api/vehicles/${vehicleId}/guidance`);
        const data = await res.json();
        setGuidance(data);
      } catch (err) {
        console.error("Mobile sync error:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchGuidance();
    const interval = setInterval(fetchGuidance, 5000);
    return () => clearInterval(interval);
  }, [vehicleId]);

  if (loading) return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center">
      <motion.div animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1 }} className="text-primary">
        <Navigation size={48} />
      </motion.div>
    </div>
  );

  return (
    <div className="min-h-screen bg-slate-950 text-white font-sans selection:bg-primary/30">
      {/* Header */}
      <header className="p-6 border-b border-white/5">
        <div className="flex justify-between items-center">
          <div>
            <h1 className="text-xs font-black tracking-widest text-slate-500 uppercase">Personal Guidance</h1>
            <p className="text-xl font-bold text-primary">{guidance?.welcome || "Welcome Back!"}</p>
          </div>
          <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary border border-primary/20">
            <Car size={20} />
          </div>
        </div>
      </header>

      <main className="p-6 space-y-8">
        {/* Active Instruction Card */}
        <motion.div 
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="bg-indigo-600 rounded-3xl p-8 shadow-[0_20px_50px_rgba(79,70,229,0.3)] relative overflow-hidden"
        >
          <div className="absolute top-0 right-0 p-8 opacity-10">
            <Navigation size={120} />
          </div>
          
          <div className="relative z-10">
            <span className="text-[10px] font-black tracking-[0.2em] opacity-60 uppercase">Current Maneuver</span>
            <p className="text-3xl font-black mt-2 leading-tight">
              {guidance?.instruction || "Scanning facility for parking route..."}
            </p>
          </div>
        </motion.div>

        {/* Target Slot Status */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-6">
            <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Target Slot</span>
            <p className="text-2xl font-black font-mono">
              {guidance?.target_slot !== -1 ? `#${guidance.target_slot}` : "AUTO"}
            </p>
          </div>
          <div className="bg-slate-900/50 border border-white/5 rounded-2xl p-6">
            <span className="text-[10px] font-bold text-slate-500 uppercase block mb-1">Status</span>
            <div className="flex items-center gap-2 text-emerald-400">
               <CheckCircle2 size={16} />
               <p className="text-xs font-black">LOCKED</p>
            </div>
          </div>
        </div>

        {/* Dynamic Route Info */}
        <div className="bg-white/5 rounded-3xl p-8 border border-white/5">
          <h3 className="text-sm font-bold flex items-center gap-3 mb-6">
            <MapPin className="text-primary" size={18} />
            Facility Perspective
          </h3>
          
          {/* Simple Top-down Simulation View */}
          <div className="aspect-square bg-slate-900 rounded-2xl border border-white/10 relative overflow-hidden">
             <div className="absolute inset-x-0 bottom-0 py-2 bg-slate-950/80 text-center text-[10px] font-bold border-t border-white/5">
                VEHICLE TRACKING: ACTIVE
             </div>
             {/* Neon Path Mockup */}
             <svg viewBox="0 0 100 100" className="w-full h-full p-10 opacity-40">
                <motion.path 
                  d="M 50 100 L 50 60 L 10 60 L 10 20" 
                  stroke="#6366f1" strokeWidth="2" fill="none"
                  strokeDasharray="4 2"
                  animate={{ strokeDashoffset: [0, -10] }}
                  transition={{ repeat: Infinity, duration: 2, ease: "linear" }}
                />
             </svg>
          </div>
        </div>
      </main>

      {/* Footer Actions */}
      <footer className="fixed bottom-0 inset-x-0 p-6 bg-slate-950/80 backdrop-blur-xl border-t border-white/5">
        <button className="w-full bg-white text-black font-black py-4 rounded-2xl text-sm shadow-xl active:scale-95 transition-all">
          RELEASE RESERVATION
        </button>
      </footer>
    </div>
  );
};

export default MobileApp;
