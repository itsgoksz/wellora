import { useState, useRef, useEffect, useCallback } from 'react';
import { useStore } from '../store/useStore';
import { motion, AnimatePresence } from 'framer-motion';
import { Sparkles, Utensils, ArrowUp, Volume2, VolumeX } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

const T = (v) => `var(${v})`;

const API_BASE = 'http://' + window.location.hostname + ':8000';

export default function Chat() {
  const { messages, addMessage } = useStore();
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const audioRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  // Play audio when available
  const playAudio = useCallback((audioUrl) => {
    if (isMuted || !audioUrl) return;
    
    // Stop any currently playing audio
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }

    const audio = new Audio(`${API_BASE}${audioUrl}`);
    audioRef.current = audio;
    
    audio.onplay = () => setIsPlaying(true);
    audio.onended = () => {
      setIsPlaying(false);
      audioRef.current = null;
    };
    audio.onerror = () => {
      setIsPlaying(false);
      audioRef.current = null;
      console.log('[Wellora] Audio playback failed — text-only mode');
    };
    
    audio.play().catch(() => {
      // Autoplay blocked by browser — silently fall back to text
      setIsPlaying(false);
      audioRef.current = null;
    });
  }, [isMuted]);

  // Interrupt audio when user starts typing
  const handleInputChange = (e) => {
    setInput(e.target.value);
    if (audioRef.current && isPlaying) {
      audioRef.current.pause();
      audioRef.current = null;
      setIsPlaying(false);
    }
  };

  const toggleMute = () => {
    if (audioRef.current && !isMuted) {
      audioRef.current.pause();
      audioRef.current = null;
      setIsPlaying(false);
    }
    setIsMuted(!isMuted);
  };

  const handleSend = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Interrupt any playing audio when user sends a new message
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
      setIsPlaying(false);
    }

    const userMsg = { id: Date.now(), text: input, sender: 'user' };
    addMessage(userMsg);
    setInput('');
    setIsTyping(true);

    try {
      const response = await fetch(`${API_BASE}/api/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: input, user_id: 1 })
      });
      const data = await response.json();
      
      const aiMsg = { 
        id: Date.now() + 1, 
        text: data.reply, 
        sender: 'ai',
        extractedData: data.extracted_data,
        audioUrl: data.audio_url,
      };
      addMessage(aiMsg);

      // Auto-play audio response
      if (data.audio_url) {
        playAudio(data.audio_url);
      }
    } catch (error) {
      addMessage({ id: Date.now() + 1, text: "Network's quiet right now. Try again in a sec.", sender: 'ai' });
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100dvh-6.5rem)] md:h-[calc(100vh-8rem)] max-w-4xl mx-auto pt-2 md:pt-6 relative">
      <div 
        className="flex-1 overflow-y-auto px-4 pb-28 md:pb-32 space-y-6 md:space-y-8 scroll-smooth hide-scrollbar"
        style={{ WebkitOverflowScrolling: 'touch', overscrollBehaviorY: 'contain' }}
      >
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-[60%] text-center opacity-50 px-4">
            <div className="w-14 h-14 md:w-16 md:h-16 rounded-full flex items-center justify-center mb-5 md:mb-6" style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}` }}>
              <Sparkles className="w-5 h-5 md:w-6 md:h-6" style={{ color: T('--text-muted') }} />
            </div>
            <p className="font-display text-xl md:text-2xl font-medium" style={{ color: T('--text-secondary') }}>What have you had to eat today?</p>
            <p className="text-xs md:text-sm mt-2 font-light max-w-xs leading-relaxed" style={{ color: T('--text-muted') }}>You can just tell me naturally like 'I had 2 idlis and a coffee'</p>
          </div>
        )}

        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              initial={{ opacity: 0, y: 15, filter: 'blur(5px)' }}
              animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
              transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
              key={msg.id}
              className={`flex w-full ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className={`flex flex-col max-w-[85%] md:max-w-[80%] ${msg.sender === 'user' ? 'items-end' : 'items-start'}`}>
                
                {msg.sender === 'ai' && (
                  <div className="flex items-center gap-2 mb-2 ml-1">
                    <div className={`w-4.5 h-4.5 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 shadow-[0_0_10px_rgba(167,139,250,0.3)] ${isPlaying && msg.id === messages[messages.length - 1]?.id ? 'animate-pulse' : ''}`}></div>
                    <span className="text-[10px] font-medium uppercase tracking-wider" style={{ color: T('--text-secondary') }}>Wellora</span>
                    {/* Voice waveform indicator */}
                    {isPlaying && msg.id === messages[messages.length - 1]?.id && (
                      <div className="flex items-center gap-0.5 ml-1">
                        {[...Array(4)].map((_, i) => (
                          <motion.div
                            key={i}
                            className="w-0.5 bg-purple-400/60 rounded-full"
                            animate={{ height: [3, 12, 5, 10, 3] }}
                            transition={{ duration: 0.8, repeat: Infinity, delay: i * 0.1 }}
                          />
                        ))}
                      </div>
                    )}
                  </div>
                )}

                <div className={`px-4 py-3 md:p-5 rounded-2xl md:rounded-3xl ${
                  msg.sender === 'user' 
                    ? 'rounded-tr-sm shadow-sm' 
                    : 'glass-card'
                }`} style={msg.sender === 'user' ? { background: T('--chat-user-bg'), border: `1px solid ${T('--chat-user-border')}`, color: T('--text-primary') } : { color: T('--text-primary') }}>
                  <div className="prose prose-p:leading-relaxed prose-p:my-1 max-w-none text-sm md:text-[15px]" style={{ color: 'inherit' }}>
                    <ReactMarkdown>{msg.text}</ReactMarkdown>
                  </div>
                </div>
                
                {/* Nutrition card for food_log */}
                {msg.sender === 'ai' && msg.extractedData?.intent === 'food_log' && msg.extractedData?.calories > 0 && !msg.extractedData?.needs_followup && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.95, y: 10 }} 
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    transition={{ delay: 0.3, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
                    className="glass-card mt-3 p-4 md:p-5 border border-purple-500/20 bg-purple-500/5 shadow-[0_0_30px_rgba(167,139,250,0.05)] w-full"
                  >
                    <div className="flex items-center gap-2 mb-3 md:mb-4 text-[10px] md:text-xs font-semibold text-purple-400 tracking-wider uppercase">
                      <Utensils size={12} />
                      Nutrition Extracted
                    </div>
                    <div className="grid grid-cols-2 gap-4 sm:flex sm:gap-6">
                      <Nutrient label="Calories" value={msg.extractedData.calories} unit="kcal" />
                      <Nutrient label="Protein" value={msg.extractedData.protein} unit="g" />
                      <Nutrient label="Carbs" value={msg.extractedData.carbs} unit="g" />
                      <Nutrient label="Fats" value={msg.extractedData.fats} unit="g" />
                    </div>
                  </motion.div>
                )}
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
        
        {isTyping && (
          <motion.div 
            initial={{ opacity: 0, y: 10 }} 
            animate={{ opacity: 1, y: 0 }} 
            className="flex justify-start animate-fade-in"
          >
            <div className="flex flex-col items-start">
               <div className="flex items-center gap-2 mb-2 ml-1">
                 <div className="w-4.5 h-4.5 rounded-full bg-gradient-to-tr from-purple-500 to-indigo-500 shadow-[0_0_10px_rgba(167,139,250,0.3)] animate-pulse"></div>
                 <span className="text-[10px] font-medium uppercase tracking-wider" style={{ color: T('--text-secondary') }}>Wellora is thinking</span>
               </div>
               <div className="glass-card px-4 py-3 md:px-5 md:py-4 flex items-center gap-1.5 md:gap-2 rounded-2xl">
                 <div className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce"></div>
                 <div className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.15s' }}></div>
                 <div className="w-1.5 h-1.5 bg-purple-400 rounded-full animate-bounce" style={{ animationDelay: '0.3s' }}></div>
               </div>
            </div>
          </motion.div>
        )}
        <div ref={messagesEndRef} className="h-2" />
      </div>

      {/* iOS/Android style elegant keyboard dock input */}
      <div 
        className="fixed bottom-0 md:bottom-8 left-0 md:left-1/2 md:-translate-x-1/2 w-full md:max-w-3xl px-0 md:px-4 pb-safe-bottom z-40 backdrop-blur-xl md:backdrop-blur-none pt-3 md:pt-0"
        style={{ 
          backgroundColor: T('--chat-dock-bg'), 
          borderTop: `1px solid ${T('--border-subtle')}`,
          paddingBottom: 'calc(env(safe-area-inset-bottom, 12px) + 8px)' 
        }}
      >
        <form onSubmit={handleSend} className="relative flex items-center shadow-2xl px-4 md:px-0">
          <div className="absolute inset-y-0 left-4 md:left-0 right-4 md:right-0 backdrop-blur-3xl rounded-full -z-10 pointer-events-none" style={{ background: T('--bg-input'), border: `1px solid ${T('--border-medium')}` }}></div>
          
          {/* Mute/Unmute toggle */}
          <button
            type="button"
            onClick={toggleMute}
            className="ml-3 md:ml-4 w-8 h-8 flex items-center justify-center active:scale-90 transition-all"
            style={{ color: T('--text-muted') }}
            title={isMuted ? "Unmute voice" : "Mute voice"}
          >
            {isMuted ? <VolumeX size={18} /> : <Volume2 size={18} />}
          </button>

          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={handleInputChange}
            className="w-full bg-transparent py-4 md:py-5 pl-3 pr-14 md:pr-16 focus:outline-none text-sm md:text-[15px]"
            style={{ color: T('--text-primary'), '--tw-placeholder-color': T('--chat-input-placeholder') }}
            placeholder="What have you had to eat?"
          />
          <button 
            type="submit" 
            disabled={!input.trim()}
            className="absolute right-6 md:right-3 w-8 h-8 md:w-10 md:h-10 flex items-center justify-center rounded-full transition-all duration-300 disabled:opacity-20 disabled:cursor-not-allowed active:scale-95"
            style={{ background: T('--chat-submit-bg'), color: T('--chat-submit-text') }}
          >
            <ArrowUp size={18} md:size={20} strokeWidth={2.5} />
          </button>
        </form>
      </div>
    </div>
  );
}

function Nutrient({ label, value, unit }) {
  if (!value && value !== 0) return null;
  return (
    <div className="flex flex-col">
      <span className="text-xl md:text-2xl font-display font-medium" style={{ color: T('--text-primary') }}>
        {Math.round(value)}
        <span className="text-xs ml-0.5" style={{ color: T('--text-muted') }}>{unit}</span>
      </span>
      <span className="text-[9px] md:text-[10px] uppercase tracking-widest mt-0.5" style={{ color: T('--text-muted') }}>{label}</span>
    </div>
  );
}
