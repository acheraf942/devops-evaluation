import os
import time

import redis
from flask import Flask, jsonify, request
from prometheus_client import Counter, Gauge, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Nombre total de requetes HTTP",
    ["method", "endpoint", "code"],
)

REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "Duree de traitement des requetes HTTP",
    ["method", "endpoint"],
)

VERSION = os.environ.get("APP_VERSION", "dev")
APP_VERSION = Gauge(
    "app_version_info",
    "Version (SHA du commit) actuellement deployee",
    ["version"],
)
APP_VERSION.labels(version=VERSION).set(1)


def get_redis_client():
    return redis.Redis(
        host=os.environ.get("REDIS_HOST", "localhost"),
        port=int(os.environ.get("REDIS_PORT", 6379)),
        decode_responses=True,
    )


@app.route("/health")
def health():
    return jsonify(status="error"), 503


@app.route("/status")
def status():
    return jsonify(service="devops-evaluation", version=VERSION), 200


@app.route("/visits")
def visits():
    count = get_redis_client().incr("visits")
    return jsonify(visits=count), 200


@app.route("/simulate-error")
def simulate_error():
    return jsonify(status="error"), 500


@app.before_request
def start_timer():
    request.start_time = time.time()


@app.after_request
def record_metrics(response):
    if request.path != "/metrics":
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            code=response.status_code,
        ).inc()
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.path,
        ).observe(time.time() - request.start_time)
    return response


@app.route("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


if __name__ == "__main__":
    app.run(host="0.0.0.0")
