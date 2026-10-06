from prometheus_client import CollectorRegistry, Counter, Histogram, generate_latest

REGISTRY = CollectorRegistry(auto_describe=True)

# Общее количество запросов к /predict
PREDICT_REQUESTS_TOTAL = Counter(
    'predict_requests_total',
    'Total number of prediction requests',
    registry=REGISTRY,
)

# Ошибки инференса
PREDICT_ERRORS_TOTAL = Counter(
    'predict_errors_total',
    'Total number of prediction errors',
    registry=REGISTRY,
)

# Латентность предсказаний
PREDICT_LATENCY_SECONDS = Histogram(
    'predict_latency_seconds',
    'Prediction request latency in seconds',
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
    registry=REGISTRY,
)


def metrics_exposition() -> bytes:
    return generate_latest(REGISTRY)
