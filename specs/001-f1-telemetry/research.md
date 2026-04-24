# Phase 0: Research & Architecture Decisions

## Ingestion Architecture

- **Decision**: Python-based UDP listener with ThreadPoolExecutor
- **Rationale**: UDP telemetry arrives at 60Hz. Sequential processing leads to packet drops. Using threads allows I/O waiting without dropping data. `confluent-kafka` will bridge Python ingestion directly to Azure Event Hubs over port 9093.

## Event Broker

- **Decision**: Azure Event Hubs (Premium Tier with Kafka surface enabled)
- **Rationale**: Integrates seamlessly with Azure Databricks without requiring a dedicated VM/Docker cluster for Zookeeper + Kafka brokers. The Premium Tier offers isolated processing units needed to guarantee low latency under the high frequency F1 data constraints.

## Stream Processing Engine

- **Decision**: PySpark Structured Streaming on Databricks
- **Rationale**: Powerful distributed state management using `transformWithState` and ease of scaling. Perfect fit for mapping telemetry metrics, preserving context (reference laps), and executing logic (retirement detection, performance decay predictive logic).

## Data Model (Medallion Architecture)

- **Decision**: Bronze, Silver, Gold pattern
- **Rationale**: Raw packets (Binary/JSON payload string) will be stored in Bronze. Silver normalizes timestamps, handles standardization (MinMax scaling, state flags), and maps properties to distance-space points. Gold surfaces aggregated metrics and predictions.

## Synthetic Data Generation

- **Decision**: Python bound-fuzzing script generating random structural telemetry data
- **Rationale**: Replicates the 60Hz UDP data emission required to natively end-to-end test the PySpark architecture without the overhead of physics simulation. Integrates flawlessly by pointing its binary output to the `udp_listener.py` on localhost:20777.
