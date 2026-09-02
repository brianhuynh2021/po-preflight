"""Orders & Findings Repository using SQLAlchemy Core."""

from __future__ import annotations

import json
from decimal import Decimal
from typing import Any
from sqlalchemy import select, insert, update, func, text, and_
from sqlalchemy.engine import Connection

from preflight.db.models import orders, order_lines, findings, customers, decisions
from preflight.models import OrderAnalysis, OrderFinding
from preflight.repositories.customers import CustomerRepository


class OrderRepository:
    def __init__(self, conn: Connection):
        self.conn = conn

    def record_analysis(self, analysis: OrderAnalysis, source_file: str = "upload.json", org_id: int = 1) -> int:
        """Records an evaluated order analysis, customer, line items, and violation findings."""
        cust_repo = CustomerRepository(self.conn)
        cust = cust_repo.get_or_create(org_id, analysis.order.customer)
        customer_id = cust["id"]

        po_num = analysis.order.po_number
        subtotal = float(analysis.order.subtotal)
        tax_amount = 0.0
        grand_total = subtotal

        # Check existing order for revision management (scoped to org_id and customer_id)
        stmt = (
            select(orders.c.id, orders.c.revision)
            .where(
                orders.c.org_id == org_id,
                orders.c.customer_id == customer_id,
                orders.c.po_number == po_num,
            )
            .order_by(orders.c.revision.desc())
        )
        existing = self.conn.execute(stmt).fetchone()

        # Determine status vs rule_status
        rule_stat = analysis.status  # ready_for_approval, review_required, blocked
        lifecycle_stat = "analyzed"

        if existing:
            # Update existing or increment revision
            order_id = existing[0]
            upd_stmt = (
                update(orders)
                .where(orders.c.id == order_id)
                .values(
                    customer_id=customer_id,
                    rule_status=rule_stat,
                    status=lifecycle_stat,
                    currency=analysis.order.currency,
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    grand_total=grand_total,
                    source_file=source_file,
                    analyzed_at=func.now(),
                )
            )
            self.conn.execute(upd_stmt)

            # Clear old lines and findings
            self.conn.execute(order_lines.delete().where(order_lines.c.order_id == order_id))
            self.conn.execute(findings.delete().where(findings.c.order_id == order_id))
        else:
            ins_stmt = (
                insert(orders)
                .values(
                    org_id=org_id,
                    customer_id=customer_id,
                    po_number=po_num,
                    revision=1,
                    status=lifecycle_stat,
                    rule_status=rule_stat,
                    currency=analysis.order.currency,
                    subtotal=subtotal,
                    tax_amount=tax_amount,
                    grand_total=grand_total,
                    source_file=source_file,
                    source_channel="web_upload",
                    analyzed_at=func.now(),
                )
                .returning(orders.c.id)
            )
            res = self.conn.execute(ins_stmt).fetchone()
            order_id = res[0]

        # Insert lines
        for idx, line in enumerate(analysis.order.items, 1):
            qty = line.quantity
            u_price = float(line.unit_price)
            l_total = float(qty * u_price)
            self.conn.execute(
                insert(order_lines).values(
                    order_id=order_id,
                    line_no=idx,
                    raw_sku=line.sku,
                    sku=line.sku,
                    quantity=qty,
                    uom=getattr(line, "uom", "PCS"),
                    base_quantity=qty,
                    unit_price=u_price,
                    discount_percent=0.0,
                    discount_amount=0.0,
                    tax_rate=0.0,
                    is_promo=False,
                    line_total=l_total,
                )
            )

        # Insert findings
        for f in analysis.findings:
            ev_json = json.dumps(f.evidence) if getattr(f, "evidence", None) else None
            self.conn.execute(
                insert(findings).values(
                    order_id=order_id,
                    code=f.code,
                    severity=f.severity,
                    message=f.message,
                    evidence_json=ev_json,
                )
            )

        return order_id

    def get_by_id(self, order_id: int) -> dict[str, Any] | None:
        stmt = (
            select(
                orders,
                customers.c.name.label("customer_name"),
                customers.c.code.label("customer_code"),
            )
            .outerjoin(customers, customers.c.id == orders.c.customer_id)
            .where(orders.c.id == order_id)
        )
        row = self.conn.execute(stmt).fetchone()
        if not row:
            return None

        data = dict(row._mapping)
        # Fetch findings
        f_stmt = select(findings).where(findings.c.order_id == order_id)
        data["findings"] = [dict(r._mapping) for r in self.conn.execute(f_stmt).fetchall()]

        # Fetch lines
        l_stmt = select(order_lines).where(order_lines.c.order_id == order_id).order_by(order_lines.c.line_no)
        data["lines"] = [dict(r._mapping) for r in self.conn.execute(l_stmt).fetchall()]

        # Fetch decisions
        d_stmt = select(decisions).where(decisions.c.order_id == order_id).order_by(decisions.c.created_at.desc())
        data["decisions"] = [dict(r._mapping) for r in self.conn.execute(d_stmt).fetchall()]

        return data

    def get_by_po_number(self, po_number: str, org_id: int = 1) -> dict[str, Any] | None:
        stmt = (
            select(orders.c.id)
            .where(orders.c.org_id == org_id, orders.c.po_number == po_number)
            .order_by(orders.c.revision.desc())
        )
        row = self.conn.execute(stmt).fetchone()
        if not row:
            return None
        return self.get_by_id(row[0])

    def list_orders(
        self,
        org_id: int = 1,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        query = (
            select(
                orders,
                customers.c.name.label("customer_name"),
            )
            .outerjoin(customers, customers.c.id == orders.c.customer_id)
            .where(orders.c.org_id == org_id)
        )
        if status:
            query = query.where(orders.c.rule_status == status)

        query = query.order_by(orders.c.created_at.desc()).limit(limit).offset(offset)
        rows = self.conn.execute(query).fetchall()

        results = []
        for r in rows:
            d = dict(r._mapping)
            f_stmt = select(findings).where(findings.c.order_id == d["id"])
            d["findings"] = [dict(f._mapping) for f in self.conn.execute(f_stmt).fetchall()]
            results.append(d)
        return results

    def get_dashboard_stats(self, org_id: int = 1) -> dict[str, Any]:
        """Calculates dashboard metrics using pure SQL GROUP BY aggregations."""
        total_orders = self.conn.execute(
            select(func.count(orders.c.id)).where(orders.c.org_id == org_id)
        ).scalar() or 0

        # Status counts
        status_rows = self.conn.execute(
            select(orders.c.rule_status, func.count(orders.c.id))
            .where(orders.c.org_id == org_id)
            .group_by(orders.c.rule_status)
        ).fetchall()
        status_dist = {r[0]: r[1] for r in status_rows}

        ready_count = status_dist.get("ready_for_approval", 0)
        review_count = status_dist.get("review_required", 0)
        blocked_count = status_dist.get("blocked", 0)

        # Approved count from decisions
        approved_count = self.conn.execute(
            select(func.count(func.distinct(decisions.c.order_id)))
            .join(orders, orders.c.id == decisions.c.order_id)
            .where(orders.c.org_id == org_id, decisions.c.decision == "approved")
        ).scalar() or 0

        # Total violations
        total_violations = self.conn.execute(
            select(func.count(findings.c.id))
            .join(orders, orders.c.id == findings.c.order_id)
            .where(orders.c.org_id == org_id)
        ).scalar() or 0

        # Violation breakdown
        v_rows = self.conn.execute(
            select(findings.c.code, func.count(findings.c.id))
            .join(orders, orders.c.id == findings.c.order_id)
            .where(orders.c.org_id == org_id)
            .group_by(findings.c.code)
            .order_by(func.count(findings.c.id).desc())
        ).fetchall()
        violation_breakdown = {r[0]: r[1] for r in v_rows}

        pass_rate = round((ready_count / total_orders * 100.0), 1) if total_orders > 0 else 0.0

        return {
            "total_orders": total_orders,
            "ready_for_approval": ready_count,
            "review_required": review_count,
            "blocked": blocked_count,
            "approved": approved_count,
            "pass_rate_percent": pass_rate,
            "total_violations": total_violations,
            "status_distribution": status_dist,
            "violation_breakdown": violation_breakdown,
        }
