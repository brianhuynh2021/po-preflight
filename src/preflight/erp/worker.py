from __future__ import annotations

import logging
from typing import Sequence

from preflight.erp.adapters.base import BaseERPAdapter
from preflight.erp.adapters.sap import MockSAPAdapter
from preflight.erp.outbox import OutboxStore
from preflight.erp.schemas import ERPSyncResponse

logger = logging.getLogger("PreflightERPWorker")


class OutboxSyncWorker:
    """Background Dispatcher that drains the Transactional Outbox to ERP adapters."""

    def __init__(
        self,
        outbox_store: OutboxStore,
        adapter: BaseERPAdapter | None = None,
    ):
        self.outbox_store = outbox_store
        self.adapter = adapter or MockSAPAdapter()

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
                        f"via {res.adapter_type.value}"
                    )
                else:
                    self.outbox_store.mark_failed(
                        event_id=event.event_id,
                        error=res.error_message or "Unknown ERP adapter error",
                    )
                responses.append(res)
            except Exception as exc:
                err_msg = f"ERP Sync Exception: {exc}"
                logger.error(err_msg)
                self.outbox_store.mark_failed(event_id=event.event_id, error=err_msg)

        return responses
