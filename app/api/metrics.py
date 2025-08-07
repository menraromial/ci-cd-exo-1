"""
Metrics endpoint for Prometheus monitoring
"""
import time
import psutil
from flask import Blueprint, Response
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

# Create Blueprint
metrics_bp = Blueprint("metrics", __name__)

# Prometheus metrics
REQUEST_COUNT = Counter("flask_requests_total", "Total number of requests", ["method", "endpoint", "status"])

REQUEST_DURATION = Histogram("flask_request_duration_seconds", "Request duration in seconds", ["method", "endpoint"])

# System metrics
CPU_USAGE = Gauge("system_cpu_usage_percent", "Current CPU usage percentage")
MEMORY_USAGE = Gauge("system_memory_usage_percent", "Current memory usage percentage")
MEMORY_AVAILABLE = Gauge("system_memory_available_bytes", "Available memory in bytes")
DISK_USAGE = Gauge("system_disk_usage_percent", "Current disk usage percentage")

# Application metrics
APP_INFO = Gauge("flask_app_info", "Application information", ["version", "python_version"])
ACTIVE_CONNECTIONS = Gauge("flask_active_connections", "Number of active connections")


def update_system_metrics():
    """Update system metrics"""
    try:
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        CPU_USAGE.set(cpu_percent)

        # Memory usage
        memory = psutil.virtual_memory()
        MEMORY_USAGE.set(memory.percent)
        MEMORY_AVAILABLE.set(memory.available)

        # Disk usage
        disk = psutil.disk_usage("/")
        disk_percent = (disk.used / disk.total) * 100
        DISK_USAGE.set(disk_percent)

    except Exception as e:
        print(f"Error updating system metrics: {e}")


@metrics_bp.route("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    # Update system metrics before serving
    update_system_metrics()

    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


def init_metrics(app):
    """Initialize metrics with app info"""
    import sys

    APP_INFO.labels(
        version=app.config.get("VERSION", "1.0.0"),
        python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
    ).set(1)


def record_request_metrics(response, request_start_time, endpoint, method):
    """Record request metrics"""
    try:
        # Record request count
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, status=response.status_code).inc()

        # Record request duration
        request_duration = time.time() - request_start_time
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(request_duration)

    except Exception as e:
        print(f"Error recording request metrics: {e}")
