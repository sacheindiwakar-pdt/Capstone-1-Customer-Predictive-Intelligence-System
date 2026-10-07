from fastapi import HTTPException
import sys
import os

sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )
)

from database import get_connection


def get_grid_features(grid_id: int):

    if grid_id < 1 or grid_id > 10000:
        raise HTTPException(
            status_code=404,
            detail="Grid not found"
        )

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT 1
        FROM dim_grid
        WHERE grid_id = %s
        """,
        (grid_id,)
    )

    if not cursor.fetchone():
        cursor.close()
        conn.close()

        raise HTTPException(
            status_code=404,
            detail="Grid not found"
        )

    cursor.execute(
        """
        SELECT
            grid_id,
            feature_timestamp,

            avg_activity,
            activity_growth,
            active_hours,
            peak_ratio,
            variability,
            internet_share

        FROM network_features
        WHERE grid_id = %s
        ORDER BY feature_timestamp DESC
        LIMIT 1
        """,
        (grid_id,)
    )

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Features not available"
        )

    return {
        "grid_id": row["grid_id"],
        "feature_timestamp": row[
            "feature_timestamp"
        ].isoformat(),

        "features": {
            "avg_activity":
                float(row["avg_activity"] or 0),

            "activity_growth":
                float(row["activity_growth"] or 0),

            "active_hours":
                int(row["active_hours"] or 0),

            "peak_ratio":
                float(row["peak_ratio"] or 0),

            "variability":
                float(row["variability"] or 0),

            "internet_share":
                float(row["internet_share"] or 0)
        },
    }