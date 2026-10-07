from datetime import datetime
import pandas as pd
from database import get_connection


ALERT_FILE = "network_alerts.csv"


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

    return datetime.combine(
        row[0],
        datetime.min.time()
    ).replace(hour=row[1])


def resolve_as_of(as_of=None):

    if as_of:

        if len(as_of) == 10:
            return datetime.strptime(
                as_of,
                "%Y-%m-%d"
            ).replace(hour=23)

        return datetime.fromisoformat(
            as_of.replace(" ", "T")
        )

    return get_default_as_of()


def get_hotspots(limit=10, as_of=None):

    effective_as_of = resolve_as_of(as_of)

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    SELECT
        g.grid_id,
        t.date,
        t.hour_of_day,
        f.total_sms,
        f.total_calls,
        f.internet_activity,
        f.total_activity
    FROM fact_network_activity f
    JOIN dim_grid g
        ON f.grid_key = g.grid_key
    JOIN dim_time t
        ON f.time_key = t.time_key
    WHERE t.date = %s
      AND t.hour_of_day = %s
    ORDER BY f.total_activity DESC
    LIMIT %s
    """

    cursor.execute(
        query,
        (
            effective_as_of.date(),
            effective_as_of.hour,
            limit
        )
    )

    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    hotspots = []

    for row in rows:

        ts = datetime.combine(
            row["date"],
            datetime.min.time()
        ).replace(
            hour=row["hour_of_day"]
        )

        hotspots.append(
            {
                "grid_id": row["grid_id"],
                "hourly_timestamp": ts.isoformat(),
                "total_sms": float(row["total_sms"] or 0),
                "total_calls": float(row["total_calls"] or 0),
                "internet_activity": float(
                    row["internet_activity"] or 0
                ),
                "total_activity": float(
                    row["total_activity"] or 0
                ),
                "status": "HOTSPOT",
                "risk": {
                    "rule_score": None,
                    "ml_score": None,
                    "risk_level": None
                }
            }
        )

    return {
        "as_of": effective_as_of.isoformat(),
        "count": len(hotspots),
        "hotspots": hotspots
    }


def get_alerts(
    limit=10,
    severity=None,
    as_of=None
):

    effective_as_of = resolve_as_of(as_of)

    df = pd.read_csv(ALERT_FILE)

    df["timestamp"] = pd.to_datetime(
        df["timestamp"]
    )

    df = df[
        df["timestamp"] <= effective_as_of
    ]

    severity_map = {
        "HIGH_ACTIVITY": "HIGH",
        "ACTIVITY_SPIKE": "MEDIUM",
        "ACTIVITY_DROP": "LOW"
    }

    df["severity"] = df["alert_type"].map(
        severity_map
    )

    if severity:
        df = df[
            df["severity"].str.upper()
            == severity.upper()
        ]

    df = df.sort_values(
        "timestamp",
        ascending=False
    ).head(limit)

    alerts = []

    for _, row in df.iterrows():

        alerts.append(
            {
                "grid_id": int(row["grid_id"]),
                "hourly_timestamp": row[
                    "timestamp"
                ].isoformat(),
                "alert_type": row["alert_type"],
                "severity": row["severity"],
                "current_activity": float(
                    row["current_activity"]
                ),
                "baseline_activity": float(
                    row["baseline_activity"]
                ),
                "reason": row["reason"],
                "risk": {
                    "rule_score": 1.0,
                    "ml_score": None,
                    "risk_level": row["severity"]
                }
            }
        )

    return {
        "as_of": effective_as_of.isoformat(),
        "count": len(alerts),
        "alerts": alerts
    }