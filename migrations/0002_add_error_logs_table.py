"""Add error_logs table

Revision ID: 0002
Revises: 0001
Create Date: 2025-09-19 01:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = '0002'
down_revision = '0001'
branch_labels = None
depends_on = None

def upgrade():
    # Create error_logs table
    op.create_table(
        'error_logs',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('(CURRENT_TIMESTAMP)')),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('error_type', sa.String(length=100), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=False),
        sa.Column('stack_trace', sa.Text(), nullable=True),
        sa.Column('context', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create index on timestamp for faster queries
    op.create_index(op.f('ix_error_logs_timestamp'), 'error_logs', ['timestamp'], unique=False)
    op.create_index(op.f('ix_error_logs_user_id'), 'error_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_error_logs_error_type'), 'error_logs', ['error_type'], unique=False)

def downgrade():
    # Drop indexes first
    op.drop_index(op.f('ix_error_logs_error_type'), table_name='error_logs')
    op.drop_index(op.f('ix_error_logs_user_id'), table_name='error_logs')
    op.drop_index(op.f('ix_error_logs_timestamp'), table_name='error_logs')
    
    # Drop the table
    op.drop_table('error_logs')
