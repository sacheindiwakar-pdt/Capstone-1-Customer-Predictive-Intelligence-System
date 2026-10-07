from pathlib import Path
from datetime import datetime
import shutil
import pandas as pd


# ==========================================================
# PATHS
# ==========================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

DATA_DIR = PROJECT_ROOT / "data"

LANDING_DIR = DATA_DIR / "landing"
RAW_DIR = DATA_DIR / "raw"
REJECTED_DIR = DATA_DIR / "rejected"
REFERENCE_DIR = DATA_DIR / "reference"

LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "ingestion_log.csv"


# ==========================================================
# EXPECTED SCHEMA (MILANO DATASET)
# ==========================================================

REQUIRED_COLUMNS = [
    "datetime",
    "CellID",
    "countrycode",
    "smsin",
    "smsout",
    "callin",
    "callout",
    "internet"
]

ACTIVITY_COLUMNS = [
    "smsin",
    "smsout",
    "callin",
    "callout",
    "internet"
]


# ==========================================================
# DIRECTORY SETUP
# ==========================================================

def ensure_directories():

    for directory in [
        LANDING_DIR,
        RAW_DIR,
        REJECTED_DIR,
        REFERENCE_DIR,
        LOG_DIR
    ]:
        directory.mkdir(
            parents=True,
            exist_ok=True
        )


# ==========================================================
# DETECT FILES
# ==========================================================

def detect_files():

    ensure_directories()

    files = sorted(
        LANDING_DIR.glob(
            "sms-call-internet-mi-*.csv"
        )
    )

    print(f"Detected {len(files)} file(s)")

    return files


# ==========================================================
# SCHEMA VALIDATION
# ==========================================================

def validate_schema(file_path):

    try:

        df = pd.read_csv(file_path)

        missing_columns = [

            col

            for col in REQUIRED_COLUMNS

            if col not in df.columns

        ]

        if missing_columns:

            return {
                "valid": False,
                "row_count": len(df),
                "reason":
                    "Missing required column(s): "
                    + ", ".join(missing_columns)
            }

        return {
            "valid": True,
            "row_count": len(df),
            "reason": "Schema validation passed"
        }

    except Exception as exc:

        return {
            "valid": False,
            "row_count": 0,
            "reason": f"Unable to read CSV: {exc}"
        }


# ==========================================================
# QUALITY VALIDATION
# ==========================================================

def validate_minimum_quality(file_path):

    try:

        df = pd.read_csv(file_path)

        row_count = len(df)

        if row_count == 0:

            return {
                "valid": False,
                "row_count": 0,
                "reason": "File contains zero rows"
            }

        # ----------------------------------
        # Timestamp Validation
        # ----------------------------------

        timestamps = pd.to_datetime(
            df["datetime"],
            errors="coerce"
        )

        invalid_timestamps = timestamps.isna().sum()

        if invalid_timestamps > 0:

            return {
                "valid": False,
                "row_count": row_count,
                "reason":
                    f"Malformed timestamp values: "
                    f"{invalid_timestamps}"
            }

        # ----------------------------------
        # Activity Columns
        # ----------------------------------

        for column in ACTIVITY_COLUMNS:

            numeric_values = pd.to_numeric(
                df[column],
                errors="coerce"
            )

            negative_values = (
                numeric_values < 0
            ).sum()

            if negative_values > 0:

                return {
                    "valid": False,
                    "row_count": row_count,
                    "reason":
                        f"Negative values found in "
                        f"{column}: {negative_values}"
                }

        return {
            "valid": True,
            "row_count": row_count,
            "reason": "Quality validation passed"
        }

    except Exception as exc:

        return {
            "valid": False,
            "row_count": 0,
            "reason": f"Validation error: {exc}"
        }


# ==========================================================
# ROUTE FILE
# ==========================================================

def route_file(
    file_path,
    valid
):

    if valid:

        destination = (
            RAW_DIR /
            file_path.name
        )

        status = "ACCEPTED"

    else:

        destination = (
            REJECTED_DIR /
            file_path.name
        )

        status = "REJECTED"

    shutil.move(
        str(file_path),
        str(destination)
    )

    return status, destination


# ==========================================================
# LOG METADATA
# ==========================================================

def write_ingestion_metadata(
    filename,
    status,
    row_count,
    reason
):

    record = pd.DataFrame([
        {
            "filename": filename,
            "status": status,
            "row_count": row_count,
            "reason": reason,
            "processed_at":
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                )
        }
    ])

    if LOG_FILE.exists():

        record.to_csv(
            LOG_FILE,
            mode="a",
            index=False,
            header=False
        )

    else:

        record.to_csv(
            LOG_FILE,
            index=False
        )


# ==========================================================
# PROCESS FILE
# ==========================================================

def process_file(file_path):

    print(f"\nProcessing {file_path.name}")

    schema_result = validate_schema(
        file_path
    )

    if not schema_result["valid"]:

        status, _ = route_file(
            file_path,
            False
        )

        write_ingestion_metadata(
            file_path.name,
            status,
            schema_result["row_count"],
            schema_result["reason"]
        )

        return

    quality_result = (
        validate_minimum_quality(
            file_path
        )
    )

    if not quality_result["valid"]:

        status, _ = route_file(
            file_path,
            False
        )

        write_ingestion_metadata(
            file_path.name,
            status,
            quality_result["row_count"],
            quality_result["reason"]
        )

        return

    status, _ = route_file(
        file_path,
        True
    )

    write_ingestion_metadata(
        file_path.name,
        status,
        quality_result["row_count"],
        "Passed validation"
    )


# ==========================================================
# PROCESS LANDING
# ==========================================================

def process_landing():

    files = detect_files()

    for file_path in files:

        process_file(file_path)

    print("\nIngestion completed.")


# ==========================================================
# LOCAL TEST
# ==========================================================

if __name__ == "__main__":

    process_landing()