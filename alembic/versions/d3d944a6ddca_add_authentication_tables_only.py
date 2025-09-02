"""Add authentication tables only

Revision ID: d3d944a6ddca
Revises: 154d711c4966
Create Date: 2025-09-02 07:34:02.181248

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3d944a6ddca'
down_revision = '154d711c4966'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('session_id', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_accessed', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('status', sa.String(20), default='active'),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text()),
        sa.Column('session_metadata', sa.JSON(), default=dict)
    )
    
    # Create indexes for user_sessions
    op.create_index('idx_user_sessions_user_id', 'user_sessions', ['user_id'])
    op.create_index('idx_user_sessions_expires_at', 'user_sessions', ['expires_at'])
    op.create_index('idx_user_sessions_status', 'user_sessions', ['status'])
    
    # Create api_keys table
    op.create_table('api_keys',
        sa.Column('key_id', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('key_hash', sa.String(255), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True)),
        sa.Column('last_used', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('permissions', sa.JSON(), default=list),
        sa.Column('usage_count', sa.Integer(), default=0),
        sa.Column('rate_limit_per_minute', sa.Integer())
    )
    
    # Create indexes for api_keys
    op.create_index('idx_api_keys_user_id', 'api_keys', ['user_id'])
    op.create_index('idx_api_keys_is_active', 'api_keys', ['is_active'])
    op.create_index('idx_api_keys_expires_at', 'api_keys', ['expires_at'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_api_keys_expires_at')
    op.drop_index('idx_api_keys_is_active')
    op.drop_index('idx_api_keys_user_id')
    op.drop_index('idx_user_sessions_status')
    op.drop_index('idx_user_sessions_expires_at')
    op.drop_index('idx_user_sessions_user_id')
    
    # Drop tables
    op.drop_table('api_keys')
    op.drop_table('user_sessions')