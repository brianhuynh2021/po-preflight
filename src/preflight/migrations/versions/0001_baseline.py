"""0001_baseline

Revision ID: 0001_baseline
Revises: 
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from preflight.db.models import metadata

# revision identifiers, used by Alembic.
revision: str = "0001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create all tables defined in metadata
    bind = op.get_bind()
    metadata.create_all(bind)


def downgrade() -> None:
    bind = op.get_bind()
    metadata.drop_all(bind)
