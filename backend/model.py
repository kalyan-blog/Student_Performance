import pandas as pd
import numpy as np
import joblib
import os
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder


class StudentPerformanceModel:
    def __init__(self, model_path=None):
        self.model = None
        self.feature_columns = None
        self.label_encoders = {}
        if model_path and os.path.exists(model_path):
            self.load(model_path)

    def load(self, model_path):
        self.model = joblib.load(model_path)
        feat_path = model_path.replace(".pkl", "_features.pkl")
        if os.path.exists(feat_path):
            self.feature_columns = joblib.load(feat_path)
        return self

    def save(self, model_path):
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(self.model, model_path)
        if self.feature_columns:
            feat_path = model_path.replace(".pkl", "_features.pkl")
            joblib.dump(self.feature_columns, feat_path)
        return model_path

    def predict(self, features):
        if self.model is None:
            raise ValueError("Model not loaded. Train or load a model first.")
        
        if isinstance(features, dict):
            if self.feature_columns:
                feature_values = np.array([[features.get(col, 0) for col in self.feature_columns]])
            else:
                feature_values = np.array([[
                    features.get("attendance", 0),
                    features.get("study_hours", 0),
                    features.get("assignment_score", 0),
                    features.get("previous_marks", 0),
                    features.get("semester", 1),
                    features.get("age", 20),
                ]])
        else:
            feature_values = np.array([features])

        prediction = self.model.predict(feature_values)[0]
        return round(float(prediction), 2)

    @staticmethod
    def get_grade(marks):
        if marks >= 90: return "A+"
        elif marks >= 80: return "A"
        elif marks >= 70: return "B+"
        elif marks >= 60: return "B"
        elif marks >= 50: return "C"
        elif marks >= 40: return "D"
        else: return "F"

    @staticmethod
    def get_performance(marks):
        if marks >= 85: return "Excellent"
        elif marks >= 70: return "Good"
        elif marks >= 50: return "Average"
        else: return "Poor"

    @staticmethod
    def get_risk_level(marks, features):
        if isinstance(features, dict):
            if features.get("attendance", 100) < 75 or marks < 40:
                return "High"
            if features.get("study_hours", 10) < 3 or marks < 60:
                return "Medium"
        return "Low"

    @staticmethod
    def get_recommendation(marks, features):
        recs = []
        if isinstance(features, dict):
            if features.get("attendance", 100) < 75:
                recs.append("Improve attendance to above 75%")
            if features.get("study_hours", 10) < 3:
                recs.append("Increase daily study hours")
            if features.get("assignment_score", 100) < 60:
                recs.append("Focus on assignment quality")
        if marks < 40:
            recs.append("Consider remedial classes")
        elif marks < 60:
            recs.append("Regular revision needed")
        elif marks >= 85:
            recs.append("Excellent work! Consider advanced courses")
        return " | ".join(recs) if recs else "Continue current habits"