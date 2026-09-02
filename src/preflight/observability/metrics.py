from __future__ import annotations

import os
import threading
import time
from collections import defaultdict
from typing import Any


class PrometheusMetricsRegistry:
    """Thread-safe Prometheus OpenMetrics Collector and Formatter."""

    def __init__(self):
        self._lock = threading.Lock()
        self.http_requests_total: dict[tuple[str, str, int], int] = defaultdict(int)
        self.http_durations: dict[tuple[str, str], list[float]] = defaultdict(list)
        self.orders_total: dict[tuple[str, str], int] = defaultdict(int)
        self.findings_total: dict[tuple[str, str], int] = defaultdict(int)
        self.sku_resolutions_total: dict[str, int] = defaultdict(int)
        self.erp_sync_total: dict[tuple[str, str], int] = defaultdict(int)
        self.analysis_durations: list[float] = []
        self.outbox_pending_count: int = 0
        self.outbox_pending_max_age_seconds: float = 0.0
        self.start_time = time.time()

    def record_http_request(self, method: str, path: str, status_code: int, duration_sec: float) -> None:
        """Record incoming HTTP request latency and status."""
        norm_path = path
        if norm_path.startswith("/api/v1/orders/") and norm_path.count("/") >= 4:
            parts = norm_path.split("/")
            if parts[4].isdigit():
                parts[4] = "{id}"
                norm_path = "/".join(parts)

        with self._lock:
            self.http_requests_total[(method, norm_path, status_code)] += 1
            durations = self.http_durations[(method, norm_path)]
            durations.append(duration_sec)
            if len(durations) > 500:
                durations.pop(0)

    def record_order_processed(self, status: str, risk_level: str) -> None:
        with self._lock:
            self.orders_total[(status, risk_level)] += 1

    def record_finding(self, code: str, severity: str = "warning") -> None:
        with self._lock:
            self.findings_total[(code, severity)] += 1

    def record_analysis_duration(self, duration_sec: float) -> None:
        with self._lock:
            self.analysis_durations.append(duration_sec)
            if len(self.analysis_durations) > 500:
                self.analysis_durations.pop(0)

    def record_sku_resolution(self, tier: str) -> None:
        with self._lock:
            self.sku_resolutions_total[tier] += 1

    def record_erp_sync(self, adapter: str, success: bool) -> None:
        with self._lock:
            st = "success" if success else "failure"
            self.erp_sync_total[(adapter, st)] += 1

    def record_outbox_pending(self, count: int, max_age_seconds: float) -> None:
        with self._lock:
            self.outbox_pending_count = count
            self.outbox_pending_max_age_seconds = max_age_seconds

    def generate_prometheus_text(self) -> str:
        """Render metrics in standard Prometheus text format (v0.0.4)."""
        lines = []

        # Info metric
        import preflight

        env = os.getenv("PREFLIGHT_ENV", "development").strip().lower()
        ver = getattr(preflight, "__version__", "0.1.0")
        lines.append("# HELP po_preflight_build_info Build and version metadata")
        lines.append("# TYPE po_preflight_build_info gauge")
        lines.append(f'po_preflight_build_info{{version="{ver}",environment="{env}"}} 1')

        # Uptime gauge
        uptime = time.time() - self.start_time
        lines.append("# HELP po_preflight_uptime_seconds Process uptime in seconds")
        lines.append("# TYPE po_preflight_uptime_seconds counter")
        lines.append(f"po_preflight_uptime_seconds {uptime:.2f}")

        # HTTP Requests Total
        lines.append("# HELP po_preflight_http_requests_total Total number of HTTP requests")
        lines.append("# TYPE po_preflight_http_requests_total counter")
        with self._lock:
            for (method, path, status), count in self.http_requests_total.items():
                lines.append(
                    f'po_preflight_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
                )

        # HTTP Request Latency Summary (P50, P90, P99)
        lines.append("# HELP po_preflight_http_request_duration_seconds HTTP request latency quantiles")
        lines.append("# TYPE po_preflight_http_request_duration_seconds summary")
        with self._lock:
            for (method, path), durations in self.http_durations.items():
                if not durations:
                    continue
                sorted_d = sorted(durations)
                n = len(sorted_d)
                p50 = sorted_d[int(n * 0.50)]
                p90 = sorted_d[min(int(n * 0.90), n - 1)]
                p99 = sorted_d[min(int(n * 0.99), n - 1)]
                lines.append(
                    f'po_preflight_http_request_duration_seconds{{method="{method}",path="{path}",quantile="0.5"}} {p50:.4f}'
                )
                lines.append(
                    f'po_preflight_http_request_duration_seconds{{method="{method}",path="{path}",quantile="0.9"}} {p90:.4f}'
                )
                lines.append(
                    f'po_preflight_http_request_duration_seconds{{method="{method}",path="{path}",quantile="0.99"}} {p99:.4f}'
                )

        # Orders processed
        lines.append("# HELP po_preflight_orders_processed_total Total purchase orders analyzed")
        lines.append("# TYPE po_preflight_orders_processed_total counter")
        with self._lock:
            for (status, risk), count in self.orders_total.items():
                lines.append(
                    f'po_preflight_orders_processed_total{{status="{status}",risk_level="{risk}"}} {count}'
                )

        # Findings Total
        lines.append("# HELP po_preflight_findings_total Total findings discovered by code and severity")
        lines.append("# TYPE po_preflight_findings_total counter")
        with self._lock:
            for (code, sev), count in self.findings_total.items():
                lines.append(f'po_preflight_findings_total{{code="{code}",severity="{sev}"}} {count}')

        # Analysis Latency Summary
        lines.append("# HELP po_preflight_analysis_duration_seconds Rule and analysis duration quantiles")
        lines.append("# TYPE po_preflight_analysis_duration_seconds summary")
        with self._lock:
            if self.analysis_durations:
                sorted_a = sorted(self.analysis_durations)
                na = len(sorted_a)
                p50_a = sorted_a[int(na * 0.50)]
                p90_a = sorted_a[min(int(na * 0.90), na - 1)]
                p99_a = sorted_a[min(int(na * 0.99), na - 1)]
                lines.append(f'po_preflight_analysis_duration_seconds{{quantile="0.5"}} {p50_a:.4f}')
                lines.append(f'po_preflight_analysis_duration_seconds{{quantile="0.9"}} {p90_a:.4f}')
                lines.append(f'po_preflight_analysis_duration_seconds{{quantile="0.99"}} {p99_a:.4f}')

        # Outbox pending gauges
        lines.append("# HELP po_preflight_outbox_pending_count Current pending outbox events")
        lines.append("# TYPE po_preflight_outbox_pending_count gauge")
        lines.append(f"po_preflight_outbox_pending_count {self.outbox_pending_count}")

        lines.append("# HELP po_preflight_outbox_pending_max_age_seconds Oldest pending outbox event age in seconds")
        lines.append("# TYPE po_preflight_outbox_pending_max_age_seconds gauge")
        lines.append(f"po_preflight_outbox_pending_max_age_seconds {self.outbox_pending_max_age_seconds:.2f}")

        # SKU resolutions by tier
        lines.append("# HELP po_preflight_sku_resolutions_total Total SKU resolutions by RAG tier")
        lines.append("# TYPE po_preflight_sku_resolutions_total counter")
        with self._lock:
            for tier, count in self.sku_resolutions_total.items():
                lines.append(f'po_preflight_sku_resolutions_total{{tier="{tier}"}} {count}')

        # ERP Syncs
        lines.append("# HELP po_preflight_erp_sync_total Total ERP synchronizations attempted")
        lines.append("# TYPE po_preflight_erp_sync_total counter")
        with self._lock:
            for (adapter, st), count in self.erp_sync_total.items():
                lines.append(f'po_preflight_erp_sync_total{{adapter="{adapter}",status="{st}"}} {count}')

        return "\n".join(lines) + "\n"


metrics_registry = PrometheusMetricsRegistry()
