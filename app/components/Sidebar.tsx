import React, { useState } from 'react';
import { Server, Database, FileSearch, Code2, Users, ChevronDown, ChevronRight, Info } from 'lucide-react';
import { DEVELOPERS, APP_NAME } from '../constants';
import Logo from './Logo';

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ isOpen, onClose }) => {
  const [isArchOpen, setIsArchOpen] = useState(true);

  return (
    <>
      {/* Overlay for mobile */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/20 dark:bg-black/40 backdrop-blur-sm z-40 md:hidden"
          onClick={onClose}
        />
      )}

      <aside 
        className={`
          fixed top-0 left-0 z-50 h-[100dvh] w-80 bg-white dark:bg-neutral-950 border-r border-slate-200 dark:border-neutral-800 shadow-xl transform transition-transform duration-300 ease-in-out flex flex-col
          md:relative md:translate-x-0 md:shadow-none md:z-0
          ${isOpen ? 'translate-x-0' : '-translate-x-full'}
        `}
      >
        <div className="p-6 border-b border-slate-100 dark:border-neutral-800 bg-slate-50/50 dark:bg-neutral-950/50">
          <div className="flex items-center gap-3 text-primary-700 dark:text-primary-400 mb-1">
            <div className="p-2 bg-white dark:bg-neutral-900 rounded-lg shadow-sm border border-primary-100 dark:border-neutral-800">
               <Logo className="w-6 h-6" />
            </div>
            <h1 className="font-bold text-xl tracking-tight text-slate-900 dark:text-slate-100">{APP_NAME}</h1>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-6 space-y-8">
          
          {/* Architecture Section - Collapsible */}
          <section>
            <button 
              onClick={() => setIsArchOpen(!isArchOpen)}
              className="w-full flex items-center justify-between text-sm font-bold text-slate-900 dark:text-slate-100 mb-4 group"
            >
              <div className="flex items-center gap-2">
                <Server size={16} className="text-primary-600 dark:text-primary-400" />
                System Architecture
              </div>
              {isArchOpen ? <ChevronDown size={16} className="text-slate-400" /> : <ChevronRight size={16} className="text-slate-400" />}
            </button>
            
            {isArchOpen && (
              <div className="space-y-4 animate-in slide-in-from-top-2 duration-200">
                <div className="p-3 bg-slate-50 dark:bg-neutral-900/50 rounded-lg border border-slate-100 dark:border-neutral-800 text-xs space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="mt-0.5 p-1.5 bg-amber-100 dark:bg-amber-900/30 rounded-md text-amber-600 dark:text-amber-400"><FileSearch size={14} /></div>
                    <div>
                      <span className="font-semibold block text-slate-700 dark:text-slate-200">File Search Agent</span>
                      <span className="text-slate-500 dark:text-slate-400 leading-tight">Semantically searches Handbook & Grading PDFs.</span>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 pt-2 border-t border-slate-200 dark:border-neutral-800/50">
                    <div className="mt-0.5 p-1.5 bg-blue-100 dark:bg-blue-900/30 rounded-md text-blue-600 dark:text-blue-400"><Database size={14} /></div>
                    <div>
                      <span className="font-semibold block text-slate-700 dark:text-slate-200">Neon PostgreSQL</span>
                      <span className="text-slate-500 dark:text-slate-400 leading-tight">Structured SQL queries for course data & catalog.</span>
                    </div>
                  </div>
                  <div className="flex items-start gap-3 pt-2 border-t border-slate-200 dark:border-neutral-800/50">
                    <div className="mt-0.5 p-1.5 bg-purple-100 dark:bg-purple-900/30 rounded-md text-purple-600 dark:text-purple-400"><Code2 size={14} /></div>
                    <div>
                      <span className="font-semibold block text-slate-700 dark:text-slate-200">Tool Routing</span>
                      <span className="text-slate-500 dark:text-slate-400 leading-tight">Intelligently switches between Policy Search and DB Query.</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* About Section */}
          <section>
             <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-3 flex items-center gap-2">
               <Info size={16} className="text-primary-600 dark:text-primary-400" />
               About
             </h3>
             <div className="bg-slate-50 dark:bg-neutral-900/30 p-3 rounded-lg border border-slate-100 dark:border-neutral-800/50">
               <p className="text-xs text-slate-600 dark:text-slate-300 leading-relaxed">
                 The IITM Advisor Agent helps students query course information, grading policies, and the student handbook using natural language.
               </p>
             </div>
          </section>

          {/* Developers Section */}
          <section>
            <h3 className="text-sm font-bold text-slate-900 dark:text-slate-100 mb-4 flex items-center gap-2">
              <Users size={16} className="text-primary-600 dark:text-primary-400" />
              Developers
            </h3>
            <div className="space-y-3">
              {DEVELOPERS.map((dev, index) => (
                <div key={index} className="group flex items-center gap-3 p-2.5 rounded-lg border border-slate-100 dark:border-neutral-800 hover:border-primary-200 dark:hover:border-primary-600 hover:bg-primary-50 dark:hover:bg-neutral-900 transition-all">
                  <div className="w-8 h-8 rounded-full bg-slate-100 dark:bg-neutral-700 flex items-center justify-center text-slate-500 dark:text-slate-300 font-bold text-xs">
                    {dev.name.charAt(0)}
                  </div>
                  <div className="flex flex-col min-w-0">
                    <span className="text-sm font-semibold text-slate-800 dark:text-slate-200 group-hover:text-primary-800 dark:group-hover:text-primary-400 truncate">{dev.name}</span>
                    <a href={`mailto:${dev.email}`} className="text-[10px] text-slate-400 dark:text-slate-500 hover:text-primary-600 dark:hover:text-primary-400 truncate transition-colors">
                      {dev.email}
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="p-4 border-t border-slate-100 dark:border-neutral-800 text-center bg-slate-50/30 dark:bg-neutral-900/30">
           <p className="text-[10px] text-slate-400 dark:text-slate-500 font-medium">
             © 2025 IITM BS Data Science
           </p>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;