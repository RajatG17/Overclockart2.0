"""expand order saga states

Revision ID: 08cf64d0cfad
Revises: 8d70c81469cb
Create Date: 2026-09-16 15:33:16.963956

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '08cf64d0cfad'
down_revision: Union[str, Sequence[str], None] = '8d70c81469cb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
