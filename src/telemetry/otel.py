# src/telemetry/otel.py
from __future__ import annotations
import os, platform, psutil
from typing import Any, Dict

from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader, ConsoleMetricExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter as OTLPGrpcMetricExporter
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter as OTLPHttpMetricExporter

def init_metrics(cfg: Dict[str, Any]) -> dict:
    ocfg = cfg.get("otel", {})
    if not ocfg.get("enabled", True):
        return {}

    service_name = ocfg.get("service_name", "cs6913-crawler")
    interval_s = float(ocfg.get("metrics_interval_s", 10))
    exporter_kind = (ocfg.get("exporter", "console") or "console").lower()

    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "service.instance.id": os.getenv("HOSTNAME", "local"),
        "os.description": platform.platform(),
        "process.pid": os.getpid(),
    })

    # Choose exporter
    if exporter_kind == "console":
        exporter = ConsoleMetricExporter()
    else:
        endpoint = ocfg.get("otlp_endpoint", "http://localhost:4317")
        use_http = bool(ocfg.get("use_http", False))
        exporter = (
            OTLPHttpMetricExporter(endpoint=endpoint, timeout=10)
            if use_http else
            OTLPGrpcMetricExporter(endpoint=endpoint, timeout=10, insecure=True)
        )

    reader = PeriodicExportingMetricReader(exporter, export_interval_millis=int(interval_s * 1000))
    provider = MeterProvider(resource=resource, metric_readers=[reader])
    set_meter_provider(provider)
    meter = provider.get_meter("crawler.metrics")

    # Instruments
    pages_total = meter.create_counter("crawler.pages_total", unit="{page}", description="All fetch attempts")
    pages_ok = meter.create_counter("crawler.pages_ok", unit="{page}", description="Fetch OK with content")
    pages_err = meter.create_counter("crawler.pages_err", unit="{page}", description="Fetch failed or empty")
    fetch_latency = meter.create_histogram("crawler.fetch_latency_ms", unit="ms", description="Fetch latency per request")

    # Observable gauges for CPU/memory (per-process)
    proc = psutil.Process(os.getpid())

    def cpu_cb(_):
        return [("value", proc.cpu_percent(interval=None))]
    def mem_cb(_):
        return [("value", proc.memory_info().rss / 1e6)]  # MB

    meter.create_observable_gauge("crawler.process_cpu_percent", callbacks=[cpu_cb], unit="percent",
                                  description="Process CPU usage percent")
    meter.create_observable_gauge("crawler.process_memory_mb", callbacks=[mem_cb], unit="MB",
                                  description="Resident set size (MB)")

    return {
        "pages_total": pages_total,
        "pages_ok": pages_ok,
        "pages_err": pages_err,
        "fetch_latency": fetch_latency,
    }
