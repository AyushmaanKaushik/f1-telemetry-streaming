-- =============================================================================
-- F1 Telemetry Dashboard — Widget SQL Queries
-- =============================================================================
-- All queries follow the "latest-window" pattern: they filter Gold tables to
-- the single most recent 1-second tumbling window so that widgets show current
-- state rather than a historical aggregate across all windows.
--
-- Source tables (all in f1_catalog.gold):
--   gold_driver_gaps        → Widget 1: Driver Position Gaps
--   gold_vehicle_health     → Widget 2: Vehicle Health Overview
--   gold_tyre_degradation   → Widget 3: Tyre Degradation Curve
--   gold_distances          → Widget 4: Player Speed KPI
-- =============================================================================


-- -----------------------------------------------------------------------------
-- Widget 1: Live Driver Position Gaps (bar chart)
-- X-axis: gap_to_leader_m   Y-axis: car_label
-- Shows each car's distance behind the race leader in the most recent window.
-- Leader always has gap = 0 and appears at the top (ascending sort).
-- -----------------------------------------------------------------------------
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
ORDER BY g.gap_to_leader_m ASC;


-- -----------------------------------------------------------------------------
-- Widget 2: Vehicle Health Overview (table with conditional formatting)
-- One row per car, ordered by tyre wear descending (most degraded first).
-- Conditional formatting thresholds (configure in dashboard widget settings):
--   tyre_wear_pct  > 80      → Red   | 50–80 → Amber | < 50 → Green
--   engine_wear_pct > 70     → Red
--   fuel_kg < 10             → Red
--   ers_pct < 20             → Amber
-- -----------------------------------------------------------------------------
WITH latest_window AS (
  SELECT MAX(last_updated) AS max_ts
  FROM f1_catalog.gold.gold_vehicle_health
)
SELECT
  CONCAT('Car ', LPAD(CAST(h.car_index AS STRING), 2, '0')) AS car_label,
  h.car_index,
  ROUND(h.tyre_wear         * 100, 1)       AS tyre_wear_pct,
  ROUND(h.engine_wear       * 100, 1)       AS engine_wear_pct,
  ROUND(h.front_wing_damage * 100, 1)       AS front_wing_pct,
  ROUND(h.rear_wing_damage  * 100, 1)       AS rear_wing_pct,
  ROUND(h.fuel_in_tank,           2)        AS fuel_kg,
  ROUND(h.ers_energy / 4000000.0 * 100, 1) AS ers_pct,
  CASE WHEN h.drs_activation THEN '✅ ON' ELSE '❌ OFF' END AS drs_status
FROM f1_catalog.gold.gold_vehicle_health h
JOIN latest_window lw
  ON h.last_updated = lw.max_ts
ORDER BY tyre_wear_pct DESC;


-- -----------------------------------------------------------------------------
-- Widget 3: Tyre Degradation Curve (multi-series line chart)
-- X-axis: distance_bin_m (50m buckets)
-- Y-axis: avg_wear_pct (0–100%)
-- Series: one line per tyre_compound ("C1"…"C5" or "Unknown")
-- Covers full session history (not just latest window) to show the curve.
-- -----------------------------------------------------------------------------
SELECT
  COALESCE(tyre_compound, 'Unknown')   AS tyre_compound,
  FLOOR(distance_traveled_m / 50) * 50 AS distance_bin_m,
  ROUND(AVG(average_wear_pct) * 100, 2) AS avg_wear_pct
FROM f1_catalog.gold.gold_tyre_degradation
WHERE distance_traveled_m IS NOT NULL
  AND average_wear_pct    IS NOT NULL
GROUP BY
  tyre_compound,
  FLOOR(distance_traveled_m / 50) * 50
ORDER BY
  tyre_compound,
  distance_bin_m;


-- -----------------------------------------------------------------------------
-- Widget 4: Player Car Live Speed KPI (counter / single-value tile)
-- Derives the player car index from the most recent bronze row, then looks up
-- that car's average speed in the latest gold_distances window.
-- -----------------------------------------------------------------------------
WITH latest_window AS (
  SELECT MAX(window.end) AS max_ts
  FROM f1_catalog.gold.gold_distances
),
player_car AS (
  SELECT m_playerCarIndex AS car_index
  FROM f1_catalog.bronze.bronze_telemetry
  ORDER BY timestamp DESC
  LIMIT 1
)
SELECT
  ROUND(d.avg_speed, 0) AS speed_kmh
FROM f1_catalog.gold.gold_distances d
JOIN latest_window lw ON d.window.end = lw.max_ts
JOIN player_car    pc ON d.car_index  = pc.car_index;
