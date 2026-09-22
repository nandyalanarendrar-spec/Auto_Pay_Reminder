-- =========================================================
-- AUTOPAY GUARD - COMPLETE SUPABASE POSTGRESQL DATABASE SCHEMA
-- =========================================================
-- Run this in Supabase SQL Editor to create all 4 core tables:
-- Users, Subscriptions, EMIs, and Transactions

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. SUBSCRIPTIONS TABLE
CREATE TABLE IF NOT EXISTS public.subscriptions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    merchant_name VARCHAR(255) NOT NULL,
    category VARCHAR(100) DEFAULT 'General',
    amount DECIMAL(10, 2) NOT NULL,
    billing_frequency VARCHAR(50) DEFAULT 'monthly',
    start_date DATE,
    next_payment_date DATE NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    is_recurring BOOLEAN DEFAULT true,
    autopay_enabled BOOLEAN DEFAULT true,
    risk_score INTEGER DEFAULT 10,
    receipt_url TEXT,
    source VARCHAR(50) DEFAULT 'user_added',
    calendar_event_id VARCHAR(255),
    calendar_id VARCHAR(255) DEFAULT 'primary',
    calendar_sync_status VARCHAR(50) DEFAULT 'PENDING',
    calendar_last_synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. EMI TABLE
CREATE TABLE IF NOT EXISTS public.emis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    loan_name VARCHAR(255) NOT NULL,
    total_installments INTEGER NOT NULL,
    installments_paid INTEGER DEFAULT 0,
    installment_amount DECIMAL(10, 2) NOT NULL,
    start_date DATE,
    next_due_date DATE NOT NULL,
    remaining_amount DECIMAL(10, 2) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    calendar_event_id VARCHAR(255),
    calendar_id VARCHAR(255) DEFAULT 'primary',
    calendar_sync_status VARCHAR(50) DEFAULT 'PENDING',
    calendar_last_synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 3. TRANSACTIONS TABLE
CREATE TABLE IF NOT EXISTS public.transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    merchant_name VARCHAR(255) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    transaction_date DATE NOT NULL,
    narration TEXT,
    mode VARCHAR(50) DEFAULT 'AUTO-DEBIT',
    is_labeled_recurring BOOLEAN DEFAULT false,
    is_labeled_emi BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- INDEXES FOR FAST QUERYING
CREATE INDEX IF NOT EXISTS idx_subscriptions_user ON public.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_merchant ON public.subscriptions(merchant_name);
CREATE INDEX IF NOT EXISTS idx_subscriptions_cal_event ON public.subscriptions(calendar_event_id);
CREATE INDEX IF NOT EXISTS idx_emis_user ON public.emis(user_id);
CREATE INDEX IF NOT EXISTS idx_emis_cal_event ON public.emis(calendar_event_id);
CREATE INDEX IF NOT EXISTS idx_transactions_user ON public.transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_merchant ON public.transactions(merchant_name);


-- ROW LEVEL SECURITY (RLS) POLICIES
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.emis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.transactions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users access own subscriptions" ON public.subscriptions FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users access own emis" ON public.emis FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users access own transactions" ON public.transactions FOR ALL USING (auth.uid() = user_id);
