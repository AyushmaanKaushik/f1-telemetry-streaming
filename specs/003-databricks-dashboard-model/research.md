# Research: F1 Telemetry Gold Data Models

This document covers technical considerations for aggregating 60Hz telemetry into Databricks Dashboard-compatible datasets.

### Decision 1: Aggregation Strategy for Dashboards
- **Decision**: Tumbling Windows (1-second intervals).
- **Rationale**: 60Hz telemetry generates roughly 1,200 rows per second for a 20-car grid. Dashboards do not need sub-second refresh rates. Tumbling windows chunk data into clean 1-second boundaries without overlap, guaranteeing perfect summation for metrics like `Distance Traveled` without double-counting frames.
- **Alternatives**: Sliding Windows (caused double counting and huge state management overhead), Session Windows (too irregular for telemetry).

### Decision 2: Driver Distance Calculation
- **Decision**: Native Spark SQL Math converting speed.
- **Rationale**: The F1 game provides Speed (km/h), not absolute distance on the track. Distance is extracted via `(Speed / 3.6) * dt_seconds`. Over a 1-second window, summing the instantaneous velocity readings provides an accurate spatial placement relative to competitors.
- **Alternatives**: Tracking coordinates XYZ (hard mapping out standard track lengths natively, would require hardcoded track maps).

### Decision 3: Databricks Compatibility
- **Decision**: DBFS Fallback endpoints.
- **Rationale**: The user is active on Databricks Community Edition. `f1_catalog` (Unity Catalog) and external Azure Data Lake mounts are completely blocked. All silver and gold tables must be written strictly to `delta` unmanaged schemas on `/FileStore/tables/` or `/tmp/tables/`. All code must avoid `.table("...")` calls that enforce Metastore permissions.

### Decision 4: Multiplexing vs Dedicated Silver Tables
- **Decision**: Dedicated Silver tables per Packet Type (Telemetry, Event, Status, Damage).
- **Rationale**: Based on user review, we moved away from a single bloated Silver table. High-frequency 60Hz telemetry metrics (Packet 6) would create massive sparse matrices when combined with 2Hz status data (Packet 7, 10). Multiplexing the PySpark `forEachBatch` logic to filter `m_packetId` and output to separate highly-dense delta tables optimizes Gold layer read limits significantly.
