import React from 'react';
import { User } from 'lucide-react';
import { NAV_TABS } from '../constants/navTabs';

export default function BottomNav({ activeTab, onSelectTab, currentUser, onOpenProfile }) {
  const initial = currentUser?.email ? currentUser.email.charAt(0).toUpperCase() : null;

  return (
    <nav className="fixed bottom-0 inset-x-0 z-40 grid grid-cols-6 bg-slate-950/95 backdrop-blur-xl border-t border-slate-800/80 shadow-[0_-8px_30px_rgba(0,0,0,0.45)]">
      {NAV_TABS.map(({ id, label, icon: Icon }) => {
        const active = activeTab === id;
        return (
          <button
            key={id}
            onClick={() => onSelectTab(id)}
            aria-label={label}
            title={label}
            className="flex items-center justify-center py-3 cursor-pointer"
          >
            <span className={`flex items-center justify-center px-4 py-3 rounded-3xl transition-all ${active ? 'bg-white/15 text-white' : 'text-slate-400 hover:text-white'}`}>
              <Icon className="w-8 h-8" strokeWidth={active ? 2.6 : 2} />
            </span>
          </button>
        );
      })}

      <button
        onClick={onOpenProfile}
        aria-label="Profile"
        title="Profile"
        className="flex items-center justify-center py-3 cursor-pointer"
      >
        <span className="flex items-center justify-center px-4 py-3 rounded-3xl">
          <span className="w-9 h-9 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-500 border-2 border-slate-600 flex items-center justify-center text-base font-bold text-white">
            {initial || <User className="w-5 h-5" />}
          </span>
        </span>
      </button>
    </nav>
  );
}
