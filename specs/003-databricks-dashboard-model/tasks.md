---
description: "Task list execution trace for Dashboard Models"
---

# Tasks: Databricks Dashboard Data Model

**Input**: Design documents from `/specs/003-databricks-dashboard-model/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure
- [ ] T001 Initialize the test suite directory `tests/databricks/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented
- [ ] T002 Modify Databricks local environment context bounds for the Delta endpoints to support `tmp` if necessary.

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Live Telemetry Aggregation (Priority: P1) 🎯 MVP

**Goal**: Filter the Bronze streaming blob into 4 distinct Silver target tables removing sparse-matrix bloat.

**Independent Test**: Running `display()` on any generated Silver table matches 100% data density bounds without nulls from mixed incoming packet types.

### Implementation for User Story 1

- [ ] T003 [P] [US1] Create Silver Telemetry 60Hz filter definition in `src/databricks/notebooks/silver_transformations.py`
- [ ] T004 [P] [US1] Create Silver Status filter definition in `src/databricks/notebooks/silver_transformations.py`
- [ ] T005 [P] [US1] Create Silver Event filter definition in `src/databricks/notebooks/silver_transformations.py`
- [ ] T006 [P] [US1] Create Silver Damage filter definition in `src/databricks/notebooks/silver_transformations.py`
- [ ] T007 [US1] Build PySpark `forEachBatch` router to natively distribute the Bronze stream into the 4 Silver tables in `src/databricks/notebooks/silver_transformations.py`

**Checkpoint**: At this point, User Story 1 should cleanly separate the blob output. 

---

## Phase 4: User Story 2 - Gold Dashboard Datamarts (Priority: P2)

**Goal**: Aggregate massive Silver structures into <500ms dashboard-ready Gold metric clusters.

**Independent Test**: Executing static SQL windowing queries against the PySpark Dataframes accurately tracks metric groupings (e.g. gap bounds).

### Tests for User Story 2

- [ ] T008 [P] [US2] Implement PySpark window equivalence tests in `tests/databricks/test_aggregations.py`

### Implementation for User Story 2

- [ ] T009 [P] [US2] Implement Vehicle Health State Tracking script caching the latest damage vs status arrays in `src/databricks/notebooks/gold_aggregations.py`
- [ ] T010 [P] [US2] Build `speed_kmh` to distance tracking math (Tumbling Window) for live Driver Gaps in `src/databricks/notebooks/gold_aggregations.py`
- [ ] T011 [P] [US2] Build `distance_traveled_m` vs `tyre_wear_pct` Aggregation logic in `src/databricks/notebooks/gold_aggregations.py`

**Checkpoint**: At this point, the entire Medalion path completes!

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T012 Confirm streaming execution bypasses all Free Tier Unity Catalog hard limitations gracefully.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User Story 1 handles the fundamental schema structuring required before User Story 2 math works. 
  - Sequential priority order (P1 → P2).

### Parallel Opportunities

- All Silver Table schema definitions ([T003], [T004], [T005], [T006]) marked `[P]` can be coded out concurrently before the router binds them.
- All Gold algorithm logics ([T009], [T010], [T011]) marked `[P]` can be mathematically drafted simultaneously without conflicting states.

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 3: User Story 1 (Silver Pipeline).
3. **STOP and VALIDATE**: Verify the Databricks notebook correctly unpacks the Silver schemas into `/tmp` delta stores cleanly natively.

### Incremental Delivery

1. Follow MVP Setup.
2. Code Gold pipeline math logic securely against the silver tables!
