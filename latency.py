import redis
import time

# =============
# Prepare Redis
# =============
pool = redis.ConnectionPool(host="localhost", port=6379, db=0, decode_responses=True)
r = redis.Redis(connection_pool=pool)


def recording_latency(duration, key):
    r.lpush(key, duration)
    r.ltrim(key, 0, 500)


def compute_latency():
    # Recommendations
    rec_key = "latency:recommender:await"
    latencies = [float(l) for l in r.lrange(rec_key, 0, -1) if l]

    n = len(latencies) - 1
    latencies = sorted(latencies)
    rec_p50 = latencies[int(0.5 * n)] if latencies else 0
    rec_p95 = latencies[int(0.95 * n)] if latencies else 0
    rec_p99 = latencies[int(0.99 * n)] if latencies else 0

    # Saving Interactions
    int_key = "latency:recommender:function"
    latencies = [float(l) for l in r.lrange(int_key, 0, -1) if l]
    n = len(latencies) - 1
    latencies = sorted(latencies)
    int_p50 = latencies[int(0.5 * n)] if latencies else 0
    int_p95 = latencies[int(0.95 * n)] if latencies else 0
    int_p99 = latencies[int(0.99 * n)] if latencies else 0

    return rec_p50, rec_p95, rec_p99, int_p50, int_p95, int_p99
