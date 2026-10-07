import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class UsageProcessor:

    def __init__(self, file_path=None, dataframe=None):
        self.file_path = file_path
        self.df = dataframe.copy() if dataframe is not None else None
        self.raw_df = None
        self.hourly_grid_summary = None
        self.daily_summary = None
        self.grid_summary = None
        self.kpis = None
        self.input_rows = 0
        self.rejected_rows = 0
        self.nulls_handled = 0

    def load_data(self):
        if self.df is not None:
            self.raw_df = self.df.copy()
            logger.info(
                "DataFrame supplied directly."
            )
        elif self.file_path is not None:
            self.raw_df = pd.read_csv(
                self.file_path
            )
            logger.info(
                f"File loaded: {self.file_path}"
            )
        else:
            raise ValueError(
                "Either file_path or dataframe must be provided."
            )
        self.input_rows = len(self.raw_df)
        logger.info(
            f"Input rows: {self.input_rows}"
        )
        return self.raw_df
 
    def canonicalize_columns(self):
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
        self.df = self.raw_df.rename(
            columns=column_mapping
        ).copy()
        required_columns = [
            "timestamp",
            "grid_id",
            "country_code",
            "sms_in",
            "sms_out",
            "call_in",
            "call_out",
            "internet_activity"
        ]
        missing_columns = [
            column
            for column in required_columns
            if column not in self.df.columns
        ]
        if missing_columns:
            raise ValueError(
                f"Missing required columns: {missing_columns}"
            )
        logger.info(
            "Columns canonicalized successfully."
        )
        return self.df

    def clean_data(self):
        df = self.df.copy()
        df["timestamp"] = pd.to_datetime(
            df["timestamp"],
            errors="coerce"
        )
        numeric_columns = [
            "grid_id",
            "country_code",
            "sms_in",
            "sms_out",
            "call_in",
            "call_out",
            "internet_activity"
        ]
        for column in numeric_columns:
            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            )
        activity_columns = [
            "sms_in",
            "sms_out",
            "call_in",
            "call_out",
            "internet_activity"
        ]
        invalid_key_rows = (
            df["timestamp"].isna()
            | df["grid_id"].isna()
        )
        negative_activity_rows = (
            df[activity_columns]
            .lt(0)
            .any(axis=1)
        )
        rejected_rows = (
            invalid_key_rows
            | negative_activity_rows
        )
        self.rejected_rows = int(
            rejected_rows.sum()
        )
        df = df[
            ~rejected_rows
        ].copy()
        self.nulls_handled = int(
            df[activity_columns]
            .isna()
            .sum()
            .sum()
        )
        df[activity_columns] = (
            df[activity_columns]
            .fillna(0)
        )
        duplicate_count = df.duplicated().sum()
        if duplicate_count > 0:
            logger.warning(
                f"Removing {duplicate_count} duplicate rows."
            )
            df = df.drop_duplicates()
        self.df = df
        logger.info(
            f"Rejected rows: {self.rejected_rows}"
        )
        logger.info(
            f"Activity nulls handled: {self.nulls_handled}"
        )
        logger.info(
            f"Rows after cleaning: {len(self.df)}"
        )
        return self.df
    
    def derive_time_features(self):
        self.df["date"] = (
            self.df["timestamp"].dt.date
        )
        self.df["hour"] = (
            self.df["timestamp"].dt.hour
        )
        self.df["day_of_week"] = (
            self.df["timestamp"].dt.day_name()
        )
        logger.info(
            "Time features derived."
        )
        return self.df
    
    def aggregate_to_grid_time(self):
        activity_columns = [
            "sms_in",
            "sms_out",
            "call_in",
            "call_out",
            "internet_activity"
        ]
        self.hourly_grid_summary = (
            self.df
            .groupby(
                ["timestamp", "grid_id"],
                as_index=False
            )[activity_columns]
            .sum()
        )
        duplicate_count = (
            self.hourly_grid_summary
            .duplicated(
                subset=[
                    "grid_id",
                    "timestamp"
                ]
            )
            .sum()
        )
        if duplicate_count != 0:
            raise ValueError(
                "Duplicate grid/hour records detected."
            )
        if len(self.hourly_grid_summary) >= len(self.df):
            raise ValueError(
                "Aggregation did not reduce row count."
            )
        logger.info(
            f"Rows before aggregation: {len(self.df)}"
        )
        logger.info(
            f"Rows after aggregation: "
            f"{len(self.hourly_grid_summary)}"
        )
        logger.info(
            "Grid/hour aggregation completed."
        )
        return self.hourly_grid_summary

    def derive_activity_features(self):
        df = self.hourly_grid_summary.copy()
        df["total_sms"] = (
            df["sms_in"]
            + df["sms_out"]
        )
        df["total_calls"] = (
            df["call_in"]
            + df["call_out"]
        )
        df["total_activity"] = (
            df["total_sms"]
            + df["total_calls"]
            + df["internet_activity"]
        )
        df["date"] = (
            df["timestamp"].dt.date
        )
        df["hour"] = (
            df["timestamp"].dt.hour
        )
        df["day_of_week"] = (
            df["timestamp"].dt.day_name()
        )
        self.hourly_grid_summary = df
        logger.info(
            "Activity features derived."
        )
        return self.hourly_grid_summary

    def compute_kpis(self):
        df = self.hourly_grid_summary.copy()
        self.daily_summary = (
            df
            .groupby(
                ["date", "grid_id"],
                as_index=False
            )["total_activity"]
            .sum()
            .rename(
                columns={
                    "total_activity":
                    "daily_activity"
                }
            )
        )
        self.grid_summary = (
            df
            .groupby(
                "grid_id",
                as_index=False
            )
            .agg(
                total_activity=(
                    "total_activity",
                    "sum"
                ),
                average_activity=(
                    "total_activity",
                    "mean"
                ),
                peak_activity=(
                    "total_activity",
                    "max"
                )
            )
            .sort_values(
                "total_activity",
                ascending=False
            )
        )
        hourly_activity = (
            df
            .groupby("timestamp")["total_activity"]
            .sum()
            .sort_values(
                ascending=False
            )
        )
        total_activity = (
            df["total_activity"].sum()
        )
        total_internet = (
            df["internet_activity"].sum()
        )
        if total_activity != 0:
            internet_share = (
                total_internet
                / total_activity
            )
        else:
            internet_share = 0
        self.kpis = {
            "total_activity":
                total_activity,
            "peak_hour":
                hourly_activity.index[0],
            "peak_activity":
                hourly_activity.iloc[0],
            "top_grid":
                int(
                    self.grid_summary
                    .iloc[0]["grid_id"]
                ),
            "internet_share":
                internet_share,
            "active_grids":
                df["grid_id"].nunique()
        }
        logger.info(
            "KPIs calculated successfully."
        )
        return self.kpis

    def export_summary(
        self,
        output_dir="outputs"
    ):
        output_path = Path(
            output_dir
        )
        output_path.mkdir(
            parents=True,
            exist_ok=True
        )
        hourly_file = (
            output_path
            / "hourly_grid_summary.csv"
        )
        self.hourly_grid_summary.to_csv(
            hourly_file,
            index=False
        )
        daily_file = (
            output_path
            / "daily_summary.csv"
        )
        self.daily_summary.to_csv(
            daily_file,
            index=False
        )
        grid_file = (
            output_path
            / "grid_summary.csv"
        )
        self.grid_summary.to_csv(
            grid_file,
            index=False
        )
        logger.info(
            f"Hourly summary saved: {hourly_file}"
        )
        logger.info(
            f"Daily summary saved: {daily_file}"
        )
        logger.info(
            f"Grid summary saved: {grid_file}"
        )
        return output_path
    def run(self):
        logger.info(
            "Starting UsageProcessor pipeline."
        )
        self.load_data()
        self.canonicalize_columns()
        self.clean_data()
        self.derive_time_features()
        self.aggregate_to_grid_time()
        self.derive_activity_features()
        self.compute_kpis()
        logger.info(
            "UsageProcessor pipeline completed."
        )
        return self.hourly_grid_summary