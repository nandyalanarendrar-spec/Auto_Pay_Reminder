import React from 'react';
import { ShieldCheck, ShieldAlert, Sun, CloudSun, Sunset, Moon } from 'lucide-react';

const getGreeting = () => {
  const h = new Date().getHours();
  if (h < 5) return { text: 'Good night', Icon: Moon, color: 'text-indigo-300' };
  if (h < 12) return { text: 'Good morning', Icon: Sun, color: 'text-amber-300' };
  if (h < 17) return { text: 'Good afternoon', Icon: CloudSun, color: 'text-sky-300' };
  if (h < 21) return { text: 'Good evening', Icon: Sunset, color: 'text-orange-300' };
  return { text: 'Good night', Icon: Moon, color: 'text-indigo-300' };
};

const titleCase = (s) => s.replace(/\b\w/g, (c) => c.toUpperCase());

// Colors are fixed hex values (not theme classes) so the hero stays dark and readable in light theme too.
export default function Navbar({ currentUser, killSwitchActive = false, children }) {
  const rawName =
    currentUser?.user_metadata?.name ||
    currentUser?.name ||
    (currentUser?.email ? currentUser.email.split('@')[0] : '');
  const name = rawName ? titleCase(rawName) : '';
  const { text: greeting, Icon: GreetIcon, color: greetColor } = getGreeting();

  return (
    <div
      role="banner"
      className="relative z-30 border-b border-white/10 bg-gradient-to-br from-[#1b0a33] via-[#0c1232] to-[#061a2e]"
    >
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute -top-16 -left-10 w-64 h-64 rounded-full bg-fuchsia-600/30 blur-3xl" />
        <div className="absolute -top-10 right-0 w-56 h-56 rounded-full bg-indigo-500/25 blur-3xl" />
        <div className="absolute -bottom-24 left-1/3 w-72 h-72 rounded-full bg-cyan-500/15 blur-3xl" />
        <div className="absolute top-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-fuchsia-400/70 to-transparent" />
      </div>

      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-5 pb-4">
        <div className="flex flex-col items-center text-center">
          <div className="flex items-center space-x-3">
            <div className="relative">
              <div className="absolute inset-0 rounded-2xl bg-fuchsia-500/50 blur-lg animate-pulse" />
              <div className="relative w-14 h-14 rounded-2xl bg-gradient-to-br from-[#ff007f] via-purple-500 to-indigo-500 p-[2px] shadow-xl shadow-fuchsia-500/30">
                <div className="w-full h-full rounded-[0.9rem] bg-[#0a0d24] flex items-center justify-center">
                  <ShieldCheck className="w-7 h-7 text-[#ff4da6]" />
                </div>
              </div>
            </div>
            <div role="heading" aria-level={1} className="text-3xl font-black tracking-tight leading-tight pb-1 bg-clip-text text-transparent bg-gradient-to-r from-[#ffffff] via-[#f5d0fe] to-[#a5b4fc]">
              Autopay Guard
            </div>
          </div>

          <div className="mt-3 flex flex-wrap items-center justify-center gap-2">
            <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-white/10 border border-white/10 backdrop-blur text-xs font-semibold text-[#e0e7ff]">
              <GreetIcon className={`w-4 h-4 ${greetColor}`} />
              <span>
                {greeting}
                {name ? `, ${name}` : ''}
              </span>
            </span>

            {killSwitchActive ? (
              <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-rose-500/20 border border-rose-400/40 text-xs font-bold text-[#fecdd3]">
                <ShieldAlert className="w-4 h-4 text-rose-300" />
                <span>Autopay paused</span>
              </span>
            ) : (
              <span className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-400/30 text-xs font-bold text-[#a7f3d0]">
                <span className="relative flex w-2 h-2">
                  <span className="absolute inline-flex w-full h-full rounded-full bg-emerald-400 opacity-75 animate-ping" />
                  <span className="relative inline-flex w-2 h-2 rounded-full bg-emerald-400" />
                </span>
                <span>Protected</span>
              </span>
            )}
          </div>
        </div>

        {children && <div className="mt-5">{children}</div>}
      </div>
    </div>
  );
}
