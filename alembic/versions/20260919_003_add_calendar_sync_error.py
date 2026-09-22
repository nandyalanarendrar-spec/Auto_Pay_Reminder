"""add calendar_sync_error column to subscriptions and emis

Revision ID: 20260919_003
Revises: 20260918_002
Create Date: 2026-09-19 18:40:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260919_003'
down_revision = '20260918_002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add calendar_sync_error to subscriptions table
    op.execute("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS calendar_sync_error VARCHAR(1024);")

    # Add calendar_sync_error to emis table
    op.execute("ALTER TABLE emis ADD COLUMN IF NOT EXISTS calendar_sync_error VARCHAR(1024);")


def downgrade() -> None:
    op.execute("ALTER TABLE subscriptions DROP COLUMN IF EXISTS calendar_sync_error;")
    op.execute("ALTER TABLE emis DROP COLUMN IF EXISTS calendar_sync_error;")
