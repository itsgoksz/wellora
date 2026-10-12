import { useState, useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import { motion, AnimatePresence, useInView } from 'framer-motion';
import { Sparkles, Clock, Trash2, ChevronDown, ChevronUp, Flame } from 'lucide-react';

const T = (v) => `var(${v})`;

// Animated count-up hook
function useCountUp(target, duration = 1200) {
  const [value, setValue] = useState(0);
  const ref = useRef(null);
  const inView = useInView(ref, { once: true });
  useEffect(() => {
    if (!inView || !target) return;
    const start = performance.now();
    const tick = (now) => {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(target * eased));
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [inView, target, duration]);
  return { value, ref };
}

const API_BASE = 'http://' + window.location.hostname + ':8000';

// Color maps for wellness modules
const COLOR_MAP = {
  orange: { bg: 'bg-orange-500/10', text: 'text-orange-400', bar: 'bg-orange-400', glow: 'rgba(251,146,60,0.15)' },
  emerald: { bg: 'bg-emerald-500/10', text: 'text-emerald-400', bar: 'bg-emerald-400', glow: 'rgba(52,211,153,0.15)' },
  blue: { bg: 'bg-blue-500/10', text: 'text-blue-400', bar: 'bg-blue-400', glow: 'rgba(96,165,250,0.15)' },
  purple: { bg: 'bg-purple-500/10', text: 'text-purple-400', bar: 'bg-purple-400', glow: 'rgba(167,139,250,0.15)' },
};

const TONE_COLORS = {
  positive: 'text-emerald-600 dark:text-emerald-400/80',
  neutral: '',
  gentle: 'text-amber-600 dark:text-amber-400/70',
  calm: 'text-purple-600 dark:text-purple-300/70',
};

export default function Dashboard() {
  const { dashboardData, setDashboardData, theme } = useStore();
  const [expandedMeal, setExpandedMeal] = useState(null);
  const isLight = theme === 'light';

  const getLocalDateString = (dateObj) => {
    const year = dateObj.getFullYear();
    const month = String(dateObj.getMonth() + 1).padStart(2, '0');
    const day = String(dateObj.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const [selectedDate, setSelectedDate] = useState(() => getLocalDateString(new Date()));

  const fetchDashboard = async (dateStr) => {
    try {
      const response = await fetch(`${API_BASE}/api/dashboard/1?date=${dateStr}`);
      const data = await response.json();
      setDashboardData(data);
    } catch (error) {
      console.error("Failed to fetch dashboard data:", error);
    }
  };

  useEffect(() => {
    fetchDashboard(selectedDate);
    let interval;
    if (selectedDate === getLocalDateString(new Date())) {
      interval = setInterval(() => fetchDashboard(selectedDate), 10000);
    }
    return () => { if (interval) clearInterval(interval); };
  }, [selectedDate]);

  const handleDeleteMeal = async (mealId) => {
    try {
      await fetch(`${API_BASE}/api/dashboard/meal/${mealId}`, { method: 'DELETE' });
      fetchDashboard(selectedDate);
    } catch (error) {
      console.error("Failed to delete meal:", error);
    }
  };

  const handleQuickLogWater = async (ml) => {
    try {
      await fetch(`${API_BASE}/api/dashboard/quick-log/water/1/${ml}`, { method: 'POST' });
      fetchDashboard(selectedDate);
    } catch (error) {
      console.error("Failed to quick log water:", error);
    }
  };

  // Calendar days
  const calendarDays = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date();
    d.setDate(d.getDate() - i);
    calendarDays.push({
      dateStr: getLocalDateString(d),
      dayName: d.toLocaleDateString('en-US', { weekday: 'short' }),
      dayNum: d.getDate(),
      isToday: getLocalDateString(d) === getLocalDateString(new Date())
    });
  }

  if (!dashboardData) return (
    <div className="space-y-5 max-w-5xl mx-auto px-2 md:px-0 pt-4 animate-pulse">
      <div className="flex justify-between items-center pb-5" style={{ borderBottom: `1px solid ${T('--border-subtle')}` }}>
        <div>
          <div className="h-7 w-48 rounded-xl mb-2" style={{ background: T('--bg-card') }}></div>
          <div className="h-4 w-32 rounded-lg" style={{ background: T('--bg-card') }}></div>
        </div>
        <div className="flex gap-1.5 p-1.5 rounded-2xl" style={{ background: T('--bg-card') }}>
          {[...Array(7)].map((_, i) => <div key={i} className="w-11 h-14 rounded-xl" style={{ background: T('--bg-elevated') }}></div>)}
        </div>
      </div>
      <div className="h-32 rounded-3xl" style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}` }}></div>
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[...Array(4)].map((_, i) => <div key={i} className="h-28 rounded-2xl" style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}` }}></div>)}
      </div>
      <div className="grid md:grid-cols-3 gap-4">
        <div className="h-44 rounded-2xl" style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}` }}></div>
        <div className="md:col-span-2 h-44 rounded-2xl" style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}` }}></div>
      </div>
    </div>
  );

  const hasMeals = dashboardData.recent_meals?.length > 0;
  const todayStr = getLocalDateString(new Date());
  const isSelectedToday = selectedDate === todayStr;
  const timePeriod = dashboardData.time_period || 'afternoon';
  const dailyRhythm = dashboardData.daily_rhythm || [];
  const wellnessModules = dashboardData.wellness_modules || [];

  // Time-adaptive ambient gradient
  const ambientGradient = timePeriod === 'morning'
    ? 'from-amber-500/5 via-purple-500/3 to-transparent'
    : timePeriod === 'evening' || timePeriod === 'night'
    ? 'from-indigo-500/5 via-purple-900/5 to-transparent'
    : 'from-purple-500/5 via-transparent to-transparent';

  // Daily state title
  const stateTitle = isSelectedToday
    ? (timePeriod === 'morning' ? 'Morning Rhythm' : timePeriod === 'afternoon' ? "Today's Rhythm" : timePeriod === 'evening' ? 'Evening Reflection' : 'Nightly Review')
    : new Date(selectedDate + "T00:00:00").toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  const stateSubtitle = isSelectedToday
    ? (timePeriod === 'morning' ? 'Your day is beginning' : timePeriod === 'afternoon' ? 'Your wellness state right now' : timePeriod === 'evening' ? 'Winding down for the day' : 'Your day in review')
    : 'Historical wellness data';

  return (
    <div className="space-y-5 max-w-5xl mx-auto px-2 md:px-0 relative overflow-x-hidden pb-8" style={{ paddingBottom: 'calc(env(safe-area-inset-bottom, 0px) + 2rem)' }}>
      {/* Time-adaptive ambient glow */}
      <div className={`fixed top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] bg-gradient-to-b ${ambientGradient} rounded-full blur-[100px] pointer-events-none -z-10 opacity-60 transition-all duration-[2000ms]`}></div>

      {/* ═══ HEADER + CALENDAR ═══ */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-5 pb-5 mt-2" style={{ borderBottom: `1px solid ${T('--border-subtle')}` }}>
        <div>
          <h1 className="font-display text-2xl md:text-3xl font-medium tracking-tight" style={{ color: T('--text-primary') }}>{stateTitle}</h1>
          <p className="text-sm mt-0.5" style={{ color: T('--text-secondary') }}>{stateSubtitle}</p>
        </div>
        <div className="flex gap-1.5 p-1.5 rounded-2xl overflow-x-auto no-scrollbar" style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}` }}>
          {calendarDays.map((day) => {
            const isSelected = selectedDate === day.dateStr;
            return (
              <button key={day.dateStr} onClick={() => setSelectedDate(day.dateStr)}
                className="relative flex flex-col items-center justify-center w-11 h-14 md:w-13 md:h-18 rounded-xl transition-all duration-300 active:scale-95 cursor-pointer select-none shrink-0"
                style={{ color: isSelected ? T('--text-primary') : T('--text-secondary') }}>
                <span className="text-[9px] md:text-[10px] font-semibold uppercase tracking-wider mb-1 opacity-70">{day.dayName}</span>
                <span className="font-display text-sm md:text-lg font-bold leading-none">{day.dayNum}</span>
                {day.isToday && <span className={`absolute bottom-2 w-1 h-1 md:w-1.5 md:h-1.5 rounded-full ${isSelected ? 'bg-purple-300' : 'bg-purple-500/60'}`}></span>}
                {isSelected && (
                  <motion.div layoutId="active-date-pill" className="absolute inset-0 border border-purple-500/30 bg-purple-500/8 rounded-xl pointer-events-none shadow-[0_0_20px_rgba(139,92,246,0.08)]"
                    transition={{ type: "spring", stiffness: 400, damping: 30 }} />
                )}
              </button>
            );
          })}
        </div>
      </div>

      <AnimatePresence mode="wait">
        <motion.div key={selectedDate} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -8 }} transition={{ duration: 0.35 }} className="space-y-6">

          {/* ═══ 1. COGNITIVE INSIGHT — emotional centerpiece ═══ */}
          <motion.div initial={{ opacity: 0, scale: 0.98 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.8, delay: 0.05, ease: [0.16, 1, 0.3, 1] }}
            className="relative overflow-hidden rounded-3xl backdrop-blur-xl p-6 md:p-8 group" style={{ background: T('--bg-card'), border: `1px solid ${T('--border-accent')}` }}>
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/[0.06] via-transparent to-indigo-500/[0.03] pointer-events-none"></div>
            <div className="absolute -top-16 -right-16 w-48 h-48 bg-purple-500/10 blur-[70px] rounded-full group-hover:bg-purple-500/15 transition-colors duration-1000"></div>
            <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-indigo-500/8 blur-[50px] rounded-full"></div>
            <h2 className="text-[10px] md:text-xs font-semibold mb-3 flex items-center gap-2 text-purple-300/80 uppercase tracking-[0.15em] relative z-10">
              <Sparkles size={12} /> Cognitive Insight
            </h2>
            <p className="text-lg md:text-xl leading-relaxed font-light relative z-10 max-w-3xl" style={{ color: T('--text-primary') }}>
              {dashboardData.insight_text}
            </p>
          </motion.div>

          {/* ═══ ALCOHOL RECOVERY INTELLIGENCE ALERT ═══ */}
          {dashboardData.recovery_alert && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.08, duration: 0.5 }}
              className="rounded-3xl backdrop-blur-xl p-5 md:p-6 border relative overflow-hidden"
              style={{
                background: dashboardData.recovery_alert.severity === 'warning'
                  ? 'linear-gradient(135deg, rgba(239, 68, 68, 0.08) 0%, rgba(139, 92, 246, 0.04) 100%)'
                  : 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(139, 92, 246, 0.04) 100%)',
                borderColor: dashboardData.recovery_alert.severity === 'warning'
                  ? 'rgba(239, 68, 68, 0.25)'
                  : 'rgba(16, 185, 129, 0.25)',
              }}
            >
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-lg">
                      {dashboardData.recovery_alert.severity === 'warning' ? '⚠️' : '✨'}
                    </span>
                    <h4
                      className="font-display font-medium text-xs md:text-sm uppercase tracking-wider"
                      style={{
                        color: dashboardData.recovery_alert.severity === 'warning'
                          ? 'rgba(248, 113, 113, 0.9)'
                          : 'rgba(52, 211, 153, 0.9)'
                      }}
                    >
                      {dashboardData.recovery_alert.title}
                    </h4>
                  </div>
                  <p className="text-xs md:text-sm max-w-2xl leading-relaxed" style={{ color: T('--text-primary') }}>
                    {dashboardData.recovery_alert.message}
                  </p>
                </div>
                {dashboardData.recovery_suggestions?.length > 0 && (
                  <div className="flex flex-wrap gap-2 shrink-0">
                    {dashboardData.recovery_suggestions.map((sug, idx) => (
                      <button
                        key={idx}
                        onClick={() => {
                          if (sug.action === 'drink_water') {
                            handleQuickLogWater(500);
                          } else if (sug.action === 'sip_water') {
                            handleQuickLogWater(250);
                          } else {
                            // Show a gentle notification or browser toast
                            alert(`Recommendation: ${sug.text}`);
                          }
                        }}
                        className="px-3.5 py-2 rounded-xl text-[11px] font-medium backdrop-blur-md transition-all duration-300 active:scale-95 cursor-pointer hover:shadow-lg border"
                        style={{
                          background: T('--bg-card'),
                          borderColor: T('--border-subtle'),
                          color: T('--text-primary'),
                        }}
                      >
                        {sug.text}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          )}

          {/* ═══ CALORIE SUMMARY HERO ═══ */}
          {hasMeals && <CalorieSummary data={dashboardData} />}

          {/* ═══ 2. DAILY RHYTHM — narrative timeline ═══ */}
          {dailyRhythm.length > 0 && (
            <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1, duration: 0.5 }}
              className="rounded-3xl backdrop-blur-xl p-5 md:p-6" style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}` }}>
              <h3 className="text-[10px] md:text-xs font-semibold uppercase tracking-[0.15em] mb-4" style={{ color: T('--text-secondary') }}>Today's Rhythm</h3>
              <div className="flex gap-2 md:gap-3 overflow-x-auto no-scrollbar md:flex-wrap pb-1 md:pb-0">
                {dailyRhythm.map((item, i) => (
                  <motion.div key={i} initial={{ opacity: 0, x: -8 }} animate={{ opacity: 1, x: 0 }} transition={{ delay: 0.15 + i * 0.06 }}
                    className={`flex items-center gap-2 px-3 py-2 rounded-xl shrink-0 whitespace-nowrap ${TONE_COLORS[item.tone] || ''}`}
                    style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}`, color: TONE_COLORS[item.tone] ? undefined : T('--text-secondary') }}>
                    <span className="text-base">{item.icon}</span>
                    <span className="text-xs md:text-sm font-medium">{item.text}</span>
                  </motion.div>
                ))}
              </div>
            </motion.div>
          )}

          {/* ═══ 3. WELLNESS MODULES — adaptive metric cards ═══ */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 md:gap-5">
            {wellnessModules.map((mod, i) => {
              const colors = COLOR_MAP[mod.color] || COLOR_MAP.purple;
              return (
                <motion.div key={mod.key} initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.15 + i * 0.07, ease: [0.16, 1, 0.3, 1] }}
                  whileHover={{ y: -2, boxShadow: 'var(--shadow-elevated)' }}
                  className="rounded-2xl md:rounded-3xl backdrop-blur-xl p-4 md:p-5 flex flex-col justify-between relative overflow-hidden cursor-default" style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}`, transition: 'all 0.4s ease' }}>
                  <div className={`absolute -top-8 -right-8 w-20 h-20 ${colors.bg} blur-[30px] rounded-full opacity-50 group-hover:opacity-80 transition-opacity duration-700`}></div>
                  <div className="flex items-center justify-between mb-3 relative z-10">
                    <h3 className="text-[10px] md:text-xs font-semibold uppercase tracking-[0.12em]" style={{ color: T('--text-secondary') }}>{mod.title}</h3>
                    <div className={`w-6 h-6 md:w-7 md:h-7 rounded-full ${colors.bg} flex items-center justify-center`}>
                      <div className={`w-2 h-2 rounded-full ${colors.bar}`}></div>
                    </div>
                  </div>
                  <div className="relative z-10">
                    <p className="font-display text-2xl md:text-3xl font-medium tracking-tight">
                      {typeof mod.value === 'number' ? Math.round(mod.value) : mod.value}
                      <span className="text-xs md:text-sm text-[#a1a1aa] ml-1 font-sans font-normal">{mod.unit}</span>
                    </p>
                    {/* Score bar */}
                    <div className="h-1.5 w-full rounded-full overflow-hidden mt-2.5 mb-1.5" style={{ background: T('--bar-track') }}>
                      <motion.div initial={{ width: 0 }} animate={{ width: `${Math.min(100, mod.score)}%` }}
                        transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1], delay: 0.3 + i * 0.1 }}
                        className={`h-full ${colors.bar} rounded-full`}
                        style={{ boxShadow: `0 0 8px ${colors.glow}` }} />
                    </div>
                    <p className="text-[10px] md:text-[11px] leading-snug" style={{ color: T('--text-muted') }}>{mod.reason}</p>
                  </div>
                </motion.div>
              );
            })}
          </div>

          {/* ═══ 4. NUTRITION TIMELINE + MACROS ═══ */}
          <div className="flex flex-col md:grid md:grid-cols-3 gap-5 md:gap-6">
            {hasMeals ? (
              <>
                {/* Macros Panel */}
                <div className="w-full md:col-span-1 rounded-2xl md:rounded-3xl backdrop-blur-xl p-5 md:p-6 flex flex-col justify-center" style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}` }}>
                  <h3 className="text-[10px] md:text-xs uppercase tracking-[0.15em] mb-1 font-semibold" style={{ color: T('--text-secondary') }}>Macro Distribution</h3>
                  <p className="text-[10px] mb-4" style={{ color: T('--text-muted') }}>Daily target progress</p>
                  <div className="space-y-2.5">
                    <MacroBar label="Protein" value={dashboardData.total_protein} max={150} color="bg-emerald-400" />
                    <MacroBar label="Carbs" value={dashboardData.total_carbs} max={300} color="bg-indigo-400" />
                    <MacroBar label="Fats" value={dashboardData.total_fats} max={100} color="bg-rose-400" />
                    <MacroBar label="Fibre" value={dashboardData.total_fibre || 0} max={30} color="bg-amber-400" />
                  </div>
                </div>

                {/* Chronological Timeline */}
                <div className="w-full md:col-span-2 rounded-2xl md:rounded-3xl backdrop-blur-xl p-4 md:p-6 overflow-hidden" style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}` }}>
                  <div className="flex items-center justify-between mb-3 md:mb-4 px-1 md:px-0">
                    <h3 className="text-[10px] md:text-xs uppercase tracking-[0.15em] font-semibold flex items-center gap-2" style={{ color: T('--text-secondary') }}>
                      <Clock size={12} /> Nutrition Timeline
                    </h3>
                    <span className="text-[10px] font-medium px-2 py-0.5 rounded-full tabular-nums" style={{ color: T('--text-muted'), background: T('--bg-input') }}>
                      {dashboardData.recent_meals.length} meal{dashboardData.recent_meals.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                  <div className="space-y-0.5">
                    <AnimatePresence>
                      {dashboardData.recent_meals.map((meal, i) => (
                        <MealTimelineEntry key={meal.id} meal={meal} index={i}
                          expanded={expandedMeal === meal.id}
                          onToggle={() => setExpandedMeal(expandedMeal === meal.id ? null : meal.id)}
                          onDelete={() => handleDeleteMeal(meal.id)} />
                      ))}
                    </AnimatePresence>
                  </div>
                </div>
              </>
            ) : (
              <div className="w-full md:col-span-3 rounded-2xl md:rounded-3xl backdrop-blur-xl p-8 md:p-14 text-center flex flex-col items-center justify-center min-h-[260px] md:min-h-[300px] relative overflow-hidden group" style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}` }}>
                <div className="absolute -top-10 -left-10 w-40 h-40 bg-purple-500/5 blur-[50px] rounded-full"></div>
                <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-indigo-500/5 blur-[50px] rounded-full"></div>
                <div className="w-14 h-14 rounded-full bg-white/[0.03] border border-white/[0.05] flex items-center justify-center mb-5 group-hover:scale-105 transition-transform duration-500">
                  <Sparkles className="text-purple-300/40" size={22} />
                </div>
                <h3 className="font-display text-xl md:text-2xl font-medium tracking-tight mb-2">
                  {isSelectedToday ? "Your day awaits 🌿" : "A quiet day in your journal"}
                </h3>
                <p className="text-[#a1a1aa] text-sm max-w-md mx-auto leading-relaxed font-light">
                  {isSelectedToday ? "Log your first meal to see your wellness rhythm come alive." : "No wellness data was logged on this day."}
                </p>
                {isSelectedToday && (
                  <motion.a href="/chat" whileHover={{ scale: 1.03 }} whileTap={{ scale: 0.97 }}
                    className="mt-6 px-6 py-2.5 bg-white text-black font-semibold text-xs md:text-sm rounded-full shadow-[0_4px_20px_rgba(255,255,255,0.1)] hover:shadow-[0_4px_25px_rgba(255,255,255,0.2)] transition-all duration-300 cursor-pointer">
                    Log a Meal
                  </motion.a>
                )}
              </div>
            )}
          </div>

        </motion.div>
      </AnimatePresence>
    </div>
  );
}

/* ═══ SUB-COMPONENTS ═══ */

function CalorieSummary({ data }) {
  const cal = useCountUp(Math.round(data.total_calories || 0));
  const compactMacros = [
    { label: 'Protein', value: Math.round(data.total_protein || 0), unit: 'g', color: 'rgb(52,211,153)' },
    { label: 'Carbs', value: Math.round(data.total_carbs || 0), unit: 'g', color: 'rgb(129,140,248)' },
    { label: 'Fats', value: Math.round(data.total_fats || 0), unit: 'g', color: 'rgb(251,113,133)' },
  ];
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.08, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="flex items-center justify-between rounded-2xl md:rounded-3xl backdrop-blur-xl px-5 py-4 md:px-8 md:py-5"
      style={{ background: T('--bg-card'), border: `1px solid ${T('--border-subtle')}` }}
    >
      <div className="flex items-center gap-3" ref={cal.ref}>
        <div className="w-9 h-9 md:w-10 md:h-10 rounded-xl flex items-center justify-center bg-orange-500/10">
          <Flame size={18} className="text-orange-400" />
        </div>
        <div>
          <p className="font-display text-2xl md:text-3xl font-semibold tabular-nums tracking-tight leading-none">
            {cal.value}
            <span className="text-xs md:text-sm font-normal ml-1" style={{ color: T('--text-muted') }}>kcal</span>
          </p>
          <span className="text-[10px] font-medium uppercase tracking-widest" style={{ color: T('--text-muted') }}>Total today</span>
        </div>
      </div>
      <div className="flex items-center gap-4 md:gap-6">
        {compactMacros.map((m) => (
          <div key={m.label} className="flex flex-col items-center">
            <span className="font-display text-sm md:text-base font-semibold tabular-nums" style={{ color: m.color }}>{m.value}<span className="text-[9px] font-normal opacity-60">{m.unit}</span></span>
            <span className="text-[8px] md:text-[9px] uppercase tracking-widest font-medium" style={{ color: T('--text-muted') }}>{m.label}</span>
          </div>
        ))}
      </div>
    </motion.div>
  );
}

const MACRO_META = {
  Protein: { target: 60, emoji: '🥩', gradient: 'from-emerald-500 to-emerald-400' },
  Carbs:   { target: 250, emoji: '🌾', gradient: 'from-indigo-500 to-indigo-400' },
  Fats:    { target: 65, emoji: '🥑', gradient: 'from-rose-500 to-rose-400' },
  Fibre:   { target: 25, emoji: '🥬', gradient: 'from-amber-500 to-amber-400' },
};

function MacroBar({ label, value, max, color }) {
  const pct = Math.min(100, Math.round((value / max) * 100));
  const meta = MACRO_META[label] || {};
  const targetPct = meta.target ? Math.min(100, Math.round((meta.target / max) * 100)) : null;

  return (
    <div className="group py-1">
      <div className="flex items-baseline justify-between mb-1.5">
        <div className="flex items-center gap-1.5">
          <span className="text-xs" aria-hidden>{meta.emoji}</span>
          <span className="text-xs md:text-sm font-medium" style={{ color: T('--text-primary') }}>{label}</span>
        </div>
        <div className="flex items-baseline gap-1.5">
          <span className="font-display text-sm md:text-base font-semibold tabular-nums" style={{ color: T('--text-primary') }}>{Math.round(value)}</span>
          <span className="text-[10px] tabular-nums" style={{ color: T('--text-muted') }}>/ {meta.target || max}g</span>
          <span className="text-[10px] font-medium tabular-nums ml-0.5 px-1.5 py-0.5 rounded-full" style={{
            color: pct >= 80 ? 'rgb(34,197,94)' : pct >= 40 ? T('--text-secondary') : 'rgb(251,146,60)',
            background: pct >= 80 ? 'rgba(34,197,94,0.1)' : pct >= 40 ? T('--bg-card') : 'rgba(251,146,60,0.1)'
          }}>{pct}%</span>
        </div>
      </div>
      <div className="relative h-2 w-full rounded-full overflow-hidden" style={{ background: T('--bar-track') }}>
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 1.2, ease: [0.16, 1, 0.3, 1] }}
          className={`h-full bg-gradient-to-r ${meta.gradient || color} rounded-full relative`}
        >
          <div className="absolute inset-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-500" style={{ boxShadow: `0 0 12px 2px rgba(139,92,246,0.15)` }} />
        </motion.div>
        {targetPct && (
          <div className="absolute top-0 h-full w-px opacity-30" style={{ left: `${targetPct}%`, background: T('--text-secondary') }} />
        )}
      </div>
    </div>
  );
}

function MealTimelineEntry({ meal, index, expanded, onToggle, onDelete }) {
  const tags = meal.tags || [];
  const foodParts = (meal.description || '').split(',');
  const mainFood = foodParts[0]?.trim();
  const sideFoods = foodParts.slice(1).map(s => s.trim()).filter(Boolean).join(', ');

  const macroPills = [
    { label: 'P', value: meal.protein, color: 'emerald' },
    { label: 'C', value: meal.carbs, color: 'indigo' },
    { label: 'F', value: meal.fats, color: 'rose' },
  ];
  if (meal.fibre > 0) macroPills.push({ label: 'Fi', value: meal.fibre, color: 'amber' });

  const bulletClass = meal.is_alcohol
    ? "from-rose-500 to-amber-500 shadow-[0_0_8px_rgba(239,68,68,0.5)]"
    : "from-purple-400 to-indigo-400 shadow-[0_0_8px_rgba(139,92,246,0.3)]";

  const mobileBulletClass = meal.is_alcohol
    ? "bg-rose-500/80 shadow-[0_0_6px_rgba(239,68,68,0.5)]"
    : "bg-purple-400/60 shadow-[0_0_6px_rgba(167,139,250,0.3)]";

  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, height: 0 }}
      transition={{ delay: index * 0.05, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="group rounded-xl md:rounded-2xl transition-all duration-300 overflow-hidden"
      style={{
        borderBottom: `1px solid ${T('--border-subtle')}`,
        background: meal.is_alcohol ? 'rgba(239, 68, 68, 0.02)' : 'transparent'
      }}
    >
      {/* ── MOBILE layout ── */}
      <div className="block md:hidden" onClick={onToggle}>
        <div className="px-3.5 py-4 cursor-pointer active:opacity-80 transition-opacity">
          <div className="flex items-start justify-between gap-3">
            <div className="flex-1 min-w-0">
              <div className="flex flex-wrap items-center gap-2 mb-1.5">
                <div className={`w-1.5 h-1.5 rounded-full ${mobileBulletClass} shrink-0`}></div>
                <span className="text-[10px] tabular-nums font-medium" style={{ color: T('--text-muted') }}>{meal.time || '—'}</span>
                {meal.meal_type && (
                  <span className="text-[7px] uppercase tracking-widest px-1.5 py-0.5 rounded-full font-bold animate-pulse" 
                    style={{ 
                      color: meal.is_alcohol ? 'rgb(239,68,68)' : T('--tag-purple-text'), 
                      background: meal.is_alcohol ? 'rgba(239,68,68,0.1)' : T('--tag-purple-bg') 
                    }}
                  >
                    {meal.is_alcohol ? '🍷 alcohol' : meal.meal_type}
                  </span>
                )}
                {tags.map((t, i) => (
                  <span key={i} className="text-[7px] uppercase tracking-widest px-1.5 py-0.5 rounded-full font-bold" style={{ color: T('--tag-amber-text'), background: T('--tag-amber-bg') }}>
                    {t}
                  </span>
                ))}
              </div>
              <p className="font-semibold text-[14px] leading-snug pl-3.5" style={{ color: T('--text-primary') }}>{mainFood}</p>
              {sideFoods && <p className="text-[11px] leading-snug pl-3.5 mt-1" style={{ color: T('--text-muted') }}>{sideFoods}</p>}
            </div>
            <div className="flex flex-col items-end gap-0.5 shrink-0">
              <p className="font-display font-semibold text-base tabular-nums leading-none" style={{ color: meal.is_alcohol ? 'rgb(239,68,68)' : T('--text-primary') }}>
                {meal.calories || '—'}
              </p>
              <span className="text-[9px] font-medium" style={{ color: T('--text-muted') }}>kcal</span>
            </div>
          </div>
        </div>
        <AnimatePresence>
          {expanded && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1] }} className="overflow-hidden">
              <div className="px-3.5 pb-4 pl-7">
                <div className="flex flex-wrap gap-1.5 mb-2.5">
                  {macroPills.map((m, i) => (
                    <motion.span key={m.label} initial={{ opacity: 0, scale: 0.8 }} animate={{ opacity: 1, scale: 1 }} transition={{ delay: i * 0.05 }}
                      className={`text-[10px] font-semibold px-2 py-1 rounded-lg tabular-nums bg-${m.color}-500/10 text-${m.color}-500`}>
                      {Math.round(m.value || 0)}g <span className="font-normal opacity-70">{m.label}</span>
                    </motion.span>
                  ))}
                </div>
                {meal.normalized && <p className="text-[10px]" style={{ color: T('--text-muted') }}>{meal.normalized}</p>}
                <button onClick={(e) => { e.stopPropagation(); onDelete(); }}
                  className="flex items-center gap-1.5 text-[10px] font-medium mt-3 px-2.5 py-1.5 rounded-lg transition-colors active:scale-95 cursor-pointer"
                  style={{ color: 'rgb(244,63,94)', background: 'rgba(244,63,94,0.08)' }}>
                  <Trash2 size={10} /> Remove
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* ── DESKTOP layout ── */}
      <div className="hidden md:block">
        <div className="flex items-center gap-4 py-4 px-5 cursor-pointer rounded-xl transition-all duration-300" onClick={onToggle}
          style={{ '--hover-bg': T('--bg-card-hover') }}>
          <div className="w-16 shrink-0 text-right">
            <span className="text-[11px] tabular-nums font-medium" style={{ color: T('--text-muted') }}>{meal.time || '—'}</span>
          </div>
          <div className="flex flex-col items-center shrink-0">
            <div className={`w-2.5 h-2.5 rounded-full bg-gradient-to-br ${bulletClass}`}></div>
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              {meal.meal_type && (
                <span className="text-[8px] uppercase tracking-widest px-2 py-0.5 rounded-full font-bold" 
                  style={{ 
                    color: meal.is_alcohol ? 'rgb(239,68,68)' : T('--tag-purple-text'), 
                    background: meal.is_alcohol ? 'rgba(239,68,68,0.1)' : T('--tag-purple-bg') 
                  }}
                >
                  {meal.is_alcohol ? '🍷 alcohol' : meal.meal_type}
                </span>
              )}
              {tags.map((t, i) => (
                <span key={i} className="text-[7px] uppercase tracking-widest px-1.5 py-0.5 rounded-full font-bold" style={{ color: T('--tag-amber-text'), background: T('--tag-amber-bg') }}>
                  {t}
                </span>
              ))}
            </div>
            <p className="font-semibold text-[15px] leading-snug truncate" style={{ color: T('--text-primary') }}>{mainFood}</p>
            {sideFoods && <p className="text-[12px] truncate mt-0.5" style={{ color: T('--text-muted') }}>{sideFoods}</p>}
          </div>
          <div className="flex items-center gap-4 shrink-0">
            <div className="text-right">
              <p className="font-display font-semibold text-xl tabular-nums leading-none" style={{ color: meal.is_alcohol ? 'rgb(239,68,68)' : T('--text-primary') }}>
                {meal.calories || '—'}
              </p>
              <span className="text-[9px] font-medium" style={{ color: T('--text-muted') }}>kcal</span>
            </div>
            <button onClick={(e) => { e.stopPropagation(); onDelete(); }}
              className="opacity-0 group-hover:opacity-100 p-2 transition-all rounded-xl active:scale-90 cursor-pointer"
              style={{ color: T('--text-muted') }}>
              <Trash2 size={14} />
            </button>
            <div className="opacity-40 group-hover:opacity-70 transition-opacity" style={{ color: T('--text-muted') }}>
              {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </div>
          </div>
        </div>
        <AnimatePresence>
          {expanded && (
            <motion.div initial={{ height: 0, opacity: 0 }} animate={{ height: 'auto', opacity: 1 }} exit={{ height: 0, opacity: 0 }} transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }} className="overflow-hidden">
              <div className="px-5 pb-4 ml-[calc(4rem+1.75rem)]">
                <div className="flex gap-2 mb-2">
                  {macroPills.map((m, i) => (
                    <motion.span key={m.label} initial={{ opacity: 0, y: 4 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: i * 0.06 }}
                      className={`text-[11px] font-semibold px-2.5 py-1 rounded-lg tabular-nums bg-${m.color}-500/10 text-${m.color}-500`}>
                      {Math.round(m.value || 0)}g <span className="font-normal opacity-60">{m.label === 'P' ? 'protein' : m.label === 'C' ? 'carbs' : m.label === 'F' ? 'fats' : 'fibre'}</span>
                    </motion.span>
                  ))}
                </div>
                {meal.normalized && <p className="text-[11px] mt-1" style={{ color: T('--text-muted') }}>{meal.normalized}</p>}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.div>
  );
}
