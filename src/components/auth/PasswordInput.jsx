import React, { useState } from 'react';
import { Eye, EyeOff } from 'lucide-react';

export default function PasswordInput({
  label = "PASSWORD",
  name = "password",
  value,
  onChange,
  placeholder = "••••••••••••",
  error,
  required = false,
  showStrengthMeter = false
}) {
  const [showPassword, setShowPassword] = useState(false);

  const getStrengthScore = (pwd) => {
    if (!pwd) return 0;
    let score = 0;
    if (pwd.length >= 8) score++;
    if (/[A-Z]/.test(pwd)) score++;
    if (/[0-9]/.test(pwd)) score++;
    if (/[^A-Za-z0-9]/.test(pwd)) score++;
    return score;
  };

  const score = getStrengthScore(value);

  const getStrengthBadge = (s) => {
    switch (s) {
      case 1: return { text: 'Weak ⚠️', color: 'text-rose-400' };
      case 2: return { text: 'Fair ⚡', color: 'text-amber-400' };
      case 3: return { text: 'Good 👍', color: 'text-indigo-400' };
      case 4: return { text: 'Strong 💪', color: 'text-[#10B981]' };
      default: return { text: '', color: 'text-slate-500' };
    }
  };

  const badge = getStrengthBadge(score);

  return (
    <div className="w-full space-y-1.5 text-left">
      <label className="block text-[10px] font-extrabold tracking-wider text-[#A19DAE] uppercase">
        {label} {required && <span className="text-[#7C3AED]">*</span>}
      </label>

      <div className="relative flex items-center">
        <input
          type={showPassword ? 'text' : 'password'}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          required={required}
          className={`w-full bg-[#1A1628] text-white text-sm rounded-xl py-3 pl-4 pr-11 border transition-all duration-200 placeholder-[#5E5870] focus:outline-none ${
            error
              ? 'border-rose-500 focus:ring-1 focus:ring-rose-500'
              : 'border-white/15 hover:border-white/30 focus:border-[#10B981] focus:ring-1 focus:ring-[#10B981]/40'
          }`}
          style={{ boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.3)' }}
        />

        <button
          type="button"
          onClick={() => setShowPassword(!showPassword)}
          className="absolute right-3 text-[#7F7990] hover:text-white transition-colors p-1"
        >
          {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
        </button>
      </div>

      {showStrengthMeter && value && badge.text && (
        <div className="pt-0.5">
          <p className={`text-[11px] font-bold ${badge.color}`}>
            {badge.text}
          </p>
        </div>
      )}

      {error && (
        <p className="text-[11px] text-rose-400 font-medium pt-0.5 animate-fadeIn">
          {error}
        </p>
      )}
    </div>
  );
}
