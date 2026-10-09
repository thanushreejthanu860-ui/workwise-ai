"""Prediction helpers for WorkWise AI ML models.

Loads the joblib models trained by train_model.py and exposes simple
functions used by the Flask API:

  - predict_roles(skills)         -> top 3 roles with probabilities
  - predict_wage(trade, city, exp)-> daily wage + range + verdict
  - predict_salary(role, skills, exp, city) -> expected monthly salary
  - skill_match_score(user_skills, job_skills) -> cosine similarity 0-100
  - compute_skill_gap(user_skills, job_skills) -> missing skills list

All predictions come from trained models (no hard-coded answers).
"""

import os

import joblib
import numpy as np

MODEL_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved_models")

SYNTHETIC_NOTE = (
    "Estimates are produced by models trained on SYNTHETIC demonstration "
    "data and are for guidance only, not real-world statistics."
)


def _load(name):
    """Load a joblib artifact from the saved_models directory."""
    return joblib.load(os.path.join(MODEL_DIR, name))


# ---------------------------------------------------------------------------
# Role classifier
# ---------------------------------------------------------------------------
def predict_roles(skills):
    """Return the top 3 predicted roles with probabilities for a skill list."""
    model = _load("role_classifier.joblib")
    enc = _load("role_encoder.joblib")
    mlb = enc["mlb"]
    clean = [s.strip() for s in skills if str(s).strip()]
    X = mlb.transform([clean])
    probs = model.predict_proba(X)[0]
    classes = model.classes_
    order = np.argsort(probs)[::-1][:3]
    return [
        {"role": str(classes[i]), "probability": round(float(probs[i]), 4)}
        for i in order
    ]


# ---------------------------------------------------------------------------
# Fair wage regressor
# ---------------------------------------------------------------------------
def predict_wage(trade, city_type, experience):
    """Predict a fair daily wage for an informal worker."""
    model = _load("wage_regressor.joblib")
    enc = _load("wage_encoder.joblib")
    trades, cities = enc["trades"], enc["city_types"]
    resid_std = enc["residual_std"]

    trade = str(trade).strip()
    city_type = str(city_type).strip()
    exp = max(0, int(experience))

    trade_vec = [1 if t == trade else 0 for t in trades]
    city_vec = [1 if c == city_type else 0 for c in cities]
    if sum(trade_vec) == 0 or sum(city_vec) == 0:
        raise ValueError(
            f"Unknown trade or city_type. Trades: {trades}. City types: {cities}."
        )
    X = np.array([trade_vec + city_vec + [exp]])
    pred = float(model.predict(X)[0])

    lower = max(0, pred - resid_std)
    upper = pred + resid_std
    # Verdict based on where the prediction sits within the typical range
    mid = (lower + upper) / 2
    if pred < lower + 0.25 * (upper - lower):
        verdict = "Under typical range"
    elif pred > upper - 0.25 * (upper - lower):
        verdict = "Above typical range"
    else:
        verdict = "Fair / typical"

    return {
        "predicted_daily_wage": round(pred, 2),
        "lower_range": round(lower, 2),
        "upper_range": round(upper, 2),
        "verdict": verdict,
        "note": SYNTHETIC_NOTE,
    }


# ---------------------------------------------------------------------------
# Job salary regressor
# ---------------------------------------------------------------------------
def predict_salary(role, skills, experience, city):
    """Predict an expected monthly salary for a formal role."""
    model = _load("salary_regressor.joblib")
    enc = _load("salary_encoder.joblib")
    roles, cities, skill_vocab = enc["roles"], enc["cities"], enc["skills"]

    role, city = str(role).strip(), str(city).strip()
    exp = max(0, int(experience))
    skill_set = {s.strip() for s in skills if str(s).strip()}

    if role not in roles:
        raise ValueError(f"Unknown role. Known roles: {roles}")
    if city not in cities:
        raise ValueError(f"Unknown city. Known cities: {cities}")

    row = (
        [1 if r == role else 0 for r in roles]
        + [1 if c == city else 0 for c in cities]
        + [1 if s in skill_set else 0 for s in skill_vocab]
        + [float(exp)]
    )
    pred = float(model.predict(np.array([row]))[0])
    return {
        "predicted_monthly_salary": round(pred, 2),
        "lower_range": round(pred * 0.9, 2),
        "upper_range": round(pred * 1.1, 2),
        "note": SYNTHETIC_NOTE,
    }


# ---------------------------------------------------------------------------
# Skill matching (cosine similarity)
# ---------------------------------------------------------------------------
def _multi_hot(skills, vocabulary):
    vec = np.zeros(len(vocabulary))
    for s in skills:
        s = s.strip().lower()
        if s in vocabulary:
            vec[vocabulary.index(s)] = 1.0
    return vec


def skill_match_score(user_skills, job_skills):
    """Cosine similarity between user skills and job skills, scaled to 0-100."""
    vocab = sorted({s.strip().lower() for s in list(user_skills) + list(job_skills)
                    if str(s).strip()})
    if not vocab:
        return 0.0
    a = _multi_hot(user_skills, vocab)
    b = _multi_hot(job_skills, vocab)
    norm = np.linalg.norm(a) * np.linalg.norm(b)
    if norm == 0:
        return 0.0
    return round(float(np.dot(a, b) / norm) * 100, 1)


def compute_skill_gap(user_skills, job_skills):
    """Return job skills the user does not have (case-insensitive)."""
    have = {str(s).strip().lower() for s in user_skills if str(s).strip()}
    missing = []
    for s in job_skills:
        s = str(s).strip()
        if s and s.lower() not in have:
            missing.append(s)
    return missing
