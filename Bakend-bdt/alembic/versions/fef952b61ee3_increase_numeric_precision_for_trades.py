"""increase_numeric_precision_for_trades

Revision ID: fef952b61ee3
Revises: 010
Create Date: 2026-10-09 13:42:32.069850
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision: str = 'fef952b61ee3'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Aumentar precisión de entry_price y close_price para soportar precios altos de XAUUSD
    op.alter_column('trades', 'entry_price',
                    existing_type=sa.NUMERIC(precision=12, scale=5),
                    type_=sa.NUMERIC(precision=16, scale=5),
                    existing_nullable=False)
    op.alter_column('trades', 'close_price',
                    existing_type=sa.NUMERIC(precision=12, scale=5),
                    type_=sa.NUMERIC(precision=16, scale=5),
                    existing_nullable=False)
    
    # Aumentar precisión de lot_size
    op.alter_column('trades', 'lot_size',
                    existing_type=sa.NUMERIC(precision=8, scale=4),
                    type_=sa.NUMERIC(precision=12, scale=4),
                    existing_nullable=True)
    
    # Aumentar precisión de net_pnl y balance
    op.alter_column('trades', 'net_pnl',
                    existing_type=sa.NUMERIC(precision=10, scale=2),
                    type_=sa.NUMERIC(precision=14, scale=2),
                    existing_nullable=False)
    op.alter_column('trades', 'balance',
                    existing_type=sa.NUMERIC(precision=10, scale=2),
                    type_=sa.NUMERIC(precision=14, scale=2),
                    existing_nullable=True)


def downgrade() -> None:
    # Revertir cambios
    op.alter_column('trades', 'balance',
                    existing_type=sa.NUMERIC(precision=14, scale=2),
                    type_=sa.NUMERIC(precision=10, scale=2),
                    existing_nullable=True)
    op.alter_column('trades', 'net_pnl',
                    existing_type=sa.NUMERIC(precision=14, scale=2),
                    type_=sa.NUMERIC(precision=10, scale=2),
                    existing_nullable=False)
    op.alter_column('trades', 'lot_size',
                    existing_type=sa.NUMERIC(precision=12, scale=4),
                    type_=sa.NUMERIC(precision=8, scale=4),
                    existing_nullable=True)
    op.alter_column('trades', 'close_price',
                    existing_type=sa.NUMERIC(precision=16, scale=5),
                    type_=sa.NUMERIC(precision=12, scale=5),
                    existing_nullable=False)
    op.alter_column('trades', 'entry_price',
                    existing_type=sa.NUMERIC(precision=16, scale=5),
                    type_=sa.NUMERIC(precision=12, scale=5),
                    existing_nullable=False)
