import { apiUrl } from '../api';
import React, { useState, useEffect, useRef } from 'react';

export default function SarvamChatbot({ isOpen, onClose }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: 'Namaste! I am your Sarvam Highway Copilot. I analyze live pavement quality telemetry, pothole coordinates, and road maintenance priorities across Indian highways. How can I assist you today?'
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    if (isOpen) scrollToBottom();
  }, [messages, isOpen]);

  const handleSend = async (textToSend) => {
    const text = textToSend || input;
    if (!text.trim() || loading) return;

    const newMsgs = [...messages, { role: 'user', content: text }];
    setMessages(newMsgs);
    setInput('');
    setLoading(true);

    try {
      const res = await fetch(apiUrl('/api/chat'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: newMsgs.map(m => ({ role: m.role, content: m.content }))
        })
      });
      const data = await res.json();
      if (res.ok && data.reply) {
        setMessages([...newMsgs, {
          role: 'assistant',
          content: data.reply
        }]);
      } else {
        setMessages([...newMsgs, {
          role: 'assistant',
          content: 'Unable to reach the copilot service. Please try again shortly.'
        }]);
      }
    } catch {
      setMessages([...newMsgs, {
        role: 'assistant',
        content: 'Connection error while contacting the road intelligence server.'
      }]);
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full sm:w-[420px] bg-white border-l border-slate-200 shadow-2xl flex flex-col font-sans">
      {/* Header */}
      <div className="p-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-bold text-sm text-slate-900 tracking-tight">Sarvam Highway Copilot</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-100/70 text-blue-800 border border-blue-200">
              Sarvam-105B Indic
            </span>
          </div>
          <p className="text-[11px] text-slate-500 mt-0.5">Civil Road AI Assistant • English & Hindi</p>
        </div>
        <button
          onClick={onClose}
          className="text-xs px-2.5 py-1 text-slate-500 hover:text-slate-900 hover:bg-slate-200 rounded transition"
        >
          Close
        </button>
      </div>

      {/* Chat Messages Feed */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3 bg-slate-50/50 text-xs">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
          >
            <div
              className={`max-w-[85%] rounded-lg p-3 leading-relaxed ${m.role === 'user'
                  ? 'bg-slate-900 text-white'
                  : 'bg-white border border-slate-200 text-slate-800 shadow-sm'
                }`}
            >
              {m.content}
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-center gap-1.5 text-slate-400 text-xs py-1">
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse" />
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse delay-100" />
            <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-pulse delay-200" />
            <span className="text-[11px]">Sarvam Copilot is analyzing road telemetry...</span>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Suggested Quick Prompts */}
      <div className="p-2.5 border-t border-slate-100 bg-white flex gap-1.5 overflow-x-auto text-[11px]">
        {[
          'Which road is in worst condition?',
          'How is NH-44 Expressway?',
          'What is ASTM PCI index?',
          'सड़क की स्थिति कैसी है?'
        ].map((prompt, i) => (
          <button
            key={i}
            onClick={() => handleSend(prompt)}
            className="whitespace-nowrap px-2.5 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSend();
        }}
        className="p-3 border-t border-slate-200 bg-white flex items-center gap-2"
      >
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask Sarvam Highway Copilot in English or Hindi..."
          className="flex-1 text-xs border border-slate-200 rounded-lg px-3 py-2 bg-slate-50 focus:outline-none focus:ring-1 focus:ring-slate-900"
        />
        <button
          type="submit"
          disabled={!input.trim() || loading}
          className="px-4 py-2 bg-slate-900 hover:bg-slate-800 disabled:opacity-40 text-white rounded-lg text-xs font-semibold transition"
        >
          Send
        </button>
      </form>
    </div>
  );
}
