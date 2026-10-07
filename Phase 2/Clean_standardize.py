from pyspark.sql import SparkSession
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

# ==================================================
# Spark Session
# ==================================================
spark = (
    SparkSession.builder
    .appName("SP2_Data_Standardization_Quality")
    .config("spark.driver.memory", "4g")
    .config("spark.executor.memory", "4g")
    .getOrCreate()
)

# ==================================================
# Read Files
# ==================================================
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
    .withColumn("input_file_name", input_file_name())
)

# ==================================================
# Record Count Before Cleaning
# ==================================================
raw_count = raw_df.count()

print("Raw Records:", raw_count)

# ==================================================
# 1. Rename Columns To Contract Names
# ==================================================
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
    df = df.withColumnRenamed(old_col, new_col)

# ==================================================
# 2. Cast Data Types
# ==================================================
df = (
    df
    .withColumn(
        "timestamp",
        to_timestamp(col("timestamp"))
    )
    .withColumn(
        "sms_in",
        col("sms_in").cast("double")
    )
    .withColumn(
        "sms_out",
        col("sms_out").cast("double")
    )
    .withColumn(
        "call_in",
        col("call_in").cast("double")
    )
    .withColumn(
        "call_out",
        col("call_out").cast("double")
    )
    .withColumn(
        "internet_activity",
        col("internet_activity").cast("double")
    )
)

# ==================================================
# Verify Hourly Cadence
# ==================================================
hourly_intervals = (
    df.select("timestamp")
      .distinct()
      .count()
)

print("Distinct Hourly Intervals:", hourly_intervals)

# ==================================================
# 3. Quarantine Bad Records
# ==================================================
reject_condition = (
    col("grid_id").isNull()
    | col("timestamp").isNull()
)

for c in [
    "sms_in",
    "sms_out",
    "call_in",
    "call_out",
    "internet_activity"
]:
    reject_condition = (
        reject_condition
        | (
            col(c).isNotNull()
            & (col(c) < 0)
        )
    )

quarantine_df = df.filter(reject_condition)

rejected_count = quarantine_df.count()

curated_df = df.filter(~reject_condition)

print("Rejected Records:", rejected_count)

# ==================================================
# Profile Null Activity Values
# ==================================================
sms_in_nulls = curated_df.filter(
    col("sms_in").isNull()
).count()

sms_out_nulls = curated_df.filter(
    col("sms_out").isNull()
).count()

call_in_nulls = curated_df.filter(
    col("call_in").isNull()
).count()

call_out_nulls = curated_df.filter(
    col("call_out").isNull()
).count()

internet_nulls = curated_df.filter(
    col("internet_activity").isNull()
).count()

total_activity_nulls = (
    sms_in_nulls
    + sms_out_nulls
    + call_in_nulls
    + call_out_nulls
    + internet_nulls
)

# ==================================================
# Null To Zero Rule
# ==================================================
curated_df = (
    curated_df
    .fillna({
        "sms_in": 0,
        "sms_out": 0,
        "call_in": 0,
        "call_out": 0,
        "internet_activity": 0
    })
)

# ==================================================
# 4. Derived Activity Metrics
# ==================================================
curated_df = (
    curated_df
    .withColumn(
        "total_sms",
        col("sms_in") + col("sms_out")
    )
    .withColumn(
        "total_calls",
        col("call_in") + col("call_out")
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

# ==================================================
# 5. Date Features
# ==================================================
curated_df = (
    curated_df
    .withColumn(
        "date",
        to_date("timestamp")
    )
    .withColumn(
        "hour",
        hour("timestamp")
    )
    .withColumn(
        "day_of_week",
        dayofweek("timestamp")
    )
)

# ==================================================
# 6. Compare Before & After
# ==================================================
clean_count = curated_df.count()

print("\nDEBUG")
print("Raw Count =", raw_count)
print("Curated Count =", curated_df.count())

print(
    "Distinct grid-hour count =",
    curated_df.select(
        "grid_id",
        "timestamp"
    ).distinct().count()
)

print("\n========== SP2 QUALITY REPORT ==========")

print("Raw Records:", raw_count)
print("Curated Records:", clean_count)
print("Rejected Records:", rejected_count)

print("\nActivity Nulls Handled")
print("sms_in:", sms_in_nulls)
print("sms_out:", sms_out_nulls)
print("call_in:", call_in_nulls)
print("call_out:", call_out_nulls)
print("internet_activity:", internet_nulls)
print("Total Null Activity Values:", total_activity_nulls)

print("\nData Quality Validation")
print(
    "Difference Check:",
    raw_count - clean_count == rejected_count
)

# ==================================================
# Sample Output
# ==================================================
curated_df.show(5)

print("\nSP2 processing completed successfully.")

# Reduce memory pressure while writing parquet
spark.conf.set(
    "parquet.enable.dictionary",
    "false"
)

print(
    "Partitions before write:",
    curated_df.rdd.getNumPartitions()
)

curated_df = curated_df.repartition(8)

# ==================================================
# SAVE CLEAN PARQUET
# ==================================================

clean_parquet_path = (
    "D:/Capstone1/parquet_output/clean_parquet"
)

(
    curated_df
    .write
    .mode("overwrite")
    .parquet(clean_parquet_path)
)

print(
    f"\nClean parquet saved to: {clean_parquet_path}"
)

spark.stop()