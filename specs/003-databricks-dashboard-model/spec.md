# Feature Specification: Databricks Dashboard Data Model

**Feature Branch**: `[003-databricks-dashboard-model]`  
**Created**: 2026-04-26  
**Status**: Draft  
**Input**: User description: "Great, now I want to build on my databricks streaming ETL pipeline. I want to store all the data being recieved in the stream and build tables for this. I also want to figure out a suitable data model for this to build live dashboards in databricks for the future phases."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Live Telemetry Aggregation (Priority: P1)

The system must clean and normalize the incoming stream from the Bronze schema into a reliable Silver schema, making it possible to query normalized metrics (like RPM scaled from 0-1) in real-time.

**Why this priority**: Without structured cleansing, the raw JSON payload in the bronze stream is useless for Databricks dashboard visualizations. Real-time normalization is the backbone of the entire live-board concept.

**Independent Test**: Can be fully tested by querying the Silver output table stream and verifying all specific fields map symmetrically to F1 packets while normalizing numerical constraints.

**Acceptance Scenarios**:

1. **Given** raw telemetry with varied metric caps, **When** processed by the stream engine, **Then** all numeric values scaling (like RPM and Speed) are appended appropriately.
2. **Given** dropped JSON packets, **When** the pipeline processes data, **Then** corrupted packets are cleanly omitted without killing the stream query.

---

### User Story 2 - Gold Dashboard Datamarts (Priority: P2)

The system must aggregate the high-frequency telemetry events into specific dashboard-ready Gold tables representing specific features like Driver Live Positions (Distance algorithms) and Vehicle Damage Health. 

**Why this priority**: Databricks dashboards cannot load 60Hz row-level events in thousands of frames a second cheaply. The Gold layer provides millisecond-latency, pre-aggregated analytics blocks perfectly mapped for live dashboard charting tools.

**Independent Test**: Can be tested by running analytical SQL queries successfully against the Gold tables representing driver-to-driver distance gaps.

**Acceptance Scenarios**:

1. **Given** continuous normalized telemetry, **When** aggregated at 1-second tumbling windows, **Then** the driver positions map accurately in meters scaled.
2. **Given** damage events arriving at 2Hz, **When** evaluated, **Then** the vehicle health overview records latest distinct state.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST establish a Silver structured layer parsing distinct packet bodies into strictly-typed column tables rather than JSON blobs.
- **FR-002**: System MUST generate a Gold layer implementing tumbling window aggregations for high-frequency measurements.
- **FR-003**: System MUST provide distinct data views specifically designed to fuel Databricks SQL Dashboards natively (e.g. Driver Position tracking metrics).
- **FR-004**: System MUST maintain streaming checkpoints independently between Silver and Gold hops so failures resume correctly natively within the Databricks file system constraints.

### Key Entities 

- **Silver Normalized Telemetry**: Structured streaming table housing every processed frame.
- **Gold Driver Positioning**: Aggregated table calculating relative metrics (Distance traveled, Speed Rolling Averages).
- **Gold Vehicle Health**: Snapshot table indexing the latest distinct status of tire wear, wings, and DRS.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Structured pipeline latency is consistently below 3 seconds from Bronze ingestion to Gold availability.
- **SC-002**: Standard Databricks dashboards load aggregate queries against the Gold datamarts in strictly under 500ms.
- **SC-003**: Delta tables actively enforce schema constraints omitting 100% of malformed synthetic packet noise.

## Assumptions

- We assume Databricks SQL Dashboards will natively read identical table constructs defined in PySpark.
- We assume checkpoint and table generation will be structured to accommodate Databricks Community Edition restrictions natively where requested.
- Tumbling windows for aggregations will use 1-second intervals by default to balance DB load against "Live" dashboard requirements.
