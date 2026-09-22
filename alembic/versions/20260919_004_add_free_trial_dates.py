"""add free trial date fields to subscriptions

Revision ID: 20260919_004
Revises: 20260919_003
Create Date: 2026-09-19 18:55:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260919_004'
down_revision = '20260919_003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS trial_start_date DATE;")
    op.execute("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS trial_end_date DATE;")
    op.execute("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS expected_first_payment_date DATE;")
    op.execute("ALTER TABLE subscriptions ADD COLUMN IF NOT EXISTS is_free_trial BOOLEAN DEFAULT FALSE;")


def downgrade() -> None:
    op.execute("ALTER TABLE subscriptions DROP COLUMN IF EXISTS trial_start_date;")
    op.execute("ALTER TABLE subscriptions DROP COLUMN IF EXISTS trial_end_date;")
    op.execute("ALTER TABLE subscriptions DROP COLUMN IF EXISTS expected_first_payment_date;")
    op.execute("ALTER TABLE subscriptions DROP COLUMN IF EXISTS is_free_trial;")
