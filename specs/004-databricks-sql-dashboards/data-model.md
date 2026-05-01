# Data Model: Databricks SQL Dashboard Queries

This document defines the SQL queries and output shape for each dashboard widget. All queries read from `f1_catalog.gold` Delta tables produced by `gold_aggregations.py`.

---

## Widget 1: Driver Position Gaps (`gold_driver_gaps`)

**Chart type**: Horizontal bar chart — `car_index` on Y-axis, `gap_to_leader_m` on X-axis

### SQL Query

```sql
-- Widget 1: Live Driver Gaps
-- Shows each car's distance behind the race leader in the most recent 1-second window.
-- The leader (gap = 0) appears at the top. Larger bar = further behind.

WITH latest_window AS (
  SELECT MAX(window.end) AS max_ts
  FROM f1_catalog.gold.gold_driver_gaps
)
SELECT
  CONCAT('Car ', LPAD(CAST(g.car_index AS STRING), 2, '0')) AS car_label,
  g.car_index,
  ROUND(g.gap_to_leader_m, 1)                               AS gap_to_leader_m,
  ROUND(g.segment_distance, 1)                              AS segment_distance_m
FROM f1_catalog.gold.gold_driver_gaps g
JOIN latest_window lw
  ON g.window.end = lw.max_ts
ORDER BY g.gap_to_leader_m ASC
```

### Output Schema

| Column | Type | Notes |
|---|---|---|
| `car_label` | STRING | Display label e.g. "Car 01", "Car 19" |
| `car_index` | INT | Raw car ID (0–19) |
| `gap_to_leader_m` | FLOAT | Distance behind P1 in metres. P1 = 0.0 |
| `segment_distance_m` | FLOAT | Raw distance in this window — useful for debugging |

---

## Widget 2: Vehicle Health Overview (`gold_vehicle_health`)

**Chart type**: Table with conditional formatting

### SQL Query

```sql
-- Widget 2: Vehicle Health Snapshot
-- Shows the latest health state for every car.
-- Ordered by tyre wear descending (most degraded first).

WITH latest_window AS (
  SELECT MAX(last_updated) AS max_ts
  FROM f1_catalog.gold.gold_vehicle_health
)
SELECT
  CONCAT('Car ', LPAD(CAST(h.car_index AS STRING), 2, '0')) AS car_label,
  h.car_index,
  ROUND(h.tyre_wear        * 100, 1)  AS tyre_wear_pct,
  ROUND(h.engine_wear      * 100, 1)  AS engine_wear_pct,
  ROUND(h.front_wing_damage* 100, 1)  AS front_wing_pct,
  ROUND(h.rear_wing_damage * 100, 1)  AS rear_wing_pct,
  ROUND(h.fuel_in_tank,          2)   AS fuel_kg,
  ROUND(h.ers_energy / 4000000.0* 100, 1) AS ers_pct,  -- ERS max = 4 MJ
  CASE WHEN h.drs_activation THEN '✅ ON' ELSE '❌ OFF' END AS drs_status
FROM f1_catalog.gold.gold_vehicle_health h
JOIN latest_window lw
  ON h.last_updated = lw.max_ts
ORDER BY tyre_wear_pct DESC
```

### Output Schema

| Column | Type | Threshold (conditional format) |
|---|---|---|
| `car_label` | STRING | — |
| `tyre_wear_pct` | FLOAT | > 80 → Red, 50–80 → Amber, < 50 → Green |
| `engine_wear_pct` | FLOAT | > 70 → Red |
| `front_wing_pct` | FLOAT | > 50 → Amber |
| `rear_wing_pct` | FLOAT | > 50 → Amber |
| `fuel_kg` | FLOAT | < 10 → Red |
| `ers_pct` | FLOAT | < 20 → Amber |
| `drs_status` | STRING | — |

---

## Widget 3: Tyre Degradation Curve (`gold_tyre_degradation`)

**Chart type**: Line chart — X-axis: `distance_bin_m`, Y-axis: `avg_wear_pct`, Series: `tyre_compound`

### SQL Query

```sql
-- Widget 3: Tyre Degradation Curve
-- Plots average tyre wear % against cumulative distance driven, grouped by compound.
-- Distance is binned into 50m intervals to smooth the curve.

SELECT
  COALESCE(tyre_compound, 'Unknown')              AS tyre_compound,
  FLOOR(distance_traveled_m / 50) * 50            AS distance_bin_m,
  ROUND(AVG(average_wear_pct) * 100, 2)           AS avg_wear_pct
FROM f1_catalog.gold.gold_tyre_degradation
WHERE distance_traveled_m IS NOT NULL
  AND average_wear_pct IS NOT NULL
GROUP BY
  tyre_compound,
  FLOOR(distance_traveled_m / 50) * 50
ORDER BY
  tyre_compound,
  distance_bin_m
```

### Output Schema

| Column | Type | Notes |
|---|---|---|
| `tyre_compound` | STRING | "C1"…"C5" or "Unknown" if null |
| `distance_bin_m` | FLOAT | 50m bucket boundary (0, 50, 100, …) |
| `avg_wear_pct` | FLOAT | Mean wear across all cars in that bin, 0–100 |

---

## Widget 4 (Optional): Live Speed KPI — Single-Value Tile

**Chart type**: Counter / single-value tile

```sql
-- Widget 4: Player Car Live Speed
-- Single-value KPI showing the player car's speed in the latest window.

WITH latest AS (
  SELECT MAX(window.end) AS max_ts
  FROM f1_catalog.gold.gold_distances
)
SELECT
  ROUND(d.avg_speed, 0) AS speed_kmh
FROM f1_catalog.gold.gold_distances d
JOIN latest l ON d.window.end = l.max_ts
WHERE d.car_index = (
  -- Derive player car index from the most recent bronze row
  SELECT m_playerCarIndex
  FROM f1_catalog.bronze.bronze_telemetry
  ORDER BY timestamp DESC
  LIMIT 1
)
```
