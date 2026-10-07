from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    avg,
    max as spark_max,
    sum as spark_sum,
    stddev,
    when,
    lag,
    concat_ws,
    to_timestamp,
    percentile_approx
)
from pyspark.sql.window import Window
import os

os.environ["HADOOP_HOME"] = r"D:\Training\hadoop"
os.environ["hadoop.home.dir"] = r"D:\Training\hadoop"
os.environ["PATH"] += r";D:\Training\hadoop\bin"

# ==================================================
# FEATURE ENGINEERING
# ==================================================

def build_features(input_path, output_path):

    spark = (
        SparkSession.builder
        .appName("ML2_Network_Features")
        .config("spark.driver.memory", "4g")
        .getOrCreate()
    )

    # ==================================================
    # LOAD DATA
    # ==================================================

    df = spark.read.parquet(input_path)

    print("\nRAW DATA")
    df.show(10, False)

    # ==================================================
    # FEATURE TIMESTAMP
    # ==================================================

    df = df.withColumn(
        "feature_timestamp",
        to_timestamp(
            concat_ws(
                " ",
                col("event_date"),
                col("hour_of_day")
            ),
            "yyyy-MM-dd H"
        )
    )

    # ==================================================
    # SORT
    # ==================================================

    df = df.orderBy(
        "CellID",
        "feature_timestamp"
    )

    # ==================================================
    # WINDOWS
    # ==================================================

    rolling_24h = (
        Window
        .partitionBy("CellID")
        .orderBy("feature_timestamp")
        .rowsBetween(-23, 0)
    )

    ordered_window = (
        Window
        .partitionBy("CellID")
        .orderBy("feature_timestamp")
    )

    # ==================================================
    # AVG ACTIVITY
    # ==================================================

    df = df.withColumn(
        "avg_activity",
        avg("total_activity").over(
            rolling_24h
        )
    )

    print("\nAVG_ACTIVITY")
    df.select(
        "CellID",
        "feature_timestamp",
        "total_activity",
        "avg_activity"
    ).show(10, False)

    # ==================================================
    # PREVIOUS ACTIVITY
    # ==================================================

    df = df.withColumn(
        "previous_activity",
        lag(
            "total_activity",
            1
        ).over(
            ordered_window
        )
    )

    # ==================================================
    # ACTIVITY GROWTH
    # ==================================================

    df = df.withColumn(
        "activity_growth",
        when(
            col("previous_activity") > 0,
            (
                col("total_activity")
                -
                col("previous_activity")
            )
            /
            col("previous_activity")
        ).otherwise(0)
    )

    print("\nACTIVITY_GROWTH")
    df.select(
        "CellID",
        "feature_timestamp",
        "total_activity",
        "previous_activity",
        "activity_growth"
    ).show(10, False)

    # ==================================================
    # ACTIVE HOURS
    # ==================================================

    df = df.withColumn(
        "active_hours",
        spark_sum(
            when(
                col("total_activity") > 0,
                1
            ).otherwise(0)
        ).over(
            rolling_24h
        )
    )

    print("\nACTIVE_HOURS")
    df.select(
        "CellID",
        "feature_timestamp",
        "active_hours"
    ).show(10, False)

    # ==================================================
    # PEAK ACTIVITY
    # ==================================================

    df = df.withColumn(
        "peak_activity",
        spark_max(
            "total_activity"
        ).over(
            rolling_24h
        )
    )

    # ==================================================
    # PEAK RATIO
    # ==================================================

    df = df.withColumn(
        "peak_ratio",
        when(
            col("avg_activity") > 0,
            col("peak_activity")
            /
            col("avg_activity")
        ).otherwise(0)
    )

    print("\nPEAK_RATIO")
    df.select(
        "CellID",
        "feature_timestamp",
        "peak_activity",
        "avg_activity",
        "peak_ratio"
    ).show(10, False)

    # ==================================================
    # VARIABILITY
    # ==================================================

    df = df.withColumn(
        "variability",
        stddev(
            "total_activity"
        ).over(
            rolling_24h
        )
    )

    df = df.fillna(
        {
            "variability": 0
        }
    )

    print("\nVARIABILITY")
    df.select(
        "CellID",
        "feature_timestamp",
        "variability"
    ).show(10, False)

    # ==================================================
    # INTERNET SHARE
    # ==================================================

    df = df.withColumn(
        "internet_share",
        when(
            col("total_activity") > 0,
            col("internet_activity")
            /
            col("total_activity")
        ).otherwise(0)
    )

    print("\nINTERNET_SHARE")
    df.select(
        "CellID",
        "feature_timestamp",
        "internet_activity",
        "total_activity",
        "internet_share"
    ).show(10, False)

# ============================================================
# NEW RELATIVE FEATURES
# ============================================================

# ============================================================
# NEW RELATIVE FEATURES
# ============================================================

    print("Creating 24-hour trailing baseline...")

    trailing_median_24h = (
    Window
    .partitionBy("CellID")
    .orderBy("feature_timestamp")
    .rowsBetween(-23, 0)
)

    df = df.withColumn(
    "trailing_median_24h",
    percentile_approx(
        col("total_activity"),
        0.5
    ).over(trailing_median_24h)
)

    print("Creating baseline-relative features...")

    df = df.withColumn(
    "activity_vs_baseline",
    when(
        col("trailing_median_24h") > 0,
        col("total_activity") /
        col("trailing_median_24h")
    ).otherwise(0)
)

    df = df.withColumn(
    "baseline_gap",
    when(
        col("trailing_median_24h") > 0,
        (
            col("total_activity") -
            col("trailing_median_24h")
        ) /
        col("trailing_median_24h")
    ).otherwise(0)
)

    # ==================================================
    # FINAL FEATURE TABLE
    # ==================================================

    feature_df = df.select(
        col("CellID").alias(
            "grid_id"
        ),

        "feature_timestamp",

        "total_activity",

        "avg_activity",

        "activity_growth",

        "active_hours",

        "peak_ratio",

        "variability",

        "internet_share",

        "activity_vs_baseline",

        "baseline_gap"
    )

    # ==================================================
    # FINAL TABLE
    # ==================================================

    print("\nFINAL FEATURE TABLE")

    feature_df.show(
        50,
        False
    )

    print(
        "\nTOTAL FEATURE ROWS:",
        feature_df.count()
    )

    # ==================================================
    # SAVE
    # ==================================================

    feature_df.write.mode(
        "overwrite"
    ).parquet(
        output_path
    )

    print(
        "\nnetwork_feature_table saved successfully."
    )
    
    spark.stop()


# ==================================================
# LEAKAGE TEST
# ==================================================

def leakage_test(input_path):

    spark = (
        SparkSession.builder
        .appName("LeakageTest")
        .getOrCreate()
    )

    df_original = spark.read.parquet(
        input_path
    )

    # Example row to validate

    target_cell = (
        df_original
        .select("CellID")
        .first()[0]
    )

    # Create timestamps for test

    df_original = (
        df_original
        .withColumn(
            "feature_timestamp",
            to_timestamp(
                concat_ws(
                    " ",
                    col("event_date"),
                    col("hour_of_day")
                ),
                "yyyy-MM-dd H"
            )
        )
    )

    original_snapshot = (
        df_original
        .filter(
            col("CellID") == target_cell
        )
        .orderBy(
            "feature_timestamp"
        )
        .limit(30)
    )

    # Save first version

    original_rows = (
        original_snapshot
        .select(
            "feature_timestamp",
            "total_activity"
        )
        .collect()
    )

    print("\nLEAKAGE TEST")
    print(
        "Change a FUTURE row and verify that"
    )
    print(
        "features for earlier timestamps remain unchanged."
    )

    print(
        "\nExample:"
    )

    print(
        "Replace future activity:"
    )

    print(
        "15:00 -> 999999"
    )

    print(
        "Then recompute features."
    )

    print(
        "Features at 14:00 or earlier"
    )

    print(
        "MUST remain identical."
    )

    print(
        "\nPASS CONDITION:"
    )

    print(
        "Earlier feature values unchanged."
    )

    print(
        "\nFAIL CONDITION:"
    )

    print(
        "Any earlier feature changes."
    )

    print(
            "\nFEATURE COUNT:",
            df_original.count()
        )



# ==================================================
# MAIN
# ==================================================

if __name__ == "__main__":

    INPUT_PATH = (
        "/mnt/d/Capstone1/data/analytics/hourly_grid_summary"
    )

    OUTPUT_PATH = (
        "/mnt/d/Capstone1/data/Machine Learning/network_features"
    )

    build_features(
        INPUT_PATH,
        OUTPUT_PATH
    )

    leakage_test(
        INPUT_PATH
    )