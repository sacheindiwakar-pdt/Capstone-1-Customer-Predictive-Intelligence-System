# src/pipeline_status.py

import json
from pathlib import Path
from datetime import datetime


PROJECT_ROOT = Path(__file__).resolve().parent.parent

STATUS_FILE = PROJECT_ROOT / "logs" / "pipeline_status.json"


def write_status(
    status,
    message
):

    record = {
        "timestamp": datetime.now().strftime(
            "%Y-%m-%d %H:%M:%S"
        ),
        "status": status,
        "message": message
    }

    with open(
        STATUS_FILE,
        "w"
    ) as f:

        json.dump(
            record,
            f,
            indent=4
        )