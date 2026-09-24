-- =========================================================
-- AUTOPAY GUARD - PERSONAL CUSTOM REMINDERS TABLE SCHEMA
-- =========================================================
-- Run this in Supabase SQL Editor (https://supabase.com/dashboard)
-- to create the 'personal_reminders' table for PostgreSQL persistence.

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.personal_reminders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    title VARCHAR(255) NOT NULL,
    notes TEXT,
    due_datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    reminder_offsets JSONB DEFAULT '[10, 30, 60, 1440]'::jsonb,
    calendar_event_id VARCHAR(255),
    is_completed BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast user scoping
CREATE INDEX IF NOT EXISTS idx_personal_reminders_user ON public.personal_reminders(user_id);

-- Row Level Security (RLS) Policy
ALTER TABLE public.personal_reminders ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users access own personal reminders" 
ON public.personal_reminders FOR ALL 
USING (auth.uid() = user_id);
