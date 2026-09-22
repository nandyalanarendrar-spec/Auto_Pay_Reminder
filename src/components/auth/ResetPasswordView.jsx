import React, { useState } from 'react';
import GlassCard from './GlassCard';
import PasswordInput from './PasswordInput';
import PrimaryButton from './PrimaryButton';
import { ShieldCheck } from 'lucide-react';

export default function ResetPasswordView({ onUpdatePasswordSuccess, onNavigateLogin }) {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!password || password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setIsLoading(true);
    try {
      if (onUpdatePasswordSuccess) await onUpdatePasswordSuccess(password);
    } catch (err) {
      setError(err.message || 'Failed to update password.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GlassCard className="animate-fadeIn">
      
      {/* Icon */}
      <div className="flex justify-center mb-3">
        <div className="w-12 h-12 rounded-2xl bg-gradient-to-br from-[#ff007f] to-[#9b1cff] p-0.5 shadow-lg shadow-[#ff007f]/20">
          <div className="w-full h-full bg-[#080F1F] rounded-[14px] flex items-center justify-center">
            <ShieldCheck className="w-6 h-6 text-[#ff007f]" />
          </div>
        </div>
      </div>

      <div className="text-center mb-6">
        <h2 className="text-2xl font-extrabold tracking-tight text-white">
          Set New Password
        </h2>
        <p className="text-xs text-[#B8BECC] mt-1">
          Choose a strong password to secure your account
        </p>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs font-medium text-center">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        
        <PasswordInput
          label="NEW PASSWORD"
          name="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••"
          showStrengthMeter={true}
          required
        />

        <PasswordInput
          label="CONFIRM NEW PASSWORD"
          name="confirmPassword"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="••••••••"
          required
        />

        <div className="pt-3">
          <PrimaryButton isLoading={isLoading} loadingText="Updating Password...">
            Update Password
          </PrimaryButton>
        </div>

      </form>

    </GlassCard>
  );
}
