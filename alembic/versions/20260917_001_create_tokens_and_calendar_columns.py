"""create oauth_tokens, device_tokens and calendar columns

Revision ID: 20260917_001
Revises: 
Create Date: 2026-09-17 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260917_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create oauth_tokens table
    op.create_table(
        'oauth_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False, server_default='google'),
        sa.Column('access_token', sa.Text(), nullable=True),
        sa.Column('refresh_token', sa.Text(), nullable=True),
        sa.Column('expires_at', sa.Float(), nullable=True),
        sa.Column('google_email', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'provider', name='oauth_tokens_user_provider_key')
    )
    op.create_index('idx_oauth_tokens_user', 'oauth_tokens', ['user_id'])

    # 2. Create device_tokens table
    op.create_table(
        'device_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('fcm_token', sa.String(512), nullable=False),
        sa.Column('platform', sa.String(50), server_default='web'),
        sa.Column('registered_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.UniqueConstraint('user_id', 'fcm_token', name='device_tokens_user_fcm_key')
    )
    op.create_index('idx_device_tokens_user', 'device_tokens', ['user_id'])

    # 3. Add calendar columns to subscriptions table if missing
    op.execute("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS calendar_event_id VARCHAR(255);")
    op.execute("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS calendar_sync_status VARCHAR(50) DEFAULT 'PENDING';")

    # 4. Add calendar columns to emis table if missing
    op.execute("ALTER TABLE emis ADD COLUMN IF NOT EXISTS calendar_event_id VARCHAR(255);")
    op.execute("ALTER TABLE emis ADD COLUMN IF NOT EXISTS calendar_sync_status VARCHAR(50) DEFAULT 'PENDING';")


def downgrade() -> None:
    op.drop_index('idx_device_tokens_user', table_name='device_tokens')
    op.drop_table('device_tokens')
    op.drop_index('idx_oauth_tokens_user', table_name='oauth_tokens')
    op.drop_table('oauth_tokens')
    op.execute("ALTER TABLE subscriptions DROP COLUMN IF EXISTS calendar_event_id;")
    op.execute("ALTER TABLE subscriptions DROP COLUMN IF EXISTS calendar_sync_status;")
    op.execute("ALTER TABLE emis DROP COLUMN IF EXISTS calendar_event_id;")
    op.execute("ALTER TABLE emis DROP COLUMN IF EXISTS calendar_sync_status;")
