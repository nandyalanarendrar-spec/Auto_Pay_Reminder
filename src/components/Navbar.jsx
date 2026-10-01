import React from 'react';
import {
  ShieldCheck,
  PlusCircle,
  LogOut,
  User,
  Clock
} from 'lucide-react';

export default function Navbar({
  currentUser,
  onLogout,
  onOpenAddModal,
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
              <span className="px-2 py-0.5 text-[9px] font-bold tracking-wider text-indigo-300 bg-indigo-950/80 border border-indigo-500/30 rounded-full uppercase">
                PRO V1.0
              </span>
            </div>
            <p className="text-[11px] text-slate-400 hidden lg:block">Smart Subscription & Autopay Renewal Vault</p>
          </div>
        </div>

        {/* PAGE NAVIGATION TABS */}
        <div className="hidden md:flex items-center space-x-1 bg-slate-900/90 p-1 rounded-2xl border border-slate-800">
          <button
            onClick={() => onSelectTab && onSelectTab('dashboard')}
            className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'dashboard'
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            Dashboard
          </button>

          <button
            onClick={() => onSelectTab && onSelectTab('reminders')}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'reminders'
                ? 'bg-gradient-to-r from-amber-500 to-indigo-600 text-white shadow-md'
                : 'text-slate-400 hover:text-white'
            }`}
          >
            <Clock className="w-3.5 h-3.5 text-amber-400" />
            <span>Reminders Hub</span>
          </button>
        </div>

        {/* GROUP 2: Primary Action + Profile */}
        <div className="flex items-center space-x-2 sm:space-x-3">

          {/* Add Subscription Button */}
          <button
            onClick={onOpenAddModal}
            className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-white font-semibold text-xs sm:text-sm shadow-md transition-all hover:scale-[1.02] cursor-pointer"
            style={{ background: 'linear-gradient(90deg, #ff007f 0%, #9b1cff 100%)' }}
          >
            <PlusCircle className="w-4 h-4" />
            <span>Add Sub</span>
          </button>

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
