"""Convert payment_method from enum to string

Revision ID: 6cf783e6d0c1
Revises: 001
Create Date: 2026-01-10 13:40:11.938618

This migration converts the payment_method column from PostgreSQL enum to VARCHAR.
Benefits:
- No migration needed when adding new payment methods
- Validation happens at application level (already implemented)
- Simpler database management
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6cf783e6d0c1'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert payment_method column from enum to varchar
    # Step 1: Add temporary column
    op.add_column('payments', sa.Column('payment_method_new', sa.String(50), nullable=True))

    # Step 2: Copy data (enum values are already strings)
    op.execute("UPDATE payments SET payment_method_new = payment_method::text")

    # Step 3: Drop old column
    op.drop_column('payments', 'payment_method')

    # Step 4: Rename new column
    op.alter_column('payments', 'payment_method_new', new_column_name='payment_method', nullable=False)

    # Step 5: Add index on payment_method
    op.create_index('ix_payments_payment_method', 'payments', ['payment_method'], unique=False)

    # Step 6: Drop the old enum type (optional, but keeps DB clean)
    op.execute("DROP TYPE IF EXISTS paymentmethod")


def downgrade() -> None:
    # Recreate the enum type
    op.execute("""
        CREATE TYPE paymentmethod AS ENUM (
            'CASH', 'CASH_ON_DELIVERY', 'VISA', 'MASTERCARD', 'AMEX',
            'JCB', 'LINE_PAY', 'PAYPAY', 'POINTS', 'GRAB_PAY',
            'BANK_TRANSFER', 'CHEQUE'
        )
    """)

    # Drop the index
    op.drop_index('ix_payments_payment_method', table_name='payments')

    # Add temporary column with enum type
    op.add_column('payments', sa.Column('payment_method_old', sa.Enum(
        'CASH', 'CASH_ON_DELIVERY', 'VISA', 'MASTERCARD', 'AMEX',
        'JCB', 'LINE_PAY', 'PAYPAY', 'POINTS', 'GRAB_PAY',
        'BANK_TRANSFER', 'CHEQUE',
        name='paymentmethod'
    ), nullable=True))

    # Copy data back
    op.execute("UPDATE payments SET payment_method_old = payment_method::paymentmethod")

    # Drop string column and rename
    op.drop_column('payments', 'payment_method')
    op.alter_column('payments', 'payment_method_old', new_column_name='payment_method', nullable=False)
