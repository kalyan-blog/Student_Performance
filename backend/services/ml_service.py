import pandas as pd
import numpy as np
import joblib
import os
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score,
    confusion_matrix
)
from sklearn.preprocessing import LabelEncoder


def train_models(X, y, algorithm=None):
    results = {}
    best_model = None
    best_score = float("-inf")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    algorithms = {
        "Linear Regression": LinearRegression(),
        "Decision Tree": DecisionTreeRegressor(random_state=42),
        "Random Forest": RandomForestRegressor(n_estimators=100, random_state=42),
    }

    if algorithm and algorithm in algorithms:
        algorithms = {algorithm: algorithms[algorithm]}

    for name, model in algorithms.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)

        mae = mean_absolute_error(y_test, y_pred)
        rmse = np.sqrt(mean_squared_error(y_test, y_pred))
        r2 = r2_score(y_test, y_pred)

        y_pred_class = np.round(y_pred).astype(int)
        y_test_class = np.round(y_test).astype(int)
        y_pred_class = np.clip(y_pred_class, y_test_class.min(), y_test_class.max())

        precision = 0.0
        recall = 0.0
        f1 = 0.0
        accuracy = 0.0

        try:
            n_classes = len(np.unique(y_test_class))
            if n_classes <= 2:
                accuracy = accuracy_score(y_test_class, y_pred_class)
                precision = precision_score(y_test_class, y_pred_class, average="weighted", zero_division=0)
                recall = recall_score(y_test_class, y_pred_class, average="weighted", zero_division=0)
                f1 = f1_score(y_test_class, y_pred_class, average="weighted", zero_division=0)
        except:
            pass

        results[name] = {
            "model": model,
            "accuracy": round(accuracy * 100, 2),
            "precision": round(precision * 100, 2),
            "recall": round(recall * 100, 2),
            "f1_score": round(f1 * 100, 2),
            "mae": round(mae, 2),
            "rmse": round(rmse, 2),
            "r2_score": round(r2, 2),
            "confusion_matrix": None,
        }

        if r2 > best_score:
            best_score = r2
            best_model = name

    if algorithm:
        best_model = algorithm

    return results, best_model


def save_model(model, filename="student_model.pkl"):
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    os.makedirs(models_dir, exist_ok=True)
    path = os.path.join(models_dir, filename)
    joblib.dump(model, path)
    return path


def load_model(filename="student_model.pkl"):
    models_dir = os.path.join(os.path.dirname(__file__), "..", "models")
    path = os.path.join(models_dir, filename)
    if not os.path.exists(path):
        return None
    return joblib.load(path)


def predict_performance(model, features):
    if isinstance(features, dict):
        feature_names = [
            "attendance", "study_hours", "assignment_score",
            "internal_marks", "previous_marks"
        ]
        feature_values = np.array([[features.get(f, 0) for f in feature_names]])
    else:
        feature_values = np.array([features])

    prediction = model.predict(feature_values)[0]

    predicted_marks = round(float(prediction), 2)
    grade = assign_grade(predicted_marks)
    performance = assign_performance(predicted_marks)
    risk_level = assign_risk(predicted_marks, features)
    recommendation = generate_recommendation(predicted_marks, features)

    return {
        "predicted_marks": predicted_marks,
        "grade": grade,
        "performance": performance,
        "risk_level": risk_level,
        "recommendation": recommendation,
    }


def assign_grade(marks):
    if marks >= 90:
        return "A+"
    elif marks >= 80:
        return "A"
    elif marks >= 70:
        return "B+"
    elif marks >= 60:
        return "B"
    elif marks >= 50:
        return "C"
    elif marks >= 40:
        return "D"
    else:
        return "F"


def assign_performance(marks):
    if marks >= 85:
        return "Excellent"
    elif marks >= 70:
        return "Good"
    elif marks >= 50:
        return "Average"
    else:
        return "Poor"


def assign_risk(marks, features):
    risk = "Low"
    if isinstance(features, dict):
        if features.get("attendance", 100) < 75:
            risk = "High"
        elif features.get("study_hours", 10) < 3:
            risk = "Medium"
        elif marks < 40:
            risk = "High"
        elif marks < 60:
            risk = "Medium"
    return risk


def generate_recommendation(marks, features):
    recs = []
    if isinstance(features, dict):
        if features.get("attendance", 100) < 75:
            recs.append("Increase attendance to above 75% for better performance.")
        if features.get("study_hours", 10) < 3:
            recs.append("Increase daily study hours to at least 3-4 hours.")
        if features.get("assignment_score", 100) < 60:
            recs.append("Focus on completing assignments with higher quality.")
        if features.get("internal_marks", 100) < 50:
            recs.append("Improve internal assessment performance.")

    if marks < 40:
        recs.append("Consider additional tutoring or remedial classes.")
    elif marks < 60:
        recs.append("Regular revision and practice can help improve scores.")
    elif marks >= 85:
        recs.append("Keep up the excellent work! Consider advanced courses.")

    return " ".join(recs) if recs else "Continue with current study habits."


def get_ai_insights(student_data):
    insights = []
    if student_data.get("attendance", 100) < 75:
        insights.append(
            f"Attendance is {student_data['attendance']}%. "
            f"Performance may decrease by {round((75 - student_data['attendance']) * 0.5, 1)}%."
        )
    if student_data.get("study_hours", 0) < 3:
        insights.append(
            f"Study hours ({student_data['study_hours']} hrs/day) are below recommended 3+ hours."
        )
    if student_data.get("internal_marks", 0) < student_data.get("previous_marks", 0):
        insights.append(
            "Internal marks are declining compared to previous semester. Needs attention."
        )
    return insights