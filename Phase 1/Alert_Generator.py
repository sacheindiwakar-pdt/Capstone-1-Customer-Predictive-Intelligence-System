import pandas as pd
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

class NetworkAlertGenerator:
    def __init__(
        self,
        hourly_grid_summary,
        activity_floor=None,
        high_threshold=1.50,
        spike_threshold=1.50,
        drop_threshold=0.50
    ):
        self.df = hourly_grid_summary.copy()

        # Thresholds
        self.high_threshold = high_threshold
        self.spike_threshold = spike_threshold
        self.drop_threshold = drop_threshold

        # Activity floor
        self.activity_floor = activity_floor

        self.alerts = None

    # -----------------------------------------------------
    # 1. Validate Input
    # -----------------------------------------------------

    def validate_input(self):

        required_columns = [
            "timestamp",
            "grid_id",
            "total_activity"
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

        # Make sure timestamp is datetime
        self.df["timestamp"] = pd.to_datetime(
            self.df["timestamp"],
            errors="coerce"
        )

        if self.df["timestamp"].isna().any():

            raise ValueError(
                "Invalid timestamp values found."
            )

        # Check grid/hour grain
        duplicate_count = (
            self.df
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
                f"Found {duplicate_count} "
                "duplicate grid/hour records."
            )

        # Check negative activity
        if (
            self.df["total_activity"] < 0
        ).any():

            raise ValueError(
                "Negative total_activity detected."
            )

        logger.info(
            "Input validation passed."
        )

        return True

    # -----------------------------------------------------
    # 2. Calculate Activity Floor
    # -----------------------------------------------------

    def calculate_activity_floor(self):

        if self.activity_floor is not None:

            logger.info(
                f"Using configured activity floor: "
                f"{self.activity_floor}"
            )

            return self.activity_floor

        # Daily total activity per grid
        daily_totals = (
            self.df
            .groupby("grid_id")["total_activity"]
            .sum()
        )

        # Choose the 10th percentile as the floor
        self.activity_floor = float(
            daily_totals.quantile(0.10)
        )

        logger.info(
            f"Calculated activity floor: "
            f"{self.activity_floor:.2f}"
        )

        return self.activity_floor

    # -----------------------------------------------------
    # 3. Calculate Within-Day Baseline
    # -----------------------------------------------------

    def calculate_baseline(self):

        df = self.df.copy()

        # Sort chronologically
        df = df.sort_values(
            [
                "grid_id",
                "timestamp"
            ]
        ).reset_index(drop=True)

        # Within-day median excluding current hour
        #
        # For every grid:
        # baseline = median of the OTHER hours
        #
        # The current hour is removed before calculating
        # the median.

        def calculate_excluding_current(values):

            result = []

            for i in range(len(values)):

                other_values = values[
                    values.index != values.index[i]
                ]

                if len(other_values) == 0:

                    result.append(float("nan"))

                else:

                    result.append(
                        other_values.median()
                    )

            return pd.Series(
                result,
                index=values.index
            )

        df["baseline_activity"] = (
            df
            .groupby("grid_id")["total_activity"]
            .transform(
                calculate_excluding_current
            )
        )

        self.df = df

        logger.info(
            "Within-day baseline calculated."
        )

        return self.df

    # -----------------------------------------------------
    # 4. Calculate Previous Hour Activity
    # -----------------------------------------------------

    def calculate_previous_activity(self):

        df = self.df.copy()

        df["previous_activity"] = (
            df
            .groupby("grid_id")["total_activity"]
            .shift(1)
        )

        self.df = df

        return self.df

    # -----------------------------------------------------
    # 5. Generate Alerts
    # -----------------------------------------------------

    def generate_alerts(self):

        df = self.df.copy()

        alerts = []

        for _, row in df.iterrows():

            current_activity = (
                row["total_activity"]
            )

            baseline_activity = (
                row["baseline_activity"]
            )

            previous_activity = (
                row["previous_activity"]
            )

            grid_id = int(
                row["grid_id"]
            )

            timestamp = row["timestamp"]

            # Skip if baseline is unavailable
            if pd.isna(baseline_activity):

                continue

            # Apply activity floor
            if (
                baseline_activity
                < self.activity_floor
            ):

                continue

            # ---------------------------------------------
            # Rule 1: HIGH_ACTIVITY
            # ---------------------------------------------

            if (
                current_activity
                >= baseline_activity
                * self.high_threshold
            ):

                alerts.append({

                    "grid_id": grid_id,

                    "timestamp": timestamp,

                    "alert_type":
                        "HIGH_ACTIVITY",

                    "current_activity":
                        current_activity,

                    "baseline_activity":
                        baseline_activity,

                    "reason":
                        (
                            "HIGH_ACTIVITY: "
                            f"current activity "
                            f"{current_activity:.2f} is "
                            f"{current_activity / baseline_activity:.2f}x "
                            f"the baseline "
                            f"{baseline_activity:.2f}."
                        )
                })

            # ---------------------------------------------
            # Rule 2: ACTIVITY_SPIKE
            # ---------------------------------------------

            if (
                pd.notna(previous_activity)
                and previous_activity > 0
                and current_activity
                >= previous_activity
                * self.spike_threshold
            ):

                alerts.append({

                    "grid_id": grid_id,

                    "timestamp": timestamp,

                    "alert_type":
                        "ACTIVITY_SPIKE",

                    "current_activity":
                        current_activity,

                    "baseline_activity":
                        baseline_activity,

                    "reason":
                        (
                            "ACTIVITY_SPIKE: "
                            f"current activity "
                            f"{current_activity:.2f} increased "
                            f"sharply from the previous hour "
                            f"{previous_activity:.2f}."
                        )
                })

            # ---------------------------------------------
            # Rule 3: ACTIVITY_DROP
            # ---------------------------------------------

            if (
                current_activity
                <= baseline_activity
                * self.drop_threshold
            ):

                alerts.append({

                    "grid_id": grid_id,

                    "timestamp": timestamp,

                    "alert_type":
                        "ACTIVITY_DROP",

                    "current_activity":
                        current_activity,

                    "baseline_activity":
                        baseline_activity,

                    "reason":
                        (
                            "ACTIVITY_DROP: "
                            f"current activity "
                            f"{current_activity:.2f} is "
                            f"{current_activity / baseline_activity:.2f}x "
                            f"the baseline "
                            f"{baseline_activity:.2f}."
                        )
                })

        self.alerts = pd.DataFrame(
            alerts,
            columns=[
                "grid_id",
                "timestamp",
                "alert_type",
                "current_activity",
                "baseline_activity",
                "reason"
            ]
        )

        logger.info(
            f"Generated {len(self.alerts)} alerts."
        )

        return self.alerts

    # -----------------------------------------------------
    # 6. Generate Summary
    # -----------------------------------------------------

    def generate_summary(self):

        if self.alerts is None:

            raise ValueError(
                "Run generate_alerts() first."
            )

        total_grid_hours = len(
            self.df
        )

        total_alerts = len(
            self.alerts
        )

        # Number of grid/hour combinations that alerted
        unique_alerted_grid_hours = (
            self.alerts[
                [
                    "grid_id",
                    "timestamp"
                ]
            ]
            .drop_duplicates()
            .shape[0]
        )

        if total_grid_hours > 0:

            alert_proportion = (
                unique_alerted_grid_hours
                / total_grid_hours
            )

        else:

            alert_proportion = 0

        alerts_by_type = (
            self.alerts[
                "alert_type"
            ]
            .value_counts()
        )

        top_10_grids = (
            self.alerts
            .groupby("grid_id")
            .size()
            .sort_values(
                ascending=False
            )
            .head(10)
        )

        summary = {

            "total_grid_hours":
                total_grid_hours,

            "total_alerts":
                total_alerts,

            "alerted_grid_hours":
                unique_alerted_grid_hours,

            "alert_proportion":
                alert_proportion,

            "alerts_by_type":
                alerts_by_type.to_dict(),

            "top_10_grids":
                top_10_grids.to_dict()
        }

        return summary

    # -----------------------------------------------------
    # 7. Export Alerts
    # -----------------------------------------------------

    def export_alerts(
        self,
        output_dir="outputs"
    ):

        if self.alerts is None:

            raise ValueError(
                "Run generate_alerts() first."
            )

        output_path = Path(
            output_dir
        )

        output_path.mkdir(
            parents=True,
            exist_ok=True
        )

        output_file = (
            output_path
            / "network_alerts.csv"
        )

        self.alerts.to_csv(
            output_file,
            index=False
        )

        logger.info(
            f"Alerts saved to: {output_file}"
        )

        return output_file

    # -----------------------------------------------------
    # 8. Run Complete NP3 Pipeline
    # -----------------------------------------------------

    def run(self):

        logger.info(
            "Starting NP3 alert generation."
        )

        self.validate_input()

        self.calculate_activity_floor()

        self.calculate_baseline()

        self.calculate_previous_activity()

        self.generate_alerts()

        logger.info(
            "NP3 alert generation completed."
        )

        return self.alerts