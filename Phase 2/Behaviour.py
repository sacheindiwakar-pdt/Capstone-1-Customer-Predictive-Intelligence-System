# ============================================================
# PHASE 2 - SP5
# Spark Performance Optimization
# ============================================================

import time

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import broadcast
import os

os.environ["HADOOP_HOME"] = r"D:\Training\hadoop"
os.environ["hadoop.home.dir"] = r"D:\Training\hadoop"
os.environ["PATH"] += r";D:\Training\hadoop\bin"

# ============================================================
# SPARK SESSION
# ============================================================

spark = (
    SparkSession.builder
    .appName("SP5_Performance_Optimization")
    .config("spark.driver.memory", "4g")
    .config("spark.executor.memory", "4g")
    .getOrCreate()
)

# ============================================================
# READ SP2 CURATED DATA
# ============================================================

clean_df = spark.read.parquet(
    "D:/Capstone1/parquet_output/clean_parquet"
)

print("\n================================")
print("INPUT DATA")
print("================================")

print(
    "Rows:",
    clean_df.count()
)

# ============================================================
# HOTSPOT AGGREGATION
# ============================================================

hotspot_df = (
    clean_df
    .groupBy("grid_id")
    .agg(
        F.sum("total_activity")
        .alias("total_activity")
    )
    .orderBy(
        F.desc("total_activity")
    )
)

# ============================================================
# ACTIVITY 1
# EXPLAIN PLAN
# ============================================================

print("\n================================")
print("ACTIVITY 1 - EXPLAIN PLAN")
print("================================")

hotspot_df.explain(True)

# ============================================================
# ACTIVITY 2
# CACHE VS NO CACHE
# ============================================================

print("\n================================")
print("ACTIVITY 2 - CACHE TEST")
print("================================")

start = time.time()

clean_df.count()

without_cache_time = (
    time.time() - start
)

print(
    "Without Cache:",
    round(without_cache_time, 2),
    "seconds"
)

clean_df.cache()

start = time.time()

clean_df.count()

first_cache_time = (
    time.time() - start
)

print(
    "First Cached Action:",
    round(first_cache_time, 2),
    "seconds"
)

start = time.time()

clean_df.count()

second_cache_time = (
    time.time() - start
)

print(
    "Second Cached Action:",
    round(second_cache_time, 2),
    "seconds"
)

# ============================================================
# ACTIVITY 3
# REPARTITION
# ============================================================

print("\n================================")
print("ACTIVITY 3 - PARTITIONS")
print("================================")

original_partitions = (
    clean_df.rdd.getNumPartitions()
)

print(
    "Original Partitions:",
    original_partitions
)

repartitioned_df = (
    clean_df.repartition("date")
)

new_partitions = (
    repartitioned_df.rdd.getNumPartitions()
)

print(
    "Partitions After Repartition:",
    new_partitions
)

# ============================================================
# ACTIVITY 4
# COLUMN PRUNING
# ============================================================

print("\n================================")
print("ACTIVITY 4 - COLUMN PRUNING")
print("================================")

pruned_df = (
    clean_df
    .select(
        "grid_id",
        "total_activity"
    )
)

pruned_hotspot = (
    pruned_df
    .groupBy("grid_id")
    .agg(
        F.sum("total_activity")
        .alias("activity")
    )
)

print(
    "\nExplain Plan After Column Pruning:"
)

pruned_hotspot.explain()

# ============================================================
# GRID LOOKUP SAMPLE
# ============================================================

grid_lookup_df = spark.createDataFrame(
    [
        (1, "geometry"),
        (2, "geometry")
    ],
    [
        "grid_id",
        "geometry"
    ]
)

# ============================================================
# ACTIVITY 5
# STANDARD JOIN PLAN
# ============================================================

print("\n================================")
print("ACTIVITY 5 - STANDARD JOIN")
print("================================")

standard_join = (
    clean_df.join(
        grid_lookup_df,
        "grid_id",
        "left"
    )
)

standard_join.explain()

# ============================================================
# BROADCAST JOIN PLAN
# ============================================================

print("\n================================")
print("ACTIVITY 5 - BROADCAST JOIN")
print("================================")

broadcast_join = (
    clean_df.join(
        broadcast(grid_lookup_df),
        "grid_id",
        "left"
    )
)

broadcast_join.explain()

# ============================================================
# ACTIVITY 6
# OVER-PARTITIONING DEMO
# ============================================================

print("\n================================")
print("ACTIVITY 6 - OVER PARTITIONING")
print("================================")

small_df = (
    clean_df.limit(1000)
)

print(
    "Partition Count Before:",
    small_df.rdd.getNumPartitions()
)

small_df = (
    small_df.repartition(100)
)

print(
    "Partition Count After:",
    small_df.rdd.getNumPartitions()
)

print(
    "\nObservation:"
)

print(
    "Creating many partitions for "
    "a very small dataset increases "
    "task scheduling overhead and "
    "usually reduces performance."
)

# ============================================================
# ACTIVITY 7
# PERFORMANCE OBSERVATIONS
# ============================================================

print("\n================================")
print("ACTIVITY 7 - OBSERVATIONS")
print("================================")

print(
    "\nObservation 1:"
)

print(
    "Caching improves repeated "
    "actions because data is "
    "kept in memory instead of "
    "being recomputed."
)

print(
    "\nObservation 2:"
)

print(
    "Broadcast joins remove "
    "large shuffle operations "
    "when joining a small lookup "
    "table with a very large table."
)

print(
    "\nObservation 3:"
)

print(
    "Column pruning reduces "
    "the volume of data read "
    "and processed by Spark."
)

# ============================================================
# OPTIMIZED VERSION
# ============================================================

print("\n================================")
print("OPTIMIZED TRANSFORMATION")
print("================================")

optimized_df = (
    clean_df
    .select(
        "grid_id",
        "date",
        "total_activity"
    )
)

optimized_result = (
    optimized_df
    .groupBy(
        "grid_id",
        "date"
    )
    .agg(
        F.sum("total_activity")
        .alias("daily_activity")
    )
)

optimized_result.show(
    10,
    truncate=False
)

# ============================================================
# SUMMARY
# ============================================================

print("\n================================")
print("SP5 SUMMARY")
print("================================")

print(
    "Explain Plan Completed"
)

print(
    "Caching Test Completed"
)

print(
    "Repartitioning Test Completed"
)

print(
    "Column Pruning Demonstrated"
)

print(
    "Broadcast Join Demonstrated"
)

print(
    "Performance Observations Documented"
)

spark.stop()