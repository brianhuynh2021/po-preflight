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
"""


class AuditStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
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
