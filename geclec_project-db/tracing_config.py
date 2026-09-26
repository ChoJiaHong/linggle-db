"""共用的 OpenTelemetry tracing 設定，main.py 呼叫 `configure_tracing()`，
把 span 用 OTLP gRPC 直接送給 Tempo（見 main_config.otelExporterOtlpEndpoint），
不經過額外的 OpenTelemetry Collector。dictionary-service 沒有 Celery 這類
跨 process 的訊息傳遞，只有進來的 HTTP 請求，context propagation 完全靠
FastAPIInstrumentor 自動處理（標準 W3C traceparent header），不需要額外的
instrumentation 套件。
"""
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

import main_config


def configure_tracing(service_name):
    provider = TracerProvider(resource=Resource.create({"service.name": service_name}))
    exporter = OTLPSpanExporter(endpoint=main_config.otelExporterOtlpEndpoint, insecure=True)
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
