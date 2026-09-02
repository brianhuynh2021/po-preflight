"""0003_align_customer_aliases

Revision ID: 0003_align_customer_aliases
Revises: 0002_import_legacy
Create Date: 2026-09-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0003_align_customer_aliases"
down_revision: Union[str, None] = "0002_import_legacy"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    if "customer_aliases" in tables:
        cols = [c["name"] for c in inspector.get_columns("customer_aliases")]
        if "alias_normalized" not in cols:
            op.drop_table("customer_aliases")
            op.create_table(
                "customer_aliases",
                sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
                sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
                sa.Column("alias_normalized", sa.String(length=255), nullable=False),
                sa.UniqueConstraint("customer_id", "alias_normalized", name="uq_customer_alias"),
            )


def downgrade() -> None:
    pass
