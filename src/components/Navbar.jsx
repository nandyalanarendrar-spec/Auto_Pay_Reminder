import React from 'react';
import {
  ShieldCheck,
  LogOut,
  User
} from 'lucide-react';
import { NAV_TABS } from '../constants/navTabs';

export default function Navbar({
  currentUser,
  onLogout,
  onOpenProfileModal,
  activeTab = 'dashboard',
  onSelectTab
}) {
  return (
    <header className="sticky top-0 z-30 glass-panel border-b border-slate-800/80 bg-slate-950/80 backdrop-blur-xl transition-colors duration-300">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between gap-4">

        {/* GROUP 1: Brand Logo & Title */}
        <div className="flex items-center space-x-3 flex-shrink-0">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-[#ff007f] via-purple-600 to-indigo-500 p-0.5 shadow-lg shadow-[#ff007f]/20">
            <div className="w-full h-full bg-slate-950 rounded-[14px] flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-[#ff007f]" />
            </div>
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-lg font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-white via-slate-100 to-indigo-200 tracking-tight">
                Autopay Guard
              </h1>
              <span className="hidden sm:inline px-2 py-0.5 text-[9px] font-bold tracking-wider text-indigo-300 bg-indigo-950/80 border border-indigo-500/30 rounded-full uppercase">
                PRO V1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden lg:block">Smart Subscription & Autopay Renewal Vault</p>
          </div>
        </div>

        {/* PAGE NAVIGATION TABS */}
        <div className="hidden md:flex items-center space-x-1 bg-slate-900/90 p-1 rounded-2xl border border-slate-800">
          {NAV_TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => onSelectTab && onSelectTab(id)}
              title={label}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === id
                  ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              <Icon className="w-3.5 h-3.5" />
              <span className="hidden lg:inline">{label}</span>
            </button>
          ))}
        </div>

        {/* GROUP 2: Profile */}
        <div className="flex items-center space-x-2 sm:space-x-3">

          {/* User Account & Profile Avatar Capsule */}
          {currentUser && (
            <div className="flex items-center space-x-1.5 pl-2 border-l border-slate-800">
              <button
                onClick={onOpenProfileModal}
                className="flex items-center space-x-2 p-1.5 rounded-xl bg-slate-900 border border-slate-800 hover:border-indigo-500/60 transition-all cursor-pointer group"
                title="View Profile Details"
              >
                <div className="w-7 h-7 rounded-full bg-gradient-to-tr from-purple-600 to-indigo-500 flex items-center justify-center text-xs font-bold text-white shadow-sm group-hover:scale-105 transition-transform">
                  {currentUser.email ? currentUser.email.charAt(0).toUpperCase() : <User className="w-3.5 h-3.5" />}
                </div>
                <span className="text-xs font-medium text-slate-300 hidden lg:inline group-hover:text-white max-w-[100px] truncate">
                  {currentUser.user_metadata?.name || currentUser.name || currentUser.email?.split('@')[0]}
                </span>
              </button>
              <button
                onClick={onLogout}
                className="p-2 rounded-xl bg-slate-900 hover:bg-rose-950/60 border border-slate-800 hover:border-rose-500/40 text-slate-400 hover:text-rose-300 transition-all cursor-pointer"
                title="Sign Out"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          )}

        </div>

      </div>
    </header>
  );
}
