"""0004_customers_contact_emails

Revision ID: 0004_customers_contact_emails
Revises: 0003_align_customer_aliases
Create Date: 2026-09-04

Adds the `contact_emails` column that SQLITE_SCHEMA/POSTGRES_SCHEMA already
declare for new installs. Databases created before the column was introduced
never received it, because `CREATE TABLE IF NOT EXISTS` leaves an existing
table untouched, so customer creation failed with:
    OperationalError: table customers has no column named contact_emails
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_customers_contact_emails"
down_revision: Union[str, None] = "0003_align_customer_aliases"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "customers" not in inspector.get_table_names():
        return

    cols = [c["name"] for c in inspector.get_columns("customers")]
    if "contact_emails" not in cols:
        op.add_column(
            "customers",
            sa.Column("contact_emails", sa.Text(), nullable=True, server_default=""),
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if "customers" not in inspector.get_table_names():
        return

    cols = [c["name"] for c in inspector.get_columns("customers")]
    if "contact_emails" in cols:
        op.drop_column("customers", "contact_emails")
