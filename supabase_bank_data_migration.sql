-- =========================================================
-- AUTOPAY GUARD - BANK DATA (Setu AA sandbox + demo bank) MIGRATION
-- =========================================================
-- Safe to run more than once. Run in the Supabase SQL Editor if the
-- backend's automatic startup migration cannot reach the database.

-- 1. Track where each transaction came from, and de-duplicate re-fetches
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS source VARCHAR(20) DEFAULT 'manual';
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE public.transactions ADD COLUMN IF NOT EXISTS account_ref TEXT;
CREATE UNIQUE INDEX IF NOT EXISTS ux_transactions_user_external ON public.transactions(user_id, external_id);
CREATE INDEX IF NOT EXISTS idx_transactions_source ON public.transactions(source);

-- 2. Payments the detector found, waiting for the user to confirm or ignore
CREATE TABLE IF NOT EXISTS public.detected_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    kind VARCHAR(20) NOT NULL,
    merchant_key VARCHAR(255) NOT NULL,
    merchant_name VARCHAR(255) NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    billing_frequency VARCHAR(20) DEFAULT 'monthly',
    next_date DATE,
    confidence INTEGER DEFAULT 50,
    flags JSONB DEFAULT '[]'::jsonb,
    details JSONB DEFAULT '{}'::jsonb,
    status VARCHAR(20) DEFAULT 'pending',
    created_item_id TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (user_id, kind, merchant_key)
);
CREATE INDEX IF NOT EXISTS idx_detected_items_user ON public.detected_items(user_id);
ALTER TABLE public.detected_items ENABLE ROW LEVEL SECURITY;
DO $$ BEGIN
    CREATE POLICY "Users access own detected items" ON public.detected_items FOR ALL USING (auth.uid() = user_id);
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
