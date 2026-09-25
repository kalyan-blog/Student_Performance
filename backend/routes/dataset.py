from flask import Blueprint, request, jsonify, session
from database.db import _insert, _all
from routes.auth import login_required
from services.preprocessing import load_csv, validate_dataset, preprocess_data
import pandas as pd
import json

dataset_bp = Blueprint("dataset", __name__, url_prefix="/api/dataset")


@dataset_bp.route("/upload", methods=["POST"])
@login_required
def upload_dataset():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file provided"}), 400
        file = request.files["file"]
        if not file.filename.endswith(".csv"):
            return jsonify({"error": "Only CSV files are supported"}), 400
        df, content = load_csv(file)
        issues = validate_dataset(df)
        rec = _insert("datasets", {"file_name": file.filename, "rows": len(df), "columns": len(df.columns), "uploaded_by": session.get("user_id", "")})
        df_clean, summary = preprocess_data(df)
        return jsonify({"message": "Dataset uploaded successfully", "rows": len(df), "columns": len(df.columns), "issues": issues, "preprocessing_summary": summary, "dataset_id": rec.data[0]["id"] if rec.data else None, "columns": list(df.columns), "sample": json.loads(df.head(10).to_json(orient="records"))}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dataset_bp.route("/list", methods=["GET"])
@login_required
def get_datasets():
    try:
        result = _all("datasets", order="uploaded_at")
        return jsonify({"datasets": result.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@dataset_bp.route("/preprocess", methods=["POST"])
@login_required
def preprocess():
    try:
        data = request.get_json()
        file_content = data.get("content", "")
        if not file_content:
            return jsonify({"error": "No data provided"}), 400
        from io import StringIO
        df = pd.read_csv(StringIO(file_content))
        df_clean, summary = preprocess_data(df)
        return jsonify({"summary": summary, "columns": list(df_clean.columns), "sample": json.loads(df_clean.head(10).to_json(orient="records"))}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500