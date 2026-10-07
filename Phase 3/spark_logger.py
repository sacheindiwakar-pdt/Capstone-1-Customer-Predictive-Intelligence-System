from pathlib import Path
from datetime import datetime
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent

LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "spark_execution_log.csv"


def log_spark_execution(
    process_name,
    status,
    message=""
):

    record = pd.DataFrame([
        {
            "timestamp": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "process_name": process_name,
            "status": status,
            "message": message
        }
    ])

    if LOG_FILE.exists():

        record.to_csv(
            LOG_FILE,
            mode="a",
            header=False,
            index=False
        )

    else:

        record.to_csv(
            LOG_FILE,
            index=False
        )

    print(
        f"[{status}] {process_name} - {message}"
    )