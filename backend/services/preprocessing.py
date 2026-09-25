import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler, MinMaxScaler
from io import StringIO


def load_csv(file_storage):
    content = file_storage.read().decode("utf-8")
    df = pd.read_csv(StringIO(content))
    return df, content


def validate_dataset(df):
    issues = []
    missing_cols = df.columns[df.isnull().any()].tolist()
    if missing_cols:
        issues.append(f"Missing values found in columns: {', '.join(missing_cols)}")
    dup_count = df.duplicated().sum()
    if dup_count > 0:
        issues.append(f"Found {dup_count} duplicate records")
    for col in df.select_dtypes(include=["object"]).columns:
        issues.append(f"Column '{col}' has non-numeric data type")
    return issues


def preprocess_data(df, target_col=None):
    summary = {"original_shape": df.shape, "changes": []}

    df_clean = df.copy()

    dup_count = df_clean.duplicated().sum()
    if dup_count > 0:
        df_clean = df_clean.drop_duplicates()
        summary["changes"].append(f"Removed {dup_count} duplicate rows")

    for col in df_clean.columns:
        if df_clean[col].dtype in ["object"]:
            if df_clean[col].nunique() <= 10:
                le = LabelEncoder()
                df_clean[col] = le.fit_transform(df_clean[col].astype(str))
                summary["changes"].append(f"Label encoded column '{col}'")
            else:
                df_clean = pd.get_dummies(df_clean, columns=[col], drop_first=True)
                summary["changes"].append(f"One-hot encoded column '{col}'")

    numeric_cols = df_clean.select_dtypes(include=[np.number]).columns
    for col in numeric_cols:
        if df_clean[col].isnull().any():
            df_clean[col] = df_clean[col].fillna(df_clean[col].median())
            summary["changes"].append(f"Filled missing values in '{col}' with median")

    Q1 = df_clean[numeric_cols].quantile(0.25)
    Q3 = df_clean[numeric_cols].quantile(0.75)
    IQR = Q3 - Q1
    outlier_mask = ((df_clean[numeric_cols] < (Q1 - 1.5 * IQR)) | (df_clean[numeric_cols] > (Q3 + 1.5 * IQR))).any(axis=1)
    outlier_count = outlier_mask.sum()
    if outlier_count > 0:
        summary["changes"].append(f"Detected {outlier_count} outlier rows")

    summary["final_shape"] = df_clean.shape
    return df_clean, summary


def normalize_features(df, feature_cols):
    scaler = MinMaxScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])
    return df, scaler


def standardize_features(df, feature_cols):
    scaler = StandardScaler()
    df[feature_cols] = scaler.fit_transform(df[feature_cols])
    return df, scaler