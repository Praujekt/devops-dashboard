from flask import Flask, jsonify, send_from_directory
import psutil
import subprocess
import os
import requests
from prometheus_client import Counter, Gauge, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)

# Prometheus metrics
api_requests = Counter("api_requests_total", "Total API requests", ["endpoint", "method"])
cpu_usage = Gauge("system_cpu_percent", "CPU usage percentage")
memory_usage = Gauge("system_memory_percent", "Memory usage percentage")
disk_usage = Gauge("system_disk_percent", "Disk usage percentage")
k8s_pod_count = Gauge("kubernetes_pods_total", "Total Kubernetes pods")


@app.route("/")
def index():
    web_dir = os.path.join(os.path.dirname(__file__), "..", "web")
    return send_from_directory(web_dir, "index.html")


@app.route("/api")
def api_info():
    return jsonify({"status": "healthy", "message": "DevOps Dashboard API"})


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/metrics")
def metrics():
    # Update gauges
    cpu_usage.set(psutil.cpu_percent(interval=1))
    memory_usage.set(psutil.virtual_memory().percent)
    disk_usage.set(psutil.disk_usage("/").percent)
    k8s_pod_count.set(get_pod_count())

    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}


# Rename the old metrics endpoint
@app.route("/api/metrics")
def get_metrics():
    return jsonify(
        {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
            "kubernetes_pods": get_pod_count(),
        }
    )


@app.route("/k8s/pods")
def get_pod_details():
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "default", "-o", "json"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            import json

            data = json.loads(result.stdout)

            pods = []
            for item in data.get("items", []):
                pod_info = {
                    "name": item["metadata"]["name"],
                    "status": item["status"]["phase"],
                    "ready": sum(1 for c in item["status"].get("containerStatuses", []) if c.get("ready", False)),
                    "total_containers": len(item["spec"]["containers"]),
                    "restarts": sum(c.get("restartCount", 0) for c in item["status"].get("containerStatuses", [])),
                    "age": item["metadata"]["creationTimestamp"],
                }
                pods.append(pod_info)

            return jsonify({"pods": pods})
        return jsonify({"error": "Failed to get pods"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def get_pod_count():
    try:
        result = subprocess.run(
            ["kubectl", "get", "pods", "-n", "default", "--no-headers"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            return len([line for line in lines if line])
        return 0
    except Exception as e:
        print(f"Error getting pod count: {e}")
        return 0


@app.route("/environment")
def get_environment():
    return jsonify(
        {
            "environment": os.environ.get("ENVIRONMENT", "unknown"),
            "version": os.environ.get("APP_VERSION", "v4"),
        }
    )


@app.route("/f1/next-race")
def next_f1_race():
    try:
        response = requests.get("https://api.openf1.org/v1/sessions?session_name=Race&year=2026", timeout=5)
        response.raise_for_status()
        data = response.json()

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        for session in data:
            session_date = datetime.fromisoformat(session["date_start"])
            if session_date > now:
                return jsonify(
                    {
                        "location": session["location"],
                        "country": session["country_name"],
                        "date": session["date_start"],
                        "circuit": session["circuit_short_name"],
                        "session_type": session["session_type"],
                    }
                )

        return jsonify({"message": "No upcoming race found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/f1/latest-race")
def latest_race():
    try:
        response = requests.get("https://api.openf1.org/v1/sessions?session_name=Race&year=2026", timeout=5)
        response.raise_for_status()
        data = response.json()

        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)

        # Find most recent race in the past
        past_races = []
        for session in data:
            session_date = datetime.fromisoformat(session["date_start"])
            if session_date < now:
                past_races.append(session)

        if past_races:
            latest = past_races[-1]  # Last one in the list
            return jsonify(
                {
                    "location": latest["location"],
                    "country": latest["country_name"],
                    "date": latest["date_start"],
                    "circuit": latest["circuit_short_name"],
                }
            )

        return jsonify({"message": "No past races found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/f1/driver-standings")
def driver_standings():
    try:
        # First get the most recent race session
        response = requests.get("https://api.openf1.org/v1/sessions?session_name=Race&year=2026", timeout=5)
        response.raise_for_status()
        sessions = response.json()

        if not sessions:
            return jsonify({"error": "No race sessions found"}), 404

        # Get the most recent session_key
        latest_session = sessions[-1]
        session_key = latest_session["session_key"]

        # Get championship standings for that session
        standings_response = requests.get(
            f"https://api.openf1.org/v1/championship_drivers?session_key={session_key}",
            timeout=5,
        )
        standings_response.raise_for_status()
        standings_data = standings_response.json()

        standings = []
        for driver in standings_data:
            standings.append(
                {
                    "position": driver["position"],
                    "driver_number": driver["driver_number"],
                    "points": driver["points"],
                }
            )

        # Sort by position
        standings.sort(key=lambda x: int(x["position"]))

        return jsonify({"standings": standings, "session_key": session_key})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
