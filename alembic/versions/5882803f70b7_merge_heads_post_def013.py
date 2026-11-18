"""merge heads post-def013

Revision ID: 5882803f70b7
Revises: 0f2176ad9045, 6668dd1b047b, c405c412a0d3
Create Date: 2026-11-17 11:46:23.467386

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5882803f70b7'
down_revision: Union[str, Sequence[str], None] = ('0f2176ad9045', '6668dd1b047b', 'c405c412a0d3')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
