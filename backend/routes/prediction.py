from flask import Blueprint, request, jsonify
from database.db import _insert, _search, _delete, _all, _find
from routes.auth import login_required
from services.prediction_service import predict_student_performance
import json

prediction_bp = Blueprint("prediction", __name__, url_prefix="/api/predictions")


@prediction_bp.route("/predict", methods=["POST"])
@login_required
def predict():
    """
    Main prediction endpoint.
    Performs validation, inference, risk classification, factor detection,
    personalized recommendation generation, and database persistence.
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        result = predict_student_performance(data)
        if "error" in result:
            return jsonify({"error": result["error"]}), result.get("status", 400)

        p = result["prediction"]
        # Format insights array for legacy frontend consumers
        insights = []
        for factor in p.get("risk_factors", []):
            insights.append(f"{factor['title']}: {factor['description']}")

        return jsonify({
            "prediction": p,
            "insights": insights,
            "record_id": p.get("record_id"),
            "risk_factors": p.get("risk_factors", []),
            "recommendations": p.get("recommendations", [])
        }), 200

    except Exception as e:
        return jsonify({"error": f"Prediction failed: {str(e)}"}), 500


@prediction_bp.route("/history", methods=["GET"])
@prediction_bp.route("", methods=["GET"])
@login_required
def get_history():
    """
    Paginated prediction history with search, department filter,
    performance level filter, and academic risk level filter.
    """
    try:
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 20, type=int)
        search = request.args.get("search", "").strip()
        dept = request.args.get("department", "").strip()
        perf = request.args.get("performance", "").strip()
        risk = request.args.get("risk_level", "").strip()

        filters = {}
        if dept:
            filters["department"] = dept
        if perf:
            filters["performance"] = perf
        if risk:
            # Match either 'High Risk' or 'High'
            if risk.lower() in ["high", "high risk"]:
                filters["risk_level"] = "High Risk"
            elif risk.lower() in ["moderate", "medium", "moderate risk"]:
                filters["risk_level"] = "Moderate Risk"
            elif risk.lower() in ["low", "low risk"]:
                filters["risk_level"] = "Low Risk"
            else:
                filters["risk_level"] = risk

        result = _search(
            "predictions",
            search,
            ["student_name", "student_id", "department"],
            order="created_at",
            desc=True,
            page=page,
            per_page=per_page,
            filters=filters
        )

        # Parse JSON fields in returned predictions
        predictions_formatted = []
        for p in result.data:
            p_dict = dict(p)
            for json_field in ["risk_factors", "recommendations", "target_values"]:
                if p_dict.get(json_field) and isinstance(p_dict[json_field], str):
                    try:
                        p_dict[json_field] = json.loads(p_dict[json_field])
                    except Exception:
                        p_dict[json_field] = []
            predictions_formatted.append(p_dict)

        return jsonify({
            "predictions": predictions_formatted,
            "total": result.count,
            "page": page,
            "per_page": per_page,
            "total_pages": max(1, -(-result.count // per_page))
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@prediction_bp.route("/<prediction_id>", methods=["GET"])
@login_required
def get_prediction_detail(prediction_id):
    """
    Fetches complete prediction details including parsed risk factors
    and prioritized action recommendations.
    """
    try:
        res = _find("predictions", "id", prediction_id)
        if not res.data:
            return jsonify({"error": "Prediction record not found"}), 404

        record = dict(res.data[0])
        for json_field in ["risk_factors", "recommendations", "target_values"]:
            if record.get(json_field) and isinstance(record[json_field], str):
                try:
                    record[json_field] = json.loads(record[json_field])
                except Exception:
                    record[json_field] = []

        return jsonify({"prediction": record}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@prediction_bp.route("/<prediction_id>", methods=["DELETE"])
@login_required
def delete_prediction(prediction_id):
    try:
        _delete("predictions", "id", prediction_id)
        return jsonify({"message": "Prediction deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@prediction_bp.route("/export", methods=["GET"])
@login_required
def export_predictions():
    """
    Exports predictions as a clean CSV format.
    """
    try:
        result = _all("predictions", order="created_at", desc=True)
        return jsonify({"predictions": result.data}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500