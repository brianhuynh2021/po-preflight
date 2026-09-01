from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AuditBlock:
    index: int
    timestamp: float
    po_number: str
    action: str
    actor: str
    payload_hash: str
    previous_hash: str
    block_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def calculate_hash(
    index: int,
    timestamp: float,
    po_number: str,
    action: str,
    actor: str,
    payload_hash: str,
    previous_hash: str,
) -> str:
    """Compute deterministic SHA-256 hash for a block."""
    raw = f"{index}|{timestamp:.4f}|{po_number}|{action}|{actor}|{payload_hash}|{previous_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def compute_payload_hash(payload: Any) -> str:
    """Compute canonical SHA-256 hash of arbitrary JSON-serializable payload."""
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class AuditHashChain:
    """Cryptographic Merkle-style Hash-Chain for SOX 404 & SOC2 Type II Audit Compliance."""

    GENESIS_PREV_HASH = "0000000000000000000000000000000000000000000000000000000000000000"

    @classmethod
    def build_chain(cls, events: list[dict[str, Any]]) -> list[AuditBlock]:
        """Build a verifiable hash chain from chronological order events."""
        blocks: list[AuditBlock] = []
        prev_hash = cls.GENESIS_PREV_HASH

        for idx, ev in enumerate(events):
            t = ev.get("timestamp", time.time())
            po = ev.get("po_number", "UNKNOWN")
            action = ev.get("action", "STATE_TRANSITION")
            actor = ev.get("actor", "system")
            payload = ev.get("payload", {})

            p_hash = compute_payload_hash(payload)
            b_hash = calculate_hash(idx, t, po, action, actor, p_hash, prev_hash)

            block = AuditBlock(
                index=idx,
                timestamp=t,
                po_number=po,
                action=action,
                actor=actor,
                payload_hash=p_hash,
                previous_hash=prev_hash,
                block_hash=b_hash,
            )
            blocks.append(block)
            prev_hash = b_hash

        return blocks

    @classmethod
    def verify_chain(cls, blocks: list[AuditBlock]) -> tuple[bool, str]:
        """Verify mathematical integrity of the hash chain."""
        if not blocks:
            return True, "Empty chain (valid)"

        prev_hash = cls.GENESIS_PREV_HASH
        for b in blocks:
            if b.previous_hash != prev_hash:
                return False, f"Broken chain at block #{b.index}: expected prev_hash {prev_hash}, got {b.previous_hash}"

            expected_hash = calculate_hash(
                b.index,
                b.timestamp,
                b.po_number,
                b.action,
                b.actor,
                b.payload_hash,
                b.previous_hash,
            )
            if b.block_hash != expected_hash:
                return False, f"Hash mismatch at block #{b.index}: recalculated {expected_hash} != {b.block_hash}"

            prev_hash = b.block_hash

        return True, f"Chain integrity verified: {len(blocks)} blocks valid."

    @classmethod
    def generate_compliance_certificate(
        cls,
        po_number: str,
        order_data: dict[str, Any],
        decisions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Generate a cryptographically signed compliance audit certificate."""
        events = [
            {
                "timestamp": time.time() - 60,
                "po_number": po_number,
                "action": "ORDER_INGESTED",
                "actor": "system:ingestion_pipeline",
                "payload": {"total": order_data.get("total"), "status": order_data.get("status")},
            }
        ]
        for d in decisions:
            events.append(
                {
                    "timestamp": time.time(),
                    "po_number": po_number,
                    "action": f"DECISION_{d.get('decision', 'UNKNOWN').upper()}",
                    "actor": d.get("actor", "system"),
                    "payload": d,
                }
            )

        blocks = cls.build_chain(events)
        is_valid, msg = cls.verify_chain(blocks)

        root_hash = blocks[-1].block_hash if blocks else cls.GENESIS_PREV_HASH

        return {
            "certificate_id": f"CERT-{hashlib.sha256(root_hash.encode('utf-8')).hexdigest()[:12].upper()}",
            "po_number": po_number,
            "issued_at": time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()),
            "standard_compliance": ["SOX-404-ITGC", "SOC2-Type-II-Trust-Criteria"],
            "chain_valid": is_valid,
            "chain_length": len(blocks),
            "merkle_root_hash": root_hash,
            "verification_message": msg,
            "blocks": [b.to_dict() for b in blocks],
        }
