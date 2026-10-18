// File: frontend/src/pages/LoginPage.jsx
// Description: SwasthyaGrid AI Login page — multilingual, accessible, responsive.
//   Uses AuthContext for login; redirects authenticated users to /dashboard.

import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Activity, Eye, EyeOff, Loader2 } from 'lucide-react';

const LANG_LABELS = {
  en: { title: 'Welcome to SwasthyaGrid AI', subtitle: 'District Health Operations Platform', usernamePlaceholder: 'Username or email', passwordPlaceholder: 'Password', loginBtn: 'Sign In', loading: 'Signing in…', errorGeneric: 'Login failed. Please check your credentials.' },
  hi: { title: 'स्वास्थ्यग्रिड AI में आपका स्वागत है', subtitle: 'जिला स्वास्थ्य संचालन प्लेटफ़ॉर्म', usernamePlaceholder: 'उपयोगकर्ता नाम या ईमेल', passwordPlaceholder: 'पासवर्ड', loginBtn: 'साइन इन करें', loading: 'लॉगिन हो रहा है…', errorGeneric: 'लॉगिन विफल। कृपया पुनः प्रयास करें।' },
  mr: { title: 'स्वास्थ्यग्रिड AI मध्ये स्वागत', subtitle: 'जिल्हा आरोग्य कार्यान्वयन प्लॅटफॉर्म', usernamePlaceholder: 'वापरकर्ता नाव किंवा ईमेल', passwordPlaceholder: 'पासवर्ड', loginBtn: 'साइन इन करा', loading: 'लॉग इन होत आहे…', errorGeneric: 'लॉगिन अयशस्वी. पुन्हा प्रयत्न करा.' },
  ta: { title: 'SwasthyaGrid AI-க்கு வரவேற்கிறோம்', subtitle: 'மாவட்ட சுகாதார இயக்க தளம்', usernamePlaceholder: 'பயனர்பெயர் அல்லது மின்னஞ்சல்', passwordPlaceholder: 'கடவுச்சொல்', loginBtn: 'உள்நுழை', loading: 'உள்நுழைகிறது…', errorGeneric: 'உள்நுழைவு தோல்வியடைந்தது.' },
  te: { title: 'SwasthyaGrid AI లోకి స్వాగతం', subtitle: 'జిల్లా ఆరోగ్య కార్యక్రమ వేదిక', usernamePlaceholder: 'యూజర్‌నేమ్ లేదా ఇమెయిల్', passwordPlaceholder: 'పాస్‌వర్డ్', loginBtn: 'సైన్ ఇన్', loading: 'లాగిన్ అవుతోంది…', errorGeneric: 'లాగిన్ విఫలమైంది.' },
  bn: { title: 'SwasthyaGrid AI-তে স্বাগতম', subtitle: 'জেলা স্বাস্থ্য পরিচালনা প্ল্যাটফর্ম', usernamePlaceholder: 'ব্যবহারকারীর নাম বা ইমেল', passwordPlaceholder: 'পাসওয়ার্ড', loginBtn: 'সাইন ইন', loading: 'লগইন হচ্ছে…', errorGeneric: 'লগইন ব্যর্থ হয়েছে।' },
};

const LANGUAGES = [
  { code: 'en', label: 'EN' }, { code: 'hi', label: 'हि' },
  { code: 'mr', label: 'म' },  { code: 'ta', label: 'த' },
  { code: 'te', label: 'తె' }, { code: 'bn', label: 'বা' },
];

export default function LoginPage() {
  const { login, isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const [username, setUsername]     = useState('');
  const [password, setPassword]     = useState('');
  const [showPass, setShowPass]     = useState(false);
  const [error, setError]           = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [lang, setLang]             = useState('en');

  const t = LANG_LABELS[lang];

  // Redirect if already authenticated
  useEffect(() => {
    if (!authLoading && isAuthenticated) {
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    }
  }, [isAuthenticated, authLoading, navigate, location]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    if (!username.trim() || !password) {
      setError('Please enter your username and password.');
      return;
    }
    setIsSubmitting(true);
    try {
      await login(username.trim(), password);
      const from = location.state?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (err) {
      setError(err.message || t.errorGeneric);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-teal-50 to-slate-100">
        <Loader2 className="w-8 h-8 text-teal-500 animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-teal-50 via-slate-50 to-cyan-50 p-4">
      <div className="w-full max-w-md">

        {/* Language Selector */}
        <div className="flex justify-center gap-2 mb-6">
          {LANGUAGES.map(({ code, label }) => (
            <button
              key={code}
              onClick={() => setLang(code)}
              className={`px-3 py-1 text-xs font-bold rounded-full transition ${
                lang === code
                  ? 'bg-teal-600 text-white shadow-sm'
                  : 'bg-white text-slate-600 border border-slate-200 hover:border-teal-300'
              }`}
              aria-label={`Switch to ${code.toUpperCase()}`}
            >
              {label}
            </button>
          ))}
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-xl border border-slate-100 overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-teal-600 to-cyan-600 px-8 py-8 text-white text-center">
            <div className="flex justify-center mb-3">
              <div className="w-14 h-14 bg-white/20 rounded-2xl flex items-center justify-center backdrop-blur-sm">
                <Activity className="w-8 h-8 text-white" />
              </div>
            </div>
            <h1 className="text-xl font-bold leading-tight">{t.title}</h1>
            <p className="text-teal-100 text-sm mt-1">{t.subtitle}</p>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="px-8 py-6 space-y-4">
            {error && (
              <div
                role="alert"
                className="bg-rose-50 border border-rose-200 text-rose-700 text-sm px-4 py-3 rounded-xl flex items-start gap-2"
              >
                <Shield className="w-4 h-4 mt-0.5 shrink-0 text-rose-500" />
                <span>{error}</span>
              </div>
            )}

            {/* Username */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">
                {lang === 'en' ? 'Username / Email' : t.usernamePlaceholder}
              </label>
              <input
                type="text"
                autoComplete="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder={t.usernamePlaceholder}
                required
                className="w-full px-4 py-2.5 rounded-xl border border-slate-200 text-slate-900 text-sm
                           focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent
                           placeholder:text-slate-400 transition"
              />
            </div>

            {/* Password */}
            <div>
              <label className="block text-xs font-semibold text-slate-600 mb-1.5 uppercase tracking-wide">
                {lang === 'en' ? 'Password' : t.passwordPlaceholder}
              </label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  autoComplete="current-password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={t.passwordPlaceholder}
                  required
                  className="w-full px-4 py-2.5 pr-11 rounded-xl border border-slate-200 text-slate-900 text-sm
                             focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent
                             placeholder:text-slate-400 transition"
                />
                <button
                  type="button"
                  onClick={() => setShowPass((v) => !v)}
                  aria-label={showPass ? 'Hide password' : 'Show password'}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPass ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Submit */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 bg-teal-600 hover:bg-teal-700 disabled:bg-teal-400 text-white
                         text-sm font-bold rounded-xl transition flex items-center justify-center gap-2
                         focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>{t.loading}</span>
                </>
              ) : (
                t.loginBtn
              )}
            </button>

            {/* Demo hint */}
            <p className="text-center text-xs text-slate-400 pt-1">
              Demo credentials: <span className="font-mono text-slate-600">admin</span> / <span className="font-mono text-slate-600">Admin1234</span>
            </p>
          </form>
        </div>

        {/* Footer branding */}
        <p className="text-center text-xs text-slate-400 mt-5">
          SwasthyaGrid AI v2.0 · PHC/CHC District Health Platform
        </p>
      </div>
    </div>
  );
}
