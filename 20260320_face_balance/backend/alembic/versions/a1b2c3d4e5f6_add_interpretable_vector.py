"""add_interpretable_vector

Revision ID: a1b2c3d4e5f6
Revises: 5a89a0151cad
Create Date: 2026-03-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '5a89a0151cad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('features', sa.Column('interpretable_vector', ARRAY(sa.Float), nullable=True))
    op.add_column('person_features', sa.Column('interpretable_vector', ARRAY(sa.Float), nullable=True))


def downgrade() -> None:
    op.drop_column('person_features', 'interpretable_vector')
    op.drop_column('features', 'interpretable_vector')
