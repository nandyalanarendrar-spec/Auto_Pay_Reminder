import React, { useState } from 'react';
import AuthLayout from './AuthLayout';
import LoginView from './LoginView';
import RegisterView from './RegisterView';
import ForgotPasswordView from './ForgotPasswordView';
import EmailVerificationView from './EmailVerificationView';
import ResetPasswordView from './ResetPasswordView';
import { supabase, isSupabaseConfigured } from '../../lib/supabaseClient';

export default function AuthContainer({ onAuthenticated }) {
  const [currentScreen, setCurrentScreen] = useState('login');
  const [userEmail, setUserEmail] = useState('');

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

    // 1. Try FastAPI backend auto-confirm signup (Bypasses email confirmation delays & trigger errors!)
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
        return handleLogin({ email, password });
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

  // Handle Forgot Password Request
  const handleForgotPassword = async (email) => {
    if (isSupabaseConfigured && supabase) {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`
      });
      if (error) throw new Error(error.message);
    }
  };

  // Handle Social Login Trigger
  const handleSocialLogin = async (provider) => {
    if (isSupabaseConfigured && supabase) {
      const { error } = await supabase.auth.signInWithOAuth({
        provider: provider
      });
      if (error) alert(`Social login note: ${error.message}`);
    } else {
      alert(`Social Login (${provider}) activated! (Configure OAuth in Supabase Dashboard)`);
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
        />
      )}

      {currentScreen === 'email_verification' && (
        <EmailVerificationView
          email={userEmail}
          onResendEmail={handleForgotPassword}
          onNavigateLogin={() => setCurrentScreen('login')}
        />
      )}

      {currentScreen === 'reset_password' && (
        <ResetPasswordView
          onNavigateLogin={() => setCurrentScreen('login')}
        />
      )}
    </AuthLayout>
  );
}
