import os
import json
import glob
import argparse
import logging
from datetime import datetime
import sys
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType,StructField,StringType,
    IntegerType,DoubleType
)
from pyspark.sql.functions import (
    col,input_file_name,to_timestamp,
    when,lit,sum as spark_sum,
    hour,dayofweek,to_date
)
from pyspark.sql.functions import broadcast
os.environ["HADOOP_HOME"] = r"D:\Training\hadoop"
os.environ["hadoop.home.dir"] = r"D:\Training\hadoop"
os.environ["PATH"] += r";D:\Training\hadoop\bin"

os.environ["PYSPARK_PYTHON"] = sys.executable
os.environ["PYSPARK_DRIVER_PYTHON"] = sys.executable

print("Python executable:", sys.executable)

def setup_logging(log_dir):
    os.makedirs(log_dir,exist_ok=True)
    log_file=os.path.join(
        log_dir,
        f"telecom_etl_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return log_file


def read_raw(spark,input_path):
    pattern=os.path.join(input_path,"sms-call-internet-mi-*.csv")
    files=glob.glob(pattern)

    if not files:
        raise FileNotFoundError(
            f"No input files found. Expected: {pattern}"
        )

    schema=StructType([
        StructField("datetime",StringType(),True),
        StructField("CellID",IntegerType(),True),
        StructField("countrycode",IntegerType(),True),
        StructField("smsin",DoubleType(),True),
        StructField("smsout",DoubleType(),True),
        StructField("callin",DoubleType(),True),
        StructField("callout",DoubleType(),True),
        StructField("internet",DoubleType(),True)
    ])

    df=(
        spark.read
        .option("header",True)
        .schema(schema)
        .csv(pattern)
        .withColumn("input_file_name",input_file_name())
    )

    rows=df.count()

    logging.info(
        f"input_rows={rows} input_files={len(files)} status=READ_SUCCESS"
    )

    return df


def clean(raw_df):
    activity_cols=[
        "sms_in",
        "sms_out",
        "call_in",
        "call_out",
        "internet_activity"
    ]

    df=(
        raw_df
        .withColumnRenamed("CellID","grid_id")
        .withColumnRenamed("countrycode","country_code")
        .withColumnRenamed("smsin","sms_in")
        .withColumnRenamed("smsout","sms_out")
        .withColumnRenamed("callin","call_in")
        .withColumnRenamed("callout","call_out")
        .withColumnRenamed("internet","internet_activity")
        .withColumn("timestamp",to_timestamp("datetime"))
        .drop("datetime")
    )

    for c in activity_cols:
        df=df.withColumn(c,col(c).cast("double"))

    invalid=(
        col("grid_id").isNull() |
        col("timestamp").isNull() |
        (col("grid_id")<1) |
        (col("grid_id")>10000) |
        (col("sms_in")<0) |
        (col("sms_out")<0) |
        (col("call_in")<0) |
        (col("call_out")<0) |
        (col("internet_activity")<0)
    )

    input_rows=df.count()
    rejected_rows=df.filter(invalid).count()

    clean_df=df.filter(~invalid)

    null_count=0

    for c in activity_cols:
        n=clean_df.filter(col(c).isNull()).count()
        null_count+=n
        clean_df=clean_df.withColumn(
            c,
            when(col(c).isNull(),lit(0.0)).otherwise(col(c))
        )

    clean_df=(
        clean_df
        .withColumn("total_sms",col("sms_in")+col("sms_out"))
        .withColumn("total_calls",col("call_in")+col("call_out"))
        .withColumn(
            "total_activity",
            col("total_sms")+col("total_calls")+col("internet_activity")
        )
        .withColumn("date",to_date("timestamp"))
        .withColumn("hour",hour("timestamp"))
        .withColumn("day_of_week",dayofweek("timestamp"))
    )

    output_rows=clean_df.count()

    logging.info(
        f"input_rows={input_rows} rejected_rows={rejected_rows} "
        f"nulls_handled={null_count} output_rows={output_rows} "
        f"status=CLEAN_SUCCESS"
    )

    return clean_df


def aggregate(clean_df):
    activity_cols=[
        "sms_in",
        "sms_out",
        "call_in",
        "call_out",
        "internet_activity"
    ]

    agg_exprs=[
        spark_sum(c).alias(c)
        for c in activity_cols
    ]

    hourly=(
        clean_df
        .groupBy("timestamp","grid_id")
        .agg(*agg_exprs)
        .withColumn("total_sms",col("sms_in")+col("sms_out"))
        .withColumn("total_calls",col("call_in")+col("call_out"))
        .withColumn(
            "total_activity",
            col("total_sms")+col("total_calls")+col("internet_activity")
        )
        .withColumn("date",to_date("timestamp"))
    )

    duplicate_count=(
        hourly
        .groupBy("grid_id","timestamp")
        .count()
        .filter(col("count")>1)
        .count()
    )

    if duplicate_count>0:
        raise ValueError(
            f"Aggregation produced {duplicate_count} duplicate grid/hour records"
        )

    output_rows=hourly.count()

    logging.info(
        f"output_rows={output_rows} duplicates={duplicate_count} "
        f"status=AGGREGATE_SUCCESS"
    )

    return hourly


def enrich(hourly_df,reference_path):
    if not os.path.exists(reference_path):
        raise FileNotFoundError(
            f"Reference GeoJSON not found: {reference_path}"
        )

    with open(reference_path,"r",encoding="utf-8") as f:
        geojson=json.load(f)

    features=[]

    for feature in geojson["features"]:
        properties=feature.get("properties",{})

        # IMPORTANT:
        # Use properties.cellId, NOT the top-level feature id.
        grid_id=properties.get("cellId")
        geometry=feature.get("geometry")

        if grid_id is not None:
            features.append(
                (int(grid_id),json.dumps(geometry))
            )

    geometry_df=hourly_df.sparkSession.createDataFrame(
        features,
        ["grid_id","geometry"]
    )

    geometry_df=geometry_df.dropDuplicates(["grid_id"])

    before=hourly_df.select("grid_id").distinct().count()

    enriched=hourly_df.join(
        broadcast(geometry_df),
        on="grid_id",
        how="left"
    )

    after=enriched.select("grid_id").distinct().count()

    missing=enriched.filter(
        col("geometry").isNull()
    ).select("grid_id").distinct().count()

    coverage=0 if before==0 else ((before-missing)/before)*100

    logging.info(
        f"distinct_grids_before={before} "
        f"distinct_grids_after={after} "
        f"missing_geometry_grids={missing} "
        f"enrichment_coverage={coverage:.2f}% "
        f"status=ENRICH_SUCCESS"
    )

    if missing>0:
        raise ValueError(
            f"Geospatial enrichment failed: {missing} grid IDs have no geometry"
        )

    return enriched


def write_outputs(clean_df,hourly_df,enriched_df,output_path):
    processed_path=os.path.join(
        output_path,
        "processed",
        "activity"
    )

    analytics_path=os.path.join(
        output_path,
        "analytics",
        "hourly_grid_summary"
    )

    dashboard_path=os.path.join(
        output_path,
        "dashboard_summary"
    )

    (
        clean_df
        .write
        .mode("overwrite")
        .partitionBy("date")
        .parquet(processed_path)
    )

    (
        hourly_df
        .write
        .mode("overwrite")
        .parquet(analytics_path)
    )

    dashboard_df=(
        hourly_df
        .groupBy("date")
        .agg(
            spark_sum("total_activity").alias("total_activity"),
            spark_sum("internet_activity").alias("internet_activity")
        )
        .orderBy("date")
    )

    (
        dashboard_df
        .coalesce(1)
        .write
        .mode("overwrite")
        .option("header",True)
        .csv(dashboard_path)
    )

    round_trip=(
        hourly_df.sparkSession
        .read
        .parquet(analytics_path)
    )

    original_count=hourly_df.count()
    round_trip_count=round_trip.count()

    if original_count!=round_trip_count:
        raise ValueError(
            f"Round-trip count mismatch: "
            f"{original_count} != {round_trip_count}"
        )

    duplicate_count=(
        round_trip
        .groupBy("grid_id","timestamp")
        .count()
        .filter(col("count")>1)
        .count()
    )

    if duplicate_count>0:
        raise ValueError(
            f"Round-trip validation found {duplicate_count} duplicates"
        )

    logging.info(
        f"output_rows={original_count} "
        f"round_trip_rows={round_trip_count} "
        f"duplicates={duplicate_count} "
        f"status=WRITE_SUCCESS"
    )

    logging.info(f"processed_path={processed_path}")
    logging.info(f"analytics_path={analytics_path}")
    logging.info(f"dashboard_path={dashboard_path}")


def main():
    parser=argparse.ArgumentParser(
        description="Reusable Telecom Spark ETL Job"
    )

    parser.add_argument(
        "--input",
        required=True,
        help="Directory containing daily Milan CSV files"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output data directory"
    )

    parser.add_argument(
        "--reference",
        required=True,
        help="Path to milano-grid.geojson"
    )

    parser.add_argument(
        "--log-dir",
        default="logs",
        help="Directory for execution logs"
    )

    args=parser.parse_args()

    log_file=setup_logging(args.log_dir)

    start=datetime.now()

    logging.info(
        f"start_time={start.isoformat()} status=STARTED"
    )

    spark=None

    try:
        spark=SparkSession.builder \
        .appName("TelecomETL") \
        .master("local[2]") \
        .config("spark.pyspark.python",sys.executable) \
        .config("spark.pyspark.driver.python",sys.executable) \
        .config("spark.python.worker.reuse","true") \
        .config("spark.sql.shuffle.partitions","8") \
        .getOrCreate()

        raw_df=read_raw(
            spark,
            args.input
        )

        clean_df=clean(raw_df)

        hourly_df=aggregate(clean_df)

        enriched_df=enrich(
            hourly_df,
            args.reference
        )

        write_outputs(
            clean_df,
            hourly_df,
            enriched_df,
            args.output
        )

        end=datetime.now()

        logging.info(
            f"end_time={end.isoformat()} "
            f"status=SUCCESS "
            f"duration_seconds={(end-start).total_seconds():.2f}"
        )

    except Exception as e:
        end=datetime.now()

        logging.error(
            f"end_time={end.isoformat()} "
            f"status=FAILED "
            f"error={str(e)} "
            f"duration_seconds={(end-start).total_seconds():.2f}"
        )

        raise

    finally:
        if spark:
            spark.stop()


if __name__=="__main__":
    main()