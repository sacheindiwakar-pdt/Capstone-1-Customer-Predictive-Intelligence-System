# ============================================================
# PHASE 2 - SP6
# Data Publishing And Storage Optimization
# ============================================================

import os
import shutil

# ============================================================
# HADOOP CONFIGURATION
# ============================================================

os.environ["HADOOP_HOME"] = r"D:\Training\hadoop"
os.environ["hadoop.home.dir"] = r"D:\Training\hadoop"
os.environ["PATH"] += r";D:\Training\hadoop\bin"

import sys

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

print("Python Executable:", sys.executable)

# ============================================================
# IMPORTS
# ============================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# ============================================================
# SPARK SESSION
# ============================================================

spark = (
    SparkSession.builder
    .appName("SP6_Data_Publishing")
    .config("spark.driver.memory", "4g")
    .config("spark.executor.memory", "4g")
    .getOrCreate()
)

# ============================================================
# INPUT DATA
# ============================================================

clean_df = spark.read.parquet(
    "D:/Capstone1/parquet_output/clean_parquet"
)

print("\n========== INPUT DATA ==========")

print(
    "Clean Data Rows:",
    clean_df.count()
)

# ============================================================
# OUTPUT PATHS
# ============================================================

processed_activity_path = (
    "D:/Capstone1/data/processed/activity"
)

hourly_summary_path = (
    "D:/Capstone1/data/analytics/hourly_grid_summary"
)

dashboard_csv_path = (
    "D:/Capstone1/data/dashboard/dashboard_summary.csv"
)

# ============================================================
# ACTIVITY 1
# WRITE CLEAN DATA AS PARQUET
# ============================================================

print("\n========== WRITING ACTIVITY DATA ==========")

(
    clean_df
    .write
    .mode("overwrite")
    .partitionBy("date")
    .parquet(processed_activity_path)
)

print(
    "Processed activity parquet created."
)

# ============================================================
# ACTIVITY 2 & 3
# CREATE HOURLY GRID SUMMARY
# ============================================================

hourly_grid_summary = (
    clean_df
    .groupBy(
        "timestamp",
        "grid_id"
    )
    .agg(
        F.sum("sms_in").alias("sms_in"),
        F.sum("sms_out").alias("sms_out"),
        F.sum("call_in").alias("call_in"),
        F.sum("call_out").alias("call_out"),
        F.sum("internet_activity")
            .alias("internet_activity"),
        F.sum("total_activity")
            .alias("total_activity")
    )
)

print("\n========== WRITING HOURLY GRID SUMMARY ==========")

(
    hourly_grid_summary
    .write
    .mode("overwrite")
    .parquet(hourly_summary_path)
)

print(
    "Hourly grid summary parquet created."
)

# ============================================================
# ACTIVITY 4
# DASHBOARD SUMMARY CSV
# ============================================================

print("\n========== CREATING DASHBOARD SUMMARY ==========")

total_records = clean_df.count()

distinct_grids = (
    clean_df
    .select("grid_id")
    .distinct()
    .count()
)

peak_hour = (
    clean_df
    .groupBy("hour")
    .agg(
        F.sum("total_activity")
        .alias("activity")
    )
    .orderBy(
        F.desc("activity")
    )
    .first()
)

top_grid = (
    clean_df
    .groupBy("grid_id")
    .agg(
        F.sum("total_activity")
        .alias("activity")
    )
    .orderBy(
        F.desc("activity")
    )
    .first()
)

dashboard_df = spark.createDataFrame(
    [
        (
            total_records,
            distinct_grids,
            peak_hour["hour"],
            float(peak_hour["activity"]),
            top_grid["grid_id"],
            float(top_grid["activity"])
        )
    ],
    [
        "total_records",
        "distinct_grids",
        "peak_hour",
        "peak_hour_activity",
        "top_grid_id",
        "top_grid_activity"
    ]
)

(
    dashboard_df
    .coalesce(1)
    .write
    .mode("overwrite")
    .option("header", True)
    .csv(dashboard_csv_path)
)

print(
    "Dashboard summary CSV created."
)

# ============================================================
# ACTIVITY 5
# READ DATA BACK AND VALIDATE
# ============================================================

print("\n========== VALIDATION ==========")

activity_validation_df = (
    spark.read.parquet(
        processed_activity_path
    )
)

hourly_validation_df = (
    spark.read.parquet(
        hourly_summary_path
    )
)

print("\nActivity Dataset Count")

print(
    "Original:",
    clean_df.count()
)

print(
    "Read Back:",
    activity_validation_df.count()
)

print("\nHourly Grid Summary Count")

print(
    hourly_validation_df.count()
)

print("\nActivity Schema")

activity_validation_df.printSchema()

print("\nHourly Summary Schema")

hourly_validation_df.printSchema()

# ============================================================
# ACTIVITY 6
# FILE SIZE COMPARISON
# ============================================================

print("\n========== FILE SIZE COMPARISON ==========")

def folder_size_mb(folder_path):

    total_size = 0

    for dirpath, dirnames, filenames in os.walk(folder_path):

        for file in filenames:

            fp = os.path.join(
                dirpath,
                file
            )

            if os.path.exists(fp):

                total_size += os.path.getsize(fp)

    return round(
        total_size / (1024 * 1024),
        2
    )

processed_size = folder_size_mb(
    processed_activity_path
)

hourly_size = folder_size_mb(
    hourly_summary_path
)

print(
    "Processed Activity Size (MB):",
    processed_size
)

print(
    "Hourly Summary Size (MB):",
    hourly_size
)

# ============================================================
# COLUMNAR STORAGE BENEFITS
# ============================================================

print("\n========== PARQUET BENEFITS ==========")

print(
    "1. Parquet stores data in columnar format."
)

print(
    "2. Spark reads only required columns."
)

print(
    "3. Storage size is typically smaller than CSV."
)

print(
    "4. Aggregations are faster because fewer "
    "columns are scanned."
)

print(
    "5. Partitioning by date reduces data scanned."
)

# ============================================================
# SUMMARY
# ============================================================

print("\n========== SP6 SUMMARY ==========")

print(
    "Processed Activity Path:"
)

print(
    processed_activity_path
)

print(
    "\nAnalytics Path:"
)

print(
    hourly_summary_path
)

print(
    "\nDashboard CSV Path:"
)

print(
    dashboard_csv_path
)

print(
    "\nSP6 Completed Successfully."
)

spark.stop()