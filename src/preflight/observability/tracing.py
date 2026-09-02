from __future__ import annotations

import contextlib
import logging
import os
from typing import Any, Generator

logger = logging.getLogger(__name__)

_OTEL_INITIALIZED = False


def is_otel_enabled() -> bool:
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    return bool(endpoint)


def setup_opentelemetry(app: Any = None) -> bool:
    """Initialize OpenTelemetry tracer provider, OTLP exporter, and FastAPI auto-instrumentation if configured."""
    global _OTEL_INITIALIZED
    if not is_otel_enabled():
        return False

    if _OTEL_INITIALIZED:
        return True

    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "").strip()
    service_name = os.getenv("OTEL_SERVICE_NAME", "po-preflight")

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)

        if app is not None:
            try:
                from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
                FastAPIInstrumentor.instrument_app(app)
            except ImportError:
                logger.info("FastAPIInstrumentor not installed; continuing without FastAPI auto-instrumentation.")

        _OTEL_INITIALIZED = True
        logger.info(f"OpenTelemetry tracing initialized with endpoint '{endpoint}' for service '{service_name}'.")
        return True
    except Exception as exc:
        logger.warning(f"Failed to initialize OpenTelemetry tracing: {exc}")
        return False


@contextlib.contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None) -> Generator[Any, None, None]:
    """Create an active trace span if OpenTelemetry is initialized, or a no-op context manager."""
    if not _OTEL_INITIALIZED:
        yield None
        return

    try:
        from opentelemetry import trace
        tracer = trace.get_tracer("preflight.observability")
        with tracer.start_as_current_span(name) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(k, str(v))
            yield span
    except Exception:
        yield None
