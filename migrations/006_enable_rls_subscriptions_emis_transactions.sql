-- Migration: 006_enable_rls_subscriptions_emis_transactions.sql
-- Description: Enables Row Level Security (RLS) and adds user ownership policies for subscriptions, emis, and transactions tables.

-- 1. Enable RLS and Policies for subscriptions
ALTER TABLE subscriptions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage their own subscriptions" ON subscriptions;
CREATE POLICY "Users manage their own subscriptions"
  ON subscriptions FOR ALL USING (auth.uid() = user_id);

-- 2. Enable RLS and Policies for emis
ALTER TABLE emis ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage their own emis" ON emis;
CREATE POLICY "Users manage their own emis"
  ON emis FOR ALL USING (auth.uid() = user_id);

-- 3. Enable RLS and Policies for transactions (if exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'transactions') THEN
        ALTER TABLE transactions ENABLE ROW LEVEL SECURITY;
        
        DROP POLICY IF EXISTS "Users manage their own transactions" ON transactions;
        EXECUTE 'CREATE POLICY "Users manage their own transactions" ON transactions FOR ALL USING (auth.uid() = user_id)';
    END IF;
END $$;
