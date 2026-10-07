# ============================================================
# PHASE 2 - SP4
# Geographic Enrichment
# ============================================================

import json

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.functions import broadcast
import os

os.environ["HADOOP_HOME"] = r"D:\Training\hadoop"
os.environ["hadoop.home.dir"] = r"D:\Training\hadoop"
os.environ["PATH"] += r";D:\Training\hadoop\bin"

import sys

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

print("Python executable:", sys.executable)

# ============================================================
# SPARK SESSION
# ============================================================

spark = (
    SparkSession.builder
    .appName("SP4_Geographic_Enrichment")
    .config("spark.driver.memory", "4g")
    .config("spark.executor.memory", "4g")
    .getOrCreate()
)

# ============================================================
# READ SP2 CLEAN PARQUET
# ============================================================

curated_df = spark.read.parquet(
    "D:/Capstone1/parquet_output/clean_parquet"
)

print("\n========== SP2 INPUT ==========")

print(
    "Rows:",
    curated_df.count()
)

curated_df.printSchema()

# ============================================================
# LOAD GEOJSON
# ============================================================

geojson_path = "../Dataset/milano-grid.geojson"

with open(
    geojson_path,
    "r",
    encoding="utf-8"
) as f:

    geojson_data = json.load(f)

# ============================================================
# INSPECT GEOJSON
# ============================================================

print("\n========== GEOJSON INSPECTION ==========")

print(
    "Top Level Type:",
    geojson_data.get("type")
)

print(
    "Number Of Features:",
    len(
        geojson_data.get("features", [])
    )
)

sample_feature = geojson_data["features"][0]

print(
    "Grid Key:",
    "properties.cellId"
)

print(
    "Geometry Type:",
    sample_feature["geometry"]["type"]
)

# ============================================================
# FLATTEN FEATURES
# properties.cellId -> grid_id
# ============================================================

grid_lookup_list = []

for feature in geojson_data["features"]:

    grid_lookup_list.append(
        (
            int(
                feature["properties"]["cellId"]
            ),
            json.dumps(
                feature["geometry"]
            )
        )
    )

grid_lookup_df = spark.createDataFrame(
    grid_lookup_list,
    [
        "grid_id",
        "geometry"
    ]
)

# ============================================================
# SIZE COMPARISON
# ============================================================

activity_rows = curated_df.count()

lookup_rows = grid_lookup_df.count()

print("\n========== SIZE COMPARISON ==========")

print(
    "Activity Rows:",
    activity_rows
)

print(
    "Grid Lookup Rows:",
    lookup_rows
)

# ============================================================
# JOIN USING BROADCAST
# ============================================================

grid_activity_geo_df = (
    curated_df
    .join(
        broadcast(grid_lookup_df),
        on="grid_id",
        how="left"
    )
)

# ============================================================
# NUMERICAL VALIDATION
# ============================================================

grids_before = (
    curated_df
    .select("grid_id")
    .distinct()
    .count()
)

grids_after = (
    grid_activity_geo_df
    .select("grid_id")
    .distinct()
    .count()
)

missing_geometry = (
    grid_activity_geo_df
    .filter(
        F.col("geometry").isNull()
    )
    .select("grid_id")
    .distinct()
    .count()
)

matched_geometry = (
    grids_after
    - missing_geometry
)

coverage_pct = (
    matched_geometry
    / grids_after
) * 100

print("\n========== COVERAGE REPORT ==========")

print(
    "Distinct Activity Grids Before:",
    grids_before
)

print(
    "Distinct Activity Grids After:",
    grids_after
)

print(
    "Missing Geometry:",
    missing_geometry
)

print(
    "Matched Geometry:",
    matched_geometry
)

print(
    "Coverage Percentage:",
    round(
        coverage_pct,
        2
    )
)
    
# ============================================================
# UNMATCHED GRID IDs
# ============================================================

unmatched_grids = (
    grid_activity_geo_df
    .filter(
        F.col("geometry").isNull()
    )
    .select("grid_id")
    .distinct()
)

print("\n========== UNMATCHED GRID IDS ==========")

unmatched_grids.show(
    50,
    truncate=False
)

# ============================================================
# GEOGRAPHIC VALIDATION
# ============================================================

print("\n========== GEOGRAPHIC VALIDATION ==========")

polygon_count = (
    grid_lookup_df
    .filter(
        F.col("geometry")
        .contains("Polygon")
    )
    .count()
)

print(
    "Polygon Geometries:",
    polygon_count
)

print(
    "\nSample Geometry Records:"
)

(
    grid_activity_geo_df
    .filter(
        F.col("geometry").isNotNull()
    )
    .select(
        "grid_id",
        "geometry"
    )
    .show(
        5,
        truncate=False
    )
)

# ============================================================
# FINAL ENRICHED DATASET
# ============================================================

grid_activity_geo_df = (
    grid_activity_geo_df
    .select(
        "timestamp",
        "grid_id",
        "sms_in",
        "sms_out",
        "call_in",
        "call_out",
        "internet_activity",
        "total_activity",
        "geometry"
    )
)

print("\n========== ENRICHED DATASET ==========")

grid_activity_geo_df.show(
    5,
    truncate=False
)

# ============================================================
# TOP HIGH ACTIVITY GRIDS
# ============================================================

top_high_activity_grids = (
    grid_activity_geo_df
    .groupBy(
        "grid_id",
        "geometry"
    )
    .agg(
        F.sum(
            "total_activity"
        ).alias(
            "overall_activity"
        )
    )
    .orderBy(
        F.desc(
            "overall_activity"
        )
    )
    .limit(10)
)

print("\n========== TOP 10 HIGH ACTIVITY GRIDS ==========")

top_high_activity_grids.show(
    truncate=False
)

# ============================================================
# FINAL SUMMARY
# ============================================================

print("\n========================================")
print("SP4 SUMMARY")
print("========================================")

print(
    "Activity Rows:",
    activity_rows
)

print(
    "Grid Lookup Rows:",
    lookup_rows
)

print(
    "Distinct Activity Grids:",
    grids_before
)

print(
    "Missing Geometry:",
    missing_geometry
)

print(
    "Coverage Percentage:",
    round(
        coverage_pct,
        2
    )
)

print(
    "Geographic Enrichment Complete"
)

grid_activity_geo_df.write \
    .mode("overwrite") \
    .parquet(
        "D:/Capstone1/parquet_output/grid_activity_geo"
    )

spark.stop()