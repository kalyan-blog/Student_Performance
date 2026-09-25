import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import json
import os


def train_and_save_model():
    dataset_path = os.path.join(os.path.dirname(__file__), "datasets", "student_dataset.csv")
    
    if not os.path.exists(dataset_path):
        print(f"Dataset not found at {dataset_path}, creating sample dataset...")
        from create_sample_data import create_dataset
        create_dataset()

    df = pd.read_csv(dataset_path)
    print(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns")

    feature_cols = [
        "attendance",
        "internal_marks",
        "assignment_score",
        "previous_marks",
        "study_hours"
    ]
    target_col = "final_score"

    X = df[feature_cols].copy()
    y = df[target_col].copy()

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    models_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(models_dir, exist_ok=True)

    # 1. Train Linear Regression (Current Baseline Model)
    lr_model = LinearRegression()
    lr_model.fit(X_train, y_train)
    y_pred_lr = lr_model.predict(X_test)

    lr_mae = mean_absolute_error(y_test, y_pred_lr)
    lr_rmse = np.sqrt(mean_squared_error(y_test, y_pred_lr))
    lr_r2 = r2_score(y_test, y_pred_lr)

    print("\n--- Model Evaluation: Linear Regression ---")
    print(f"  MAE:      {lr_mae:.2f}")
    print(f"  RMSE:     {lr_rmse:.2f}")
    print(f"  R² Score: {lr_r2:.4f}")

    # 2. Train Random Forest Regressor (Enhanced Ensemble Model)
    rf_model = RandomForestRegressor(n_estimators=100, max_depth=12, random_state=42)
    rf_model.fit(X_train, y_train)
    y_pred_rf = rf_model.predict(X_test)

    rf_mae = mean_absolute_error(y_test, y_pred_rf)
    rf_rmse = np.sqrt(mean_squared_error(y_test, y_pred_rf))
    rf_r2 = r2_score(y_test, y_pred_rf)

    print("\n--- Model Evaluation: Random Forest Regressor ---")
    print(f"  MAE:      {rf_mae:.2f}")
    print(f"  RMSE:     {rf_rmse:.2f}")
    print(f"  R² Score: {rf_r2:.4f}")

    # Compare models
    best_model_name = "Linear Regression" if lr_r2 >= rf_r2 else "Random Forest"
    best_model = lr_model if lr_r2 >= rf_r2 else rf_model
    print(f"\nBest Performing Model: {best_model_name}")

    # Save models
    joblib.dump(lr_model, os.path.join(models_dir, "linear_regression.pkl"))
    joblib.dump(rf_model, os.path.join(models_dir, "random_forest.pkl"))
    # Save default active model as student_model.pkl
    joblib.dump(best_model, os.path.join(models_dir, "student_model.pkl"))
    joblib.dump(feature_cols, os.path.join(models_dir, "feature_columns.pkl"))

    # Save validation metrics comparison
    metrics = {
        "features": feature_cols,
        "target": target_col,
        "sample_count": len(df),
        "best_model": best_model_name,
        "models": {
            "Linear Regression": {
                "mae": round(float(lr_mae), 2),
                "rmse": round(float(lr_rmse), 2),
                "r2_score": round(float(lr_r2), 4),
                "accuracy": round(float(max(0, lr_r2 * 100)), 2),
                "file": "linear_regression.pkl"
            },
            "Random Forest": {
                "mae": round(float(rf_mae), 2),
                "rmse": round(float(rf_rmse), 2),
                "r2_score": round(float(rf_r2), 4),
                "accuracy": round(float(max(0, rf_r2 * 100)), 2),
                "file": "random_forest.pkl"
            }
        }
    }

    metrics_path = os.path.join(models_dir, "model_metrics.json")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"\nSaved models to: {models_dir}")
    print(f"Saved metrics to: {metrics_path}")
    return metrics


if __name__ == "__main__":
    train_and_save_model()