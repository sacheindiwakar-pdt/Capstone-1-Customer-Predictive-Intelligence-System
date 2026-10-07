import os
import joblib
import pandas as pd

# =====================================================
# CONFIG
# =====================================================

FEATURE_PATH = r"/mnt/d/Capstone1/data/Machine Learning/network_features"

MODEL_PATH = r"/mnt/d/Capstone1/ml3_risk_model.pkl"

OUTPUT_PATH = r"/mnt/d/Capstone1/Phase 6/network_risk_scores.csv"

TOP20_PATH = r"/mnt/d/Capstone1/Phase 6/top20_risk_report.csv"

# =====================================================
# CHECK MODEL
# =====================================================

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(
        f"Model file not found: {MODEL_PATH}"
    )

# =====================================================
# LOAD MODEL PACKAGE
# =====================================================

print("\nLoading ML3 model package...")

model_package = joblib.load(
    MODEL_PATH
)

# Current ML3 model is stored inside dictionary
model = model_package["model"]

MODEL_VERSION = model_package.get(
    "model_version",
    "Unknown"
)

MODEL_FEATURES = model_package.get(
    "features"
)

print("Model loaded successfully")
print("Model Version:", MODEL_VERSION)
print("Model Features:", MODEL_FEATURES)

# =====================================================
# LOAD FEATURES
# =====================================================

print("\nLoading network features...")

df = pd.read_parquet(
    FEATURE_PATH
)

df["feature_timestamp"] = pd.to_datetime(
    df["feature_timestamp"]
)

print(
    f"Feature Rows: {len(df):,}"
)

# =====================================================
# MODEL FEATURES
# =====================================================

feature_columns = [
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
# VERIFY MODEL FEATURES
# =====================================================

if MODEL_FEATURES != feature_columns:

    print(
        "\nWARNING: Model feature list differs from expected features."
    )

    print(
        "Model expects:",
        MODEL_FEATURES
    )

    print(
        "Code provides:",
        feature_columns
    )

# =====================================================
# CHECK REQUIRED COLUMNS
# =====================================================

missing_columns = [
    column
    for column in feature_columns
    if column not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing feature columns: {missing_columns}"
    )

# =====================================================
# PREPARE INPUT
# =====================================================

X = df[
    feature_columns
].copy()

X = X.fillna(0)

# =====================================================
# SCORE
# =====================================================

print("\nGenerating risk predictions...")

risk_scores = model.predict_proba(
    X
)[:, 1]

df["risk_score"] = risk_scores

# =====================================================
# RISK LEVEL
# =====================================================

def determine_risk_level(score):

    if score >= 0.80:
        return "HIGH"

    elif score >= 0.50:
        return "MEDIUM"

    return "LOW"


df["risk_level"] = (
    df["risk_score"]
    .apply(determine_risk_level)
)

df["model_version"] = (
    MODEL_VERSION
)

# =====================================================
# NETWORK RISK SCORES
# =====================================================

network_risk_scores = df[
    [
        "grid_id",
        "feature_timestamp",
        "risk_score",
        "risk_level",
        "model_version"
    ]
].copy()

network_risk_scores.rename(
    columns={
        "feature_timestamp":
        "score_timestamp"
    },
    inplace=True
)

# =====================================================
# SAVE RISK SCORES
# =====================================================

network_risk_scores.to_csv(
    OUTPUT_PATH,
    index=False
)

print(
    f"\nCreated: {OUTPUT_PATH}"
)

# =====================================================
# SUMMARY
# =====================================================

print("\nRISK LEVEL DISTRIBUTION")

print(
    network_risk_scores[
        "risk_level"
    ].value_counts()
)

# =====================================================
# TOP 20 OPERATIONAL ATTENTION REPORT
# =====================================================

top20 = (
    network_risk_scores
    .sort_values(
        by="risk_score",
        ascending=False
    )
    .head(20)
)

top20.to_csv(
    TOP20_PATH,
    index=False
)

print(
    f"\nCreated: {TOP20_PATH}"
)

print("\nTOP 20 HIGH-RISK RECORDS")

print(
    top20[
        [
            "grid_id",
            "score_timestamp",
            "risk_score",
            "risk_level"
        ]
    ]
)

# =====================================================
# BASIC METRICS
# =====================================================

print("\nSUMMARY")

print(
    f"Total Records: "
    f"{len(network_risk_scores):,}"
)

print(
    f"Average Risk Score: "
    f"{network_risk_scores['risk_score'].mean():.4f}"
)

print(
    f"Maximum Risk Score: "
    f"{network_risk_scores['risk_score'].max():.4f}"
)

print(
    f"Minimum Risk Score: "
    f"{network_risk_scores['risk_score'].min():.4f}"
)

print(
    "\nML6 COMPLETE"
)

# =====================================================
# OPTIONAL MYSQL LOAD
# =====================================================

# from sqlalchemy import create_engine

# engine = create_engine(
#     "mysql+pymysql://root:root@localhost:3306/telecom_warehouse_copy"
# )

# network_risk_scores.to_sql(
#     "network_risk_scores",
#     con=engine,
#     if_exists="replace",
#     index=False,
#     chunksize=5000
# )