from __future__ import annotations

import os
from typing import Mapping

from preflight.erp.adapters.base import BaseERPAdapter
from preflight.erp.adapters.misa_live import MisaAmisLiveAdapter
from preflight.erp.adapters.odoo import MockOdooAdapter
from preflight.erp.adapters.odoo_live import OdooLiveAdapter
from preflight.erp.adapters.sap import MockSAPAdapter
from preflight.erp.adapters.sap_live import SAPLiveAdapter
from preflight.erp.schemas import ERPAdapterType


def get_adapter(name: str | ERPAdapterType | None = None) -> BaseERPAdapter:
    """Resolve and return an ERP backend adapter instance based on configuration or explicit override."""
    if name is None:
        raw_name = os.getenv("ERP_DEFAULT_ADAPTER", "MOCK_SAP")
    elif isinstance(name, ERPAdapterType):
        raw_name = name.value
    else:
        raw_name = str(name)

    clean_name = raw_name.strip().upper()

    if clean_name in ("MOCK_SAP", "SAP", "MOCK"):
        return MockSAPAdapter()
    elif clean_name in ("MOCK_ODOO", "ODOO_MOCK"):
        return MockOdooAdapter()
    elif clean_name in ("ODOO_LIVE", "ODOO"):
        return OdooLiveAdapter()
    elif clean_name in ("SAP_LIVE", "SAP_ODATA_LIVE", "SAP_ODATA"):
        return SAPLiveAdapter()
    elif clean_name in ("MISA_AMIS_LIVE", "MISA_LIVE", "MISA"):
        return MisaAmisLiveAdapter()
    else:
        # Default fallback to MockSAPAdapter
        return MockSAPAdapter()


get_erp_adapter = get_adapter

