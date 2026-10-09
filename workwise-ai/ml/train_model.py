"""ML training pipeline for WorkWise AI.

Trains and saves three models into ml/saved_models/:
  1. Job Role Classifier (RandomForest / DecisionTree / LogisticRegression)
  2. Fair Wage Regressor (RandomForestRegressor / GradientBoostingRegressor)
  3. Job Salary Regressor (RandomForestRegressor)

Evaluation reports (JSON, PNG, CSV) are written to ml/reports/.

Usage:
    python ml/train_model.py
"""

import json
import os
import sys

import joblib
import matplotlib

matplotlib.use("Agg")  # non-interactive backend, safe for servers
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.ensemble import (GradientBoostingRegressor,
                              RandomForestClassifier,
                              RandomForestRegressor)
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, classification_report,
                             confusion_matrix, mean_absolute_error,
                             mean_squared_error, r2_score)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import LabelBinarizer, MultiLabelBinarizer
from sklearn.tree import DecisionTreeClassifier

# Make `import predict` work when this file is run as a script
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(ROOT, "data")
MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_models")
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "reports")

SYNTHETIC_WARNING = (
    "WARNING: Using SYNTHETIC training data. Results are for demonstration "
    "only and are not real-world salary or employment statistics."
)


def ensure_dirs():
    """Create model and report directories if they do not exist."""
    os.makedirs(MODEL_DIR, exist_ok=True)
    os.makedirs(REPORT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Job Role Classifier
# ---------------------------------------------------------------------------
def train_role_classifier():
    """Train a multi-class role classifier on multi-hot encoded skills."""
    print("\n=== Training Job Role Classifier ===")
    df = pd.read_csv(os.path.join(DATA_DIR, "job_skills_training.csv"))
    df["skill_list"] = df["skills"].apply(lambda s: [x.strip() for x in str(s).split(";") if x.strip()])

    # Multi-hot encoding of the skill vocabulary
    mlb = MultiLabelBinarizer()
    X = mlb.fit_transform(df["skill_list"])
    skill_names = list(mlb.classes_)

    y = df["role"].values
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train and cross-validate three different algorithms
    candidates = {
        "RandomForest": RandomForestClassifier(n_estimators=200, random_state=42),
        "DecisionTree": DecisionTreeClassifier(random_state=42, max_depth=12),
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=42),
    }
    cv_results = {}
    for name, model in candidates.items():
        scores = cross_val_score(model, X_train, y_train, cv=5, scoring="accuracy")
        cv_results[name] = round(float(scores.mean()), 4)
        print(f"  {name}: 5-fold CV accuracy = {cv_results[name]:.4f}")

    best_name = max(cv_results, key=cv_results.get)
    best_model = candidates[best_name]
    best_model.fit(X_train, y_train)

    y_pred = best_model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)

    # Confusion matrix plot
    labels = sorted(np.unique(np.concatenate([y_test, y_pred])))
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    plt.figure(figsize=(9, 7))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=labels, yticklabels=labels)
    plt.title(f"Role Classifier Confusion Matrix ({best_name}) - SYNTHETIC DATA")
    plt.xlabel("Predicted")
    plt.ylabel("Actual")
    plt.tight_layout()
    cm_path = os.path.join(REPORT_DIR, "role_confusion_matrix.png")
    plt.savefig(cm_path, dpi=110)
    plt.close()

    # Feature importance report (tree models have feature_importances_)
    if hasattr(best_model, "feature_importances_"):
        importance = best_model.feature_importances_
    else:  # LogisticRegression: use absolute coefficient magnitude
        importance = np.abs(best_model.coef_).mean(axis=0)
    fi_df = pd.DataFrame({
        "skill": skill_names,
        "importance": importance,
    }).sort_values("importance", ascending=False)
    fi_path = os.path.join(REPORT_DIR, "role_feature_importance.csv")
    fi_df.to_csv(fi_path, index=False)

    metrics = {
        "model": best_name,
        "cross_validation_accuracy": cv_results,
        "test_accuracy": round(float(acc), 4),
        "weighted_precision": round(float(report["weighted avg"]["precision"]), 4),
        "weighted_recall": round(float(report["weighted avg"]["recall"]), 4),
        "weighted_f1": round(float(report["weighted avg"]["f1-score"]), 4),
        "per_class": {
            cls: {
                "precision": round(float(report[cls]["precision"]), 4),
                "recall": round(float(report[cls]["recall"]), 4),
                "f1-score": round(float(report[cls]["f1-score"]), 4),
                "support": int(report[cls]["support"]),
            }
            for cls in report if cls not in ("accuracy", "macro avg", "weighted avg")
        },
        "synthetic_data": True,
        "classes": sorted(list(mlb.classes_)),
        "roles": sorted(np.unique(y)),
    }
    with open(os.path.join(REPORT_DIR, "role_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    joblib.dump(best_model, os.path.join(MODEL_DIR, "role_classifier.joblib"))
    joblib.dump({"skills": skill_names, "mlb": mlb, "model_name": best_name},
                os.path.join(MODEL_DIR, "role_encoder.joblib"))
    print(f"  Best model: {best_name} | Test accuracy: {acc:.4f}")
    print(f"  Saved model + encoder and reports (confusion matrix, feature importance).")
    return metrics


# ---------------------------------------------------------------------------
# 2. Fair Wage Regressor (informal workers)
# ---------------------------------------------------------------------------
def train_wage_regressor():
    """Train a daily-wage regressor for informal Indian workers."""
    print("\n=== Training Fair Wage Regressor ===")
    df = pd.read_csv(os.path.join(DATA_DIR, "wages.csv"))

    trades = sorted(df["trade"].unique())
    cities = sorted(df["city_type"].unique())

    # One-hot encode trade and city type; keep numeric experience
    X = np.column_stack([
        (df["trade"].values[:, None] == np.array(trades)[None, :]).astype(int),
        (df["city_type"].values[:, None] == np.array(cities)[None, :]).astype(int),
        df["experience"].values.reshape(-1, 1),
    ])
    y = df["daily_wage"].values.astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    candidates = {
        "RandomForestRegressor": RandomForestRegressor(n_estimators=300, random_state=42),
        "GradientBoostingRegressor": GradientBoostingRegressor(n_estimators=300, random_state=42),
    }
    cv_results = {}
    for name, model in candidates.items():
        neg_mse = cross_val_score(model, X_train, y_train, cv=5,
                                  scoring="neg_mean_squared_error")
        cv_results[name] = round(float(np.sqrt(-neg_mse.mean())), 2)
        print(f"  {name}: 5-fold CV RMSE = {cv_results[name]:.2f}")

    best_name = min(cv_results, key=cv_results.get)
    best_model = candidates[best_name]
    best_model.fit(X_train, y_train)

    pred = best_model.predict(X_test)
    residuals = y_test - pred
    resid_std = float(residuals.std())

    metrics = {
        "model": best_name,
        "cross_validation_rmse": cv_results,
        "mae": round(float(mean_absolute_error(y_test, pred)), 2),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, pred))), 2),
        "r2": round(float(r2_score(y_test, pred)), 4),
        "residual_std": round(resid_std, 2),
        "synthetic_data": True,
        "trades": trades,
        "city_types": cities,
    }
    with open(os.path.join(REPORT_DIR, "wage_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    joblib.dump(best_model, os.path.join(MODEL_DIR, "wage_regressor.joblib"))
    joblib.dump({"trades": trades, "city_types": cities,
                 "model_name": best_name, "residual_std": resid_std},
                os.path.join(MODEL_DIR, "wage_encoder.joblib"))
    print(f"  Best model: {best_name} | MAE={metrics['mae']} RMSE={metrics['rmse']} R2={metrics['r2']}")
    return metrics


# ---------------------------------------------------------------------------
# 3. Job Salary Regressor (formal roles)
# ---------------------------------------------------------------------------
def train_salary_regressor():
    """Train a monthly-salary regressor for formal roles."""
    print("\n=== Training Job Salary Regressor ===")
    df = pd.read_csv(os.path.join(DATA_DIR, "salaries.csv"))

    roles = sorted(df["role"].unique())
    cities = sorted(df["city"].unique())
    all_skills = sorted({s.strip() for row in df["skills"] for s in str(row).split(";") if s.strip()})

    role_oh = (df["role"].values[:, None] == np.array(roles)[None, :]).astype(int)
    city_oh = (df["city"].values[:, None] == np.array(cities)[None, :]).astype(int)

    # Multi-hot skills
    skill_matrix = np.zeros((len(df), len(all_skills)), dtype=int)
    for i, row in enumerate(df["skills"]):
        for s in str(row).split(";"):
            s = s.strip()
            if s in all_skills:
                skill_matrix[i, all_skills.index(s)] = 1

    X = np.column_stack([role_oh, city_oh, skill_matrix,
                         df["experience"].values.reshape(-1, 1).astype(float)])
    y = df["salary"].values.astype(float)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    model = RandomForestRegressor(n_estimators=300, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    metrics = {
        "model": "RandomForestRegressor",
        "mae": round(float(mean_absolute_error(y_test, pred)), 2),
        "rmse": round(float(np.sqrt(mean_squared_error(y_test, pred))), 2),
        "r2": round(float(r2_score(y_test, pred)), 4),
        "synthetic_data": True,
        "roles": roles,
        "cities": cities,
        "skills": all_skills,
    }
    with open(os.path.join(REPORT_DIR, "salary_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    joblib.dump(model, os.path.join(MODEL_DIR, "salary_regressor.joblib"))
    joblib.dump({"roles": roles, "cities": cities, "skills": all_skills,
                 "model_name": "RandomForestRegressor"},
                os.path.join(MODEL_DIR, "salary_encoder.joblib"))
    print(f"  MAE={metrics['mae']} RMSE={metrics['rmse']} R2={metrics['r2']}")
    return metrics


def main():
    print(SYNTHETIC_WARNING)
    ensure_dirs()
    role_metrics = train_role_classifier()
    wage_metrics = train_wage_regressor()
    salary_metrics = train_salary_regressor()

    summary = {"role_classifier": role_metrics, "wage_regressor": wage_metrics,
               "salary_regressor": salary_metrics, "synthetic_data": True}
    with open(os.path.join(REPORT_DIR, "training_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print("\nAll models trained and saved to", MODEL_DIR)
    print("Reports saved to", REPORT_DIR)


if __name__ == "__main__":
    main()
