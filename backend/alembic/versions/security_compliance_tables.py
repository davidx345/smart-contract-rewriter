"""Add security and compliance tables

Revision ID: security_compliance_tables
Revises: 0a3a62f47835
Create Date: 2025-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'security_compliance_tables'
down_revision = '0a3a62f47835'
branch_labels = None
depends_on = None


def upgrade():
    # GDPR Consent table
    op.create_table('gdpr_consents',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('purpose', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.Column('withdrawn_at', sa.DateTime(), nullable=True),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('consent_text', sa.Text(), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Data Processing Records
    op.create_table('data_processing_records',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('processing_purpose', sa.String(50), nullable=False),
        sa.Column('data_categories', sa.Text(), nullable=False),
        sa.Column('data_subjects', sa.String(100), nullable=False),
        sa.Column('recipients', sa.Text(), nullable=True),
        sa.Column('retention_period', sa.String(100), nullable=False),
        sa.Column('security_measures', sa.Text(), nullable=False),
        sa.Column('legal_basis', sa.String(100), nullable=False),
        sa.Column('third_country_transfers', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Data Breach Records
    op.create_table('data_breach_records',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('incident_id', sa.String(50), unique=True, nullable=False),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('reported_to_authority_at', sa.DateTime(), nullable=True),
        sa.Column('reported_to_subjects_at', sa.DateTime(), nullable=True),
        sa.Column('breach_type', sa.String(50), nullable=False),
        sa.Column('affected_data_categories', sa.Text(), nullable=False),
        sa.Column('affected_subjects_count', sa.Integer(), nullable=False),
        sa.Column('risk_level', sa.String(20), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('containment_measures', sa.Text(), nullable=True),
        sa.Column('notification_required', sa.Boolean(), default=True),
        sa.Column('authority_notified', sa.Boolean(), default=False),
        sa.Column('subjects_notified', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Data Retention Policies
    op.create_table('data_retention_policies',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('data_category', sa.String(50), nullable=False),
        sa.Column('processing_purpose', sa.String(50), nullable=False),
        sa.Column('retention_period_days', sa.Integer(), nullable=False),
        sa.Column('legal_basis', sa.String(100), nullable=False),
        sa.Column('deletion_criteria', sa.Text(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Security Alerts
    op.create_table('security_alerts',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('alert_id', sa.String(50), unique=True, nullable=False),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('threat_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), default='open'),
        sa.Column('source_ip', sa.String(45), nullable=True),
        sa.Column('target_endpoint', sa.String(500), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('technical_details', sa.Text(), nullable=True),
        sa.Column('affected_systems', sa.Text(), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=False, default=0.0),
        sa.Column('detected_at', sa.DateTime(), nullable=False),
        sa.Column('acknowledged_at', sa.DateTime(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(), nullable=True),
        sa.Column('assigned_to', sa.String(100), nullable=True),
        sa.Column('resolution_notes', sa.Text(), nullable=True),
        sa.Column('false_positive', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    # Security Metrics
    op.create_table('security_metrics',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_type', sa.String(50), nullable=False),
        sa.Column('tags', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, default=sa.func.now()),
    )

    # Create indexes for better performance
    op.create_index('idx_gdpr_consents_user_purpose', 'gdpr_consents', ['user_id', 'purpose'])
    op.create_index('idx_security_alerts_severity_status', 'security_alerts', ['severity', 'status'])
    op.create_index('idx_security_alerts_detected_at', 'security_alerts', ['detected_at'])
    op.create_index('idx_security_metrics_name_timestamp', 'security_metrics', ['metric_name', 'timestamp'])
    op.create_index('idx_data_breach_incident_id', 'data_breach_records', ['incident_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_gdpr_consents_user_purpose')
    op.drop_index('idx_security_alerts_severity_status')
    op.drop_index('idx_security_alerts_detected_at')
    op.drop_index('idx_security_metrics_name_timestamp')
    op.drop_index('idx_data_breach_incident_id')
    
    # Drop tables
    op.drop_table('security_metrics')
    op.drop_table('security_alerts')
    op.drop_table('data_retention_policies')
    op.drop_table('data_breach_records')
    op.drop_table('data_processing_records')
    op.drop_table('gdpr_consents')
