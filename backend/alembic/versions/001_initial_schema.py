"""Initial schema for Meu Carro

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trial_ends_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('plan', sa.String(length=20), nullable=False, default='trial'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('referral_code', sa.String(length=20), nullable=False, unique=True),
        sa.Column('referred_by', sa.String(length=20), nullable=True)
    )

    # Vehicles table
    op.create_table(
        'vehicles',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('brand', sa.String(length=50), nullable=False),
        sa.Column('model', sa.String(length=50), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('version', sa.String(length=50), nullable=True),
        sa.Column('fuel_type', sa.String(length=30), nullable=False, default='flex'),
        sa.Column('current_odometer', sa.Integer(), nullable=False, default=0),
        sa.Column('license_plate', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Fuel records table
    op.create_table(
        'fuel_records',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('vehicle_id', sa.Integer(), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.String(length=10), nullable=False),
        sa.Column('odometer', sa.Integer(), nullable=False),
        sa.Column('liters', sa.Float(), nullable=False),
        sa.Column('price_per_liter', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('fuel_type', sa.String(length=30), nullable=False),
        sa.Column('station', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('consumption_km_per_l', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Maintenance records table
    op.create_table(
        'maintenance_records',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('vehicle_id', sa.Integer(), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.String(length=10), nullable=False),
        sa.Column('odometer', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('workshop', sa.String(length=100), nullable=True),
        sa.Column('cost', sa.Float(), nullable=False),
        sa.Column('next_due_odometer', sa.Integer(), nullable=True),
        sa.Column('next_due_date', sa.String(length=10), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Expense records table
    op.create_table(
        'expense_records',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('vehicle_id', sa.Integer(), sa.ForeignKey('vehicles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('date', sa.String(length=10), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Feedback table
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True)
    )

    # Analytics Events table
    op.create_table(
        'analytics_events',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_name', sa.String(length=100), nullable=False),
        sa.Column('metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True)
    )

def downgrade() -> None:
    op.drop_table('analytics_events')
    op.drop_table('feedback')
    op.drop_table('expense_records')
    op.drop_table('maintenance_records')
    op.drop_table('fuel_records')
    op.drop_table('vehicles')
    op.drop_table('users')
