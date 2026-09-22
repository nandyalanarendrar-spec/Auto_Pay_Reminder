import React, { useState } from 'react';
import GlassCard from './GlassCard';
import InputField from './InputField';
import PasswordInput from './PasswordInput';
import PrimaryButton from './PrimaryButton';
import SocialLoginButton from './SocialLoginButton';
import { Shield } from 'lucide-react';

export default function LoginView({ 
  onLoginSuccess, 
  onNavigateRegister, 
  onNavigateForgotPassword,
  onSocialLogin 
}) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setErrorMessage('');
    if (!email || !password) {
      setErrorMessage('Invalid login credentials');
      return;
    }

    setIsLoading(true);
    try {
      await onLoginSuccess({ email, password });
    } catch (err) {
      setErrorMessage(err.message || 'Invalid login credentials');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GlassCard topError={errorMessage} className="animate-fadeIn">
      
      {/* Brand Icon & Name */}
      <div className="flex items-center justify-center space-x-2 mb-4">
        <div className="w-9 h-9 rounded-xl bg-[#7C3AED] flex items-center justify-center shadow-lg shadow-[#7C3AED]/30">
          <Shield className="w-5 h-5 text-white" />
        </div>
        <span className="text-xl font-extrabold text-white tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-purple-300 via-white to-purple-400">
          AutopayGuard
        </span>
      </div>

      {/* Heading */}
      <div className="text-center mb-6">
        <h2 className="text-2xl font-extrabold tracking-tight text-white">
          Welcome Back!
        </h2>
        <p className="text-xs text-[#A19DAE] mt-1">
          Login to continue to your account.
        </p>
      </div>

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        
        {/* Username or Email Address */}
        <InputField
          label="USERNAME OR GMAIL ADDRESS"
          type="text"
          name="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="narendra"
          required
        />

        {/* Password */}
        <div>
          <PasswordInput
            label="PASSWORD"
            name="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••••••"
            required
          />
          
          <div className="flex justify-end pt-1.5">
            <button
              type="button"
              onClick={onNavigateForgotPassword}
              className="text-xs font-semibold text-[#8B5CF6] hover:text-[#A78BFA] transition-colors"
            >
              Forgot Password?
            </button>
          </div>
        </div>

        {/* Login Button */}
        <div className="pt-2">
          <PrimaryButton isLoading={isLoading} loadingText="Logging in...">
            Login
          </PrimaryButton>
        </div>

      </form>

      {/* Social Google Login */}
      <SocialLoginButton onGoogleClick={() => onSocialLogin('google')} />

      {/* Register Link */}
      <div className="mt-6 text-center text-xs text-[#A19DAE]">
        New here?{' '}
        <button
          type="button"
          onClick={onNavigateRegister}
          className="font-bold text-[#8B5CF6] hover:text-[#A78BFA] transition-colors hover:underline"
        >
          Create an Account
        </button>
      </div>

    </GlassCard>
  );
}
