import React, { useState } from 'react';
import { X, Sparkles, Send, Bot, User, ShieldAlert, CheckCircle2, AlertCircle } from 'lucide-react';
import { supabase, isSupabaseConfigured } from '../lib/supabaseClient';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

export default function AIChatDrawer({ isOpen, onClose, subscriptions }) {
  const [messages, setMessages] = useState([
    {
      id: 'msg-1',
      sender: 'bot',
      text: 'Hello! I am your Autopay Guard AI Assistant. Ask me how to cancel any subscription (e.g., "How to cancel Netflix?") or ask natural language questions about your spending!'
    }
  ]);
  const [inputQuery, setInputQuery] = useState('');
  const [isTyping, setIsTyping] = useState(false);

  if (!isOpen) return null;

  const handleSend = async (textToSend) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

    // Add user message
    const userMsg = { id: `user-${Date.now()}`, sender: 'user', text: query };
    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInputQuery('');
    setIsTyping(true);

    try {
      let token = null;
      if (isSupabaseConfigured && supabase) {
        const { data: { session } } = await supabase.auth.getSession();
        token = session?.access_token;
      }

      const headers = { 'Content-Type': 'application/json' };
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }

      const res = await fetch(`${API_BASE_URL}/chatbot/ask`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ query })
      });

      if (res.ok) {
        const data = await res.json();
        let replyText = data.reply || 'AI response received.';

        if (data.query_type === 'cancellation_guide' && data.cancellation_steps?.length > 0) {
          replyText = `📋 **Cancellation Steps for ${data.matched_merchant || 'Service'}**:\n` +
            data.cancellation_steps.join('\n') +
            (data.official_url ? `\n\n🔗 Official URL: ${data.official_url}` : '');
        }

        setMessages(prev => [...prev, { id: `bot-${Date.now()}`, sender: 'bot', text: replyText }]);
        setIsTyping(false);
        return;
      } else {
        console.warn("Backend Chatbot API response not OK:", res.status, res.statusText);
      }
    } catch (err) {
      console.warn("Backend Chatbot API note:", err);
    }

    // Fallback Smart Local Logic
    setTimeout(() => {
      let replyText = "I've analyzed your active subscriptions. ";
      const lowerQ = query.toLowerCase();

      if (lowerQ.includes('renew') || lowerQ.includes('upcoming') || lowerQ.includes('week')) {
        const soon = subscriptions ? subscriptions.filter(s => new Date(s.next_renewal_date || s.next_payment_date) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000)) : [];
        if (soon.length > 0) {
          replyText += `You have ${soon.length} renewal(s) coming up within the next 7 days:\n` + 
            soon.map(s => `• ${s.merchant_name || s.name}: ₹${s.amount} on ${s.next_renewal_date || s.next_payment_date}`).join('\n');
        } else {
          replyText += "Good news! You have no renewals coming up in the next 7 days.";
        }
      } else if (lowerQ.includes('cancel') || lowerQ.includes('save') || lowerQ.includes('trial')) {
        const trials = subscriptions ? subscriptions.filter(s => s.is_free_trial || s.status === 'trial') : [];
        const expensive = subscriptions ? subscriptions.filter(s => parseFloat(s.amount) > 1000) : [];
        
        replyText += `Here is your spending analysis:\n`;
        if (trials.length > 0) {
          replyText += `⚠️ High Priority: Cancel ${trials.map(t => t.merchant_name || t.name).join(', ')} before the free trial converts.\n`;
        }
        if (expensive.length > 0) {
          replyText += `💡 Highest debits: Consider evaluating ${expensive.map(e => e.merchant_name || e.name).join(', ')} (₹${expensive[0]?.amount}/mo).`;
        }
      } else {
        const total = subscriptions ? subscriptions.reduce((acc, s) => acc + (parseFloat(s.amount) || 0), 0) : 0;
        replyText += `Your current total monthly expenditure across ${subscriptions ? subscriptions.length : 0} active subscriptions is ₹${total.toFixed(2)}. Ask me about renewals or cancellations!`;
      }

      setMessages(prev => [...prev, { id: `bot-${Date.now()}`, sender: 'bot', text: replyText }]);
      setIsTyping(false);
    }, 600);
  };

  const quickPrompts = [
    'How to cancel Netflix?',
    'Which trials expire soon?',
    'How much do I spend monthly?',
    'Tips to lower my risk score'
  ];

  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md bg-slate-950/95 border-l border-slate-800 shadow-2xl backdrop-blur-xl flex flex-col animate-slideLeft">
      
      {/* Drawer Header */}
      <div className="p-4 border-b border-slate-800 flex items-center justify-between bg-slate-900/60">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-purple-500 to-indigo-600 flex items-center justify-center text-white">
            <Sparkles className="w-4 h-4" />
          </div>
          <div>
            <h3 className="font-bold text-white text-sm">Autopay Guard AI</h3>
            <p className="text-[10px] text-slate-400">Gemini AI & Rule-Based Cancellation Guide</p>
          </div>
        </div>

        <button onClick={onClose} className="p-1 rounded-lg text-slate-400 hover:text-white bg-slate-800">
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Quick Prompt Chips */}
      <div className="p-3 border-b border-slate-800/60 flex items-center gap-2 overflow-x-auto text-[11px]">
        {quickPrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => handleSend(prompt)}
            className="px-2.5 py-1 rounded-full bg-indigo-950/60 border border-indigo-500/30 text-indigo-300 hover:text-white whitespace-nowrap"
          >
            {prompt}
          </button>
        ))}
      </div>

      {/* Messages Feed */}
      <div className="flex-1 p-4 overflow-y-auto space-y-3">
        {messages.map(msg => {
          const isUser = msg.sender === 'user';
          return (
            <div key={msg.id} className={`flex items-start space-x-2 ${isUser ? 'flex-row-reverse space-x-reverse' : ''}`}>
              <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs text-white ${isUser ? 'bg-indigo-600' : 'bg-purple-600'}`}>
                {isUser ? <User className="w-3.5 h-3.5" /> : <Bot className="w-3.5 h-3.5" />}
              </div>

              <div className={`max-w-[80%] rounded-2xl p-3 text-xs leading-relaxed ${
                isUser ? 'bg-indigo-600 text-white rounded-tr-none' : 'bg-slate-900 border border-slate-800 text-slate-200 rounded-tl-none whitespace-pre-line'
              }`}>
                {msg.text}
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="flex items-center space-x-2 text-slate-400 text-xs">
            <Bot className="w-4 h-4 text-purple-400 animate-spin" />
            <span>Autopay Guard AI is thinking...</span>
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="p-3 border-t border-slate-800 bg-slate-900/80">
        <form onSubmit={(e) => { e.preventDefault(); handleSend(); }} className="flex items-center space-x-2">
          <input
            type="text"
            placeholder="Ask about subscriptions or cancellation steps..."
            value={inputQuery}
            onChange={(e) => setInputQuery(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500"
          />
          <button
            type="submit"
            className="p-2 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-600 text-white hover:scale-105 transition-all"
          >
            <Send className="w-4 h-4" />
          </button>
        </form>
      </div>

    </div>
  );
}
