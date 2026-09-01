from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from preflight.models import Analysis


SCHEMA = """
CREATE TABLE IF NOT EXISTS analyses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_number TEXT NOT NULL,
    customer TEXT NOT NULL,
    status TEXT NOT NULL,
    total TEXT NOT NULL,
    source_file TEXT NOT NULL,
    order_json TEXT NOT NULL,
    findings_json TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_analyses_po ON analyses(po_number);
CREATE TABLE IF NOT EXISTS decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_number TEXT NOT NULL,
    decision TEXT NOT NULL,
    actor TEXT NOT NULL,
    note TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS customer_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL,
    raw_query TEXT NOT NULL,
    target_sku TEXT NOT NULL,
    confidence REAL NOT NULL DEFAULT 1.0,
    created_at TEXT NOT NULL,
    UNIQUE(customer_id, raw_query)
);
CREATE INDEX IF NOT EXISTS idx_customer_aliases ON customer_aliases(customer_id, raw_query);
"""


class AuditStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path, check_same_thread=False)
        self.connection.row_factory = sqlite3.Row
        self.connection.executescript(SCHEMA)

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> "AuditStore":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def has_po(self, po_number: str) -> bool:
        row = self.connection.execute(
            "SELECT 1 FROM analyses WHERE po_number = ? LIMIT 1", (po_number,)
        ).fetchone()
        return row is not None

    def record_analysis(self, analysis: Analysis, source_file: str) -> int:
        cursor = self.connection.execute(
            """
            INSERT INTO analyses (
                po_number, customer, status, total, source_file,
                order_json, findings_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                analysis.order.po_number,
                analysis.order.customer,
                analysis.status,
                str(analysis.order.total),
                source_file,
                json.dumps(analysis.order.to_dict(), ensure_ascii=False),
                json.dumps(
                    [finding.to_dict() for finding in analysis.findings],
                    ensure_ascii=False,
                ),
                datetime.now(UTC).isoformat(),
            ),
        )
        self.connection.commit()
        analysis.analysis_id = int(cursor.lastrowid)
        return analysis.analysis_id

    def update_analysis(self, order_id: int, analysis: Analysis) -> None:
        """Update an existing analysis with confirmed order details and preflight findings."""
        with self.connection:
            self.connection.execute(
                """
                UPDATE analyses
                SET po_number = ?, customer = ?, status = ?, total = ?,
                    order_json = ?, findings_json = ?
                WHERE id = ?
                """,
                (
                    analysis.order.po_number,
                    analysis.order.customer,
                    analysis.status,
                    str(analysis.order.total),
                    json.dumps(analysis.order.to_dict(), ensure_ascii=False),
                    json.dumps(
                        [finding.to_dict() for finding in analysis.findings],
                        ensure_ascii=False,
                    ),
                    order_id,
                ),
            )

    def record_decision(
        self, po_number: str, decision: str, actor: str, note: str = ""
    ) -> int:
        if decision not in {"approved", "rejected", "needs_changes"}:
            raise ValueError("Decision must be approved, rejected, or needs_changes")
        if not self.has_po(po_number):
            raise ValueError(f"PO {po_number} was not found")
        cursor = self.connection.execute(
            """
            INSERT INTO decisions (po_number, decision, actor, note, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (po_number, decision, actor, note, datetime.now(UTC).isoformat()),
        )
        self.connection.commit()
        return int(cursor.lastrowid)

    def history(self, po_number: str) -> dict[str, list[dict[str, object]]]:
        analyses = [
            dict(row)
            for row in self.connection.execute(
                "SELECT * FROM analyses WHERE po_number = ? ORDER BY id", (po_number,)
            )
        ]
        decisions = [
            dict(row)
            for row in self.connection.execute(
                "SELECT * FROM decisions WHERE po_number = ? ORDER BY id", (po_number,)
            )
        ]
        return {"analyses": analyses, "decisions": decisions}

    def list_orders(
        self,
        status: str | None = None,
        search: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        query = """
            SELECT 
                a.id,
                a.po_number,
                a.customer,
                a.status,
                a.total,
                a.source_file,
                a.order_json,
                a.findings_json,
                a.created_at,
                (SELECT d.decision FROM decisions d WHERE d.po_number = a.po_number ORDER BY d.id DESC LIMIT 1) AS latest_decision,
                (SELECT d.actor FROM decisions d WHERE d.po_number = a.po_number ORDER BY d.id DESC LIMIT 1) AS latest_actor,
                (SELECT d.created_at FROM decisions d WHERE d.po_number = a.po_number ORDER BY d.id DESC LIMIT 1) AS decided_at
            FROM analyses a
            WHERE 1=1
        """
        params: list[Any] = []
        if status:
            query += " AND a.status = ?"
            params.append(status)
        if search:
            query += " AND (a.po_number LIKE ? OR a.customer LIKE ?)"
            term = f"%{search}%"
            params.extend([term, term])

        query += " ORDER BY a.id DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = self.connection.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def get_order(self, po_or_id: str | int) -> dict[str, Any] | None:
        if isinstance(po_or_id, int) or str(po_or_id).isdigit():
            row = self.connection.execute(
                "SELECT * FROM analyses WHERE id = ? LIMIT 1", (int(po_or_id),)
            ).fetchone()
        else:
            row = self.connection.execute(
                "SELECT * FROM analyses WHERE po_number = ? ORDER BY id DESC LIMIT 1",
                (str(po_or_id),),
            ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["decisions"] = [
            dict(d)
            for d in self.connection.execute(
                "SELECT * FROM decisions WHERE po_number = ? ORDER BY id ASC",
                (data["po_number"],),
            ).fetchall()
        ]
        return data

    def get_dashboard_stats(self) -> dict[str, Any]:
        total_orders = self.connection.execute(
            "SELECT COUNT(*) AS c FROM analyses"
        ).fetchone()["c"]
        status_counts = {
            row["status"]: row["c"]
            for row in self.connection.execute(
                "SELECT status, COUNT(*) AS c FROM analyses GROUP BY status"
            ).fetchall()
        }
        decisions_count = {
            row["decision"]: row["c"]
            for row in self.connection.execute(
                "SELECT decision, COUNT(*) AS c FROM decisions GROUP BY decision"
            ).fetchall()
        }
        recent_rows = self.connection.execute(
            """
            SELECT id, po_number, customer, status, total, created_at 
            FROM analyses ORDER BY id DESC LIMIT 5
            """
        ).fetchall()
        return {
            "total_orders": total_orders,
            "status_counts": status_counts,
            "decisions_count": decisions_count,
            "recent_orders": [dict(r) for r in recent_rows],
        }

    def learn_alias(
        self,
        customer_id: str,
        raw_query: str,
        target_sku: str,
        confidence: float = 1.0,
    ) -> None:
        """Record or update a learned customer-specific product alias for active learning."""
        now = datetime.now(UTC).isoformat()
        normalized_query = raw_query.strip().lower()
        normalized_sku = target_sku.strip().upper()
        self.connection.execute(
            """
            INSERT INTO customer_aliases (customer_id, raw_query, target_sku, confidence, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(customer_id, raw_query) DO UPDATE SET
                target_sku = excluded.target_sku,
                confidence = excluded.confidence,
                created_at = excluded.created_at
            """,
            (customer_id.strip(), normalized_query, normalized_sku, confidence, now),
        )
        self.connection.commit()

    def get_customer_alias(self, customer_id: str, raw_query: str) -> str | None:
        """Lookup a learned alias for a specific customer."""
        normalized_query = raw_query.strip().lower()
        row = self.connection.execute(
            """
            SELECT target_sku FROM customer_aliases
            WHERE customer_id = ? AND raw_query = ?
            LIMIT 1
            """,
            (customer_id.strip(), normalized_query),
        ).fetchone()
        return str(row["target_sku"]) if row else None

    def list_customer_aliases(self, customer_id: str | None = None) -> list[dict[str, Any]]:
        """List learned customer aliases."""
        if customer_id:
            rows = self.connection.execute(
                "SELECT * FROM customer_aliases WHERE customer_id = ? ORDER BY id DESC",
                (customer_id.strip(),),
            ).fetchall()
        else:
            rows = self.connection.execute(
                "SELECT * FROM customer_aliases ORDER BY id DESC"
            ).fetchall()
        return [dict(r) for r in rows]

