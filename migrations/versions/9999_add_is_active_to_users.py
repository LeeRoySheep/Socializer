"""Add is_active to users

Revision ID: 9999
Revises: 0002_add_error_logs_table
Create Date: 2025-09-19 09:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9999'
down_revision = '0002_add_error_logs_table'
branch_labels = None
depends_on = None

def upgrade():
    # Add is_active column with default True for existing users
    op.add_column('users', 
                 sa.Column('is_active', sa.Boolean(), 
                          server_default=sa.text('1'), 
                          nullable=False))

def downgrade():
    # Remove the is_active column if we need to rollback
    op.drop_column('users', 'is_active')
