import { create } from 'zustand'

const getInitialTheme = () => {
  if (typeof window !== 'undefined') {
    const saved = localStorage.getItem('wellora-theme');
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }
  return 'dark';
};

export const useStore = create((set, get) => ({
  user: { id: 1, name: "Test User" },
  setUser: (user) => set({ user }),
  
  messages: [
    { id: 1, text: "Hi there! I'm Wellora, your personal wellness companion. What have you had to eat today? You can just tell me naturally like 'I had 2 idlis and a coffee'.", sender: "ai" }
  ],
  addMessage: (msg) => set((state) => ({ messages: [...state.messages, msg] })),
  
  dashboardData: null,
  setDashboardData: (data) => set({ dashboardData: data }),

  // Theme
  theme: getInitialTheme(),
  toggleTheme: () => {
    const next = get().theme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('wellora-theme', next);
    document.documentElement.classList.toggle('light', next === 'light');
    set({ theme: next });
  },
}))
