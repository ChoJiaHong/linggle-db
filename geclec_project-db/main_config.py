import os

origins = ["*"]

mongodbIp = os.environ.get("MONGODB_HOST", "mongodb")
mongodbPort = int(os.environ.get("MONGODB_PORT", "27017"))
mongodbDb = os.environ.get("MONGODB_DB", "local")
mongodbCollection = os.environ.get("MONGODB_COLLECTION", "grammar")
mongodbUsername = os.environ.get("MONGODB_USERNAME", "")
mongodbPassword = os.environ.get("MONGODB_PASSWORD", "")

redisHost = os.environ.get("REDIS_CACHE_HOST", "redis-cache")
redisPort = int(os.environ.get("REDIS_CACHE_PORT", "6379"))
redisDb = int(os.environ.get("REDIS_CACHE_DB", "0"))
redisPassword = os.environ.get("REDIS_PASSWORD", "")
cacheTtlSeconds = int(os.environ.get("REDIS_CACHE_TTL_SECONDS", "600"))

# Distributed tracing：span 直接用 OTLP gRPC 送給 Tempo，見 tracing_config.py
otelExporterOtlpEndpoint = os.environ.get(
    "OTEL_EXPORTER_OTLP_ENDPOINT", "http://tempo.observability.svc.cluster.local:4317"
)
