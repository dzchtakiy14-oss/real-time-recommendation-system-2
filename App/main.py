import time
 
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response 
from fastapi.middleware.cors import CORSMiddleware

from App.router import router_recommender
from latency import recording_latency

# ==========
# Create App
# ==========
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def measure_latency(request: Request, call_next):
    if request.url.path == "/recommender":
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        key = "latency:recommender:await"
        recording_latency(duration, key)
        return response
        
    return await call_next(request)

#================
# Endpoint Health
#================
@app.get("/health")
def health():
    return {"status": "ok"}

# ======
# Router
# ======
app.include_router(router_recommender, prefix="/api", tags=["Recommendations"])

# ==========
# Monitoring
# ==========
REQUEST_COUNT = Counter(
    "request_count", "total HTTP requests", ["method", "endpoint", "http_status"]
)

REQUEST_LATENCY = Histogram(
    "request_latency_seconds", "HTTP request latency", ["method", "endpoint"]
)

ERROR_COUNT = Counter(
    "error_count",
    "http requests resulting in errors",
    ["method", "endpoint", "http_status"],
)


# =====================
# Monitoring Middleware
# =====================
EXCLUDED_PATHS = ["/metrics", "/docs", "/openapi.json"]


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    if request.url.path in EXCLUDED_PATHS:
        return await call_next(request)

    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    # Registering Requests
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        http_status=response.status_code,
    ).inc()

    # Recording Execution Time
    REQUEST_LATENCY.labels(method=request.method, endpoint=request.url.path).observe(
        duration
    )

    # Recording Errors
    if response.status_code >= 400:
        ERROR_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            http_status=response.status_code,
        ).inc()

    return response


# ===============================
# Endpoint Metrics for Prometheus
# ===============================
@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
