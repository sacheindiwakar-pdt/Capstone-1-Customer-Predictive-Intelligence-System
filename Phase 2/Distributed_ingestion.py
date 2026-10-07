from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    IntegerType,
    DoubleType
)
from pyspark.sql.functions import input_file_name, col, to_timestamp
import glob
import os

os.environ["HADOOP_HOME"] = r"D:\Training\hadoop"
os.environ["hadoop.home.dir"] = r"D:\Training\hadoop"
os.environ["PATH"] += r";D:\Training\hadoop\bin"
# ==================================================
# 1. Create Spark Session
# ==================================================
spark = (
    SparkSession.builder
    .appName("SP1_Distributed_Ingestion")
    .getOrCreate()
)

# ==================================================
# 2. Read daily files using pattern
# sms-call-internet-mi-*.csv
# ==================================================
csv_pattern = r"../Dataset/sms-call-internet-mi-*.csv"

print("Current Working Directory:")
print(os.getcwd())

files = glob.glob(csv_pattern)

print("\nFiles Found:", len(files))
for file in files:
    print(file)

if len(files) == 0:
    raise FileNotFoundError(
        f"No files found using pattern: {csv_pattern}"
    )

# ==================================================
# 3. Compare inferSchema vs Manual StructType
# ==================================================

# Infer Schema
infer_df = (
    spark.read
    .option("header", True)
    .option("inferSchema", True)
    .csv(files)
)

print("\nSchema Using inferSchema:")
infer_df.printSchema()

# Manual Schema
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

raw_network_df = (
    spark.read
    .option("header", True)
    .schema(schema)
    .csv(files)
    .withColumn("input_file_name", input_file_name())
)

print("\nSchema Using Manual StructType:")
raw_network_df.printSchema()

print("\nSchema Comparison:")
print("- inferSchema: Spark scans data to determine column types.")
print("- Manual StructType: Schema is predefined.")
print("- inferSchema is easier but slower due to extra file scan.")
print("- StructType is faster and preferred in production.")

# ==================================================
# Convert datetime column
# ==================================================
raw_network_df = raw_network_df.withColumn(
    "datetime",
    to_timestamp("datetime")
)

# ==================================================
# 4. Count rows, files, grids, country codes, hours
# ==================================================
row_count = raw_network_df.count()

file_count = (
    raw_network_df
    .select("input_file_name")
    .distinct()
    .count()
)

grid_count = (
    raw_network_df
    .select("CellID")
    .distinct()
    .count()
)

country_count = (
    raw_network_df
    .select("countrycode")
    .distinct()
    .count()
)

hour_count = (
    raw_network_df
    .select("datetime")
    .distinct()
    .count()
)

# ==================================================
# 5. input_file_name already added for traceability
# ==================================================

# ==================================================
# 6. Inspect partition count
# ==================================================
partition_count = raw_network_df.rdd.getNumPartitions()

# ==================================================
# Validation Summary
# ==================================================
print("\n========== SP1 VALIDATION ==========")

print("Total Rows:", row_count)
print("Source Files:", file_count)
print("Unique Grids:", grid_count)
print("Country-Code Categories:", country_count)
print("Distinct Hourly Intervals:", hour_count)
print("Partitions:", partition_count)

# ==================================================
# Grid Range
# ==================================================
print("\nGrid Range:")

raw_network_df.selectExpr(
    "min(CellID) as min_grid",
    "max(CellID) as max_grid"
).show()

# ==================================================
# Rows Per Source File
# ==================================================
print("\nRows Per Source File:")

raw_network_df.groupBy(
    "input_file_name"
).count().show(truncate=False)

# ==================================================
# Explain Partitions
# ==================================================
print("\nPartition Explanation:")
print(
    "Spark processes data in partitions. "
    "File layout affects how partitions are created. "
    "Many small files can create excessive scheduling overhead, "
    "while large files may reduce parallelism. "
    "Balanced file sizes generally improve Spark performance."
)

# ==================================================
# Assertions
# ==================================================
assert grid_count > 0, "No grids found."

assert (
    raw_network_df.filter(
        (col("CellID") < 1) |
        (col("CellID") > 10000)
    ).count() == 0
), "Invalid CellID values found."

assert (
    raw_network_df.filter(
        col("input_file_name").isNull()
    ).count() == 0
), "Null input file names found."

print("\nSP1 validation passed.")

# ==================================================
# SAVE RAW PARQUET
# ==================================================

raw_parquet_path = (
    "D:/Capstone1/parquet_output/raw_parquet"
)

raw_network_df.write \
    .mode("overwrite") \
    .parquet(raw_parquet_path)

print(
    f"Raw parquet saved to: {raw_parquet_path}"
)

# ==================================================
# Stop Spark
# ==================================================
spark.stop()