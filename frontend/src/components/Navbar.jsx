import { Link, useLocation } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sun, Moon } from 'lucide-react';
import { useStore } from '../store/useStore';

export default function Navbar() {
  const location = useLocation();
  const isActive = (path) => location.pathname === path;
  const { theme, toggleTheme } = useStore();
  const isLight = theme === 'light';

  return (
    <motion.nav 
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      className="fixed top-0 left-0 right-0 z-50 flex justify-center pt-4 md:pt-6 px-4 pointer-events-none"
    >
      <div className="glass-panel rounded-full px-4 md:px-6 py-2.5 md:py-3 flex items-center justify-between w-full max-w-lg md:max-w-none md:justify-center gap-4 sm:gap-8 md:gap-12 pointer-events-auto">
        <Link to="/" className="flex items-center gap-1.5 md:gap-2 group">
          <div className="w-5 h-5 md:w-6 md:h-6 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 group-hover:scale-110 transition-transform duration-500"
            style={{ boxShadow: 'var(--shadow-glow)' }}></div>
          <span className="font-display font-medium text-base md:text-lg tracking-wide transition-colors"
            style={{ color: 'var(--text-primary)' }}>
            Wellora
          </span>
        </Link>
        
        <div className="flex items-center gap-4 sm:gap-6 md:gap-8 text-xs md:text-sm font-medium">
          <Link 
            to="/chat" 
            className="transition-colors duration-300 py-1"
            style={{ color: isActive('/chat') ? 'var(--text-primary)' : 'var(--text-secondary)' }}
          >
            Companion
          </Link>
          <Link 
            to="/dashboard" 
            className="transition-colors duration-300 py-1"
            style={{ color: isActive('/dashboard') ? 'var(--text-primary)' : 'var(--text-secondary)' }}
          >
            Intelligence
          </Link>
        </div>
        
        <div className="flex items-center gap-2">
          {/* Theme toggle */}
          <button 
            onClick={toggleTheme}
            className="w-7 h-7 md:w-8 md:h-8 rounded-full flex items-center justify-center transition-all duration-300 cursor-pointer active:scale-90"
            style={{ 
              background: isLight ? 'rgba(139,92,246,0.1)' : 'rgba(255,255,255,0.1)',
              border: `1px solid ${isLight ? 'rgba(139,92,246,0.15)' : 'rgba(255,255,255,0.05)'}`,
              color: isLight ? 'var(--accent-violet)' : 'rgba(255,255,255,0.6)'
            }}
            title={isLight ? 'Switch to dark mode' : 'Switch to light mode'}
          >
            {isLight ? <Moon size={14} /> : <Sun size={14} />}
          </button>

          <div className="w-7 h-7 md:w-8 md:h-8 rounded-full flex items-center justify-center text-xs cursor-pointer transition-colors active:scale-95"
            style={{
              background: isLight ? 'rgba(139,92,246,0.08)' : 'rgba(255,255,255,0.1)',
              border: `1px solid ${isLight ? 'rgba(139,92,246,0.1)' : 'rgba(255,255,255,0.05)'}`,
              color: 'var(--text-secondary)'
            }}>
            G
          </div>
        </div>
      </div>
    </motion.nav>
  );
}
