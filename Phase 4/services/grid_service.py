from datetime import datetime, timedelta
from fastapi import HTTPException

from database import get_connection


def get_default_as_of():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, hour_of_day
        FROM dim_time
        ORDER BY date DESC, hour_of_day DESC
        LIMIT 1
    """)

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if not row:
        raise Exception("Unable to determine AS_OF")

    return datetime.combine(
        row[0],
        datetime.min.time()
    ).replace(hour=row[1])


def validate_grid(grid_id):
    if grid_id < 1 or grid_id > 10000:
        raise HTTPException(
            status_code=404,
            detail="Grid not found"
        )

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT 1 FROM dim_grid WHERE grid_id = %s",
        (grid_id,)
    )

    exists = cursor.fetchone()

    cursor.close()
    conn.close()

    if not exists:
        raise HTTPException(
            status_code=404,
            detail="Grid not found"
        )


def get_grid_activity(
    grid_id,
    date=None,
    hour=None,
    as_of=None
):
    validate_grid(grid_id)

    if as_of:

        if len(as_of) == 10:
            effective_as_of = datetime.strptime(
            as_of,
            "%Y-%m-%d"
        ).replace(hour=23)

        elif "T" in as_of:
            effective_as_of = datetime.fromisoformat(as_of)

        else:
            effective_as_of = datetime.strptime(
            as_of,
            "%Y-%m-%d %H:%M:%S"
        )

    elif date and hour is not None:

        effective_as_of = datetime.strptime(
            f"{date} {hour}",
            "%Y-%m-%d %H"
        )

    else:

        effective_as_of = get_default_as_of()

    window_start = effective_as_of - timedelta(hours=23)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        t.date,
        t.hour_of_day,
        f.total_sms,
        f.total_calls,
        f.internet_activity,
        f.total_activity
    FROM fact_network_activity f
    JOIN dim_time t
        ON f.time_key = t.time_key
    JOIN dim_grid g
        ON f.grid_key = g.grid_key
    WHERE g.grid_id = %s
      AND TIMESTAMP(t.date,
            MAKETIME(t.hour_of_day,0,0))
          BETWEEN %s AND %s
    ORDER BY t.date, t.hour_of_day
    """

    cursor.execute(
        query,
        (
            grid_id,
            window_start,
            effective_as_of
        )
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    activity_series = []

    total_activity_sum = 0
    peak_activity = 0

    for row in rows:

        timestamp = datetime.combine(
            row["date"],
            datetime.min.time()
        ).replace(
            hour=row["hour_of_day"]
        )

        activity = float(row["total_activity"] or 0)

        total_activity_sum += activity

        if activity > peak_activity:
            peak_activity = activity

        activity_series.append(
            {
                "timestamp": timestamp.isoformat(),
                "total_sms": float(row["total_sms"] or 0),
                "total_calls": float(row["total_calls"] or 0),
                "internet_activity": float(
                    row["internet_activity"] or 0
                ),
                "total_activity": activity
            }
        )

    hours_returned = len(activity_series)

    avg_hourly_activity = (
        total_activity_sum / hours_returned
        if hours_returned > 0
        else 0
    )

    return {
        "grid_id": grid_id,
        "as_of": effective_as_of.isoformat(),
        "hours_returned": hours_returned,
        "summary": {
            "total_24h_activity": total_activity_sum,
            "avg_hourly_activity": avg_hourly_activity,
            "peak_activity": peak_activity
        },
        "activity_series": activity_series
    }