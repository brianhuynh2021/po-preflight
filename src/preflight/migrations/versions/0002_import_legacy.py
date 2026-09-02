"""0002_import_legacy

Revision ID: 0002_import_legacy
Revises: 0001_baseline
Create Date: 2026-09-02

"""
import json
from decimal import Decimal
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0002_import_legacy"
down_revision: Union[str, None] = "0001_baseline"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    tables = inspector.get_table_names()

    # Handle legacy customer_aliases schema if it had raw_query (old SKU alias format)
    if "customer_aliases" in tables:
        ca_cols = [c["name"] for c in inspector.get_columns("customer_aliases")]
        if "raw_query" in ca_cols and "alias_normalized" not in ca_cols:
            op.rename_table("customer_aliases", "legacy_customer_sku_aliases")
            # Create fresh customer_aliases table
            op.create_table(
                "customer_aliases",
                sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
                sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True),
                sa.Column("alias_normalized", sa.String(length=255), nullable=False),
                sa.UniqueConstraint("customer_id", "alias_normalized", name="uq_customer_alias"),
            )

    # If legacy table analyses exists, migrate data
    if "analyses" in tables:
        analyses_cols = [c["name"] for c in inspector.get_columns("analyses")]
        file_col = "raw_file" if "raw_file" in analyses_cols else ("raw_filename" if "raw_filename" in analyses_cols else "NULL as raw_file")

        # Check if default organization exists
        org_res = conn.execute(sa.text("SELECT id FROM organizations WHERE code = 'default'")).fetchone()
        if not org_res:
            conn.execute(sa.text("INSERT INTO organizations (code, name) VALUES ('default', 'Công ty Mặc định')"))
            org_id = conn.execute(sa.text("SELECT id FROM organizations WHERE code = 'default'")).fetchone()[0]
        else:
            org_id = org_res[0]

        # Fetch legacy analyses
        legacy_rows = conn.execute(sa.text(f"SELECT id, po_number, customer, status, findings_json, order_json, {file_col}, created_at FROM analyses")).fetchall()

        cust_counter = 1
        customer_map = {}

        for row in legacy_rows:
            a_id, po_num, cust_name, status, findings_json, order_json, raw_file, created_at = row
            
            # Find or create customer
            norm_cust = cust_name.strip().lower() if cust_name else "khách hàng vãng lai"
            if norm_cust not in customer_map:
                cust_res = conn.execute(
                    sa.text("SELECT id FROM customers WHERE org_id = :org_id AND normalized_name = :norm"),
                    {"org_id": org_id, "norm": norm_cust}
                ).fetchone()
                if cust_res:
                    customer_map[norm_cust] = cust_res[0]
                else:
                    code = f"C{cust_counter:04d}"
                    cust_counter += 1
                    conn.execute(
                        sa.text("INSERT INTO customers (org_id, code, name, normalized_name) VALUES (:org_id, :code, :name, :norm)"),
                        {"org_id": org_id, "code": code, "name": cust_name or "Khách hàng vãng lai", "norm": norm_cust}
                    )
                    c_id = conn.execute(
                        sa.text("SELECT id FROM customers WHERE org_id = :org_id AND code = :code"),
                        {"org_id": org_id, "code": code}
                    ).fetchone()[0]
                    customer_map[norm_cust] = c_id

            customer_id = customer_map[norm_cust]

            # Parse order_json
            parsed_order = {}
            if order_json:
                try:
                    parsed_order = json.loads(order_json)
                except Exception:
                    pass

            currency = parsed_order.get("currency", "VND")
            items = parsed_order.get("items", [])

            # Check if order already exists
            existing_ord = conn.execute(
                sa.text("SELECT id FROM orders WHERE org_id = :org_id AND po_number = :po_num AND revision = 1"),
                {"org_id": org_id, "po_num": po_num}
            ).fetchone()

            if not existing_ord:
                # Insert order
                conn.execute(
                    sa.text("""
                        INSERT INTO orders (
                            org_id, customer_id, po_number, revision, status, rule_status, currency,
                            subtotal, tax_amount, grand_total, source_file, source_channel, created_at
                        ) VALUES (
                            :org_id, :customer_id, :po_number, 1, :status, :rule_status, :currency,
                            :subtotal, :tax_amount, :grand_total, :source_file, :source_channel, :created_at
                        )
                    """),
                    {
                        "org_id": org_id,
                        "customer_id": customer_id,
                        "po_number": po_num,
                        "status": "analyzed" if status in ("ready_for_approval", "review_required", "blocked") else status,
                        "rule_status": status if status in ("ready_for_approval", "review_required", "blocked") else "ready_for_approval",
                        "currency": currency,
                        "subtotal": 0.0,
                        "tax_amount": 0.0,
                        "grand_total": 0.0,
                        "source_file": raw_file,
                        "source_channel": "legacy_import",
                        "created_at": created_at,
                    }
                )
                order_id = conn.execute(
                    sa.text("SELECT id FROM orders WHERE org_id = :org_id AND po_number = :po_num AND revision = 1"),
                    {"org_id": org_id, "po_num": po_num}
                ).fetchone()[0]

                # Insert order lines
                line_subtotal = 0.0
                for idx, it in enumerate(items, 1):
                    qty = it.get("quantity", 1)
                    u_price = float(it.get("unit_price", 0))
                    l_total = float(qty * u_price)
                    line_subtotal += l_total
                    conn.execute(
                        sa.text("""
                            INSERT INTO order_lines (
                                order_id, line_no, raw_sku, sku, quantity, uom, base_quantity,
                                unit_price, discount_percent, discount_amount, tax_rate, is_promo, line_total
                            ) VALUES (
                                :order_id, :line_no, :raw_sku, :sku, :quantity, 'PCS', :quantity,
                                :unit_price, 0.0, 0.0, 0.0, 0, :line_total
                            )
                        """),
                        {
                            "order_id": order_id,
                            "line_no": idx,
                            "raw_sku": it.get("sku"),
                            "sku": it.get("sku", "UNKNOWN"),
                            "quantity": qty,
                            "unit_price": u_price,
                            "line_total": l_total,
                        }
                    )

                # Update order totals
                conn.execute(
                    sa.text("UPDATE orders SET subtotal = :tot, grand_total = :tot WHERE id = :order_id"),
                    {"tot": line_subtotal, "order_id": order_id}
                )

                # Insert findings
                if findings_json:
                    try:
                        f_list = json.loads(findings_json)
                        for f in f_list:
                            conn.execute(
                                sa.text("""
                                    INSERT INTO findings (order_id, code, severity, message, evidence_json)
                                    VALUES (:order_id, :code, :sev, :msg, :ev)
                                """),
                                {
                                    "order_id": order_id,
                                    "code": f.get("code", "UNKNOWN"),
                                    "sev": f.get("severity", "error"),
                                    "msg": f.get("message", ""),
                                    "ev": json.dumps(f.get("evidence", {})) if f.get("evidence") else None,
                                }
                            )
                    except Exception:
                        pass


def downgrade() -> None:
    pass
