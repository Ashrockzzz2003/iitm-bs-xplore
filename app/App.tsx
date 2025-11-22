import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import { Menu, X, Sun, Moon } from 'lucide-react';
import { APP_NAME } from './constants';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';

const AppContent: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const { theme, toggleTheme } = useTheme();

  return (
    <div className="flex h-[100dvh] w-full bg-slate-50 dark:bg-black overflow-hidden transition-colors duration-300">
      {/* Background Pattern */}
      <div className="fixed inset-0 z-0 pointer-events-none opacity-40 dark:opacity-20"
           style={{
             backgroundImage: `radial-gradient(circle at 2px 2px, rgb(203 213 225) 1px, transparent 0)`,
             backgroundSize: '24px 24px'
           }}
      ></div>

      {/* Sidebar */}
      <Sidebar isOpen={isSidebarOpen} onClose={() => setIsSidebarOpen(false)} />

      {/* Main Content */}
      <main className="flex-1 flex flex-col h-full w-full relative">
        
        {/* Mobile Header */}
        <header className="md:hidden flex items-center justify-between px-4 py-3 bg-white dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700 z-20">
          <div className="flex items-center gap-2 font-semibold text-slate-800 dark:text-slate-100">
             {APP_NAME}
          </div>
          <div className="flex items-center gap-2">
            <button 
              onClick={toggleTheme}
              className="p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-md transition-colors"
              title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            >
              {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
            </button>
            <button 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="p-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-md transition-colors"
            >
              {isSidebarOpen ? <X size={20} /> : <Menu size={20} />}
            </button>
          </div>
        </header>


        {/* Chat Area */}
        <div className="flex-1 relative h-full">
            <ChatInterface />
        </div>

      </main>
    </div>
  );
};

const App: React.FC = () => {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
};

export default App;