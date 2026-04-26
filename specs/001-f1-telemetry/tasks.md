---
description: "Task list for feature implementation"
---

# Tasks: F1 Telemetry Streaming

**Input**: Design documents from `/specs/001-f1-telemetry/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks based on Constitution requirements for unit testing.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Create project directories (src/ingestion, src/databricks, tests/)
- [x] T002 Initialize Python environment with dependencies (confluent-kafka, pyspark, pytest)
- [x] T003 [P] Configure code linting and formatting (e.g. autopep8/flake8)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Define reusable logging configuration in `src/ingestion/logger.py`
- [x] T005 [P] Setup base configuration parser for Azure Connection Strings in `src/ingestion/config.py`
- [x] T006 [P] Add Pytest basic configuration in `tests/conftest.py`

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Python Ingress and Event Hub (Priority: P1) 🎯 MVP

**Goal**: Ingest raw UDP telemetry from the F1 Game on port 20777 and produce Kafka JSON messages to Event Hub.

**Independent Test**: Run the python edge listener. It must receive packets, decode them, and publish successfully to Event Hub without dropping the 60Hz stream.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

- [x] T010 [P] [US1] Unit test for UDP parsing binary logic in `tests/ingestion/test_parser.py`
- [x] T011 [US1] Integration test targeting local EventHub mock in `tests/ingestion/test_producer.py`

### Implementation for User Story 1

- [x] T012 [P] [US1] Create F1 Telemetry data structures in `src/ingestion/models.py` (Packet IDs 3, 6, 7, 10 based on data-model.md)
- [x] T013 [P] [US1] Implement UDP Listener and binary unpacking in `src/ingestion/udp_listener.py`
- [x] T014 [US1] Implement Event Hubs Producer using confluent-kafka in `src/ingestion/eventhub_producer.py`
- [x] T015 [US1] Integrate `ThreadPoolExecutor` within `src/ingestion/udp_listener.py` to decouple packet reception from HTTP Kafka publishing

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 - Silver Layer Normalization (Priority: P2)

**Goal**: Consume Event Hubs Kafka stream into Databricks bronze tables and promote it to silver tables with min-max scaling and `transformWithState`.

**Independent Test**: Connect the Databricks notebook to the telemetry_topic and execute the notebook. Data must flow from JSON schemas into structured Silver tables.

### Implementation for User Story 2

- [x] T016 [P] [US2] Create PySpark utilities for reading Event Hub source in `src/databricks/lib/streaming_utils.py`
- [x] T017 [US2] Implement Bronze ingestion notebook extracting Kafka payload from `from_json` in `src/databricks/notebooks/bronze_ingestion.py`
- [x] T018 [US2] Implement Silver normalization (min/max scaling on metrics like RPM) in `src/databricks/notebooks/silver_transformations.py`
- [x] T019 [US2] Add `transformWithState` processing in `src/databricks/notebooks/silver_transformations.py` to identify RTMT events and flag drivers inactive

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 - Gold Aggregation & Monitoring (Priority: P3)

**Goal**: Present cleaned actionable insights (Distance-Space correlation) and ensure Azure observability configurations are robust.

**Independent Test**: The Databricks console must produce reliable distance-space predictions over a sample set of silver table laps.

### Implementation for User Story 3

- [x] T020 [US3] Implement Distance-Space conversion in `src/databricks/notebooks/gold_aggregations.py`
- [x] T021 [US3] Add ADLS Gen2 Checkpointing config across all Databricks notebooks
- [x] T022 [US3] Create an overview README detailing Azure Monitor config metrics for Event Hub Throttling requests

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: User Story 4 - Synthetic Data Generator (Priority: P2)

**Goal**: Implement a script that mathematically simulates structural telemetry data to mimic raw F1 Game UDP output, enabling offline development and load testing.

**Independent Test**: Running the simulator script pushes binary bounds-fuzzed packets to port `20777`, triggering the locally running `udp_listener.py`.

### Implementation for User Story 4

- [x] T026 [P] [US4] Formulate struct binary packing methodology mapping to F1 packet structures in `src/ingestion/synthetic_generator.py`
- [x] T027 [US4] Develop randomized fuzzy bounds logic loop mimicking 60Hz intervals for packets 3, 6, 7 & 10 in `src/ingestion/synthetic_generator.py`
- [x] T028 [US4] Deploy and visually test the binary handshake between `synthetic_generator.py` and `udp_listener.py` on `127.0.0.1`

**Checkpoint**: The Databricks environment can now be tested locally without an active racing game running!

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T023 Code cleanup, removing debug logging from Databricks notebooks
- [x] T024 Performance optimization validation checking CPU overhead on the Python UDP producer
- [x] T025 Run `quickstart.md` validation from scratch and update deployment docs

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2)
- **User Story 2 (P2)**: Can start concurrently with US1 theoretically, but practically needs the schema contracts produced by US1 to test accurately. It is loosely coupled via the Kafka topic contract.
- **User Story 3 (P3)**: Depends on User Story 2's silver table outputs.

### Parallel Opportunities

- Foundation components [P] can be created in parallel.
- `models.py` and `udp_listener.py` unpacking logic can run while someone does `test_parser.py`.
- The Databricks processing team can mock the Event Hub stream and begin Phase 4 independently of the UDP component in Phase 3.
