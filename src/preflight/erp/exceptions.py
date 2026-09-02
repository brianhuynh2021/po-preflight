from __future__ import annotations


class ERPConfigurationError(Exception):
    """Raised when ERP adapter credentials or configurations are missing in production."""
    pass


class ERPConnectionError(Exception):
    """Raised when communication with upstream ERP endpoint fails."""
    pass
