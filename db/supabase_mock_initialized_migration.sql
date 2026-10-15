-- =========================================================
-- AUTOPAY GUARD - MOCK DATA ONE-TIME INITIALIZATION MIGRATION
-- =========================================================
-- Run this in Supabase SQL Editor to add mock_data_initialized column and user_settings table:

-- 1. Add mock_data_initialized column to public.users if table exists
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'users') THEN
        IF NOT EXISTS (SELECT FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'users' AND column_name = 'mock_data_initialized') THEN
            ALTER TABLE public.users ADD COLUMN mock_data_initialized BOOLEAN DEFAULT FALSE NOT NULL;
        END IF;
    END IF;
END $$;

-- 2. Create public.user_settings table for user preferences and initialization flags
CREATE TABLE IF NOT EXISTS public.user_settings (
    user_id UUID PRIMARY KEY,
    mock_data_initialized BOOLEAN DEFAULT FALSE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable RLS on user_settings
ALTER TABLE public.user_settings ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "Users access own settings" ON public.user_settings;
CREATE POLICY "Users access own settings" ON public.user_settings FOR ALL USING (auth.uid() = user_id);
