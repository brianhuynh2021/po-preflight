from __future__ import annotations

import unittest

from starlette.testclient import TestClient

from preflight.api.app import app
from preflight.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerOpenException, CircuitState
from preflight.security.audit_chain import AuditBlock, AuditHashChain
from scripts.run_evals import run_evals


class TestEvalsAndHashChain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_audit_hash_chain_integrity_and_tamper_detection(self):
        """Test cryptographic hash chain verification and tamper detection."""
        events = [
            {"timestamp": 1000.0, "po_number": "PO-TEST-01", "action": "INGEST", "actor": "system", "payload": {"qty": 10}},
            {"timestamp": 1010.0, "po_number": "PO-TEST-01", "action": "APPROVE", "actor": "manager", "payload": {"note": "ok"}},
        ]
        blocks = AuditHashChain.build_chain(events)
        self.assertEqual(len(blocks), 2)

        # 1. Valid chain passes
        is_valid, msg = AuditHashChain.verify_chain(blocks)
        self.assertTrue(is_valid)

        # 2. Tampering with block payload fails verification
        tampered_block = AuditBlock(
            index=blocks[0].index,
            timestamp=blocks[0].timestamp,
            po_number=blocks[0].po_number,
            action=blocks[0].action,
            actor=blocks[0].actor,
            payload_hash="tampered_fake_hash_12345",
            previous_hash=blocks[0].previous_hash,
            block_hash=blocks[0].block_hash,
        )
        tampered_blocks = [tampered_block, blocks[1]]
        is_valid_tampered, _ = AuditHashChain.verify_chain(tampered_blocks)
        self.assertFalse(is_valid_tampered)

    def test_audit_certificate_endpoint(self):
        """Test GET /api/v1/orders/{id}/audit-certificate."""
        res_orders = self.client.get("/api/v1/orders")
        self.assertEqual(res_orders.status_code, 200)
        orders = res_orders.json()
        if orders:
            first_id = orders[0]["id"]
            res_cert = self.client.get(f"/api/v1/orders/{first_id}/audit-certificate")
            self.assertEqual(res_cert.status_code, 200)
            cert = res_cert.json()
            self.assertTrue(cert["chain_valid"])
            self.assertIn("CERT-", cert["certificate_id"])
            self.assertIn("SOX-404-ITGC", cert["standard_compliance"])

    def test_circuit_breaker_trip_and_recovery(self):
        """Test Circuit Breaker state machine (CLOSED -> OPEN -> HALF_OPEN -> CLOSED)."""
        cb = CircuitBreaker("test_service", failure_threshold=2, recovery_timeout_sec=0.1)

        def failing_function():
            raise ValueError("Upstream outage")

        def successful_function():
            return "OK"

        # 1. Initially CLOSED
        self.assertEqual(cb.state, CircuitState.CLOSED)

        # 2. Trip to OPEN after 2 failures
        with self.assertRaises(ValueError):
            cb.call(failing_function)
        with self.assertRaises(ValueError):
            cb.call(failing_function)

        self.assertEqual(cb.state, CircuitState.OPEN)

        # 3. Fast-fails with CircuitBreakerOpenException
        with self.assertRaises(CircuitBreakerOpenException):
            cb.call(successful_function)

    def test_evals_execution(self):
        """Test Evals suite runs and achieves composite score."""
        report = run_evals()
        self.assertGreaterEqual(report["composite_f1_score"], 90.0)
        self.assertEqual(report["hallucination_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
