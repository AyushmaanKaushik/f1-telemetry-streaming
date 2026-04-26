# Phase 1: Data Model & Contracts

## Data Model (Entities)

### Event Message (Packet ID 3)
Tracks boolean logic and discrete session changes.
* Fields: 
    * `eventId` (String): EVENT_SSTA, EVENT_SEND, EVENT_RTMT, EVENT_DRSE
    * `timestamp` (Timestamp): UTC time
    * `driverId` (Int): Foreign key for driver reference.

### Car Telemetry (Packet ID 6)
Frequent vehicle mechanical state, recorded at 60Hz.
* Fields:
    * `timestamp` (Timestamp)
    * `driverId` (Int)
    * `speed_kmh` (Int): 0-350+
    * `engine_rpm` (Int): 0-15000
    * `gear` (Int)
    * `throttle` (Float): 0.0 - 1.0
    * `brake` (Float): 0.0 - 1.0
    * `engine_temperature` (Int)

### Car Status (Packet ID 7)
Session and strategical health, low frequency updates.
* Fields:
    * `timestamp` (Timestamp)
    * `driverId` (Int)
    * `fuel_in_tank` (Float)
    * `ers_energy` (Float)
    * `tyre_compound` (String)
    * `tyre_age_laps` (Int)
    * `drs_activation` (Boolean)

### Car Damage (Packet ID 10)
High significance integrity states.
* Fields:
    * `timestamp` (Timestamp)
    * `driverId` (Int)
    * `front_wing_damage` (Float)
    * `rear_wing_damage` (Float)
    * `engine_wear` (Float)
    * `tyre_wear` (Float)

## Interface Contracts

### Event Hub Topic Setup
* **Topics**: Single unified `telemetry_topic` with 32 partitions.
* **Partitioning Strategy**: Partitions are keyed on `m_playerCarIndex` (Driver ID) guaranteeing chronological order for downstream stream processing.

### Structured Streaming Source
* **Format**: Kafka JSON Payload.
* **Read Contract**: Standard un-nesting via `from_json` inside the Bronze layer notebooks before triggering `.transformWithState()` transformations.
