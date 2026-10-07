from database import get_connection


def get_effective_as_of(as_of=None):
    if as_of:
        return as_of

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT MAX(date)
        FROM dim_time
    """)

    result = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return result

def get_total_activity(as_of):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
SELECT SUM(f.total_activity)
FROM fact_network_activity f
JOIN dim_time t
    ON f.time_key = t.time_key
WHERE t.date <= %s
"""

    cursor.execute(query, (as_of,))
    result = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return float(result or 0)

def get_active_grids(as_of):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
SELECT COUNT(DISTINCT f.grid_key)
FROM fact_network_activity f
JOIN dim_time t
    ON f.time_key = t.time_key
WHERE t.date <= %s
"""

    cursor.execute(query, (as_of,))
    result = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return int(result or 0)


def get_peak_hour(as_of):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
SELECT
    t.hour_of_day,
    SUM(f.total_activity) AS activity
FROM fact_network_activity f
JOIN dim_time t
    ON f.time_key = t.time_key
WHERE t.date <= %s
GROUP BY t.hour_of_day
ORDER BY activity DESC
LIMIT 1
"""

    cursor.execute(query, (as_of,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return int(result[0]) if result else 0

def get_top_grid(as_of):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
SELECT
    g.grid_id,
    SUM(f.total_activity) AS activity
FROM fact_network_activity f
JOIN dim_time t
    ON f.time_key = t.time_key
JOIN dim_grid g
    ON f.grid_key = g.grid_key
WHERE t.date <= %s
GROUP BY g.grid_id
ORDER BY activity DESC
LIMIT 1
"""

    cursor.execute(query, (as_of,))
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    return int(result[0]) if result else 0

def get_network_summary(as_of=None):

    effective_as_of = get_effective_as_of(as_of)

    return {
        "as_of": str(effective_as_of),
        "total_activity": get_total_activity(effective_as_of),
        "active_grids": get_active_grids(effective_as_of),
        "peak_hour": get_peak_hour(effective_as_of),
        "top_grid": get_top_grid(effective_as_of)
    }
