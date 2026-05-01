# Tasks: Databricks SQL Dashboards

**Input**: Design documents from `specs/004-databricks-sql-dashboards/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the output directory and shared SQL query file used by all stories.

- [x] T001 Create `src/databricks/dashboards/` directory and add `__init__.py` placeholder
- [x] T002 Create `src/databricks/dashboards/f1_dashboard_queries.sql` containing all 4 widget SQL queries from `specs/004-databricks-sql-dashboards/data-model.md` (driver gaps, vehicle health, tyre degradation, player speed KPI), clearly separated by widget header comments

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Validate Gold tables have data before building dashboard widgets against them. All user story work is blocked until this passes.

- [x] T003 Add a validation notebook cell to `src/databricks/notebooks/gold_aggregations.py` that runs `SELECT COUNT(*) FROM f1_catalog.gold.gold_driver_gaps` and asserts count > 0, confirming the pipeline is producing data before dashboard work begins

**Checkpoint**: Gold tables confirmed populated — user story implementation can begin.

---

## Phase 3: User Story 1 — Live Driver Position Gaps (Priority: P1) 🎯 MVP

**Goal**: A horizontal bar chart showing each car's gap to the race leader in metres, sourced from `gold_driver_gaps`, auto-refreshing every 30 seconds.

**Independent Test**: Run the synthetic generator for 30s, run the Widget 1 SQL query from `f1_dashboard_queries.sql` directly in the Databricks SQL Editor, confirm rows exist with `gap_to_leader_m = 0` for the leader and positive values for trailing cars.

### Implementation for User Story 1

- [x] T004 [US1] Write the `f1_dashboard.lvdash.json` skeleton file in `src/databricks/dashboards/f1_dashboard.lvdash.json` — dashboard-level metadata (name, description, default refresh interval of 30s)
- [x] T005 [US1] Add Widget 1 (Driver Position Gaps) dataset definition to `src/databricks/dashboards/f1_dashboard.lvdash.json` — embed the driver gaps SQL query from `f1_dashboard_queries.sql` as a named dataset
- [x] T006 [US1] Add Widget 1 chart widget block to `src/databricks/dashboards/f1_dashboard.lvdash.json` — horizontal bar chart, `car_label` on Y-axis, `gap_to_leader_m` on X-axis, ordered ascending by gap
- [x] T007 [US1] Deploy draft dashboard using CLI: `databricks lakeview create --json @src/databricks/dashboards/f1_dashboard.lvdash.json` and record the returned `dashboard_id` in `specs/004-databricks-sql-dashboards/quickstart.md`

**Checkpoint**: Driver gaps bar chart visible in Databricks workspace. US1 independently testable.

---

## Phase 4: User Story 2 — Vehicle Health Overview (Priority: P2)

**Goal**: A table widget with conditional colour formatting showing all 7 health fields per car, sourced from `gold_vehicle_health`.

**Independent Test**: With pipeline running, the vehicle health table widget shows non-null values for all 7 fields (tyre_wear, engine_wear, front_wing, rear_wing, fuel, ERS, DRS) for at least one car.

### Implementation for User Story 2

- [ ] T008 [US2] Add Widget 2 (Vehicle Health) dataset definition to `src/databricks/dashboards/f1_dashboard.lvdash.json` — embed the vehicle health SQL query with all 7 fields + display labels
- [ ] T009 [US2] Add Widget 2 table widget block to `src/databricks/dashboards/f1_dashboard.lvdash.json` — table type, with conditional formatting rules: `tyre_wear_pct > 80` → Red, `50–80` → Amber, `< 50` → Green; `fuel_kg < 10` → Red; `engine_wear_pct > 70` → Red
- [ ] T010 [US2] Update deployed dashboard via CLI: `databricks lakeview update <dashboard_id> --json @src/databricks/dashboards/f1_dashboard.lvdash.json`

**Checkpoint**: Vehicle health table visible with colour-coded thresholds. US2 independently testable alongside US1.

---

## Phase 5: User Story 3 — Tyre Degradation Curve (Priority: P3)

**Goal**: A multi-series line chart showing average tyre wear % vs cumulative distance, one line per compound, sourced from `gold_tyre_degradation`.

**Independent Test**: Run the synthetic generator for 60+ seconds, then the tyre degradation chart shows at least one upward-trending line per active tyre compound.

### Implementation for User Story 3

- [ ] T011 [US3] Add Widget 3 (Tyre Degradation) dataset definition to `src/databricks/dashboards/f1_dashboard.lvdash.json` — embed the tyre degradation SQL query with 50m binning and compound grouping
- [ ] T012 [US3] Add Widget 3 line chart widget block to `src/databricks/dashboards/f1_dashboard.lvdash.json` — line chart, X-axis: `distance_bin_m`, Y-axis: `avg_wear_pct`, series grouped by `tyre_compound`, distinct colour per compound
- [ ] T013 [US3] Update deployed dashboard via CLI: `databricks lakeview update <dashboard_id> --json @src/databricks/dashboards/f1_dashboard.lvdash.json`

**Checkpoint**: All 3 widgets live on the dashboard. Full spec delivered.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Publish the dashboard, add the optional speed KPI tile, and write the deployment guide.

- [ ] T014 [P] Add Widget 4 (Player Speed KPI) dataset + counter tile to `src/databricks/dashboards/f1_dashboard.lvdash.json` — single-value tile showing player car's average speed from `gold_distances`
- [ ] T015 [P] Write `specs/004-databricks-sql-dashboards/quickstart.md` — step-by-step guide covering: prerequisites check, CLI create command, how to find `dashboard_id`, CLI update and publish commands, and how to open the dashboard URL in the browser
- [ ] T016 Publish the final dashboard via CLI: `databricks lakeview publish <dashboard_id>` making it accessible via shareable URL

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (shared SQL file must exist first)
- **US1 (Phase 3)**: Depends on Phase 2 — Gold tables must be confirmed populated
- **US2 (Phase 4)**: Depends on T007 — dashboard must exist (`dashboard_id` required for update commands)
- **US3 (Phase 5)**: Depends on T007 — same reason
- **Polish (Phase 6)**: Depends on T013 — all widgets complete before publish

### Within User Story Phases

- Dataset definition task MUST complete before chart widget task (widget references dataset by name)
- CLI deploy/update task MUST be last within each story

### Parallel Opportunities

- T008 and T011 (dataset definitions for US2 and US3) can be authored in parallel in the JSON file since they are independent dataset blocks
- T014 and T015 (speed KPI + quickstart) are fully parallel polish tasks

---

## Parallel Example: US2 + US3 (after US1 MVP)

```text
# After T007 (dashboard deployed), US2 and US3 dataset blocks can be authored together:
Task T008: Add vehicle health dataset block to f1_dashboard.lvdash.json
Task T011: Add tyre degradation dataset block to f1_dashboard.lvdash.json

# Then widget blocks (each references its own dataset, no conflict):
Task T009: Add vehicle health table widget block
Task T012: Add tyre degradation line chart widget block

# Then single update push:
Task T010/T013: databricks lakeview update
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational validation (T003)
3. Complete Phase 3: US1 — driver gaps bar chart (T004–T007)
4. **STOP and VALIDATE**: Open Databricks workspace → confirm bar chart renders with live data
5. Deploy / share if ready

### Incremental Delivery

1. MVP (US1) → Driver gaps chart live ✅
2. Add US2 → Vehicle health table with colour coding ✅
3. Add US3 → Tyre degradation curve ✅
4. Polish → Publish with shareable URL ✅
