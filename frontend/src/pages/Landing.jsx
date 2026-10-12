import { motion } from 'framer-motion';
import { Link } from 'react-router-dom';
import ThreeOrb from '../components/ThreeOrb';
import { Shield, Brain, Zap, Activity } from 'lucide-react';

const T = (v) => `var(${v})`;

export default function Landing() {
  return (
    <div className="flex flex-col items-center w-full overflow-hidden">
      {/* Hero Section */}
      <section className="relative w-full min-h-[85vh] md:min-h-[90vh] flex flex-col items-center justify-center pt-10 md:pt-20">
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[320px] sm:max-w-[600px] aspect-square pointer-events-none z-0">
          <ThreeOrb className="w-full h-full opacity-60 mix-blend-screen" />
        </div>
        
        <div className="z-10 flex flex-col items-center text-center space-y-6 md:space-y-8 max-w-4xl mx-auto px-4 mt-12 md:mt-20">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          >
            <h1 className="font-display text-4xl sm:text-6xl md:text-8xl font-medium tracking-tight text-glow leading-tight">
              Intelligence for a <br className="hidden md:block" />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-indigo-400">
                healthier life.
              </span>
            </h1>
          </motion.div>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 1.2, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
            className="text-base sm:text-lg md:text-2xl font-light tracking-wide max-w-2xl px-2"
            style={{ color: T('--text-secondary') }}
          >
            Private. Adaptive. Human-centered. <br/>
            An AI wellness operating system that understands you.
          </motion.p>

          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 1, delay: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="pt-4 md:pt-8"
          >
            <Link to="/chat">
              <button className="relative overflow-hidden rounded-full px-8 py-3.5 md:px-10 md:py-4 font-medium text-base md:text-lg tracking-wide hover:scale-105 active:scale-95 transition-transform duration-500 ease-out flex items-center gap-3" style={{ background: T('--chat-submit-bg'), color: T('--chat-submit-text') }}>
                <span>Meet Wellora</span>
                <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse"></div>
              </button>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Local AI Privacy Section */}
      <section className="w-full max-w-6xl py-16 md:py-32 px-4 md:px-6">
        <motion.div 
          initial={{ opacity: 0, y: 40 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-50px" }}
          transition={{ duration: 1 }}
          className="glass-card p-8 sm:p-12 md:p-20 relative overflow-hidden"
        >
          {/* Subtle grid background */}
          <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_50%_50%_at_50%_50%,#000_20%,transparent_100%)]"></div>
          
          <div className="relative z-10 grid md:grid-cols-2 gap-10 md:gap-16 items-center">
            <div>
              <div className="w-10 h-10 md:w-12 md:h-12 rounded-xl md:rounded-2xl bg-indigo-500/20 flex items-center justify-center mb-6 md:mb-8 border border-indigo-500/30">
                <Shield className="text-indigo-400 w-5 h-5 md:w-6 md:h-6" />
              </div>
              <h2 className="font-display text-3xl md:text-5xl font-medium mb-4 md:mb-6">Private intelligence by design.</h2>
              <p className="text-base md:text-lg leading-relaxed mb-6 md:mb-8" style={{ color: T('--text-secondary') }}>
                Your data stays yours. Wellora processes wellness metrics locally, creating a secure environment where you can freely explore your mental and physical health without surveillance.
              </p>
              <ul className="space-y-3.5">
                {['Local LLM Execution', 'Encrypted Memory Systems', 'Zero-Surveillance Architecture'].map((item, i) => (
                  <li key={i} className="flex items-center gap-3 text-sm" style={{ color: T('--text-primary') }}>
                    <div className="w-1.5 h-1.5 rounded-full bg-indigo-500"></div>
                    {item}
                  </li>
                ))}
              </ul>
            </div>
            <div className="relative w-full max-w-[280px] sm:max-w-[360px] mx-auto aspect-square flex items-center justify-center">
              <div className="absolute inset-0 bg-indigo-500/10 blur-[60px] md:blur-[100px] rounded-full"></div>
              <div className="w-full h-full border border-white/5 rounded-full border-dashed animate-[spin_60s_linear_infinite] flex items-center justify-center">
                <div className="w-[80%] h-[80%] border border-indigo-500/20 rounded-full border-dashed animate-[spin_40s_linear_infinite_reverse] flex items-center justify-center">
                   <div className="w-[60%] h-[60%] bg-indigo-500/10 rounded-full backdrop-blur-3xl border border-white/10 flex items-center justify-center shadow-[0_0_50px_rgba(99,102,241,0.2)]">
                      <Shield size={36} className="text-indigo-300 md:hidden" strokeWidth={1} />
                      <Shield size={48} className="text-indigo-300 hidden md:block" strokeWidth={1} />
                   </div>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Multi-Agent Visualization */}
      <section className="w-full max-w-6xl py-16 md:py-32 px-4 md:px-6">
        <div className="text-center mb-12 md:mb-20">
          <h2 className="font-display text-3xl md:text-5xl font-medium mb-4 md:mb-6">The Nervous System</h2>
          <p className="text-base md:text-lg max-w-2xl mx-auto" style={{ color: T('--text-secondary') }}>
            Wellora is powered by an orchestrated network of specialized AI agents working asynchronously to understand your holistic wellbeing.
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-6">
          <AgentCard 
            icon={<Brain />} 
            title="Memory Agent" 
            desc="Synthesizes conversational history to build long-term contextual understanding."
            color="purple"
            delay={0.1}
          />
          <AgentCard 
            icon={<Activity />} 
            title="Nutrition Agent" 
            desc="Analyzes meals, extracts macros, and visualizes dietary patterns in real-time."
            color="emerald"
            delay={0.2}
          />
          <AgentCard 
            icon={<Zap />} 
            title="Companion Agent" 
            desc="Provides emotionally intelligent responses and adaptive coaching."
            color="rose"
            delay={0.3}
          />
        </div>
      </section>
    </div>
  );
}

function AgentCard({ icon, title, desc, color, delay }) {
  const colorMap = {
    purple: "text-purple-400 bg-purple-500/10 border-purple-500/20 shadow-purple-500/5",
    emerald: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20 shadow-emerald-500/5",
    rose: "text-rose-400 bg-rose-500/10 border-rose-500/20 shadow-rose-500/5"
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, margin: "-50px" }}
      transition={{ duration: 0.8, delay }}
      className={`glass-card p-6 md:p-8 group hover:scale-[1.02] active:scale-[0.98] transition-all duration-500 border ${colorMap[color].split(' ')[2]}`}
    >
      <div className={`w-12 h-12 md:w-14 md:h-14 rounded-xl md:rounded-2xl flex items-center justify-center mb-5 md:mb-6 transition-transform duration-500 group-hover:-translate-y-2 ${colorMap[color].split(' ').slice(0,2).join(' ')}`}>
        {icon}
      </div>
      <h3 className="font-display text-lg md:text-xl font-medium mb-2.5 md:mb-3" style={{ color: T('--text-primary') }}>{title}</h3>
      <p className="text-sm leading-relaxed" style={{ color: T('--text-secondary') }}>{desc}</p>
    </motion.div>
  );
}
