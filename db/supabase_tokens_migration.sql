-- =========================================================
-- AUTOPAY GUARD - COMPLETE SUPABASE MIGRATION SCRIPT
-- =========================================================
-- Run this in Supabase SQL Editor to create missing tables and columns

-- 1. Create oauth_tokens table
CREATE TABLE IF NOT EXISTS public.oauth_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    provider VARCHAR(50) NOT NULL DEFAULT 'google',
    access_token TEXT,
    refresh_token TEXT,
    expires_at DOUBLE PRECISION,
    google_email TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT oauth_tokens_user_provider_key UNIQUE (user_id, provider)
);

-- 2. Create device_tokens table
CREATE TABLE IF NOT EXISTS public.device_tokens (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    fcm_token TEXT NOT NULL,
    platform VARCHAR(50) DEFAULT 'web',
    registered_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT device_tokens_user_fcm_key UNIQUE (user_id, fcm_token)
);

-- 3. Add calendar_event_id and sync status columns to subscriptions & emis tables
ALTER TABLE public.subscriptions ADD COLUMN IF NOT EXISTS calendar_event_id VARCHAR(255);
ALTER TABLE public.subscriptions ADD COLUMN IF NOT EXISTS calendar_sync_status VARCHAR(50) DEFAULT 'PENDING';

ALTER TABLE public.emis ADD COLUMN IF NOT EXISTS calendar_event_id VARCHAR(255);
ALTER TABLE public.emis ADD COLUMN IF NOT EXISTS calendar_sync_status VARCHAR(50) DEFAULT 'PENDING';

-- 4. Create Indexes
CREATE INDEX IF NOT EXISTS idx_oauth_tokens_user ON public.oauth_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_device_tokens_user ON public.device_tokens(user_id);

-- 5. Enable Row Level Security (RLS) Policies
ALTER TABLE public.oauth_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.device_tokens ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users access own oauth tokens"
  ON public.oauth_tokens FOR ALL
  USING (auth.uid() = user_id);

CREATE POLICY "Users access own device tokens"
  ON public.device_tokens FOR ALL
  USING (auth.uid() = user_id);
