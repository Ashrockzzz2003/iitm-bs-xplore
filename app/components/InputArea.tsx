import React, { useState, useRef, useEffect } from 'react';
import { Send, Sparkles } from 'lucide-react';

interface InputAreaProps {
  onSend: (text: string) => void;
  disabled: boolean;
  suggestions: string[];
}

const InputArea: React.FC<InputAreaProps> = ({ onSend, disabled, suggestions }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e?: React.FormEvent) => {
    e?.preventDefault();
    if (input.trim() && !disabled) {
      onSend(input.trim());
      setInput('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  return (
    <div className="relative z-10">
      {/* Gradient Fade for scroll under */}
      <div className="absolute bottom-full left-0 w-full h-12 bg-gradient-to-t from-white via-white/80 to-transparent dark:from-black dark:via-black/80 pointer-events-none"></div>
      
      <div className="bg-white dark:bg-black p-4 md:p-6 pt-2">
        <div className="max-w-5xl mx-auto space-y-4">
          
          {/* Suggestions (Chips) */}
          {suggestions.length > 0 && !disabled && (
             <div className="flex overflow-x-auto gap-2 pb-2 no-scrollbar mask-fade-right snap-x">
               {suggestions.map((s, i) => (
                 <button
                   key={i}
                   onClick={() => onSend(s)}
                   className="flex-shrink-0 snap-start px-3 py-1.5 bg-slate-50 dark:bg-neutral-900 hover:bg-primary-50 dark:hover:bg-primary-900/20 text-xs text-slate-600 dark:text-slate-300 hover:text-primary-700 dark:hover:text-primary-400 border border-slate-200 dark:border-neutral-800 hover:border-primary-200 dark:hover:border-primary-600 rounded-full transition-colors whitespace-nowrap flex items-center gap-1.5 group"
                 >
                   <Sparkles size={12} className="text-amber-500 dark:text-amber-400 group-hover:rotate-12 transition-transform" />
                   {s}
                 </button>
               ))}
             </div>
          )}

          <div className="relative bg-slate-50 dark:bg-neutral-900/50 p-2 rounded-[24px] border border-slate-200 dark:border-neutral-800 shadow-sm focus-within:border-slate-300 dark:focus-within:border-neutral-700 transition-all duration-300">
            <form onSubmit={handleSubmit} className="flex items-end gap-2">
              
              <textarea
                ref={textareaRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={disabled}
                placeholder="Ask anything about IITM BS..."
                className="flex-1 bg-transparent border-none focus:ring-0 outline-none text-sm md:text-base text-slate-800 dark:text-slate-200 placeholder:text-slate-400 dark:placeholder:text-slate-500 resize-none py-3 px-3 min-h-[44px] max-h-[160px]"
                rows={1}
              />
              
              {/* Send Button */}
              <button
                type="submit"
                disabled={!input.trim() || disabled}
                className={`p-2.5 rounded-xl flex-shrink-0 transition-all duration-200 mb-0.5 ${
                  input.trim() && !disabled
                    ? 'bg-primary-600 dark:bg-primary-600 text-white shadow-md hover:bg-primary-700 dark:hover:bg-primary-500 hover:scale-105 active:scale-95'
                    : 'bg-slate-200 dark:bg-slate-700 text-slate-400 dark:text-slate-500 cursor-not-allowed'
                }`}
              >
                <Send size={20} className={input.trim() ? 'ml-0.5' : ''} />
              </button>
            </form>
          </div>
          
          <div className="text-center">
             <p className="text-[10px] text-slate-400 dark:text-slate-500 font-medium">
               AI can make mistakes. Verify with official documents.
             </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InputArea;