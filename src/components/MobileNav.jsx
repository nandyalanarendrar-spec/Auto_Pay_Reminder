import React from 'react';
import { NAV_TABS } from '../constants/navTabs';

export default function MobileNav({ activeTab, onSelectTab }) {
  return (
    <nav className="md:hidden fixed bottom-0 inset-x-0 z-40 bg-slate-950/95 backdrop-blur-xl border-t border-slate-800/80">
      <div className="grid grid-cols-5">
        {NAV_TABS.map(({ id, label, icon: Icon }) => {
          const active = activeTab === id;
          return (
            <button
              key={id}
              onClick={() => onSelectTab(id)}
              className={`flex flex-col items-center justify-center gap-0.5 py-2.5 transition-colors cursor-pointer ${
                active ? 'text-white' : 'text-slate-500'
              }`}
            >
              <span className={`p-1.5 rounded-xl transition-all ${active ? 'bg-gradient-to-r from-indigo-600 to-purple-600 shadow-md' : ''}`}>
                <Icon className="w-5 h-5" />
              </span>
              <span className="text-[10px] font-semibold">{label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
