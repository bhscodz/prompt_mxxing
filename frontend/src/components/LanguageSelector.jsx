// File: frontend/src/components/LanguageSelector.jsx
// Description: Language dropdown switcher supporting 6 Indian languages with native scripts
// Accessibility: aria-expanded, aria-haspopup, aria-label, role="listbox"

import React, { useState, useRef, useEffect } from 'react';
import { useLanguage } from '../i18n/LanguageContext';
import { Globe, Check, ChevronDown } from 'lucide-react';

export default function LanguageSelector() {
  const { currentLang, setLanguage, languages } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    }
    function handleEscape(event) {
      if (event.key === 'Escape') setIsOpen(false);
    }
    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleEscape);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleEscape);
    };
  }, []);

  const activeLang = languages.find(l => l.code === currentLang) || languages[0];

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-haspopup="listbox"
        aria-expanded={isOpen}
        aria-label={`Select language. Currently: ${activeLang.label}`}
        className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-200 bg-white hover:bg-slate-50 focus:outline-none focus:ring-2 focus:ring-teal-500 focus:ring-offset-1 transition text-sm font-medium text-slate-700 shadow-sm"
      >
        <Globe className="w-4 h-4 text-teal-600" aria-hidden="true" />
        <span>{activeLang.native}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} aria-hidden="true" />
      </button>

      {isOpen && (
        <ul
          role="listbox"
          aria-label="Available languages"
          className="absolute right-0 mt-2 w-48 rounded-xl bg-white shadow-xl border border-slate-100 py-1.5 z-50 animate-in fade-in slide-in-from-top-2 duration-150"
        >
          <li className="px-3 py-1 text-xs font-semibold text-slate-400 uppercase tracking-wider" role="presentation">
            Select Language
          </li>
          {languages.map((lang) => (
            <li key={lang.code} role="option" aria-selected={currentLang === lang.code}>
              <button
                onClick={() => {
                  setLanguage(lang.code);
                  setIsOpen(false);
                }}
                className={`w-full flex items-center justify-between px-3 py-2 text-sm text-left hover:bg-teal-50 focus:outline-none focus:bg-teal-50 transition ${
                  currentLang === lang.code ? 'font-semibold text-teal-700 bg-teal-50/60' : 'text-slate-700'
                }`}
              >
                <div>
                  <div className="leading-tight">{lang.native}</div>
                  <div className="text-[11px] text-slate-400">{lang.label}</div>
                </div>
                {currentLang === lang.code && (
                  <Check className="w-4 h-4 text-teal-600" aria-hidden="true" />
                )}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

