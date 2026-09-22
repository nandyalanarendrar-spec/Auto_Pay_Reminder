"""add mock_data_initialized flag and user_settings table

Revision ID: 20260918_002
Revises: 20260917_001
Create Date: 2026-09-18 22:58:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260918_002'
down_revision = '20260917_001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add mock_data_initialized to users table if exists
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS mock_data_initialized BOOLEAN DEFAULT FALSE NOT NULL;")

    # 2. Create user_settings table
    op.create_table(
        'user_settings',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('mock_data_initialized', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'))
    )


def downgrade() -> None:
    op.drop_table('user_settings')
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS mock_data_initialized;")
