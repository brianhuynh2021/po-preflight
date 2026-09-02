from __future__ import annotations

import logging
import time
from typing import Sequence

from preflight.erp.adapters.base import BaseERPAdapter
from preflight.erp.adapters.sap import MockSAPAdapter
from preflight.erp.exceptions import ERPConfigurationError
from preflight.erp.outbox import BaseOutboxStore
from preflight.erp.schemas import ERPAdapterType, ERPSyncResponse
from preflight.observability.metrics import PrometheusMetricsRegistry

logger = logging.getLogger("PreflightERPWorker")


class OutboxSyncWorker:
    """Background Dispatcher that drains the Transactional Outbox to ERP adapters."""

    def __init__(
        self,
        outbox_store: BaseOutboxStore,
        adapter: BaseERPAdapter | None = None,
        metrics_registry: PrometheusMetricsRegistry | None = None,
    ):
        self.outbox_store = outbox_store
        self.adapter = adapter or MockSAPAdapter()
        self.metrics_registry = metrics_registry

    def process_batch(self, limit: int = 10) -> list[ERPSyncResponse]:
        """Fetch pending outbox events and dispatch them to ERP."""
        pending_events = self.outbox_store.fetch_pending(limit=limit)
        responses: list[ERPSyncResponse] = []

        for event in pending_events:
            try:
                res = self.adapter.sync_order(event)
                if res.success and res.transaction_id:
                    self.outbox_store.mark_sent(
                        event_id=event.event_id,
                        tx_id=res.transaction_id,
                        adapter_type=res.adapter_type,
                    )
                    logger.info(
                        f"ERP Sync Success: PO '{event.po_number}' -> ERP TxID '{res.transaction_id}' "
                        f"via {res.adapter_type.value} [mode={res.mode}]"
                    )
                    if self.metrics_registry:
                        self.metrics_registry.record_erp_sync(res.adapter_type.value, True)
                else:
                    self.outbox_store.mark_failed(
                        event_id=event.event_id,
                        error=res.error_message or "Unknown ERP adapter error",
                    )
                    if self.metrics_registry:
                        self.metrics_registry.record_erp_sync(res.adapter_type.value, False)
                responses.append(res)
            except ERPConfigurationError as exc:
                err_msg = f"ERP Configuration Error: {exc}"
                logger.error(err_msg)
                self.outbox_store.mark_failed(event_id=event.event_id, error=err_msg)
                failed_res = ERPSyncResponse(
                    success=False,
                    transaction_id=None,
                    adapter_type=getattr(self.adapter, "adapter_type", ERPAdapterType.MOCK_SAP),
                    idempotency_key=event.idempotency_key,
                    mode="live",
                    timestamp=time.time(),
                    error_message=err_msg,
                )
                if self.metrics_registry:
                    self.metrics_registry.record_erp_sync(failed_res.adapter_type.value, False)
                responses.append(failed_res)
            except Exception as exc:
                err_msg = f"ERP Sync Exception: {exc}"
                logger.exception(err_msg)
                self.outbox_store.mark_failed(event_id=event.event_id, error=err_msg)
                failed_res = ERPSyncResponse(
                    success=False,
                    transaction_id=None,
                    adapter_type=getattr(self.adapter, "adapter_type", ERPAdapterType.MOCK_SAP),
                    idempotency_key=event.idempotency_key,
                    mode="live",
                    timestamp=time.time(),
                    error_message=err_msg,
                )
                if self.metrics_registry:
                    self.metrics_registry.record_erp_sync(failed_res.adapter_type.value, False)
                responses.append(failed_res)

        return responses
