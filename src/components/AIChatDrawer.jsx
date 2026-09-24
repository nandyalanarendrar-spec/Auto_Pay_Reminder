import React, { useState, useRef, useEffect } from 'react';
import { X, Sparkles, Send, Bot, User, Zap, MessageCircle, ArrowRight } from 'lucide-react';
import { supabase, isSupabaseConfigured } from '../lib/supabaseClient';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

/* ── Animated Typing Dots ─────────────────────────────── */
function TypingDots() {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, padding: '14px 18px' }}>
      <div style={{
        width: 28, height: 28, borderRadius: '50%',
        background: 'linear-gradient(135deg, #a855f7, #6366f1)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: '0 0 12px rgba(168,85,247,0.4)'
      }}>
        <Bot style={{ width: 14, height: 14, color: '#fff' }} />
      </div>
      <div style={{
        display: 'flex', gap: 5, padding: '10px 16px',
        background: 'rgba(30,41,66,0.7)', borderRadius: 16,
        border: '1px solid rgba(139,92,246,0.15)'
      }}>
        {[0, 1, 2].map(i => (
          <span key={i} style={{
            width: 7, height: 7, borderRadius: '50%',
            background: 'linear-gradient(135deg, #a855f7, #6366f1)',
            animation: `aichat-bounce 1.2s ease-in-out ${i * 0.15}s infinite`,
            opacity: 0.8
          }} />
        ))}
      </div>
    </div>
  );
}

/* ── Message Bubble ───────────────────────────────────── */
function ChatBubble({ msg, isLatestBot }) {
  const isUser = msg.sender === 'user';
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => setVisible(true), 60);
    return () => clearTimeout(t);
  }, []);

  return (
    <div style={{
      display: 'flex', alignItems: 'flex-end', gap: 8,
      flexDirection: isUser ? 'row-reverse' : 'row',
      opacity: visible ? 1 : 0,
      transform: visible ? 'translateY(0)' : 'translateY(12px)',
      transition: 'all 0.35s cubic-bezier(0.4,0,0.2,1)',
      marginBottom: 4
    }}>
      {/* Avatar */}
      <div style={{
        width: 30, height: 30, borderRadius: '50%', flexShrink: 0,
        background: isUser
          ? 'linear-gradient(135deg, #3b82f6, #6366f1)'
          : 'linear-gradient(135deg, #a855f7, #ec4899)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        boxShadow: isUser
          ? '0 0 14px rgba(99,102,241,0.35)'
          : '0 0 14px rgba(168,85,247,0.35)',
        border: `2px solid ${isUser ? 'rgba(99,102,241,0.3)' : 'rgba(168,85,247,0.3)'}`
      }}>
        {isUser
          ? <User style={{ width: 14, height: 14, color: '#fff' }} />
          : <Sparkles style={{ width: 14, height: 14, color: '#fff' }} />
        }
      </div>

      {/* Bubble */}
      <div style={{
        maxWidth: '78%', borderRadius: 18,
        ...(isUser
          ? { borderBottomRightRadius: 4 }
          : { borderBottomLeftRadius: 4 }
        ),
        padding: '11px 16px',
        fontSize: 13, lineHeight: 1.6, letterSpacing: '0.01em',
        whiteSpace: 'pre-line', wordBreak: 'break-word',
        ...(isUser ? {
          background: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
          color: '#fff',
          boxShadow: '0 4px 20px -4px rgba(99,102,241,0.35)'
        } : {
          background: 'rgba(20,28,50,0.85)',
          border: '1px solid rgba(139,92,246,0.12)',
          color: '#e2e8f0',
          backdropFilter: 'blur(8px)',
          boxShadow: '0 4px 20px -4px rgba(0,0,0,0.3)'
        })
      }}>
        {msg.text}
      </div>
    </div>
  );
}

/* ── Main Drawer ──────────────────────────────────────── */
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
  const [isFocused, setIsFocused] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  if (!isOpen) return null;

  const handleSend = async (textToSend) => {
    const query = textToSend || inputQuery;
    if (!query.trim()) return;

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
        const subList = subscriptions ? subscriptions.map((s, idx) => `• **${s.merchant_name || s.name}**: ₹${parseFloat(s.amount).toFixed(2)}/mo (${s.status === 'trial' || s.is_free_trial ? 'Free Trial' : 'Active'})`).join('\n') : 'No subscriptions found.';
        replyText = `You currently have **${subscriptions ? subscriptions.length : 0} active subscriptions** totaling **₹${total.toFixed(2)}/mo**:\n\n${subList}\n\nAsk me about renewal dates or cancellation steps!`;
      }

      setMessages(prev => [...prev, { id: `bot-${Date.now()}`, sender: 'bot', text: replyText }]);
      setIsTyping(false);
    }, 600);
  };

  const quickPrompts = [
    { icon: '🚫', label: 'Cancel Netflix' , query: 'How to cancel Netflix?' },
    { icon: '⏰', label: 'Trials Expiring' , query: 'Which trials expire soon?' },
    { icon: '💰', label: 'Monthly Spend'   , query: 'How much do I spend monthly?' },
    { icon: '📉', label: 'Lower Risk'      , query: 'Tips to lower my risk score' },
  ];

  return (
    <>
      {/* Keyframe Styles */}
      <style>{`
        @keyframes aichat-slideIn {
          from { transform: translateX(100%); opacity: 0; }
          to   { transform: translateX(0);    opacity: 1; }
        }
        @keyframes aichat-bounce {
          0%, 80%, 100% { transform: scale(0.6); opacity: 0.4; }
          40%           { transform: scale(1.1); opacity: 1; }
        }
        @keyframes aichat-glow {
          0%, 100% { box-shadow: 0 0 20px rgba(168,85,247,0.15); }
          50%      { box-shadow: 0 0 40px rgba(168,85,247,0.3); }
        }
        @keyframes aichat-gradient {
          0%   { background-position: 0% 50%; }
          50%  { background-position: 100% 50%; }
          100% { background-position: 0% 50%; }
        }
        @keyframes aichat-shimmer {
          0%   { background-position: -200% center; }
          100% { background-position: 200% center; }
        }
        .aichat-scrollbar::-webkit-scrollbar { width: 4px; }
        .aichat-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .aichat-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(139,92,246,0.25); border-radius: 99px;
        }
        .aichat-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(168,85,247,0.5);
        }
      `}</style>

      {/* Backdrop overlay */}
      <div
        onClick={onClose}
        style={{
          position: 'fixed', inset: 0, zIndex: 49,
          background: 'rgba(0,0,0,0.4)',
          backdropFilter: 'blur(4px)',
          animation: 'fadeIn 0.3s ease'
        }}
      />

      {/* Drawer Panel */}
      <div style={{
        position: 'fixed', top: 0, right: 0, bottom: 0, zIndex: 50,
        width: '100%', maxWidth: 420,
        display: 'flex', flexDirection: 'column',
        background: 'linear-gradient(180deg, #0c1225 0%, #080f1f 40%, #0a0e1f 100%)',
        borderLeft: '1px solid rgba(139,92,246,0.12)',
        boxShadow: '-20px 0 60px -12px rgba(0,0,0,0.7), 0 0 60px rgba(139,92,246,0.08)',
        animation: 'aichat-slideIn 0.35s cubic-bezier(0.16,1,0.3,1)',
        overflow: 'hidden'
      }}>

        {/* ─── Header ─── */}
        <div style={{
          padding: '16px 18px',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          background: 'linear-gradient(135deg, rgba(139,92,246,0.08), rgba(236,72,153,0.06))',
          borderBottom: '1px solid rgba(139,92,246,0.1)',
          position: 'relative', overflow: 'hidden'
        }}>
          {/* Animated gradient line at top */}
          <div style={{
            position: 'absolute', top: 0, left: 0, right: 0, height: 2,
            background: 'linear-gradient(90deg, #a855f7, #ec4899, #6366f1, #a855f7)',
            backgroundSize: '200% 100%',
            animation: 'aichat-gradient 3s linear infinite'
          }} />

          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            {/* Logo */}
            <div style={{
              width: 40, height: 40, borderRadius: 12,
              background: 'linear-gradient(135deg, #a855f7, #ec4899)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              boxShadow: '0 0 20px rgba(168,85,247,0.3)',
              animation: 'aichat-glow 3s ease-in-out infinite',
              position: 'relative'
            }}>
              <Sparkles style={{ width: 20, height: 20, color: '#fff' }} />
              {/* Live status dot */}
              <div style={{
                position: 'absolute', top: -2, right: -2,
                width: 10, height: 10, borderRadius: '50%',
                background: '#22c55e',
                border: '2px solid #0c1225',
                boxShadow: '0 0 6px rgba(34,197,94,0.6)'
              }} />
            </div>
            <div>
              <h3 style={{
                margin: 0, fontSize: 15, fontWeight: 700, color: '#fff',
                letterSpacing: '0.02em',
                display: 'flex', alignItems: 'center', gap: 6
              }}>
                Autopay Guard AI
                <span style={{
                  fontSize: 9, fontWeight: 600, padding: '2px 7px',
                  borderRadius: 99, color: '#c084fc',
                  background: 'rgba(168,85,247,0.15)',
                  border: '1px solid rgba(168,85,247,0.2)',
                  letterSpacing: '0.05em', textTransform: 'uppercase'
                }}>
                  PRO
                </span>
              </h3>
              <p style={{
                margin: 0, fontSize: 11, color: '#94a3b8', letterSpacing: '0.02em',
                display: 'flex', alignItems: 'center', gap: 4
              }}>
                <Zap style={{ width: 10, height: 10, color: '#facc15' }} />
                Powered by Gemini AI
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            style={{
              width: 32, height: 32, borderRadius: 10,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'rgba(255,255,255,0.05)',
              border: '1px solid rgba(255,255,255,0.08)',
              color: '#94a3b8', cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={e => { e.target.style.background = 'rgba(239,68,68,0.15)'; e.target.style.color = '#ef4444'; e.target.style.borderColor = 'rgba(239,68,68,0.3)'; }}
            onMouseLeave={e => { e.target.style.background = 'rgba(255,255,255,0.05)'; e.target.style.color = '#94a3b8'; e.target.style.borderColor = 'rgba(255,255,255,0.08)'; }}
          >
            <X style={{ width: 16, height: 16 }} />
          </button>
        </div>

        {/* ─── Quick Prompt Chips ─── */}
        <div style={{
          padding: '12px 16px',
          display: 'flex', gap: 8, overflowX: 'auto',
          borderBottom: '1px solid rgba(139,92,246,0.06)',
          scrollbarWidth: 'none', msOverflowStyle: 'none'
        }}>
          {quickPrompts.map((p, idx) => (
            <button
              key={idx}
              onClick={() => handleSend(p.query)}
              style={{
                display: 'flex', alignItems: 'center', gap: 5,
                padding: '7px 14px', borderRadius: 99, whiteSpace: 'nowrap',
                fontSize: 11, fontWeight: 500, cursor: 'pointer',
                color: '#c4b5fd',
                background: 'rgba(139,92,246,0.08)',
                border: '1px solid rgba(139,92,246,0.15)',
                transition: 'all 0.25s cubic-bezier(0.4,0,0.2,1)',
                letterSpacing: '0.01em'
              }}
              onMouseEnter={e => {
                e.currentTarget.style.background = 'rgba(139,92,246,0.18)';
                e.currentTarget.style.borderColor = 'rgba(139,92,246,0.35)';
                e.currentTarget.style.color = '#e9d5ff';
                e.currentTarget.style.transform = 'translateY(-1px)';
                e.currentTarget.style.boxShadow = '0 4px 12px -2px rgba(139,92,246,0.2)';
              }}
              onMouseLeave={e => {
                e.currentTarget.style.background = 'rgba(139,92,246,0.08)';
                e.currentTarget.style.borderColor = 'rgba(139,92,246,0.15)';
                e.currentTarget.style.color = '#c4b5fd';
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <span style={{ fontSize: 13 }}>{p.icon}</span>
              {p.label}
            </button>
          ))}
        </div>

        {/* ─── Messages Feed ─── */}
        <div className="aichat-scrollbar" style={{
          flex: 1, padding: '16px 14px', overflowY: 'auto',
          display: 'flex', flexDirection: 'column', gap: 12
        }}>
          {/* Welcome Card (only if first message) */}
          {messages.length === 1 && !isTyping && (
            <div style={{
              margin: '20px 0',
              padding: 20, borderRadius: 16,
              background: 'linear-gradient(135deg, rgba(139,92,246,0.08), rgba(236,72,153,0.06))',
              border: '1px solid rgba(139,92,246,0.12)',
              textAlign: 'center'
            }}>
              <div style={{
                width: 52, height: 52, borderRadius: 16, margin: '0 auto 14px',
                background: 'linear-gradient(135deg, #a855f7, #ec4899)',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                boxShadow: '0 0 30px rgba(168,85,247,0.25)'
              }}>
                <MessageCircle style={{ width: 24, height: 24, color: '#fff' }} />
              </div>
              <p style={{ margin: 0, fontSize: 13, color: '#cbd5e1', lineHeight: 1.6 }}>
                Ask me anything about your subscriptions, cancellations, or spending insights.
              </p>
              <div style={{
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                gap: 6, marginTop: 14, fontSize: 11, color: '#8b5cf6'
              }}>
                <ArrowRight style={{ width: 12, height: 12 }} />
                Try a quick prompt above to get started
              </div>
            </div>
          )}

          {messages.map((msg, idx) => (
            <ChatBubble
              key={msg.id}
              msg={msg}
              isLatestBot={msg.sender === 'bot' && idx === messages.length - 1}
            />
          ))}

          {isTyping && <TypingDots />}
          <div ref={messagesEndRef} />
        </div>

        {/* ─── Input Bar ─── */}
        <div style={{
          padding: '12px 14px 14px',
          borderTop: '1px solid rgba(139,92,246,0.08)',
          background: 'linear-gradient(180deg, rgba(12,18,37,0.6), rgba(12,18,37,0.9))',
          backdropFilter: 'blur(16px)'
        }}>
          <form
            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
            style={{
              display: 'flex', alignItems: 'center', gap: 10,
              padding: '4px 4px 4px 16px',
              borderRadius: 16,
              background: 'rgba(15,23,42,0.8)',
              border: `1px solid ${isFocused ? 'rgba(139,92,246,0.4)' : 'rgba(139,92,246,0.1)'}`,
              boxShadow: isFocused ? '0 0 20px rgba(139,92,246,0.1)' : 'none',
              transition: 'all 0.3s ease'
            }}
          >
            <input
              ref={inputRef}
              type="text"
              placeholder="Ask about subscriptions, cancellations..."
              value={inputQuery}
              onChange={(e) => setInputQuery(e.target.value)}
              onFocus={() => setIsFocused(true)}
              onBlur={() => setIsFocused(false)}
              style={{
                flex: 1, border: 'none', outline: 'none',
                background: 'transparent', color: '#e2e8f0',
                fontSize: 13, letterSpacing: '0.01em',
                padding: '10px 0'
              }}
            />
            <button
              type="submit"
              disabled={!inputQuery.trim()}
              style={{
                width: 40, height: 40, borderRadius: 12,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                border: 'none', cursor: inputQuery.trim() ? 'pointer' : 'default',
                background: inputQuery.trim()
                  ? 'linear-gradient(135deg, #a855f7, #ec4899)'
                  : 'rgba(139,92,246,0.12)',
                color: inputQuery.trim() ? '#fff' : '#6b7280',
                transition: 'all 0.3s cubic-bezier(0.4,0,0.2,1)',
                boxShadow: inputQuery.trim() ? '0 4px 16px -2px rgba(168,85,247,0.4)' : 'none',
                transform: inputQuery.trim() ? 'scale(1)' : 'scale(0.95)',
                flexShrink: 0
              }}
              onMouseEnter={e => { if (inputQuery.trim()) e.currentTarget.style.transform = 'scale(1.08)'; }}
              onMouseLeave={e => { if (inputQuery.trim()) e.currentTarget.style.transform = 'scale(1)'; }}
            >
              <Send style={{ width: 16, height: 16 }} />
            </button>
          </form>

          {/* Footer */}
          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            gap: 4, marginTop: 8, fontSize: 10, color: '#475569',
            letterSpacing: '0.03em'
          }}>
            <Sparkles style={{ width: 9, height: 9, color: '#6b21a8' }} />
            Autopay Guard AI &middot; Secure &amp; Private
          </div>
        </div>
      </div>
    </>
  );
}
