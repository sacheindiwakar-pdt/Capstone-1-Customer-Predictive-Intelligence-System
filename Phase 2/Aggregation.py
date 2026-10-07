# ============================================================
# PHASE 2 - SP3
# Operational KPI Aggregation
# ============================================================

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType
)
from pyspark.sql.functions import (
    col,
    to_timestamp,
    input_file_name,
    hour,
    dayofweek,
    to_date
)
import glob
import os

os.environ["HADOOP_HOME"] = r"D:\Training\hadoop"
os.environ["hadoop.home.dir"] = r"D:\Training\hadoop"
os.environ["PATH"] += r";D:\Training\hadoop\bin"

# ============================================================
# SPARK SESSION
# ============================================================

spark = (
    SparkSession.builder
    .appName("SP3_Operational_KPI")
    .getOrCreate()
)

# ============================================================
# READ SOURCE DATA
# ============================================================

files = glob.glob(
    r"../Dataset/sms-call-internet-mi-*.csv"
)

schema = StructType([
    StructField("datetime", StringType(), True),
    StructField("CellID", IntegerType(), True),
    StructField("countrycode", IntegerType(), True),
    StructField("smsin", DoubleType(), True),
    StructField("smsout", DoubleType(), True),
    StructField("callin", DoubleType(), True),
    StructField("callout", DoubleType(), True),
    StructField("internet", DoubleType(), True)
])

raw_df = (
    spark.read
    .option("header", True)
    .schema(schema)
    .csv(files)
    .withColumn(
        "input_file_name",
        input_file_name()
    )
)

# ============================================================
# SP2 TRANSFORMATIONS
# ============================================================

column_mapping = {
    "datetime": "timestamp",
    "CellID": "grid_id",
    "countrycode": "country_code",
    "smsin": "sms_in",
    "smsout": "sms_out",
    "callin": "call_in",
    "callout": "call_out",
    "internet": "internet_activity"
}

df = raw_df

for old_col, new_col in column_mapping.items():
    df = df.withColumnRenamed(
        old_col,
        new_col
    )

df = (
    df
    .withColumn(
        "timestamp",
        to_timestamp("timestamp")
    )
    .fillna({
        "sms_in": 0,
        "sms_out": 0,
        "call_in": 0,
        "call_out": 0,
        "internet_activity": 0
    })
)

curated_df = df

# ============================================================
# SP3 - ACTIVITY 1
# COLLAPSE TO GRID + TIMESTAMP
# ============================================================

hourly_grid_summary = (
    curated_df
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
            .alias("internet_activity")
    )
)

print("HOURLY GRID SUMMARY CREATED")

# ============================================================
# SP3 - ACTIVITY 2
# KPI CALCULATIONS
# ============================================================

hourly_grid_summary = (
    hourly_grid_summary
    .withColumn(
        "total_sms_activity",
        col("sms_in")
        + col("sms_out")
    )
    .withColumn(
        "total_call_activity",
        col("call_in")
        + col("call_out")
    )
    .withColumn(
        "total_activity",
        col("sms_in")
        + col("sms_out")
        + col("call_in")
        + col("call_out")
        + col("internet_activity")
    )
)

# ============================================================
# DAILY ACTIVITY PER GRID
# ============================================================

daily_grid_activity = (
    hourly_grid_summary
    .withColumn(
        "date",
        to_date("timestamp")
    )
    .groupBy(
        "grid_id",
        "date"
    )
    .agg(
        F.sum("total_activity")
        .alias("daily_activity")
    )
)

# ============================================================
# SP3 - ACTIVITY 3
# TOP 10 HIGH ACTIVITY GRIDS
# ============================================================

top_10_grids = (
    hourly_grid_summary
    .groupBy("grid_id")
    .agg(
        F.sum("total_activity")
        .alias("overall_activity")
    )
    .orderBy(
        F.desc("overall_activity")
    )
    .limit(10)
)

print("\n================================")
print("TOP 10 HIGH ACTIVITY GRIDS")
print("================================")

top_10_grids.show(
    truncate=False
)

# ============================================================
# SP3 - ACTIVITY 4
# PEAK ACTIVITY HOUR
# ============================================================

peak_hour_df = (
    hourly_grid_summary
    .withColumn(
        "hour",
        hour("timestamp")
    )
    .groupBy("hour")
    .agg(
        F.sum("total_activity")
        .alias("hourly_activity")
    )
    .orderBy(
        F.desc("hourly_activity")
    )
)

print("\n================================")
print("PEAK ACTIVITY HOUR")
print("================================")

peak_hour_df.show(
    5,
    truncate=False
)

# ============================================================
# SP3 - ACTIVITY 5
# INTERNET SHARE
# ============================================================

hourly_grid_summary = (
    hourly_grid_summary
    .withColumn(
        "internet_share_pct",
        F.when(
            col("total_activity") > 0,
            (
                col("internet_activity")
                / col("total_activity")
            ) * 100
        ).otherwise(0)
    )
)

# ============================================================
# SP3 - ACTIVITY 6
# VALIDATE GRAIN
# EXACTLY ONE RECORD
# PER GRID_ID + TIMESTAMP
# ============================================================

duplicate_records = (
    hourly_grid_summary
    .groupBy(
        "grid_id",
        "timestamp"
    )
    .count()
    .filter(
        col("count") > 1
    )
    .count()
)

print("\n================================")
print("GRAIN VALIDATION")
print("================================")

print(
    "Duplicate Grid-Hour Records:",
    duplicate_records
)

assert duplicate_records == 0, \
    "Duplicate grid-hour combinations found."

print(
    "PASS: Exactly one record per "
    "grid_id + timestamp"
)

# ============================================================
# SUMMARY
# ============================================================

print("\n================================")
print("SP3 SUMMARY")
print("================================")

print(
    "Hourly Grid Summary Rows:",
    hourly_grid_summary.count()
)

print(
    "Daily Grid Activity Rows:",
    daily_grid_activity.count()
)

print(
    "Distinct Grids:",
    hourly_grid_summary
    .select("grid_id")
    .distinct()
    .count()
)

print(
    "Distinct Hours:",
    hourly_grid_summary
    .select("timestamp")
    .distinct()
    .count()
)

# ============================================================
# SAMPLE OUTPUTS
# ============================================================

print("\nHOURLY GRID SUMMARY")

hourly_grid_summary.show(
    10,
    truncate=False
)

print("\nDAILY GRID ACTIVITY")

daily_grid_activity.show(
    10,
    truncate=False
)

hourly_grid_summary.write \
    .mode("overwrite") \
    .parquet(
        "D:/Capstone1/parquet_output/hourly_grid_summary"
    )
daily_grid_activity.write \
    .mode("overwrite") \
    .parquet(
        "D:/Capstone1/parquet_output/daily_grid_activity"
    )

spark.stop()