# Feature Specification: Databricks SQL Dashboards

**Feature Branch**: `004-databricks-sql-dashboards`
**Created**: 2026-04-29
**Status**: Draft
**Input**: User description: "Build the dashboards based on the databricks notebooks that we have built in the previous iteration"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Live Driver Position Tracker (Priority: P1)

A user watching or analysing a session wants to see, in near-real time, the spatial gap between each car on the grid and the race leader. The dashboard widget reads from `gold_driver_gaps` and displays each car's gap (in metres) to the leader within the most recent 1-second window.

**Why this priority**: This is the single most compelling "live" view. It answers the core question "where is each car right now?" and is the key differentiator from a static replay tool. All other widgets build on this foundation of understanding position.

**Independent Test**: Can be fully tested by running the synthetic generator for 30 seconds, then querying `gold_driver_gaps` directly in a Databricks SQL Dashboard table or bar chart widget and confirming that (a) rows exist, (b) the P1 car has `gap_to_leader_m = 0`, and (c) trailing cars have increasing positive gap values.

**Acceptance Scenarios**:

1. **Given** the Gold pipeline is running and receiving telemetry, **When** the dashboard is opened, **Then** a bar chart shows all active cars ordered by gap to leader, refreshing at most every 5 seconds.
2. **Given** a car retires (RTMT event received), **When** the dashboard refreshes, **Then** the retired car's gap is no longer displayed or is clearly marked as inactive.
3. **Given** the pipeline has no data (generator stopped), **When** the dashboard is viewed, **Then** an empty-state message is shown rather than an error.

---

### User Story 2 — Vehicle Health Overview (Priority: P2)

A user wants to see the current damage and resource state for each car — tyre wear, engine wear, wing damage, fuel level, and ERS energy — in a single glanceable panel. The widget reads from `gold_vehicle_health`.

**Why this priority**: Vehicle degradation drives race strategy. Knowing which cars are critically damaged or fuel-low is the next most actionable insight after position. This widget directly supports the "build live dashboards" goal stated by the user.

**Independent Test**: Can be tested independently by querying `gold_vehicle_health` in a Databricks SQL Dashboard and confirming that all 7 health fields (`tyre_wear`, `engine_wear`, `front_wing_damage`, `rear_wing_damage`, `fuel_in_tank`, `ers_energy`, `drs_activation`) contain non-null values for at least one car after 10 seconds of synthetic data.

**Acceptance Scenarios**:

1. **Given** damage and status packets are flowing, **When** the dashboard is viewed, **Then** a table or gauge panel displays the latest health values for each car, updated within 5 seconds of new data arriving.
2. **Given** a car has `tyre_wear > 80%`, **When** the dashboard renders, **Then** the value is visually highlighted (e.g. red colour coding) to indicate critical degradation.
3. **Given** DRS is active for a car, **When** the dashboard renders, **Then** a clear boolean indicator (e.g. ✅ / ❌) is shown in the DRS column.

---

### User Story 3 — Tyre Degradation Curve (Priority: P3)

A user wants to see how tyre wear accumulates over driven distance for each compound currently in use, to understand which compound is degrading fastest. The widget reads from `gold_tyre_degradation`.

**Why this priority**: The degradation curve provides strategic insight (when to pit) and is visually distinctive as a line chart. It is lower priority than position and health because it requires sustained session data to become meaningful, whereas the P1/P2 widgets are immediately useful.

**Independent Test**: Can be tested independently by running the synthetic generator for 60+ seconds, then plotting `distance_traveled_m` (x-axis) vs `average_wear_pct` (y-axis) grouped by `tyre_compound` in a Databricks SQL Dashboard line chart and confirming that wear increases as distance increases.

**Acceptance Scenarios**:

1. **Given** at least 30 seconds of telemetry and damage data, **When** the tyre chart widget is viewed, **Then** a line chart shows wear percentage on the y-axis and cumulative distance on the x-axis, with one line per tyre compound.
2. **Given** multiple tyre compounds are in use simultaneously, **When** the chart renders, **Then** each compound is represented by a distinct colour.
3. **Given** insufficient data (under 5 rows), **When** the chart renders, **Then** a placeholder message "Collecting data…" is shown instead of a misleading flat line.

---

### Edge Cases

- What happens when `gold_driver_gaps` has gaps for only some cars (partial data window)? Dashboard should still render with available cars only.
- What happens when the Databricks cluster auto-terminates (Community Edition 6h limit)? Dashboard queries will fail; the dashboard should show a stale-data warning rather than a hard error.
- What if `tyre_compound` is `NULL` in `gold_tyre_degradation`? Rows with null compound should be grouped under "Unknown" rather than dropped.

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The dashboard MUST display live driver gaps sourced from `gold_driver_gaps`, refreshing automatically at a configurable interval (default: 5 seconds).
- **FR-002**: The dashboard MUST display vehicle health metrics from `gold_vehicle_health`, including all 7 fields: tyre wear, engine wear, front/rear wing damage, fuel level, ERS energy, and DRS state.
- **FR-003**: The dashboard MUST display a tyre degradation chart from `gold_tyre_degradation`, grouped by `tyre_compound`.
- **FR-004**: Each widget MUST be independently queryable via Databricks SQL so it can be refreshed or embedded separately.
- **FR-005**: The dashboard MUST use only the existing Gold Delta tables as data sources — no additional transformation layers or intermediate queries.
- **FR-006**: Critical health thresholds (e.g. tyre wear > 80%, fuel < 10%) MUST be visually highlighted using conditional formatting.

### Key Entities

- **Driver Gap**: A per-car, per-1-second-window measure of distance behind the race leader (metres). Sourced from `gold_driver_gaps`.
- **Vehicle Health Snapshot**: The latest aggregated state of a car's damage and resource levels within a 1-second window. Sourced from `gold_vehicle_health`.
- **Tyre Wear Point**: A data point recording average tyre wear at a measured cumulative distance, grouped by tyre compound. Sourced from `gold_tyre_degradation`.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All three dashboard widgets load and display data within 5 seconds of opening the dashboard, given the pipeline has been running for at least 30 seconds.
- **SC-002**: Driver gap values update within 10 seconds of new telemetry arriving from the synthetic generator or game.
- **SC-003**: Vehicle health panel displays non-null values for 100% of the fields for at least the player car when telemetry is active.
- **SC-004**: The tyre degradation chart produces a monotonically increasing wear trend when the synthetic generator runs for 60+ uninterrupted seconds.
- **SC-005**: The dashboard remains readable and shows a clear empty or stale-data state when no pipeline data has arrived in the last 60 seconds.

---

## Assumptions

- The three Gold Delta tables (`gold_driver_gaps`, `gold_vehicle_health`, `gold_tyre_degradation`) are populated and accessible in `f1_catalog.gold` before the dashboard is built.
- Databricks SQL (serverless or Classic) is available on the user's Community Edition workspace for creating dashboards. If not available, widgets will be built as notebook `display()` cells instead.
- Dashboard refresh rate of 5 seconds is a reasonable default; individual widgets may use longer intervals (e.g. 30s for the tyre chart) to reduce query load on Community Edition.
- The synthetic generator (`synthetic_generator.py`) will be used as the primary data source during development and validation, since the actual F1 game may not always be running.
- Conditional formatting thresholds (e.g. tyre wear > 80%) are fixed defaults for now; user-configurable thresholds are out of scope for this iteration.
