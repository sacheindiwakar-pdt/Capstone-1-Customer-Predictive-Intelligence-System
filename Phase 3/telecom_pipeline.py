import argparse
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    sum,
    avg,
    max,
    hour,
    when,
    dense_rank,
    to_date,
    dayofweek
)
from pyspark.sql.window import Window

from spark_logger import log_spark_execution

# ==========================================================
# SPARK SESSION
# ==========================================================

def create_spark():

    return (
        SparkSession.builder
        .appName("TelecomPipeline")
        .config("spark.driver.memory", "8g")
        .config("spark.executor.memory", "8g")
        .getOrCreate()
    )


# ==========================================================
# VALIDATE REFERENCE
# ==========================================================

def validate_reference(reference_path):

    reference_file = Path(reference_path)

    if not reference_file.exists():

        raise FileNotFoundError(
            f"Reference file not found: {reference_path}"
        )

    print(
        f"Reference file found: {reference_path}"
    )


# ==========================================================
# READ ALL CSV FILES
# ==========================================================

def read_raw_data(
    spark,
    input_path
):

    input_directory = Path(input_path)

    csv_files = sorted(
        [
            str(file)
            for file in input_directory.glob("*.csv")
        ]
    )

    print(
        f"Files found: {len(csv_files)}"
    )

    for file in csv_files:

        print(
            f"Reading: {file}"
        )

    if len(csv_files) == 0:

        return None

    dataframe = (
        spark.read
        .option("header", True)
        .option("inferSchema", True)
        .csv(csv_files)
    )

    print(
        f"Total Records Loaded: {dataframe.count()}"
    )

    return dataframe

# ==========================================================
# CLEAN DATA
# ==========================================================

def clean_data(dataframe):

    activity_columns = [
        "smsin",
        "smsout",
        "callin",
        "callout",
        "internet"
    ]

    for column_name in activity_columns:

        dataframe = dataframe.withColumn(
            column_name,
            when(
                col(column_name).isNull(),
                0
            ).otherwise(
                col(column_name)
            )
        )

    dataframe = dataframe.filter(
        col("CellID").isNotNull()
    )

    return dataframe


# ==========================================================
# ENRICH DATA
# ==========================================================

def enrich_data(dataframe):

    dataframe = (
        dataframe
        .withColumn(
            "event_time",
            col("datetime")
        )
        .withColumn(
            "event_date",
            to_date(col("datetime"))
        )
        .withColumn(
            "day_of_week",
            dayofweek(col("datetime"))
        )
        .withColumn(
            "hour_of_day",
            hour(col("datetime"))
        )
    )

    dataframe = dataframe.withColumn(
        "total_sms",
        col("smsin")
        + col("smsout")
    )

    dataframe = dataframe.withColumn(
        "total_calls",
        col("callin")
        + col("callout")
    )

    dataframe = dataframe.withColumn(
        "internet_activity",
        col("internet")
    )

    dataframe = dataframe.withColumn(
        "total_activity",
        col("total_sms")
        + col("total_calls")
        + col("internet_activity")
    )

    return dataframe


# ==========================================================
# HOURLY SUMMARY
# ==========================================================

def build_hourly_summary(dataframe):

    return (
        dataframe
        .groupBy(
            "CellID",
            "event_date",
            "hour_of_day",
            "day_of_week"
        )
        .agg(
            sum(
                "total_sms"
            ).alias(
                "total_sms"
            ),

            sum(
                "total_calls"
            ).alias(
                "total_calls"
            ),

            sum(
                "internet_activity"
            ).alias(
                "internet_activity"
            ),

            sum(
                "total_activity"
            ).alias(
                "total_activity"
            )
        )
    )


# ==========================================================
# DAILY SUMMARY
# ==========================================================

def build_daily_summary(dataframe):

    return (
        dataframe
        .groupBy(
            "CellID",
            "event_date"
        )
        .agg(
            sum(
                "total_sms"
            ).alias(
                "daily_sms"
            ),

            sum(
                "total_calls"
            ).alias(
                "daily_calls"
            ),

            sum(
                "internet_activity"
            ).alias(
                "daily_internet"
            ),

            sum(
                "total_activity"
            ).alias(
                "daily_total_activity"
            ),

            avg(
                "total_activity"
            ).alias(
                "average_activity"
            ),

            max(
                "total_activity"
            ).alias(
                "peak_activity"
            )
        )
    )


# ==========================================================
# HOTSPOTS
# ==========================================================

def build_hotspots(dataframe):

    hotspot_dataframe = (
        dataframe
        .groupBy(
            "CellID"
        )
        .agg(
            sum(
                "total_activity"
            ).alias(
                "activity_score"
            )
        )
    )

    ranking_window = Window.orderBy(
        col(
            "activity_score"
        ).desc()
    )

    hotspot_dataframe = hotspot_dataframe.withColumn(
        "rank",
        dense_rank().over(
            ranking_window
        )
    )

    return hotspot_dataframe.filter(
        col("rank") <= 10
    )


# ==========================================================
# ALERTS
# ==========================================================

def build_alerts(dataframe):

    threshold = 10000

    return (
        dataframe
        .filter(
            col(
                "total_activity"
            ) > threshold
        )
        .select(
            "CellID",
            "event_time",
            "total_activity"
        )
    )


# ==========================================================
# RISK TABLE
# ==========================================================

def build_risk_table(dataframe):

    return (
        dataframe
        .groupBy(
            "CellID"
        )
        .agg(
            avg(
                "total_activity"
            ).alias(
                "risk_score"
            )
        )
    )


# ==========================================================
# WRITE PROCESSED
# ==========================================================

def write_processed_data(
    processed_dataframe,
    processed_path
):

    (
        processed_dataframe
        .coalesce(4)
        .write
        .mode("overwrite")
        .parquet(
            f"{processed_path}/clean_data"
        )
    )
    print("Processed dataframe schema:")
    processed_dataframe.printSchema()

    # print("Processed rows:")
    # print(processed_dataframe.count())

# ==========================================================
# WRITE ANALYTICS
# ==========================================================

def write_analytics(
    hourly_dataframe,
    daily_dataframe,
    hotspot_dataframe,
    alerts_dataframe,
    risk_dataframe,
    analytics_path
):

    (
        hourly_dataframe.coalesce(4)
        .write
        .mode("overwrite")
        .parquet(
            f"{analytics_path}/hourly_grid_summary"
        )
    )

    (
        daily_dataframe.coalesce(4)
        .write
        .mode("overwrite")
        .parquet(
            f"{analytics_path}/daily_grid_summary"
        )
    )

    (
        hotspot_dataframe.coalesce(4)
        .write
        .mode("overwrite")
        .parquet(
            f"{analytics_path}/hotspots"
        )
    )

    (
        alerts_dataframe.coalesce(4)
        .write
        .mode("overwrite")
        .parquet(
            f"{analytics_path}/alerts"
        )
    )

    (
        risk_dataframe.coalesce(4)
        .write
        .mode("overwrite")
        .parquet(
            f"{analytics_path}/risk"
        )
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        required=True
    )

    parser.add_argument(
        "--reference",
        required=True
    )

    parser.add_argument(
        "--processed",
        required=True
    )

    parser.add_argument(
        "--analytics",
        required=True
    )

    args = parser.parse_args()

    validate_reference(
        args.reference
    )

    spark = create_spark()

    try:

        log_spark_execution(
            "PIPELINE",
            "STARTED"
        )

        dataframe = read_raw_data(
            spark,
            args.input
        )

        required_columns = [
            "datetime",
            "CellID",
            "smsin",
            "smsout",
            "callin",
            "callout",
            "internet"
        ]

        if dataframe is None:
        
                    print(
                        "No data available."
                    )
        
                    return
        
        missing_columns = [
            column
            for column in required_columns
                if column not in dataframe.columns
        ]

        
        if missing_columns:

            raise Exception(
            f"Missing columns: {missing_columns}"
        )        

        

        processed_dataframe = clean_data(
            dataframe
        )

        processed_dataframe = enrich_data(
            processed_dataframe
        )
        processed_dataframe.printSchema()

        hourly_dataframe = build_hourly_summary(
            processed_dataframe
        )

        daily_dataframe = build_daily_summary(
            processed_dataframe
        )

        hotspot_dataframe = build_hotspots(
            processed_dataframe
        )

        alerts_dataframe = build_alerts(
            processed_dataframe
        )

        risk_dataframe = build_risk_table(
            processed_dataframe
        )

        # print(
        #     "Hourly Summary Rows:",
        #     hourly_dataframe.count()
        # )

        hourly_dataframe.printSchema()
        processed_dataframe.printSchema()
        print(processed_dataframe.count())

        write_processed_data(
            processed_dataframe,
            args.processed
        )

        write_analytics(
            hourly_dataframe,
            daily_dataframe,
            hotspot_dataframe,
            alerts_dataframe,
            risk_dataframe,
            args.analytics
        )

        log_spark_execution(
            "PIPELINE",
            "SUCCESS"
        )

        print(
            "Telecom pipeline completed successfully."
        )

    except Exception as error:

        log_spark_execution(
            "PIPELINE",
            "FAILED",
            str(error)
        )

        raise

    finally:

        spark.stop()


if __name__ == "__main__":
    main()