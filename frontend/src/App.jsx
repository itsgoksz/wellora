import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import Navbar from './components/Navbar';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Chat from './pages/Chat';
import SmoothScroll from './components/SmoothScroll';
import { useStore } from './store/useStore';

function App() {
  const theme = useStore((s) => s.theme);

  useEffect(() => {
    document.documentElement.classList.toggle('light', theme === 'light');
  }, [theme]);

  return (
    <Router>
      <SmoothScroll>
        <div className="min-h-screen relative overflow-x-hidden transition-colors duration-500"
          style={{ backgroundColor: 'var(--bg-base)', color: 'var(--text-primary)' }}>
          {/* Global Ambient Glow */}
          <div className="fixed top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] rounded-full blur-[120px] pointer-events-none -z-10 transition-colors duration-1000"
            style={{ backgroundColor: theme === 'light' ? 'rgba(139,92,246,0.06)' : 'rgba(88,28,135,0.1)' }}></div>
          
          <Navbar />
          
          <main className="relative z-0 pt-20 md:pt-28 pb-10 md:pb-20 px-4 md:px-6 mx-auto max-w-7xl">
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/chat" element={<Chat />} />
            </Routes>
          </main>
        </div>
      </SmoothScroll>
    </Router>
  );
}

export default App;
