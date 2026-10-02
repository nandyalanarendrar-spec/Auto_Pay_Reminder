import React from 'react';
import { User } from 'lucide-react';
import { NAV_TABS } from '../constants/navTabs';

export default function BottomNav({ activeTab, onSelectTab, currentUser, onOpenProfile }) {
  const initial = currentUser?.email ? currentUser.email.charAt(0).toUpperCase() : null;

  return (
    <nav className="fixed bottom-0 inset-x-0 z-40 flex justify-center pointer-events-none">
      <div className="pointer-events-auto w-full max-w-3xl grid grid-cols-6 bg-slate-950/95 backdrop-blur-xl border-t md:border border-slate-800/80 md:rounded-t-3xl shadow-[0_-8px_30px_rgba(0,0,0,0.4)]">
        {NAV_TABS.map(({ id, label, icon: Icon }) => {
          const active = activeTab === id;
          return (
            <button
              key={id}
              onClick={() => onSelectTab(id)}
              aria-label={label}
              title={label}
              className="flex items-center justify-center py-2.5 cursor-pointer"
            >
              <span className={`p-2.5 rounded-2xl transition-all ${active ? 'bg-white/15 text-white' : 'text-slate-400 hover:text-white'}`}>
                <Icon className="w-7 h-7" strokeWidth={active ? 2.6 : 2} />
              </span>
            </button>
          );
        })}

        <button
          onClick={onOpenProfile}
          aria-label="Profile"
          title="Profile"
          className="flex items-center justify-center py-2.5 cursor-pointer"
        >
          <span className="p-2.5 rounded-2xl">
            <span className="w-8 h-8 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-500 border-2 border-slate-700 flex items-center justify-center text-sm font-bold text-white">
              {initial || <User className="w-4 h-4" />}
            </span>
          </span>
        </button>
      </div>
    </nav>
  );
}
