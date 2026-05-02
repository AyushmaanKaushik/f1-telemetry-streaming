# Research: Databricks SQL Dashboards for F1 Telemetry

This document covers the technical decisions for building live Databricks SQL Dashboard widgets on top of the Gold Delta tables produced by the Medallion pipeline.

---

## Decision 1: Databricks SQL Dashboard vs Notebook `display()` widgets

- **Decision**: Use **Databricks SQL Dashboards** (the native Lakeview dashboard editor) as the primary delivery mechanism. Notebook `display()` cells are the documented fallback if SQL Dashboards are unavailable on Community Edition.
- **Rationale**: Databricks SQL Dashboards support auto-refresh intervals (5s minimum), conditional formatting, and shareable URLs — all required by the spec. Notebook `display()` cells do not auto-refresh and cannot be shared as a standalone URL.
- **Alternatives considered**: Grafana (requires external server), Streamlit (requires separate compute), Power BI (requires premium connector).

---

## Decision 2: SQL query pattern — latest window snapshot

- **Decision**: All dashboard widgets query Gold tables using a **latest-window subquery** pattern:
  ```sql
  SELECT * FROM f1_catalog.gold.<table>
  WHERE window.end = (SELECT MAX(window.end) FROM f1_catalog.gold.<table>)
  ```
- **Rationale**: Gold tables accumulate rows per 1-second window. A dashboard showing "current state" must filter to the most recent window only. Without this filter, bar charts would aggregate across all historical windows, producing meaningless totals.
- **Alternatives considered**: `LIMIT` + `ORDER BY` (non-deterministic with ties), streaming views (not supported in SQL Dashboard query editor).

---

## Decision 3: Refresh interval per widget

- **Decision**: Default refresh interval of **30 seconds** for all widgets on Community Edition.
- **Rationale**: Community Edition clusters have limited concurrency. The spec allows up to 10 seconds for gap updates but a 5-second refresh on CE would generate constant query load and potentially starve the streaming pipeline of cluster resources. 30 seconds is a pragmatic default that keeps the dashboard "live" without competing with the running streams. Users can reduce to 5s on dedicated clusters.
- **Alternatives considered**: 5s (too aggressive for CE shared compute), 60s (too stale for a live dashboard feel).

---

## Decision 4: Conditional formatting thresholds

- **Decision**: Apply colour-coded thresholds using Databricks SQL Dashboard **conditional formatting** rules:
  - `tyre_wear > 80` → Red
  - `tyre_wear 50–80` → Amber
  - `tyre_wear < 50` → Green
  - `fuel_in_tank < 10` → Red
  - `engine_wear > 70` → Red
  - `drs_activation = true` → Green badge
- **Rationale**: These thresholds match typical F1 strategy monitoring conventions. They are hardcoded for v1 per the spec assumption; user-configurable thresholds are out of scope.
- **Alternatives considered**: Percentage-based normalised scale (loses absolute meaning), traffic lights only (loses granularity).

---

## Decision 5: Tyre degradation chart X-axis binning

- **Decision**: X-axis uses **`distance_traveled_m` grouped into 50-metre bins** via integer division: `FLOOR(distance_traveled_m / 50) * 50`.
- **Rationale**: Raw 1-second window distance values are small (~30–50m at race pace) and would produce an extremely dense, jagged x-axis. Binning into 50m intervals produces a smooth, readable curve while preserving the degradation trend.
- **Alternatives considered**: Time-based x-axis (less intuitive than distance for tyre wear), raw per-window values (too noisy).

---

## Decision 6: Driver gap chart — player car highlighting

- **Decision**: The driver gaps bar chart highlights the player car (`car_index` matching the `m_playerCarIndex` value from the most recent bronze row) using a **fixed colour override** in the chart series configuration.
- **Rationale**: The user is a player in the simulation, so knowing their own gap relative to others is the primary use case. Visual distinction makes this instantly readable.
- **Alternatives considered**: Separate widget for player only (loses competitive context), tooltip-only indication (too subtle).
