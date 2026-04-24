# Feature Specification: packet-structures

**Feature Branch**: `002-packet-structures`  
**Created**: 2026-04-24  
**Status**: Draft  
**Input**: User description: "implement the correct binary structures for the other packets aswell (3, 7, 10)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Full Synthetic Telemetry Parsing (Priority: P1)

Data engineering developers must be able to view fully mapped JSON telemetry inside Azure Event Hubs for all major F1 packets (3, 7, and 10), beyond just the header metadata, in order to test downstream Databricks notebook integration thoroughly.

**Why this priority**: It is a hard prerequisite for End-to-End pipeline testing offline.

**Independent Test**: Fully verifiable by running the isolated Python generator script and verifying the target JSON schemas directly in Azure.

**Acceptance Scenarios**:

1. **Given** the synthetic generator pushes a Packet 3 (Event), **When** received by the listener, **Then** it is fully unpacked and includes the `eventCode` variable.
2. **Given** the synthetic generator pushes a Packet 7 (Status), **When** received, **Then** it includes `fuel_in_tank`, `ers_energy`, `tyre_compound`, `tyre_age_laps`, and `drs_activation` mapped correctly.
3. **Given** the synthetic generator pushes a Packet 10 (Damage), **When** received, **Then** it includes `front_wing_damage`, `rear_wing_damage`, `engine_wear`, and `tyre_wear` mapped correctly.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST unpack F1 Packet 3 (Event) binary byte arrays.
- **FR-002**: System MUST unpack F1 Packet 7 (Car Status) binary byte arrays.
- **FR-003**: System MUST unpack F1 Packet 10 (Car Damage) binary byte arrays.
- **FR-004**: The mock generator script MUST mathematically formulate and emit the payload structures matching definitions for Packets 3, 7, and 10 exactly.

### Key Entities *(include if feature involves data)*

- **EventPacket**: String code sequence representing active track flags.
- **CarStatusPacket**: Float metrics and int states indicating mechanical performance thresholds.
- **CarDamagePacket**: Float percentages mapping vehicle wing/engine integrity.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The listener correctly passes 100% of defined target properties into the `payload` JSON outputs for Packets 3, 7, and 10 without generating payload out-of-bounds padding exceptions.

## Assumptions

- Development is constrained to mapping the Python properties explicitly pre-defined in `src/ingestion/models.py`. The exhaustive 1:1 C-pointer mapping of all 22 opponent telemetry structures is not required to feed the Silver Databricks ingestion pattern.
