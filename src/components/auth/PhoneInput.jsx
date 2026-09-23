import React from 'react';

export const COUNTRY_CODES = [
  { code: '+91', country: 'IN', flag: '🇮🇳', name: 'India' },
  { code: '+1', country: 'US', flag: '🇺🇸', name: 'USA' },
  { code: '+44', country: 'GB', flag: '🇬🇧', name: 'UK' },
  { code: '+971', country: 'AE', flag: '🇦🇪', name: 'UAE' },
];

export default function PhoneInput({
  label = "PHONE NUMBER",
  countryCode = "+91",
  onCountryCodeChange,
  value,
  onChange,
  error,
  required = true
}) {
  return (
    <div className="w-full space-y-1.5 text-left">
      <label className="block text-[10px] font-extrabold tracking-wider text-[#A19DAE] uppercase">
        {label} {required && <span className="text-[#7C3AED]">*</span>}
      </label>

      <div className="flex items-center space-x-2">
        
        {/* Country Select */}
        <div className="relative">
          <select
            value={countryCode}
            onChange={(e) => onCountryCodeChange(e.target.value)}
            className="bg-[#1A1628] text-white text-xs font-bold rounded-xl py-3 px-3 border border-white/15 focus:border-[#10B981] focus:outline-none cursor-pointer hover:border-white/30 transition-all"
            style={{ boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.3)' }}
          >
            {COUNTRY_CODES.map((item) => (
              <option key={item.code} value={item.code} className="bg-[#151221] text-white">
                {item.flag} {item.code}
              </option>
            ))}
          </select>
        </div>

        {/* Phone Input */}
        <div className="relative flex-1 flex items-center">
          <input
            type="tel"
            name="phoneNumber"
            value={value}
            onChange={onChange}
            placeholder="9876543210"
            required={required}
            className={`w-full bg-[#1A1628] text-white text-sm rounded-xl py-3 px-4 border transition-all duration-200 placeholder-[#5E5870] focus:outline-none ${
              error
                ? 'border-rose-500 focus:ring-1 focus:ring-rose-500'
                : 'border-white/15 hover:border-white/30 focus:border-[#10B981] focus:ring-1 focus:ring-[#10B981]/40'
            }`}
            style={{ boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.3)' }}
          />
        </div>

      </div>

      <p className="text-[10px] text-[#7F7990]">
        Used for WhatsApp & Push payment reminder alerts
      </p>

      {error && (
        <p className="text-[11px] text-rose-400 font-medium pt-0.5 animate-fadeIn">
          {error}
        </p>
      )}
    </div>
  );
}
