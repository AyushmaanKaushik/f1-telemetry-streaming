# Phase 1: Data Model & Contracts

## In-Memory C-Struct Representations

### Event Message (Packet ID 3)
* Length: 4 bytes
* Format: `<4s`
* `eventCode` (String): e.g. `SSTA` (Session Start)

### Car Status (Packet ID 7)
* Length: 11 bytes
* Format: `<ffBBB`
* `fuel_in_tank` (Float)
* `ers_energy` (Float)
* `tyre_compound` (UInt8 converted to String enum downstream)
* `tyre_age_laps` (UInt8)
* `drs_activation` (UInt8 treated as boolean logic)

### Car Damage (Packet ID 10)
* Length: 16 bytes
* Format: `<ffff`
* `front_wing_damage` (Float)
* `rear_wing_damage` (Float)
* `engine_wear` (Float)
* `tyre_wear` (Float)
