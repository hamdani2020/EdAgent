"""Add privacy audit table

Revision ID: privacy_audit_001
Revises: d3d944a6ddca
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

# revision identifiers, used by Alembic.
revision = 'privacy_audit_001'
down_revision = 'd3d944a6ddca'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add privacy audit table"""
    op.create_table(
        'privacy_audit_log',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ip_address', sa.String(45)),  # IPv6 compatible
        sa.Column('user_agent', sa.Text),
        sa.Column('metadata', sa.JSON, default=dict),
        sa.Column('success', sa.Boolean, default=True),
        sa.Column('error_message', sa.Text),
        
        # Indexes for performance
        sa.Index('idx_privacy_audit_user_id', 'user_id'),
        sa.Index('idx_privacy_audit_action', 'action'),
        sa.Index('idx_privacy_audit_timestamp', 'timestamp'),
    )
    
    # Add privacy settings table
    op.create_table(
        'user_privacy_settings',
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('data_retention_days', sa.Integer),
        sa.Column('allow_analytics', sa.Boolean, default=True),
        sa.Column('allow_personalization', sa.Boolean, default=True),
        sa.Column('allow_marketing', sa.Boolean, default=False),
        sa.Column('auto_delete_conversations', sa.Boolean, default=False),
        sa.Column('conversation_retention_days', sa.Integer, default=365),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
    )
    
    # Add consent records table
    op.create_table(
        'user_consent_records',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('consent_type', sa.String(50), nullable=False),
        sa.Column('granted', sa.Boolean, nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text),
        sa.Column('consent_version', sa.String(10), default='1.0'),
        
        # Indexes for performance
        sa.Index('idx_consent_user_id', 'user_id'),
        sa.Index('idx_consent_type', 'consent_type'),
        sa.Index('idx_consent_granted_at', 'granted_at'),
        
        # Unique constraint for user + consent type (latest record wins)
        sa.UniqueConstraint('user_id', 'consent_type', name='unique_user_consent_type'),
    )


def downgrade() -> None:
    """Remove privacy audit table"""
    op.drop_table('user_consent_records')
    op.drop_table('user_privacy_settings')
    op.drop_table('privacy_audit_log')