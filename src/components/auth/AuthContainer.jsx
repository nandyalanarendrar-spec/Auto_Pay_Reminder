import React, { useState } from 'react';
import AuthLayout from './AuthLayout';
import LoginView from './LoginView';
import RegisterView from './RegisterView';
import ForgotPasswordView from './ForgotPasswordView';
import EmailVerificationView from './EmailVerificationView';
import ResetPasswordView from './ResetPasswordView';
import { supabase, isSupabaseConfigured } from '../../lib/supabaseClient';

export default function AuthContainer({ onAuthenticated, onPasswordResetStarted, onPasswordResetComplete }) {
  const [currentScreen, setCurrentScreen] = useState('login');
  const [userEmail, setUserEmail] = useState('');
  const [isForgotPasswordFlow, setIsForgotPasswordFlow] = useState(false);

  // Handle Login submission
  const handleLogin = async ({ email, password }) => {
    if (isSupabaseConfigured && supabase) {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (error) {
        if (error.message.includes('Email not confirmed')) {
          setUserEmail(email);
          setCurrentScreen('email_verification');
          throw new Error('Email not confirmed yet. Please check your inbox.');
        }
        throw new Error(error.message);
      }

      if (data.user && onAuthenticated) {
        onAuthenticated(data.user);
      }
    } else {
      // Demo Mock mode fallback
      if (onAuthenticated) {
        onAuthenticated({ id: 'demo-user-1', email, user_metadata: { name: 'Narendra' } });
      }
    }
  };

  // Handle Registration submission
  const handleRegister = async ({ fullName, email, phoneNumber, countryCode, password }) => {
    setUserEmail(email);

    // 1. Try FastAPI backend signup (sends OTP email for verification)
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/auth/signup', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          password,
          name: fullName,
          phone_number: phoneNumber
        })
      });

      const resData = await res.json().catch(() => ({}));
      if (res.ok) {
        // Signup successful — now send 6-digit OTP email for verification
        if (isSupabaseConfigured && supabase) {
          await supabase.auth.signInWithOtp({ email });
        }
        setCurrentScreen('email_verification');
        return;
      } else if (resData && resData.detail) {
        throw new Error(resData.detail);
      }
    } catch (apiErr) {
      if (apiErr.message && !apiErr.message.includes('fetch')) {
        throw apiErr;
      }
      console.warn("Backend signup endpoint note:", apiErr);
    }

    // 2. Direct Supabase Client fallback
    if (isSupabaseConfigured && supabase) {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: fullName,
            phone_number: phoneNumber,
            country_code: countryCode
          }
        }
      });

      if (error) throw new Error(error.message);

      if (data.user && !data.session) {
        setCurrentScreen('email_verification');
      } else if (data.user && onAuthenticated) {
        onAuthenticated(data.user);
      }
    } else {
      setCurrentScreen('email_verification');
    }
  };

  // Handle 6-Digit Email OTP Verification Submission
  const handleVerifyEmailOtp = async (email, token) => {
    if (isSupabaseConfigured && supabase) {
      const { data, error } = await supabase.auth.verifyOtp({
        email,
        token,
        type: 'email'
      });
      if (error) throw new Error(error.message);

      // If user came from forgot password flow → show Set New Password screen
      if (isForgotPasswordFlow) {
        setCurrentScreen('reset_password');
        return;
      }

      if (data.user && onAuthenticated) {
        onAuthenticated(data.user);
      }
    } else {
      if (onAuthenticated) {
        onAuthenticated({ id: 'demo-user-1', email, user_metadata: { name: 'Verified User' } });
      }
    }
  };

  // Handle Set New Password (after forgot password OTP verification)
  const handleSetNewPassword = async (newPassword) => {
    if (isSupabaseConfigured && supabase) {
      const { error } = await supabase.auth.updateUser({ password: newPassword });
      if (error) throw new Error(error.message);
      // Sign out so user must login with new password
      await supabase.auth.signOut();
    }
    setIsForgotPasswordFlow(false);
    if (onPasswordResetComplete) onPasswordResetComplete();
    setCurrentScreen('login');
  };

  // Handle Forgot Password Request
  const handleForgotPassword = async (email) => {
    if (isSupabaseConfigured && supabase) {
      const { error } = await supabase.auth.signInWithOtp({
        email,
        options: { shouldCreateUser: false }
      });
      if (error) throw new Error(error.message);
    }
  };

  // Handle Social Login Trigger (Google / Social OAuth)
  const handleSocialLogin = async (provider) => {
    if (isSupabaseConfigured && supabase) {
      try {
        const { error } = await supabase.auth.signInWithOAuth({
          provider: provider,
          options: {
            redirectTo: `${window.location.origin}`
          }
        });
        if (error) {
          throw new Error(error.message);
        }
      } catch (err) {
        alert(`Google Login Note: ${err.message}\n\nMake sure Google Provider is enabled in your Supabase Dashboard (Authentication -> Providers -> Google).`);
      }
    } else {
      // Demo Mock Mode: Instant Google Login simulation
      if (onAuthenticated) {
        onAuthenticated({
          id: 'google-demo-user-123',
          email: 'nandyalanarendrar@gmail.com',
          user_metadata: {
            full_name: 'Narendra (Google)',
            avatar_url: 'https://lh3.googleusercontent.com/a/default-user'
          }
        });
      }
    }
  };

  return (
    <AuthLayout>
      {currentScreen === 'login' && (
        <LoginView
          onLoginSuccess={handleLogin}
          onNavigateRegister={() => setCurrentScreen('register')}
          onNavigateForgotPassword={() => setCurrentScreen('forgot_password')}
          onSocialLogin={handleSocialLogin}
        />
      )}

      {currentScreen === 'register' && (
        <RegisterView
          onRegisterSuccess={handleRegister}
          onNavigateLogin={() => setCurrentScreen('login')}
          onSocialLogin={handleSocialLogin}
        />
      )}

      {currentScreen === 'forgot_password' && (
        <ForgotPasswordView
          onResetRequested={handleForgotPassword}
          onNavigateLogin={() => setCurrentScreen('login')}
          onOtpSent={(email) => {
            setUserEmail(email);
            setIsForgotPasswordFlow(true);
            if (onPasswordResetStarted) onPasswordResetStarted();
            setCurrentScreen('email_verification');
          }}
        />
      )}

      {currentScreen === 'email_verification' && (
        <EmailVerificationView
          email={userEmail}
          onVerifyOtp={handleVerifyEmailOtp}
          onResendEmail={handleForgotPassword}
          onNavigateLogin={() => setCurrentScreen('login')}
        />
      )}

      {currentScreen === 'reset_password' && (
        <ResetPasswordView
          onUpdatePasswordSuccess={handleSetNewPassword}
          onNavigateLogin={() => setCurrentScreen('login')}
        />
      )}
    </AuthLayout>
  );
}
