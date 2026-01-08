"""Initial migration - create payments table

Revision ID: 001
Revises:
Create Date: 2024-01-01 00:00:00.000000

Creates the payments table with all columns needed for the payment system.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create PaymentMethod enum type
    payment_method_enum = postgresql.ENUM(
        'CASH', 'CASH_ON_DELIVERY', 'VISA', 'MASTERCARD', 'AMEX',
        'JCB', 'LINE_PAY', 'PAYPAY', 'POINTS', 'GRAB_PAY',
        'BANK_TRANSFER', 'CHEQUE',
        name='paymentmethod',
        create_type=True
    )

    # Create payments table
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('customer_id', sa.String(length=255), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('price_modifier', sa.Numeric(precision=4, scale=2), nullable=False),
        sa.Column('final_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('payment_method', payment_method_enum, nullable=False),
        sa.Column('additional_item', sa.JSON(), nullable=True),
        sa.Column('datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for efficient querying
    op.create_index('ix_payment_id', 'payments', ['id'], unique=False)
    op.create_index('ix_payment_customer_id', 'payments', ['customer_id'], unique=False)
    op.create_index('ix_payment_datetime', 'payments', ['datetime'], unique=False)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_payment_datetime', table_name='payments')
    op.drop_index('ix_payment_customer_id', table_name='payments')
    op.drop_index('ix_payment_id', table_name='payments')

    # Drop payments table
    op.drop_table('payments')

    # Drop enum type
    op.execute('DROP TYPE IF EXISTS paymentmethod')
