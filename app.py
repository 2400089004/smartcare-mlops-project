import os
from flask import Flask, jsonify, request, render_template
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from ml.inference import load_heart_model, predict_heart_risk
from ml.measurement_checks import check_measurements
from ml.storage import init_db, save_measurement, list_measurements

REQUEST_COUNT = Counter("smartcare_http_requests_total", "HTTP requests", ["method", "endpoint", "status"])
REQUEST_LATENCY = Histogram("smartcare_http_request_duration_seconds", "HTTP request latency", ["endpoint"])
SCREENINGS = Counter("smartcare_measurement_checks_total", "Measurement checks submitted")
app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
init_db()

@app.before_request
def start_timer():
    request._smartcare_timer = REQUEST_LATENCY.labels(request.endpoint or "unknown").time()
    request._smartcare_timer.__enter__()

@app.after_request
def observe_request(response):
    if hasattr(request, "_smartcare_timer"):
        request._smartcare_timer.__exit__(None, None, None)
    REQUEST_COUNT.labels(request.method, request.endpoint or "unknown", str(response.status_code)).inc()
    return response

@app.get("/")
def dashboard():
    return render_template("index.html")

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/ready")
def ready():
    return jsonify({"status": "ready", "heart_model_available": load_heart_model() is not None})

@app.get("/metrics")
def metrics():
    return generate_latest(), 200, {"Content-Type": CONTENT_TYPE_LATEST}

@app.get("/api/v1/measurements")
def get_measurements():
    try:
        limit = min(max(int(request.args.get("limit", 50)), 1), 200)
    except ValueError:
        return jsonify({"error": "limit must be an integer"}), 400
    return jsonify({"items": list_measurements(limit)})

@app.post("/api/v1/measurements/check")
def measurements_check():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Expected a JSON object"}), 400
    try:
        flags = check_measurements(payload)
        saved = save_measurement(payload, flags)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    SCREENINGS.inc()
    return jsonify({
        "id": saved["id"], "created_at": saved["created_at"],
        "measurements": payload, "flags": flags,
        "notice": "Educational screening only; not a diagnosis or substitute for clinical assessment."
    }), 201

@app.post("/api/v1/models/heart-risk")
def heart_risk():
    if not request.is_json:
        return jsonify({"error": "Content-Type must be application/json"}), 415
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        return jsonify({"error": "Expected a JSON object"}), 400
    try:
        result = predict_heart_risk(payload)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    except FileNotFoundError:
        return jsonify({"error": "Heart model is not trained yet"}), 503
    return jsonify({"type": "educational_model_estimate", "result": result,
                    "notice": "Research prototype only; not a diagnosis."})

@app.errorhandler(500)
def server_error(_error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "3000")), debug=False)
