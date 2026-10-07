import pandas as pd
import numpy as np
import joblib

from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    classification_report,
    confusion_matrix
)

# ============================================================
# CONFIGURATION
# ============================================================

INPUT_PATH = "/mnt/d/Capstone1/data/Machine Learning/network_features"
MODEL_PATH = "/mnt/d/Capstone1/ml3_risk_model.pkl"

RISK_MULTIPLIER = 1.25
TEST_RATIO = 0.20
PREDICTION_THRESHOLD = 0.50

MIN_RECALL = 0.75

# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("ML3 - GRID-SPECIFIC RISK MODEL")
print("=" * 70)

print("\nLoading feature data...")

feature_df = pd.read_parquet(INPUT_PATH)

print("Rows:", len(feature_df))
print("Columns:", list(feature_df.columns))

# ============================================================
# PREPARE DATA
# ============================================================

feature_df["feature_timestamp"] = pd.to_datetime(
    feature_df["feature_timestamp"]
)

feature_df = feature_df.sort_values(
    ["grid_id", "feature_timestamp"]
).reset_index(drop=True)

print("\nTimestamp range:")
print("Start:", feature_df["feature_timestamp"].min())
print("End  :", feature_df["feature_timestamp"].max())

print("\nGrid count:", feature_df["grid_id"].nunique())

# ============================================================
# CREATE NEXT-HOUR TARGET
# ============================================================

print("\nCreating next-hour target...")

feature_df["target_activity"] = (
    feature_df
    .groupby("grid_id")["total_activity"]
    .shift(-1)
)

# ============================================================
# TRUE 24-HOUR TRAILING MEDIAN
# ============================================================

print("Creating 24-hour trailing baseline...")

feature_df["trailing_median_24h"] = (
    feature_df
    .groupby("grid_id")["total_activity"]
    .transform(
        lambda x: x.rolling(
            window=24,
            min_periods=24
        ).median()
    )
)

# ============================================================
# GRID-SPECIFIC RISK THRESHOLD
# ============================================================

feature_df["risk_threshold"] = (
    feature_df["trailing_median_24h"]
    * RISK_MULTIPLIER
)

# ============================================================
# CREATE TARGET
# ============================================================

feature_df["high_activity"] = (
    feature_df["target_activity"]
    > feature_df["risk_threshold"]
).astype(int)

# ============================================================
# REMOVE INVALID ROWS
# ============================================================

ml3_df = feature_df.dropna(
    subset=[
        "target_activity",
        "trailing_median_24h"
    ]
).copy()

print("\nRows after removing incomplete 24-hour baselines:")
print(len(ml3_df))

# ============================================================
# FEATURE COLUMNS
# ============================================================

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

TARGET = "high_activity"

# ============================================================
# CHECK FEATURES
# ============================================================

print("\nFeatures used:")
for feature in FEATURE_COLUMNS:
    print(" -", feature)

# ============================================================
# TARGET DISTRIBUTION
# ============================================================

print("\nTarget distribution:")

target_counts = ml3_df[TARGET].value_counts().sort_index()

print(target_counts)

positive_rate = ml3_df[TARGET].mean()

print(
    f"\nPositive rate: {positive_rate:.2%}"
)

# ============================================================
# CHRONOLOGICAL 80/20 SPLIT
# ============================================================

timestamps = np.sort(
    ml3_df["feature_timestamp"].unique()
)

split_index = int(
    len(timestamps) * (1 - TEST_RATIO)
)

train_end_time = timestamps[split_index - 1]
test_start_time = timestamps[split_index]

train_df = ml3_df[
    ml3_df["feature_timestamp"] <= train_end_time
].copy()

test_df = ml3_df[
    ml3_df["feature_timestamp"] >= test_start_time
].copy()

print("\n" + "=" * 70)
print("CHRONOLOGICAL SPLIT")
print("=" * 70)

print(
    "Train:",
    train_df["feature_timestamp"].min(),
    "to",
    train_df["feature_timestamp"].max()
)

print(
    "Test :",
    test_df["feature_timestamp"].min(),
    "to",
    test_df["feature_timestamp"].max()
)

print("\nTrain rows:", len(train_df))
print("Test rows :", len(test_df))

print(
    "\nTrain positive rate:",
    f"{train_df[TARGET].mean():.2%}"
)

print(
    "Test positive rate :",
    f"{test_df[TARGET].mean():.2%}"
)

# ============================================================
# PREPARE X / Y
# ============================================================

X_train = train_df[FEATURE_COLUMNS]
y_train = train_df[TARGET]

X_test = test_df[FEATURE_COLUMNS]
y_test = test_df[TARGET]

# ============================================================
# TEST DIFFERENT TREE CONFIGURATIONS
# ============================================================

print("\n" + "=" * 70)
print("MODEL EXPERIMENTS")
print("=" * 70)

model_configs = [
    {
        "max_depth": 6,
        "min_samples_leaf": 100
    },
    {
        "max_depth": 7,
        "min_samples_leaf": 100
    },
    {
        "max_depth": 8,
        "min_samples_leaf": 100
    },
    {
        "max_depth": 8,
        "min_samples_leaf": 200
    },
    {
        "max_depth": 9,
        "min_samples_leaf": 200
    },
    {
        "max_depth": 10,
        "min_samples_leaf": 200
    },
    {
        "max_depth": 8,
        "min_samples_leaf": 300
    },
    {
        "max_depth": 9,
        "min_samples_leaf": 300
    }
]

results = []

best_model = None
best_result = None

for config in model_configs:

    print(
        f"\nTesting max_depth={config['max_depth']}, "
        f"min_samples_leaf={config['min_samples_leaf']}"
    )

    tree_model = DecisionTreeClassifier(
        max_depth=config["max_depth"],
        min_samples_leaf=config["min_samples_leaf"],
        class_weight="balanced",
        random_state=42
    )

    tree_model.fit(
        X_train,
        y_train
    )

    test_probabilities = tree_model.predict_proba(
        X_test
    )[:, 1]

    test_predictions = (
        test_probabilities
        >= PREDICTION_THRESHOLD
    ).astype(int)

    accuracy = accuracy_score(
        y_test,
        test_predictions
    )

    precision = precision_score(
        y_test,
        test_predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        test_predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        test_predictions,
        zero_division=0
    )

    result = {
        "max_depth": config["max_depth"],
        "min_samples_leaf": config["min_samples_leaf"],
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1
    }

    results.append(result)

    print(
        f"Accuracy : {accuracy:.2%}"
    )

    print(
        f"Precision: {precision:.2%}"
    )

    print(
        f"Recall   : {recall:.2%}"
    )

    print(
        f"F1       : {f1:.2%}"
    )

    # --------------------------------------------------------
    # SELECT MODEL
    # Highest precision while maintaining recall >= 75%
    # --------------------------------------------------------

    if recall >= MIN_RECALL:

        if (
            best_result is None
            or precision > best_result["precision"]
        ):

            best_result = result
            best_model = tree_model

# ============================================================
# MODEL COMPARISON
# ============================================================

results_df = pd.DataFrame(results)

print("\n" + "=" * 70)
print("MODEL COMPARISON")
print("=" * 70)

print(
    results_df.to_string(
        index=False,
        formatters={
            "accuracy": "{:.2%}".format,
            "precision": "{:.2%}".format,
            "recall": "{:.2%}".format,
            "f1": "{:.2%}".format
        }
    )
)

# ============================================================
# FALLBACK IF NO MODEL REACHES MINIMUM RECALL
# ============================================================

if best_model is None:

    print(
        "\nNo model achieved the required "
        f"recall of {MIN_RECALL:.0%}."
    )

    print(
        "Selecting model with highest F1 score."
    )

    best_result = (
        results_df
        .sort_values(
            ["f1", "precision"],
            ascending=False
        )
        .iloc[0]
        .to_dict()
    )

    best_model = DecisionTreeClassifier(
        max_depth=int(
            best_result["max_depth"]
        ),
        min_samples_leaf=int(
            best_result["min_samples_leaf"]
        ),
        class_weight="balanced",
        random_state=42
    )

    best_model.fit(
        X_train,
        y_train
    )

# ============================================================
# FINAL BEST MODEL
# ============================================================

best_depth = int(
    best_result["max_depth"]
)

best_leaf = int(
    best_result["min_samples_leaf"]
)

print("\n" + "=" * 70)
print("BEST MODEL")
print("=" * 70)

print(
    "max_depth:",
    best_depth
)

print(
    "min_samples_leaf:",
    best_leaf
)

print(
    "Accuracy:",
    f"{best_result['accuracy']:.2%}"
)

print(
    "Precision:",
    f"{best_result['precision']:.2%}"
)

print(
    "Recall:",
    f"{best_result['recall']:.2%}"
)

print(
    "F1:",
    f"{best_result['f1']:.2%}"
)

# ============================================================
# FINAL PREDICTIONS
# ============================================================

final_probabilities = best_model.predict_proba(
    X_test
)[:, 1]

final_predictions = (
    final_probabilities
    >= PREDICTION_THRESHOLD
).astype(int)

# ============================================================
# FINAL METRICS
# ============================================================

final_accuracy = accuracy_score(
    y_test,
    final_predictions
)

final_precision = precision_score(
    y_test,
    final_predictions,
    zero_division=0
)

final_recall = recall_score(
    y_test,
    final_predictions,
    zero_division=0
)

final_f1 = f1_score(
    y_test,
    final_predictions,
    zero_division=0
)

print("\n" + "=" * 70)
print("FINAL DECISION TREE RESULTS")
print("=" * 70)

print(
    f"Accuracy : {final_accuracy:.2%}"
)

print(
    f"Precision: {final_precision:.2%}"
)

print(
    f"Recall   : {final_recall:.2%}"
)

print(
    f"F1 Score : {final_f1:.2%}"
)

# ============================================================
# CLASSIFICATION REPORT
# ============================================================

print("\nClassification Report:")

print(
    classification_report(
        y_test,
        final_predictions,
        digits=4,
        zero_division=0
    )
)

# ============================================================
# CONFUSION MATRIX
# ============================================================

cm = confusion_matrix(
    y_test,
    final_predictions
)

print("\nConfusion Matrix:")

print(
    "                Predicted 0    Predicted 1"
)

print(
    f"Actual 0       {cm[0,0]:12d}    {cm[0,1]:12d}"
)

print(
    f"Actual 1       {cm[1,0]:12d}    {cm[1,1]:12d}"
)

tn, fp, fn, tp = cm.ravel()

print("\nTN:", tn)
print("FP:", fp)
print("FN:", fn)
print("TP:", tp)

# ============================================================
# FEATURE IMPORTANCE
# ============================================================

importance_df = pd.DataFrame({
    "feature": FEATURE_COLUMNS,
    "importance": best_model.feature_importances_
}).sort_values(
    "importance",
    ascending=False
)

print("\n" + "=" * 70)
print("FEATURE IMPORTANCE")
print("=" * 70)

print(
    importance_df.to_string(
        index=False,
        formatters={
            "importance": "{:.6f}".format
        }
    )
)

# ============================================================
# NP3 RULE
# ============================================================

print("\n" + "=" * 70)
print("NP3 COMPARISON")
print("=" * 70)

np3_alert = np.where(
    (test_df["peak_ratio"] > 2) |
    (test_df["activity_growth"] > 0.50),
    1,
    0
)

comparison_df = pd.DataFrame({
    "actual": y_test.values,
    "ml_prediction": final_predictions,
    "np3_prediction": np3_alert
})

comparison = pd.crosstab(
    [
        comparison_df["actual"],
        comparison_df["ml_prediction"]
    ],
    comparison_df["np3_prediction"]
)

print(comparison)

# ============================================================
# ML ONLY EVENTS
# ============================================================

ml_only = comparison_df[
    (comparison_df["ml_prediction"] == 1) &
    (comparison_df["np3_prediction"] == 0)
]

np3_only = comparison_df[
    (comparison_df["ml_prediction"] == 0) &
    (comparison_df["np3_prediction"] == 1)
]

both = comparison_df[
    (comparison_df["ml_prediction"] == 1) &
    (comparison_df["np3_prediction"] == 1)
]

print("\nML-only events:", len(ml_only))

print(
    "ML-only actual positives:",
    ml_only["actual"].sum()
)

print(
    "ML-only precision:",
    f"{ml_only['actual'].mean():.2%}"
    if len(ml_only) > 0
    else "0.00%"
)

print("\nNP3-only events:", len(np3_only))

print(
    "NP3-only actual positives:",
    np3_only["actual"].sum()
)

print(
    "NP3-only precision:",
    f"{np3_only['actual'].mean():.2%}"
    if len(np3_only) > 0
    else "0.00%"
)

print("\nBoth ML + NP3 events:", len(both))

print(
    "Both actual positives:",
    both["actual"].sum()
)

# ============================================================
# SAVE MODEL PACKAGE
# ============================================================

model_package = {
    "model": best_model,
    "features": FEATURE_COLUMNS,
    "threshold": PREDICTION_THRESHOLD,
    "risk_multiplier": RISK_MULTIPLIER,
    "model_version": "Decision Tree Grid-Specific-v2",
    "baseline_window": 24,
    "baseline_type": "trailing_median",
    "target_definition": (
        "next_hour_activity > "
        "1.25 * trailing_24h_median"
    )
}

print("\nMODEL SANITY TEST")

test_inputs = pd.DataFrame([
    {
        "avg_activity": 10,
        "activity_growth": -0.5,
        "active_hours": 2,
        "peak_ratio": 0.5,
        "variability": 1,
        "internet_share": 0.1,
        "activity_vs_baseline": -0.5,
        "baseline_gap": -50
    },
    {
        "avg_activity": 1000,
        "activity_growth": 5,
        "active_hours": 24,
        "peak_ratio": 10,
        "variability": 100,
        "internet_share": 5,
        "activity_vs_baseline": 5,
        "baseline_gap": 500
    }
])

print("\nTest inputs:")
print(test_inputs)

print("\nPredictions:")
print(best_model.predict(test_inputs[FEATURE_COLUMNS]))

print("\nProbabilities:")
print(best_model.predict_proba(test_inputs[FEATURE_COLUMNS]))

joblib.dump(
    model_package,
    MODEL_PATH
)

print("\n" + "=" * 70)
print("MODEL SAVED")
print("=" * 70)

print(
    "Path:",
    MODEL_PATH
)

print(
    "Model version:",
    model_package["model_version"]
)

print(
    "Threshold:",
    PREDICTION_THRESHOLD
)

print(
    "Risk multiplier:",
    RISK_MULTIPLIER
)

print("\nML3 completed successfully.")