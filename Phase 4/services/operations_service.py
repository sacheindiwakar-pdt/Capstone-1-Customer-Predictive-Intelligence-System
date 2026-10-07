import json
import math
from datetime import datetime

from fastapi import HTTPException
from database import get_connection


STATUS_FILE = "D:\\Capstone1\\logs\\pipeline_status.json"


def get_pipeline_status():

    with open(STATUS_FILE, "r") as f:
        status_data = json.load(f)

    conn = get_connection()
    cursor = conn.cursor()

    # Fact row count
    cursor.execute("""
        SELECT COUNT(*)
        FROM fact_network_activity
    """)
    rows_published = cursor.fetchone()[0]

    # Grid count
    cursor.execute("""
        SELECT COUNT(*)
        FROM dim_grid
    """)
    grid_count = cursor.fetchone()[0]

    # Time count
    cursor.execute("""
        SELECT COUNT(*)
        FROM dim_time
    """)
    time_count = cursor.fetchone()[0]

    # Latest AS_OF from warehouse
    cursor.execute("""
        SELECT
            date,
            hour_of_day
        FROM dim_time
        ORDER BY date DESC,
                 hour_of_day DESC
        LIMIT 1
    """)
    latest = cursor.fetchone()

    cursor.close()
    conn.close()

    as_of = datetime.combine(
        latest[0],
        datetime.min.time()
    ).replace(
        hour=latest[1]
    )

    healthy = (
        status_data["status"].upper() == "SUCCESS"
    )

    reasons = []

    if not healthy:
        reasons.append(
            f"Pipeline status is {status_data['status']}"
        )

    return {
        "healthy": healthy,
        "reasons": reasons,

        "run_timestamp": status_data["timestamp"],
        "status": status_data["status"],
        "message": status_data["message"],

        "as_of": as_of.isoformat(),

        "pipeline_metrics": {
            "rows_published": rows_published,
            "grid_count": grid_count,
            "time_count": time_count
        }
    }


def get_grid_location(grid_id: int):

    if grid_id < 1 or grid_id > 10000:
        raise HTTPException(
            status_code=404,
            detail="Grid not found"
        )

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            grid_id,
            centroid_latitude,
            centroid_longitude,
            geometry_reference
        FROM dim_grid
        WHERE grid_id = %s
        """,
        (grid_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Grid not found"
        )

    return {
        "grid_id": row["grid_id"],
        "centroid_latitude": float(
            row["centroid_latitude"]
        ),
        "centroid_longitude": float(
            row["centroid_longitude"]
        ),
        "polygon_reference": row["geometry_reference"]
    }


def get_neighbours(
    grid_id: int,
    limit: int = 5
):

    if grid_id < 1 or grid_id > 10000:
        raise HTTPException(
            status_code=404,
            detail="Grid not found"
        )

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Target grid
    cursor.execute(
        """
        SELECT
            grid_id,
            centroid_latitude,
            centroid_longitude
        FROM dim_grid
        WHERE grid_id = %s
        """,
        (grid_id,)
    )

    target = cursor.fetchone()

    if not target:
        cursor.close()
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Grid not found"
        )

    target_lat = float(
        target["centroid_latitude"]
    )

    target_lon = float(
        target["centroid_longitude"]
    )

    # Remaining grids
    cursor.execute(
        """
        SELECT
            grid_id,
            centroid_latitude,
            centroid_longitude
        FROM dim_grid
        WHERE grid_id <> %s
        """,
        (grid_id,)
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    distances = []

    for row in rows:

        lat = float(
            row["centroid_latitude"]
        )

        lon = float(
            row["centroid_longitude"]
        )

        distance = math.sqrt(
            (target_lat - lat) ** 2 +
            (target_lon - lon) ** 2
        )

        distances.append(
            (
                distance,
                row["grid_id"]
            )
        )

    distances.sort()

    neighbours = [
        grid_id
        for _, grid_id in distances[:limit]
    ]

    return {
        "grid_id": grid_id,
        "neighbours": neighbours
    }