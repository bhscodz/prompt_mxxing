// File: frontend/src/pages/AIAgentChat.jsx
// Description: Multilingual AI Health Assistant chat UI for SwasthyaGrid AI.
//   Connects to WebSocket /ws/agent-chat and REST /api/v1/agent/chat.
//   Supports 6 Indian languages with quick-prompt chips.

import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Send, Loader2, MessageSquare, Globe2, Zap, RefreshCw } from 'lucide-react';
import { getAuthHeaders } from '../services/authService';

const WS_URL = `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/agent-chat`;

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिन्दी' },
  { code: 'mr', label: 'मराठी' },
  { code: 'ta', label: 'தமிழ்' },
  { code: 'te', label: 'తెలుగు' },
  { code: 'bn', label: 'বাংলা' },
];

const QUICK_PROMPTS = {
  en: [
    'Show medicine stock status',
    'How many patients today?',
    'Are there any critical alerts?',
    'What is the bed occupancy?',
    'Show budget utilization',
    'Which doctors are absent today?',
  ],
  hi: [
    'दवाई स्टॉक की स्थिति दिखाएं',
    'आज कितने मरीज हैं?',
    'कोई गंभीर अलर्ट है?',
    'बेड ऑक्युपेंसी बताएं',
    'बजट उपयोग दिखाएं',
    'आज कौन से डॉक्टर अनुपस्थित हैं?',
  ],
  mr: [
    'औषध स्टॉक स्थिती दाखवा',
    'आज किती रुग्ण आहेत?',
    'गंभीर इशारे आहेत का?',
    'बेड ऑक्युपेंसी सांगा',
    'बजट वापर दाखवा',
    'आज कोण डॉक्टर अनुपस्थित आहेत?',
  ],
  ta: [
    'மருந்து இருப்பு நிலை காட்டு',
    'இன்று எத்தனை நோயாளிகள்?',
    'முக்கியமான எச்சரிக்கைகள் உள்ளதா?',
    'படுக்கை ஆக்கிரமிப்பு என்ன?',
    'பட்ஜெட் பயன்பாடு காட்டு',
    'இன்று எந்த மருத்துவர்கள் இல்லை?',
  ],
  te: [
    'మందు స్టాక్ స్థితి చూపించు',
    'ఈ రోజు ఎంత మంది రోగులు?',
    'క్రిటికల్ అలర్ట్లు ఉన్నాయా?',
    'బెడ్ ఆక్యుపెన్సీ చెప్పు',
    'బడ్జెట్ వినియోగం చూపించు',
    'ఈ రోజు ఏ డాక్టర్లు లేరు?',
  ],
  bn: [
    'ওষুধ স্টক অবস্থা দেখান',
    'আজ কত রোগী আছে?',
    'কোনো জরুরি সতর্কতা আছে?',
    'বেড অকুপেন্সি কত?',
    'বাজেট ব্যবহার দেখান',
    'আজ কোন ডাক্তার অনুপস্থিত?',
  ],
};

const INTENT_COLORS = {
  INVENTORY: 'teal', FOOTFALL: 'blue', BEDS: 'violet',
  STAFF: 'amber', ALERTS: 'rose', ECONOMICS: 'emerald', GENERAL: 'slate',
};

function Message({ msg }) {
  const isUser = msg.role === 'user';
  const intentColor = INTENT_COLORS[msg.intent] || 'slate';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} gap-2`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-teal-100 flex items-center justify-center shrink-0 mt-1">
          <Zap className="w-4 h-4 text-teal-600" />
        </div>
      )}
      <div className={`max-w-[75%] ${isUser ? 'items-end' : 'items-start'} flex flex-col gap-1`}>
        {!isUser && msg.intent && msg.intent !== 'GENERAL' && (
          <span className={`text-[10px] font-bold uppercase bg-${intentColor}-100 text-${intentColor}-700 px-2 py-0.5 rounded-full`}>
            {msg.intent}
          </span>
        )}
        <div
          className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
            isUser
              ? 'bg-teal-600 text-white rounded-tr-sm'
              : 'bg-white border border-slate-200 text-slate-800 rounded-tl-sm shadow-sm'
          }`}
        >
          {msg.content}
        </div>
        <span className="text-[10px] text-slate-400">
          {msg.language && !isUser && `${msg.language.toUpperCase()} · `}
          {new Date(msg.ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
        </span>
      </div>
    </div>
  );
}

export default function AIAgentChat({ facilities = [], selectedFacilityId }) {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: '👋 Hi! I\'m the SwasthyaGrid AI Health Assistant. I can answer questions about medicine inventory, patient footfall, bed availability, staff attendance, alerts, and economics — in 6 languages. How can I help you today?',
      intent: 'GENERAL',
      language: 'en',
      ts: Date.now(),
    },
  ]);
  const [input, setInput]         = useState('');
  const [lang, setLang]           = useState('en');
  const [facilityId, setFacilityId] = useState(selectedFacilityId || '');
  const [isThinking, setIsThinking] = useState(false);
  const [wsStatus, setWsStatus]   = useState('disconnected'); // connected|connecting|disconnected
  const wsRef     = useRef(null);
  const bottomRef = useRef(null);
  const inputRef  = useRef(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isThinking]);

  // WebSocket connection
  const connectWs = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    setWsStatus('connecting');
    const ws = new WebSocket(WS_URL);

    ws.onopen = () => setWsStatus('connected');
    ws.onclose = () => setWsStatus('disconnected');
    ws.onerror = () => setWsStatus('disconnected');

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'thinking') {
          setIsThinking(true);
        } else if (msg.type === 'final') {
          setIsThinking(false);
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: msg.content,
            intent: msg.intent,
            language: msg.language,
            ts: Date.now(),
          }]);
        } else if (msg.type === 'error') {
          setIsThinking(false);
          setMessages(prev => [...prev, {
            role: 'assistant',
            content: `⚠️ ${msg.content}`,
            intent: 'GENERAL',
            language: lang,
            ts: Date.now(),
          }]);
        }
      } catch {
        // ignore parse errors
      }
    };

    wsRef.current = ws;
  }, [lang]);

  useEffect(() => {
    connectWs();
    return () => wsRef.current?.close();
  }, [connectWs]);

  const sendMessage = useCallback(async (text) => {
    const query = text || input.trim();
    if (!query) return;

    setInput('');
    setMessages(prev => [...prev, { role: 'user', content: query, ts: Date.now() }]);
    setIsThinking(true);

    const payload = JSON.stringify({ query, language: lang, facility_id: facilityId || null });

    // Try WebSocket first, fall back to REST
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(payload);
    } else {
      // REST fallback
      try {
        const headers = { 'Content-Type': 'application/json', ...getAuthHeaders() };
        const res = await fetch('/api/v1/agent/chat', {
          method: 'POST',
          headers,
          body: JSON.stringify({ query, language: lang, facility_id: facilityId || null }),
        });
        const data = await res.json();
        setIsThinking(false);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.response,
          intent: data.intent,
          language: data.language,
          ts: Date.now(),
        }]);
      } catch (err) {
        setIsThinking(false);
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `⚠️ Agent error: ${err.message}`,
          intent: 'GENERAL',
          language: 'en',
          ts: Date.now(),
        }]);
      }
    }

    inputRef.current?.focus();
  }, [input, lang, facilityId]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  };

  const wsColorClass = wsStatus === 'connected' ? 'bg-teal-500' : wsStatus === 'connecting' ? 'bg-amber-400' : 'bg-slate-400';

  return (
    <div className="flex flex-col h-[calc(100vh-7rem)] max-h-[780px]">
      {/* Header */}
      <div className="bg-white border border-slate-200 rounded-t-2xl px-5 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-teal-100 rounded-xl flex items-center justify-center">
            <MessageSquare className="w-5 h-5 text-teal-600" />
          </div>
          <div>
            <h1 className="font-bold text-slate-800">AI Health Assistant</h1>
            <div className="flex items-center gap-1.5">
              <span className={`w-2 h-2 rounded-full ${wsColorClass}`} />
              <span className="text-xs text-slate-500 capitalize">{wsStatus}</span>
              {wsStatus !== 'connected' && (
                <button onClick={connectWs} className="text-xs text-teal-600 hover:underline ml-1">
                  Reconnect
                </button>
              )}
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Facility */}
          <select
            value={facilityId}
            onChange={e => setFacilityId(e.target.value)}
            className="text-xs px-3 py-1.5 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-400"
          >
            <option value="">All Facilities</option>
            {facilities.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>

          {/* Language */}
          <div className="flex items-center gap-1 bg-slate-50 border border-slate-200 rounded-lg p-1">
            <Globe2 className="w-3.5 h-3.5 text-slate-400 ml-1" />
            {LANGUAGES.map(({ code, label }) => (
              <button
                key={code}
                onClick={() => setLang(code)}
                className={`text-xs px-2 py-1 rounded-md font-semibold transition ${
                  lang === code ? 'bg-teal-600 text-white' : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Quick prompts */}
      <div className="bg-slate-50 border-x border-slate-200 px-4 py-2 flex gap-2 overflow-x-auto">
        {(QUICK_PROMPTS[lang] || QUICK_PROMPTS.en).map((p, i) => (
          <button
            key={i}
            onClick={() => sendMessage(p)}
            className="text-xs whitespace-nowrap px-3 py-1.5 bg-white border border-slate-200 rounded-full text-slate-600 hover:border-teal-400 hover:text-teal-700 transition font-medium"
          >
            {p}
          </button>
        ))}
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto bg-slate-50 border-x border-slate-200 px-4 py-4 space-y-4">
        {messages.map((msg, i) => <Message key={i} msg={msg} />)}
        {isThinking && (
          <div className="flex items-center gap-2 text-slate-400 text-sm">
            <div className="w-8 h-8 rounded-full bg-teal-100 flex items-center justify-center">
              <Loader2 className="w-4 h-4 text-teal-600 animate-spin" />
            </div>
            <span className="italic">AI is thinking…</span>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div className="bg-white border border-slate-200 rounded-b-2xl px-4 py-3 flex items-end gap-2">
        <textarea
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={lang === 'en' ? 'Ask about inventory, patients, beds, staff…' : 'यहाँ लिखें…'}
          rows={1}
          className="flex-1 resize-none px-4 py-2.5 text-sm border border-slate-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-teal-500 placeholder:text-slate-400 max-h-32"
          style={{ minHeight: '42px' }}
        />
        <button
          onClick={() => sendMessage()}
          disabled={!input.trim() || isThinking}
          className="p-2.5 bg-teal-600 hover:bg-teal-700 disabled:bg-teal-300 text-white rounded-xl transition"
          aria-label="Send message"
        >
          <Send className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
