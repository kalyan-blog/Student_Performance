from flask import Blueprint, request, jsonify
from database.db import _all, _find, _insert, _update, _delete, init_db
from routes.auth import login_required
from services.ml_service import train_models, save_model, load_model
import pandas as pd
from datetime import datetime

ml_bp = Blueprint("ml", __name__, url_prefix="/api/ml")


@ml_bp.route("/train", methods=["POST"])
@login_required
def train():
    try:
        data = request.get_json()
        algorithm = data.get("algorithm")
        target_col = data.get("target", "internal_marks")
        students = _all("students")
        if not students.data or len(students.data) < 5:
            return jsonify({"error": "Need at least 5 student records to train"}), 400
        df = pd.DataFrame(students.data)
        feature_cols = ["attendance", "study_hours", "assignment_score", "internal_marks", "previous_marks", "semester", "age"]
        for col in ["gender", "department"]:
            if col in df.columns:
                df[col] = df[col].astype("category").cat.codes
                feature_cols.append(col)
        available_features = [c for c in feature_cols if c in df.columns and c != target_col]
        available_features = [c for c in available_features if c in df.columns]
        if target_col not in df.columns:
            return jsonify({"error": f"Target column '{target_col}' not found"}), 400
        X = df[available_features].fillna(0)
        y = df[target_col].fillna(0)
        results, best_model_name = train_models(X, y, algorithm)
        model_results = {}
        saved_path = None
        for name, res in results.items():
            model_results[name] = {k: v for k, v in res.items() if k != "model"}
            if name == best_model_name:
                saved_path = save_model(res["model"], f"{name.lower().replace(' ', '_')}.pkl")
                _insert("ml_models", {"model_name": f"{name}_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}", "algorithm": name, "accuracy": res["accuracy"], "precision": res["precision"], "recall": res["recall"], "f1_score": res["f1_score"], "mae": res["mae"], "rmse": res["rmse"], "r2_score": res["r2_score"], "file_path": saved_path, "is_active": True})
        return jsonify({"models": model_results, "best_model": best_model_name, "saved_path": saved_path, "features_used": available_features}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_bp.route("/models", methods=["GET"])
@login_required
def get_models():
    try:
        result = _all("ml_models", order="created_at")
        return jsonify({"models": result.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_bp.route("/models/<model_id>/activate", methods=["PUT"])
@login_required
def activate_model(model_id):
    try:
        models = _all("ml_models")
        for m in models.data:
            active = 1 if m["id"] == model_id else 0
            _update("ml_models", "id", m["id"], {"is_active": active})
        return jsonify({"message": "Model activated"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@ml_bp.route("/models/<model_id>", methods=["DELETE"])
@login_required
def delete_model(model_id):
    try:
        _delete("ml_models", "id", model_id)
        return jsonify({"message": "Model deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500