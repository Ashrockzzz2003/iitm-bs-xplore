import React from 'react';
import { Sparkles, BookOpen, Scale, FileText } from 'lucide-react';
import { APP_NAME } from '../constants';
import Logo from './Logo';

interface HeroSectionProps {
  onSuggestionClick: (text: string) => void;
  suggestions: string[];
}

const HeroSection: React.FC<HeroSectionProps> = ({ onSuggestionClick, suggestions }) => {
  return (
    <div className="flex-1 flex flex-col items-center justify-center p-4 md:p-8 animate-in fade-in duration-700">
      <div className="max-w-2xl w-full space-y-8 text-center">
        
        {/* Logo/Icon */}
        <div className="relative mx-auto w-20 h-20 bg-white dark:bg-neutral-900 rounded-2xl shadow-xl flex items-center justify-center border border-slate-100 dark:border-neutral-800 mb-6 group transition-transform hover:scale-105 duration-300">
          <div className="absolute inset-0 bg-gradient-to-br from-primary-100 to-transparent dark:from-primary-900/20 rounded-2xl opacity-50"></div>
          <Logo className="w-12 h-12 relative z-10" />
        </div>

        {/* Title & Subtitle */}
        <div className="space-y-3">
          <h1 className="text-3xl md:text-4xl font-bold text-slate-900 dark:text-white tracking-tight">
            {APP_NAME}
          </h1>
          <p className="text-slate-500 dark:text-slate-400 text-lg max-w-lg mx-auto leading-relaxed">
            Your intelligent academic companion. Ask about courses, policies, and grades.
          </p>
        </div>

        {/* Suggestion Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl mt-8">
          {suggestions.map((suggestion, idx) => {
            // Assign icons based on content (simple heuristic)
            let Icon = Sparkles;
            if (suggestion.toLowerCase().includes('course') || suggestion.toLowerCase().includes('syllabus')) Icon = BookOpen;
            if (suggestion.toLowerCase().includes('grade') || suggestion.toLowerCase().includes('gpa')) Icon = Scale;
            if (suggestion.toLowerCase().includes('handbook') || suggestion.toLowerCase().includes('rule')) Icon = FileText;

            return (
              <button
                key={idx}
                onClick={() => onSuggestionClick(suggestion)}
                className="flex items-start gap-3 p-4 text-left bg-white dark:bg-neutral-900 hover:bg-slate-50 dark:hover:bg-neutral-800 border border-slate-200 dark:border-neutral-800 hover:border-primary-200 dark:hover:border-primary-500/30 rounded-xl shadow-sm hover:shadow-md transition-all duration-200 group"
              >
                <div className="mt-0.5 p-2 bg-slate-50 dark:bg-neutral-800 rounded-lg text-slate-500 dark:text-slate-400 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                  <Icon size={18} />
                </div>
                <span className="text-sm text-slate-700 dark:text-slate-300 group-hover:text-slate-900 dark:group-hover:text-slate-100 font-medium">
                  {suggestion}
                </span>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default HeroSection;
