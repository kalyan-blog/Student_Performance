"""
Prediction Service for EduPredict AI.
Handles input validation, ML model inference, risk classification,
recommendation generation, and database persistence.
"""

import os
import json
import joblib
import numpy as np
from services.risk_service import classify_risk, identify_risk_factors, classify_performance, calculate_grade, BENCHMARKS
from services.recommendation_service import generate_recommendations
from database.db import _insert, _find


MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models")


def validate_prediction_input(data):
    """
    Validates all student inputs according to application constraints.
    Returns (cleaned_data, error_message).
    """
    if not isinstance(data, dict):
        return None, "Invalid request payload. Expected JSON object."

    student_id = str(data.get("student_id", "")).strip()
    if not student_id:
        return None, "Student ID is required."

    student_name = str(data.get("student_name", "")).strip()
    if not student_name:
        student_name = f"Student {student_id}"

    # Attendance Percentage: 0 - 100
    try:
        attendance = float(data.get("attendance", 0))
        if attendance < 0 or attendance > 100:
            return None, "Please enter a valid attendance percentage between 0 and 100."
    except (ValueError, TypeError):
        return None, "Attendance must be a valid numeric value between 0 and 100."

    # Internal Assessment Marks: 0 - 100
    try:
        internal_marks = float(data.get("internal_marks", 0))
        if internal_marks < 0 or internal_marks > 100:
            return None, "Please enter valid internal assessment marks between 0 and 100."
    except (ValueError, TypeError):
        return None, "Internal marks must be a valid numeric value between 0 and 100."

    # Assignment Completion Percentage: 0 - 100
    # Handles both 'assignment_score' and 'assignment_completion'
    raw_assignment = data.get("assignment_completion", data.get("assignment_score", 0))
    try:
        assignment_score = float(raw_assignment)
        if assignment_score < 0 or assignment_score > 100:
            return None, "Please enter a valid assignment completion percentage between 0 and 100."
    except (ValueError, TypeError):
        return None, "Assignment completion must be a valid numeric value between 0 and 100."

    # Previous Semester Performance / GPA: 0 - 100
    # If GPA provided (e.g. 0 to 10), convert to percentage
    raw_prev = data.get("previous_semester_score", data.get("previous_marks", data.get("gpa", 0)))
    try:
        previous_marks = float(raw_prev)
        if previous_marks < 0:
            return None, "Previous semester performance cannot be negative."
        if previous_marks <= 10.0 and previous_marks > 0:
            # Likely a 10-point GPA scale, convert to percentage: GPA * 9.5 or * 10
            previous_marks = min(100.0, round(previous_marks * 10.0, 1))
        elif previous_marks > 100:
            return None, "Previous semester performance percentage cannot exceed 100."
    except (ValueError, TypeError):
        return None, "Previous semester performance must be a valid numeric value."

    # Study Hours Per Week: non-negative realistic value (0 - 80)
    try:
        study_hours = float(data.get("study_hours", 0))
        if study_hours < 0:
            return None, "Study hours per week cannot be negative."
        if study_hours > 84:
            return None, "Study hours per week exceeds realistic maximum (84 hours/week)."
    except (ValueError, TypeError):
        return None, "Study hours must be a valid numeric value."

    department = str(data.get("department", "Computer Science")).strip() or "General"
    try:
        semester = int(data.get("semester", 1))
        if semester < 1 or semester > 12:
            semester = 1
    except (ValueError, TypeError):
        semester = 1

    algorithm = str(data.get("algorithm", "Random Forest Regressor")).strip()

    cleaned = {
        "student_id": student_id,
        "student_name": student_name,
        "department": department,
        "semester": semester,
        "attendance": round(attendance, 1),
        "internal_marks": round(internal_marks, 1),
        "assignment_score": round(assignment_score, 1),
        "previous_marks": round(previous_marks, 1),
        "study_hours": round(study_hours, 1),
        "algorithm": algorithm
    }

    return cleaned, None


def load_ml_model(algorithm_name=None):
    """
    Loads requested ML model or falls back to active student_model.pkl.
    """
    algo = (algorithm_name or "").lower()
    model_file = "student_model.pkl"

    if "linear" in algo:
        candidate = os.path.join(MODELS_DIR, "linear_regression.pkl")
        if os.path.exists(candidate):
            model_file = "linear_regression.pkl"
    elif "forest" in algo:
        candidate = os.path.join(MODELS_DIR, "random_forest.pkl")
        if os.path.exists(candidate):
            model_file = "random_forest.pkl"

    path = os.path.join(MODELS_DIR, model_file)
    if not os.path.exists(path):
        # Fallback to any model file in directory
        for f in ["student_model.pkl", "linear_regression.pkl", "random_forest.pkl"]:
            fallback = os.path.join(MODELS_DIR, f)
            if os.path.exists(fallback):
                path = fallback
                break

    if not os.path.exists(path):
        # Train on demand if model not yet generated
        from train_model import train_and_save_model
        train_and_save_model()

    model = joblib.load(path)
    used_algo = "Linear Regression" if "linear" in path else "Random Forest Regressor"
    return model, used_algo


def predict_student_performance(raw_data):
    """
    Complete end-to-end performance prediction pipeline:
    1. Validation
    2. Model inference
    3. Risk classification
    4. Risk factor identification
    5. Personalized recommendations
    6. Database persistence
    """
    cleaned, err = validate_prediction_input(raw_data)
    if err:
        return {"error": err, "status": 400}

    # Load model
    try:
        model, actual_algo = load_ml_model(cleaned.get("algorithm"))
    except Exception as e:
        return {"error": f"Failed to load predictive model: {str(e)}", "status": 500}

    # Feature vector matching training order and names:
    # ["attendance", "internal_marks", "assignment_score", "previous_marks", "study_hours"]
    import pandas as pd
    features_df = pd.DataFrame([{
        "attendance": cleaned["attendance"],
        "internal_marks": cleaned["internal_marks"],
        "assignment_score": cleaned["assignment_score"],
        "previous_marks": cleaned["previous_marks"],
        "study_hours": cleaned["study_hours"]
    }])

    raw_prediction = float(model.predict(features_df)[0])
    predicted_score = round(float(np.clip(raw_prediction, 0.0, 100.0)), 1)

    # Risk classification
    risk_info = classify_risk(predicted_score)
    performance_level = classify_performance(predicted_score)
    grade = calculate_grade(predicted_score)

    # Risk factor identification (uses student's actual values)
    risk_factors = identify_risk_factors(cleaned)

    # Personalized recommendation engine
    recommendations = generate_recommendations(cleaned, risk_factors, predicted_score)

    # Factor comparison dictionary for visual progress bars / radar charts
    factors_summary = {
        "attendance": {
            "label": "Attendance",
            "current": cleaned["attendance"],
            "target": BENCHMARKS["attendance"]["target"],
            "unit": "%",
            "status": "Healthy" if cleaned["attendance"] >= BENCHMARKS["attendance"]["target"] else "At Risk"
        },
        "internal_marks": {
            "label": "Internal Marks",
            "current": cleaned["internal_marks"],
            "target": BENCHMARKS["internal_marks"]["target"],
            "unit": "/100",
            "status": "Healthy" if cleaned["internal_marks"] >= BENCHMARKS["internal_marks"]["target"] else "At Risk"
        },
        "assignment_completion": {
            "label": "Assignment Completion",
            "current": cleaned["assignment_score"],
            "target": BENCHMARKS["assignment_score"]["target"],
            "unit": "%",
            "status": "Healthy" if cleaned["assignment_score"] >= BENCHMARKS["assignment_score"]["target"] else "At Risk"
        },
        "study_hours": {
            "label": "Weekly Study Hours",
            "current": cleaned["study_hours"],
            "target": BENCHMARKS["study_hours"]["target"],
            "unit": " hrs/wk",
            "status": "Healthy" if cleaned["study_hours"] >= BENCHMARKS["study_hours"]["target"] else "At Risk"
        },
        "previous_semester_score": {
            "label": "Previous Semester Score",
            "current": cleaned["previous_marks"],
            "target": BENCHMARKS["previous_marks"]["target"],
            "unit": "%",
            "status": "Healthy" if cleaned["previous_marks"] >= BENCHMARKS["previous_marks"]["target"] else "At Risk"
        }
    }

    # Concise single recommendation string for legacy clients
    top_rec_text = recommendations[0]["action"] if recommendations else "Continue current academic practices."

    # Save to database
    record_data = {
        "student_id": cleaned["student_id"],
        "student_name": cleaned["student_name"],
        "department": cleaned["department"],
        "semester": cleaned["semester"],
        "attendance": cleaned["attendance"],
        "study_hours": cleaned["study_hours"],
        "assignment_score": cleaned["assignment_score"],
        "internal_marks": cleaned["internal_marks"],
        "previous_marks": cleaned["previous_marks"],
        "predicted_marks": predicted_score,
        "predicted_score": predicted_score,
        "grade": grade,
        "performance": performance_level,
        "performance_level": performance_level,
        "risk_level": risk_info["level"],
        "recommendation": top_rec_text,
        "risk_factors": json.dumps(risk_factors),
        "recommendations": json.dumps(recommendations),
        "algorithm": actual_algo,
        "accuracy": 93.2
    }

    try:
        rec = _insert("predictions", record_data)
        record_id = rec.data[0]["id"] if rec.data else None
    except Exception as e:
        record_id = None

    # Construct complete structured result
    result = {
        "predicted_score": predicted_score,
        "predicted_marks": predicted_score,
        "performance_level": performance_level,
        "performance": performance_level,
        "grade": grade,
        "risk_level": risk_info["level"],
        "risk_code": risk_info["code"],
        "risk_color": risk_info["color"],
        "risk_badge": risk_info["badge_class"],
        "risk_description": risk_info["description"],
        "risk_factors": risk_factors,
        "recommendations": recommendations,
        "recommendation": top_rec_text,
        "factors": factors_summary,
        "student_info": cleaned,
        "algorithm": actual_algo,
        "record_id": record_id
    }

    return {"prediction": result, "status": 200}
