import React, { useState } from 'react';
import GlassCard from './GlassCard';
import InputField from './InputField';
import PasswordInput from './PasswordInput';
import PhoneInput from './PhoneInput';
import PrimaryButton from './PrimaryButton';
import SocialLoginButton from './SocialLoginButton';
import { Shield } from 'lucide-react';

export default function RegisterView({ onRegisterSuccess, onNavigateLogin, onSocialLogin }) {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [countryCode, setCountryCode] = useState('+91');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const validateForm = () => {
    const errs = {};
    if (!fullName.trim()) errs.fullName = "Please enter your full name.";
    
    if (!email.trim() || !/\S+@\S+\.\S+/.test(email)) {
      errs.email = "Please enter a valid email address.";
    }

    const cleanPhone = phoneNumber.replace(/\s+/g, '');
    if (!cleanPhone) {
      errs.phoneNumber = "Phone number is required for notification alerts.";
    } else if (countryCode === '+91' && !/^[6-9]\d{9}$/.test(cleanPhone)) {
      errs.phoneNumber = "Please enter a valid 10-digit Indian mobile number.";
    }

    if (!password || password.length < 8) {
      errs.password = "Password must be at least 8 characters long.";
    }

    if (password !== confirmPassword) {
      errs.confirmPassword = "Passwords do not match.";
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsLoading(true);
    try {
      const formattedPhone = `${countryCode}${phoneNumber.replace(/\s+/g, '')}`;

      await onRegisterSuccess({
        fullName,
        email,
        phoneNumber: formattedPhone,
        countryCode,
        password
      });
    } catch (err) {
      setErrors({ form: err.message || 'An error occurred during registration.' });
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <GlassCard topError={errors.form} className="animate-fadeIn">
      
      {/* Brand Header */}
      <div className="flex items-center justify-center space-x-2 mb-3">
        <div className="w-8 h-8 rounded-xl bg-[#7C3AED] flex items-center justify-center shadow-lg shadow-[#7C3AED]/40">
          <Shield className="w-4 h-4 text-white" />
        </div>
        <span className="text-lg font-extrabold text-white tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-purple-200 via-white to-purple-300">
          AutopayGuard
        </span>
      </div>

      {/* Heading */}
      <div className="text-center mb-5">
        <h2 className="text-xl font-extrabold tracking-tight text-white">
          Create Account
        </h2>
        <p className="text-xs text-[#A19DAE] mt-0.5">
          Join AutopayGuard to track your finances.
        </p>
      </div>

      {/* Form Body - Only storing required database fields */}
      <form onSubmit={handleSubmit} className="space-y-4">
        
        {/* Full Name */}
        <InputField
          label="FULL NAME"
          name="fullName"
          value={fullName}
          onChange={(e) => setFullName(e.target.value)}
          placeholder="Nandyala Narendra Redy"
          error={errors.fullName}
          required
        />

        {/* Email Address */}
        <InputField
          label="EMAIL ADDRESS"
          type="email"
          name="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="nandyalanarendrar@gmail.com"
          error={errors.email}
          required
        />

        {/* Phone Number (+91 default) */}
        <PhoneInput
          label="PHONE NUMBER"
          countryCode={countryCode}
          onCountryCodeChange={setCountryCode}
          value={phoneNumber}
          onChange={(e) => setPhoneNumber(e.target.value)}
          error={errors.phoneNumber}
          required
        />

        {/* Password */}
        <PasswordInput
          label="PASSWORD"
          name="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          placeholder="••••••••••••"
          error={errors.password}
          showStrengthMeter={true}
          required
        />

        {/* Confirm Password */}
        <PasswordInput
          label="CONFIRM PASSWORD"
          name="confirmPassword"
          value={confirmPassword}
          onChange={(e) => setConfirmPassword(e.target.value)}
          placeholder="••••••••••••"
          error={errors.confirmPassword}
          required
        />

        {/* Create Account Button */}
        <div className="pt-2">
          <PrimaryButton isLoading={isLoading} loadingText="Creating Account...">
            Create Account
          </PrimaryButton>
        </div>

      </form>

      {/* Social Google Login */}
      <SocialLoginButton onGoogleClick={() => onSocialLogin && onSocialLogin('google')} />

      {/* Switch to Login */}
      <div className="mt-5 text-center text-xs text-[#A19DAE]">
        Already have an account?{' '}
        <button
          type="button"
          onClick={onNavigateLogin}
          className="font-bold text-[#8B5CF6] hover:text-[#A78BFA] transition-colors hover:underline"
        >
          Login
        </button>
      </div>

    </GlassCard>
  );
}
