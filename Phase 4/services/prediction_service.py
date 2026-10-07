import os
import joblib
import numpy as np
import pandas as pd

MODEL_PATH = r"D:\Capstone1\ml3_risk_model.pkl"

MODEL_VERSION = "Decision Tree Model-v1"

FEATURE_COLUMNS = [
    "avg_activity",
    "activity_growth",
    "active_hours",
    "peak_ratio",
    "variability",
    "internet_share",
    "activity_vs_baseline",
    "baseline_gap"
    
]

# =====================================================
# LOAD MODEL
# =====================================================

if not os.path.exists(MODEL_PATH):

    raise RuntimeError(
        f"Model artifact not found: {MODEL_PATH}"
    )

model_package = joblib.load(MODEL_PATH)
model = model_package["model"]
MODEL_VERSION = model_package["model_version"]

print(
    f"Loaded model from {MODEL_PATH}"
)

# =====================================================
# RISK LEVEL
# =====================================================

def get_risk_level(score):

    if score >= 0.80:
        return "HIGH"

    if score >= 0.50:
        return "MEDIUM"

    return "LOW"

# =====================================================
# CONTRIBUTING FEATURES
# =====================================================

def get_top_features(features):

    importances = model.feature_importances_

    values = np.array([
        features.avg_activity,
        features.activity_growth,
        features.active_hours,
        features.peak_ratio,
        features.variability,
        features.internet_share,
        features.activity_vs_baseline,
        features.baseline_gap
        
    ])

    contributions = np.abs(
        importances * values
    )

    contribution_df = pd.DataFrame({
        "feature": FEATURE_COLUMNS,
        "contribution": contributions
    })

    contribution_df = contribution_df.sort_values(
        by="contribution",
        ascending=False
    )

    return contribution_df[
        "feature"
    ].head(3).tolist()

# =====================================================
# PREDICTION
# =====================================================

def predict_risk(features):
    feature_vector = pd.DataFrame([{
        "avg_activity": features.avg_activity,
        "activity_growth": features.activity_growth,
        "active_hours": features.active_hours,
        "peak_ratio": features.peak_ratio,
        "variability": features.variability,
        "internet_share": features.internet_share,
        "activity_vs_baseline": features.activity_vs_baseline,
        "baseline_gap": features.baseline_gap
    }])

    print("\n========== PREDICTION DEBUG ==========")
    print("Grid ID:", features.grid_id)
    print("Input features:")
    print(feature_vector.to_dict(orient="records")[0])

    print("\nModel expected features:")
    print(model_package["features"])

    risk_score = float(
        model.predict_proba(
            feature_vector[model_package["features"]]
        )[0][1]
    )

    prediction = int(
        model.predict(
            feature_vector[model_package["features"]]
        )[0]
    )

    print("\nModel prediction:", prediction)
    print("Risk score:", risk_score)
    print("======================================\n")

    risk_level = get_risk_level(risk_score)

    top_features = get_top_features(features)

    explanation = (
        f"Top contributing features: "
        f"{', '.join(top_features)}. "
        f"Predicted probability of future "
        f"high activity risk is "
        f"{risk_score:.2%}."
    )

    return {
        "grid_id": features.grid_id,
        "risk_score": round(risk_score * 100, 4),
        "risk_level": risk_level,
        "model_version": MODEL_VERSION,
        "explanation_note": explanation
    }