import os
import sys
from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_session import Session
from config import Config
from database.db import init_db

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

init_db()

app = Flask(__name__, static_folder="../frontend", static_url_path="")
app.config["SECRET_KEY"] = Config.SECRET_KEY
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_USE_SIGNER"] = True
app.config["SESSION_FILE_DIR"] = os.path.join(os.path.dirname(__file__), "..", "flask_session")

os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)

frontend_env = os.getenv("FRONTEND_URL", "")
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5000",
    "http://127.0.0.1:5000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]
if frontend_env:
    for u in frontend_env.split(","):
        u = u.strip()
        if u and u not in allowed_origins:
            allowed_origins.append(u)

CORS(app, origins=allowed_origins, supports_credentials=True)
Session(app)

from routes.auth import auth_bp
from routes.students import students_bp
from routes.prediction import prediction_bp
from routes.analytics import analytics_bp
from routes.reports import reports_bp
from routes.ml import ml_bp
from routes.dataset import dataset_bp

app.register_blueprint(auth_bp)
app.register_blueprint(students_bp)
app.register_blueprint(prediction_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(reports_bp)
app.register_blueprint(ml_bp)
app.register_blueprint(dataset_bp)

# Convenient aliases matching Master Prompt endpoints
from routes.prediction import predict as do_predict, get_history as do_get_predictions
from routes.analytics import get_dashboard as do_get_dashboard

@app.route("/api/predict", methods=["POST"])
def api_predict_alias():
    return do_predict()

@app.route("/api/predictions", methods=["GET"])
def api_predictions_alias():
    return do_get_predictions()

@app.route("/api/dashboard/stats", methods=["GET"])
def api_dashboard_stats_alias():
    return do_get_dashboard()

from database.db import check_db_health
from flask import jsonify

@app.route("/api/health", methods=["GET"])
def api_health():
    health = check_db_health()
    status_code = 200 if health.get("status") == "ok" else 503
    return jsonify(health), status_code

print(f"Database initialized at backend/data/spp.db")



@app.route("/")
def serve_index():
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def serve_static(path):
    file_path = os.path.join(app.static_folder, path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return send_from_directory(app.static_folder, path)
    return send_from_directory(app.static_folder, "index.html")


@app.errorhandler(404)
def not_found(e):
    return {"error": "Not found"}, 404


@app.errorhandler(500)
def server_error(e):
    return {"error": "Internal server error"}, 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=Config.DEBUG)