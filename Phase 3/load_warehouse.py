print("Step 1: Starting script")

import pandas as pd
print("Step 2: Pandas loaded")

import geopandas as gpd
print("Step 3: GeoPandas loaded")

import mysql.connector
print("Step 4: MySQL connector loaded")

print("Step 5: Connecting to MySQL...")


# =====================================================
# MYSQL CONNECTION
# =====================================================

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="telecom_warehouse"
)

print("Step 6: Connected to MySQL.")

cursor = conn.cursor()


# =====================================================
# LOAD DIM_GRID
# =====================================================

print("Loading dim_grid...")

gdf = gpd.read_file(
    r"D:\Capstone1\data\reference\milano-grid.geojson"
)

grid_records = []

for _, row in gdf.iterrows():

    grid_id = int(row["cellId"])

    centroid = row.geometry.centroid

    grid_records.append(
        (
            grid_id,
            float(centroid.y),
            float(centroid.x),
            f"GRID_{grid_id}"
        )
    )

cursor.executemany(
    """
    INSERT IGNORE INTO dim_grid
    (
        grid_id,
        centroid_latitude,
        centroid_longitude,
        geometry_reference
    )
    VALUES (%s,%s,%s,%s)
    """,
    grid_records
)

conn.commit()

print(
    f"dim_grid loaded: {len(grid_records)}"
)


# =====================================================
# READ ANALYTICS OUTPUT
# =====================================================

print("Loading analytics output...")

activity = pd.read_parquet(
    r"D:\Capstone1\data\analytics\hourly_grid_summary"
)

print("Columns Found:")
print(activity.columns.tolist())

print(
    f"Analytics Rows: {len(activity)}"
)


# =====================================================
# LOAD DIM_TIME
# =====================================================

print("Loading dim_time...")

unique_times = (
    activity[
        [
            "event_date",
            "hour_of_day",
            "day_of_week"
        ]
    ]
    .drop_duplicates()
)

time_records = []

for _, row in unique_times.iterrows():

    time_records.append(
        (
            str(row["event_date"]),
            int(row["hour_of_day"]),
            int(row["day_of_week"])
        )
    )

cursor.executemany(
    """
    INSERT IGNORE INTO dim_time
    (
        date,
        hour_of_day,
        day_of_week
    )
    VALUES
    (
        %s,
        %s,
        %s
    )
    """,
    time_records
)

conn.commit()

print(
    f"dim_time loaded: {len(time_records)}"
)


# =====================================================
# BUILD LOOKUPS
# =====================================================

print("Building dimension lookups...")

cursor.execute(
    """
    SELECT
        time_key,
        date,
        hour_of_day,
        day_of_week
    FROM dim_time
    """
)

time_lookup = {}

for time_key, date_value, hour_of_day, day_of_week in cursor.fetchall():

    time_lookup[
        (
            str(date_value),
            int(hour_of_day),
            int(day_of_week)
        )
    ] = int(time_key)

cursor.execute(
    """
    SELECT
        grid_key,
        grid_id
    FROM dim_grid
    """
)

grid_lookup = {}

for grid_key, grid_id in cursor.fetchall():

    grid_lookup[
        int(grid_id)
    ] = int(grid_key)

print(
    f"Time Lookups: {len(time_lookup)}"
)

print(
    f"Grid Lookups: {len(grid_lookup)}"
)


# =====================================================
# PREPARE FACT RECORDS
# =====================================================

print("Preparing fact records...")

fact_records = []

for _, row in activity.iterrows():

    grid_id = int(
        row["CellID"]
    )

    if grid_id not in grid_lookup:

        continue

    lookup_key = (
        str(row["event_date"]),
        int(row["hour_of_day"]),
        int(row["day_of_week"])
    )

    if lookup_key not in time_lookup:

        continue

    fact_records.append(
        (
            time_lookup[lookup_key],
            grid_lookup[grid_id],
            float(row["total_sms"]),
            float(row["total_calls"]),
            float(row["internet_activity"]),
            float(row["total_activity"])
        )
    )

print(
    f"Fact Records Prepared: {len(fact_records)}"
)


# =====================================================
# LOAD FACT TABLE
# =====================================================

print("Loading fact_network_activity...")

batch_size = 10000

for start in range(
    0,
    len(fact_records),
    batch_size
):

    end = min(
        start + batch_size,
        len(fact_records)
    )

    batch = fact_records[start:end]

    cursor.executemany(
        """
        INSERT INTO fact_network_activity
        (
            time_key,
            grid_key,
            total_sms,
            total_calls,
            internet_activity,
            total_activity
        )
        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )
        """,
        batch
    )

    print("fact_network_activity loaded Successfully.")
    conn.commit()