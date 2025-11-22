import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Message, Source } from '../types';
import { Bot, User, FileText, Database, ExternalLink, Zap, ChevronDown, ChevronUp, Copy, Check } from 'lucide-react';

interface MessageBubbleProps {
  message: Message;
}

const MessageBubble: React.FC<MessageBubbleProps> = ({ message }) => {
  const isBot = message.role === 'bot';
  const [isToolsExpanded, setIsToolsExpanded] = useState(false);
  const [isSourcesExpanded, setIsSourcesExpanded] = useState(true);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`flex w-full ${isBot ? 'justify-start' : 'justify-end'} mb-6 group animate-in slide-in-from-bottom-2 duration-500`}>
      <div className={`flex max-w-[90%] md:max-w-[85%] lg:max-w-[80%] ${isBot ? 'flex-row' : 'flex-row-reverse'} gap-3`}>
        
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center shadow-sm ${isBot ? 'bg-white dark:bg-neutral-800 border border-slate-200 dark:border-neutral-700 text-primary-600 dark:text-primary-400' : 'bg-slate-900 dark:bg-neutral-700 text-white'}`}>
          {isBot ? <Bot size={18} /> : <User size={18} />}
        </div>

        {/* Content Wrapper */}
        <div className={`flex flex-col ${isBot ? 'items-start' : 'items-end'} w-full min-w-0`}>
          
          {/* Name & Time (Optional, for pro feel) */}
          <div className={`flex items-center gap-2 mb-1 px-1 ${isBot ? '' : 'flex-row-reverse'}`}>
            <span className="text-[11px] font-medium text-slate-900 dark:text-slate-200">
              {isBot ? 'Advisor Agent' : 'You'}
            </span>
            <span className="text-[10px] text-slate-400 dark:text-slate-500">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          </div>

          <div className={`relative px-5 py-4 rounded-2xl shadow-sm text-sm leading-relaxed overflow-hidden group/bubble transition-all ${
            isBot 
              ? 'bg-white dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 text-slate-800 dark:text-slate-200 rounded-tl-none overflow-x-auto' 
              : 'bg-primary-600 dark:bg-primary-700 text-white rounded-tr-none shadow-md'
          }`}>
            
            {/* Copy Button for Bot */}
            {isBot && !message.isThinking && (
              <button 
                onClick={handleCopy}
                className="absolute top-2 right-2 p-1.5 text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 opacity-0 group-hover/bubble:opacity-100 transition-opacity rounded-md hover:bg-slate-100 dark:hover:bg-slate-700"
                title="Copy response"
              >
                {copied ? <Check size={14} className="text-green-500" /> : <Copy size={14} />}
              </button>
            )}

            {message.isThinking ? (
              <div className="flex items-center gap-3 text-slate-500 dark:text-slate-400">
                <div className="flex gap-1 h-5 items-center">
                  <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce [animation-delay:-0.3s]"></span>
                  <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce [animation-delay:-0.15s]"></span>
                  <span className="w-1.5 h-1.5 bg-current rounded-full animate-bounce"></span>
                </div>
                <span className="text-xs animate-pulse">Thinking...</span>
              </div>
            ) : (
              <div className={`prose ${isBot ? 'prose-slate dark:prose-invert' : 'prose-invert'} max-w-none prose-sm prose-p:leading-relaxed prose-pre:bg-slate-800 prose-pre:text-slate-100 prose-pre:border prose-pre:border-slate-700`}>
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {message.content}
                </ReactMarkdown>
              </div>
            )}
          </div>

          {/* Function Calls Section - Collapsible */}
          {isBot && message.functionCalls && message.functionCalls.length > 0 && (
            <div className="mt-2 w-full max-w-md">
              <button 
                onClick={() => setIsToolsExpanded(!isToolsExpanded)}
                className="flex items-center gap-1.5 text-[10px] font-medium text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-300 transition-colors mb-1.5 select-none"
              >
                <Zap size={12} />
                <span>Process Details</span>
                {isToolsExpanded ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
              </button>
              
              {isToolsExpanded && (
                <div className="space-y-2 animate-in slide-in-from-top-2 fade-in duration-200">
                  {message.functionCalls.map((funcCall, idx) => (
                    <div
                      key={idx}
                      className="flex flex-col gap-1.5 p-2.5 bg-slate-50 dark:bg-neutral-900/50 border border-slate-200 dark:border-neutral-800/50 rounded-lg text-xs shadow-sm"
                    >
                      <div className="flex items-center justify-between">
                        <div className="font-mono font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-1.5">
                          <div className="w-1.5 h-1.5 rounded-full bg-blue-500"></div>
                          {funcCall.name}
                        </div>
                        <span className="text-[10px] text-slate-400 font-mono opacity-75">ID: {funcCall.id?.slice(-4)}</span>
                      </div>
                      {Object.keys(funcCall.args || {}).length > 0 && (
                        <div className="bg-white dark:bg-black/50 p-2 rounded border border-slate-100 dark:border-neutral-900/50 font-mono text-[10px] text-slate-600 dark:text-slate-400 overflow-x-auto">
                          <pre>{JSON.stringify(funcCall.args, null, 2)}</pre>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Sources Section - Enhanced */}
          {isBot && message.sources && message.sources.length > 0 && (
            <div className="mt-2 w-full">
               <div className="flex items-center gap-2 mb-2">
                 <div className="h-px flex-1 bg-slate-200 dark:bg-neutral-800"></div>
                 <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider flex items-center gap-1">
                    <FileText size={10} /> Sources
                 </span>
                 <div className="h-px flex-1 bg-slate-200 dark:bg-neutral-800"></div>
               </div>
               
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {message.sources.map((source, idx) => (
                  <a
                    key={idx}
                    href={source.uri.startsWith('http') ? source.uri : '#'}
                    target="_blank"
                    rel="noreferrer"
                    className="group flex items-start gap-2 p-2 bg-white dark:bg-neutral-900 border border-slate-200 dark:border-neutral-800 rounded-lg text-xs text-slate-600 dark:text-slate-300 hover:bg-primary-50 dark:hover:bg-neutral-800/50 hover:border-primary-200 dark:hover:border-primary-500/30 transition-all shadow-sm hover:shadow-md"
                  >
                    <div className="mt-0.5 text-primary-500 dark:text-primary-400">
                       {source.uri.endsWith('.pdf') ? <FileText size={14} /> : <Database size={14} />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium truncate group-hover:text-primary-700 dark:group-hover:text-primary-300 transition-colors">
                        {source.title || "Document Source"}
                      </p>
                      <p className="text-[10px] text-slate-400 truncate font-mono mt-0.5">
                        {source.uri}
                      </p>
                    </div>
                    {source.uri.startsWith('http') && <ExternalLink size={10} className="opacity-0 group-hover:opacity-50 transition-opacity mt-0.5" />}
                  </a>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default MessageBubble;