import React from 'react';

export default function InputField({
  label,
  type = 'text',
  name,
  value,
  onChange,
  placeholder,
  error,
  required = false,
  disabled = false
}) {
  return (
    <div className="w-full space-y-1.5 text-left">
      {label && (
        <label className="block text-[10px] font-extrabold tracking-wider text-[#B8BECC] uppercase">
          {label} {required && <span className="text-[#ff007f]">*</span>}
        </label>
      )}

      <div className="relative flex items-center">
        <input
          type={type}
          name={name}
          value={value}
          onChange={onChange}
          placeholder={placeholder}
          disabled={disabled}
          required={required}
          className={`w-full bg-[#12192B]/80 text-white text-sm rounded-xl py-3 pl-4 pr-10 border transition-all duration-200 placeholder-[#7F8798] focus:outline-none ${
            error
              ? 'border-rose-500 focus:ring-1 focus:ring-rose-500'
              : 'border-white/18 hover:border-white/30 focus:border-[#00F2FE] focus:ring-1 focus:ring-[#00F2FE]/40'
          }`}
          style={{
            boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.3)'
          }}
        />

        {/* Cyan indicator dot matching Photo 1 when value is filled */}
        {value && !error && (
          <span className="absolute right-3 w-2 h-2 rounded-full bg-[#00F2FE] shadow-[0_0_8px_#00F2FE] pointer-events-none"></span>
        )}
      </div>

      {error && (
        <p className="text-[11px] text-rose-400 font-medium pt-0.5 animate-fadeIn">
          {error}
        </p>
      )}
    </div>
  );
}
