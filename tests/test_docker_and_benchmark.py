from __future__ import annotations

import unittest
from pathlib import Path

from scripts.benchmark_50_orders import generate_50_enterprise_orders, run_benchmark


class TestDockerAndBenchmark(unittest.TestCase):
    def test_dockerfile_and_compose_configs(self):
        """Validate Dockerfile and docker-compose.yml configuration files."""
        dockerfile = Path("Dockerfile")
        self.assertTrue(dockerfile.exists())
        content = dockerfile.read_text(encoding="utf-8")
        self.assertTrue("FROM python:3.12-slim" in content or "FROM python:3.11-slim" in content)
        self.assertIn("useradd -r", content)
        self.assertIn("USER preflight", content)
        self.assertIn("HEALTHCHECK", content)

        compose = Path("docker-compose.yml")
        self.assertTrue(compose.exists())
        compose_content = compose.read_text(encoding="utf-8")
        self.assertIn("po-preflight-backend", compose_content)
        self.assertIn("8001:8001", compose_content)

        env_example = Path(".env.example")
        self.assertTrue(env_example.exists())

    def test_50_enterprise_orders_generator(self):
        """Validate generation of 50 diverse enterprise purchase orders."""
        orders = generate_50_enterprise_orders()
        self.assertEqual(len(orders), 50)

        # Verify category diversity
        categories = {o["category"] for o in orders}
        self.assertGreaterEqual(len(categories), 4)

        # Verify multi-currency presence
        currencies = {o["currency"] for o in orders}
        self.assertTrue({"VND", "USD", "EUR"}.issubset(currencies))

    def test_benchmark_execution(self):
        """Run benchmark to verify latency collection and metrics generation."""
        metrics = run_benchmark()

        self.assertEqual(metrics["total_orders"], 50)
        self.assertGreater(metrics["throughput_orders_per_sec"], 0)
        self.assertIn("p50", metrics["latency_ms"])
        self.assertIn("p95", metrics["latency_ms"])
        self.assertIn("p99", metrics["latency_ms"])
        self.assertTrue(metrics["sla_p95_compliant"])


if __name__ == "__main__":
    unittest.main()
