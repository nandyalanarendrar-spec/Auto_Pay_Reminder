-- Migration: 005_create_notification_logs_table.sql
-- Description: Drops existing table if present and creates notification_logs table with UUID user_id referencing auth.users(id), UNIQUE constraint, and RLS

DROP TABLE IF EXISTS notification_logs CASCADE;

CREATE TABLE notification_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    entity_type TEXT NOT NULL CHECK (entity_type IN ('subscription', 'emi')),
    entity_id TEXT NOT NULL,
    notification_type TEXT NOT NULL CHECK (notification_type IN ('7d', '3d', '1d', '0d')),
    sent_date DATE NOT NULL DEFAULT CURRENT_DATE,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    channel TEXT NOT NULL DEFAULT 'web',
    
    -- UNIQUE constraint matching (user_id, entity_type, entity_id, notification_type, sent_date)
    CONSTRAINT unique_user_entity_notif_date UNIQUE (user_id, entity_type, entity_id, notification_type, sent_date)
);

-- Index for fast lookup in get_due_reminders_for_user query
CREATE INDEX idx_notification_logs_lookup 
ON notification_logs (user_id, entity_type, entity_id, notification_type, sent_date);

-- Enable Row Level Security (RLS)
ALTER TABLE notification_logs ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Users can view their own notification logs
DROP POLICY IF EXISTS "Users can view their own notification logs" ON notification_logs;
CREATE POLICY "Users can view their own notification logs" 
ON notification_logs FOR SELECT 
USING (auth.uid() = user_id);

-- RLS Policy: Users can insert their own notification logs
DROP POLICY IF EXISTS "Users can insert their own notification logs" ON notification_logs;
CREATE POLICY "Users can insert their own notification logs" 
ON notification_logs FOR INSERT 
WITH CHECK (auth.uid() = user_id);

-- RLS Policy: Users can manage their own notification logs
DROP POLICY IF EXISTS "Users can manage their own notification logs" ON notification_logs;
CREATE POLICY "Users can manage their own notification logs" 
ON notification_logs FOR ALL 
USING (auth.uid() = user_id);
