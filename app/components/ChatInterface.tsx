import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Message, FunctionCall } from '../types';
import { streamMessage, SessionData, createSession } from '../services/api';
import { AGENT_APP_NAME, SUGGESTIONS } from '../constants';
import MessageBubble from './MessageBubble';
import InputArea from './InputArea';
import HeroSection from './HeroSection';
import { AlertCircle, MessageSquarePlus, Sun, Moon } from 'lucide-react';
import { useTheme } from '../contexts/ThemeContext';

const STORAGE_KEYS = {
  SESSION: 'iitm_advisor_session'
};

const generateUUID = () => {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
};

const ChatInterface: React.FC = () => {
  const { theme, toggleTheme } = useTheme();
  const [messages, setMessages] = useState<Message[]>([]);

  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [sessionData, setSessionData] = useState<SessionData | null>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEYS.SESSION);
      if (stored) {
        return JSON.parse(stored);
      }
    } catch (e) {
      console.warn('Failed to load session from storage', e);
    }
    return null;
  });
  
  const [userId] = useState(() => "web-user");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const accumulatedTextRef = useRef<string>('');
  const functionCallsRef = useRef<FunctionCall[]>([]);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Persistence effects
  useEffect(() => {
    if (sessionData) {
      try {
        localStorage.setItem(STORAGE_KEYS.SESSION, JSON.stringify(sessionData));
      } catch (e) {
        console.warn('Failed to save session to storage', e);
      }
    } else {
      localStorage.removeItem(STORAGE_KEYS.SESSION);
    }
  }, [sessionData]);

  const handleNewChat = useCallback(() => {
    if (messages.length > 0 && window.confirm('Are you sure you want to start a new chat? Current history will be cleared.')) {
      setSessionData(null);
      setMessages([]);
      setError(null);
    }
  }, [messages.length]);

  const handleSend = useCallback(async (text: string) => {
    if (!text.trim()) return;

    let currentSessionData = sessionData;
    let isNewSession = false;
    
    if (!currentSessionData) {
      const generatedSessionId = generateUUID();
      currentSessionData = {
        userId,
        sessionId: generatedSessionId,
        appName: AGENT_APP_NAME
      };
      setSessionData(currentSessionData);
      isNewSession = true;
      console.log('Created new session locally:', generatedSessionId);
    }

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: Date.now(),
    };

    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);

    // Add placeholder thinking message
    const botMsgId = (Date.now() + 1).toString();
    const botMsg: Message = {
      id: botMsgId,
      role: 'bot',
      content: '',
      timestamp: Date.now(),
      isThinking: true
    };
    
    setMessages(prev => [...prev, botMsg]);
    accumulatedTextRef.current = ''; 
    functionCallsRef.current = []; 

    const processStream = async (sessionId: string) => {
      let eventReceived = false;

      for await (const event of streamMessage(text, sessionId)) {
        eventReceived = true;
        
        if (event.content && event.content.parts) {
          const textParts: string[] = [];
          const newFunctionCalls: FunctionCall[] = [];
          
          for (const part of event.content.parts) {
            if (part.text) textParts.push(part.text);
            if (part.functionCall) {
              newFunctionCalls.push({
                name: part.functionCall.name || 'unknown',
                args: part.functionCall.args || {},
                id: part.functionCall.id
              });
            }
          }

          if (newFunctionCalls.length > 0) {
            functionCallsRef.current = [...functionCallsRef.current, ...newFunctionCalls];
            setMessages(prev => prev.map(msg => {
              if (msg.id === botMsgId) {
                return {
                  ...msg,
                  functionCalls: [...functionCallsRef.current],
                  isThinking: !accumulatedTextRef.current.trim()
                };
              }
              return msg;
            }));
          }

          if (textParts.length > 0) {
            const newText = textParts.join('');
            accumulatedTextRef.current += newText;
            setMessages(prev => prev.map(msg => {
              if (msg.id === botMsgId) {
                return {
                  ...msg,
                  content: accumulatedTextRef.current,
                  isThinking: false
                };
              }
              return msg;
            }));
          }
        }
      }

      // Force thinking false when stream ends
      setMessages(prev => prev.map(msg => {
        if (msg.id === botMsgId) {
          return {
            ...msg,
            isThinking: false
          };
        }
        return msg;
      }));

      if (!eventReceived) {
        if (accumulatedTextRef.current === '' && functionCallsRef.current.length === 0) {
          throw new Error("No response received");
        }
      }
    };

    try {
      if (isNewSession) {
        console.log('Initializing session on backend...');
        await createSession(currentSessionData.sessionId, userId);
      }

      try {
        await processStream(currentSessionData.sessionId);
      } catch (err) {
        // Check for session not found or no response, and retry once
        const isSessionError = err instanceof Error && err.message.includes("Session not found");
        const isNoResponse = err instanceof Error && err.message === "No response received";

        if (isSessionError || isNoResponse) {
          console.log("Session issue encountered, attempting to recreate and retry...", err);
          await createSession(currentSessionData.sessionId, userId);
          
          // Reset for retry
          accumulatedTextRef.current = ''; 
          functionCallsRef.current = []; 
          
          await processStream(currentSessionData.sessionId);
        } else {
          throw err;
        }
      }

    } catch (err) {
      console.error('Error sending message:', err);
      const errorMessage = err instanceof Error 
        ? err.message 
        : "Failed to connect to the Advisor Agent. Please try again later.";
      
      setError(errorMessage);
      
      setMessages(prev => prev.map(msg => {
        if (msg.id === botMsgId) {
          return {
            ...msg,
            content: `Sorry, there was an error: ${errorMessage}`,
            isThinking: false
          };
        }
        return msg;
      }));
    } finally {
      setIsLoading(false);
    }
  }, [sessionData, userId]);

  return (
    <div className="flex flex-col h-full bg-white dark:bg-black relative">
      <div className="absolute top-4 right-4 z-20 flex items-center gap-2">
        <button 
          onClick={toggleTheme}
          className="p-2 bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm text-slate-600 dark:text-slate-300 rounded-full shadow-sm border border-slate-200 dark:border-slate-700 hover:bg-slate-50 dark:hover:bg-slate-700 transition-all"
          title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
        >
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
        </button>
        <button 
          onClick={handleNewChat}
          disabled={isLoading}
          className="p-2 bg-white/90 dark:bg-slate-800/90 backdrop-blur-sm text-slate-600 dark:text-slate-300 rounded-full shadow-sm border border-slate-200 dark:border-slate-700 hover:bg-primary-50 dark:hover:bg-slate-700 hover:text-primary-600 dark:hover:text-primary-400 hover:border-primary-200 dark:hover:border-primary-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed group"
          title="Start New Chat"
        >
          <MessageSquarePlus size={20} className="group-hover:scale-110 transition-transform" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 md:p-8 scroll-smooth">
        {messages.length === 0 ? (
          <div className="max-w-5xl mx-auto h-full flex flex-col">
            <HeroSection onSuggestionClick={handleSend} suggestions={SUGGESTIONS} />
          </div>
        ) : (
          <div className="max-w-5xl mx-auto min-h-full flex flex-col justify-end">
            {messages.map((msg) => (
              <MessageBubble key={msg.id} message={msg} />
            ))}
            
            {error && (
              <div className="flex items-center gap-2 p-4 mb-6 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg text-red-700 dark:text-red-400 text-sm animate-in fade-in">
                <AlertCircle size={16} />
                {error}
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      <InputArea 
        onSend={handleSend} 
        disabled={isLoading} 
        suggestions={messages.length > 0 && messages.length < 3 ? SUGGESTIONS : []}
      />
    </div>
  );
};

export default ChatInterface;
