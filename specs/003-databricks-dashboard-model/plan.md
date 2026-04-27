# Implementation Plan: Databricks Dashboard Data Model

**Branch**: `[003-databricks-dashboard-model]` | **Date**: 2026-04-26 | **Spec**: [specs/003-databricks-dashboard-model/spec.md]
**Input**: Feature specification from `/specs/003-databricks-dashboard-model/spec.md`

## Summary

Build PySpark Structured Streaming Databricks notebooks to transition data from Bronze JSON payloads to tightly typed Silver schemas, applying normalization, followed by tumbling-window aggregated Gold datamarts (Driver Distances, Vehicle Health) optimized for <500ms dashboard reads.

## Technical Context

**Language/Version**: Python 3.11+
**Primary Dependencies**: PySpark (Spark 3.5.0), Delta Lake
**Storage**: Local DBFS (/tmp/tables) as fallback for Community Edition, Delta Parquet
**Testing**: Spark testing utilities (Dataframe equality checks) locally
**Target Platform**: Databricks (Community Edition Compatible)
**Project Type**: Data Engineering ETL Pipeline
**Performance Goals**: < 3-second streaming latency, <500ms dashboard query serving
**Constraints**: Must bypass Unity Catalog limitations on Free Tier

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
Since constitution placeholders exist, standard Spark constraints apply. TDD concepts can be mapped via data contract validation tests prior to executing the cluster block.

## Project Structure

### Documentation (this feature)

```text
specs/003-databricks-dashboard-model/
├── plan.md              # This file
├── research.md          # Tumbling window & aggregation approaches
├── data-model.md        # Delta schema definitions for Gold tables
└── tasks.md             # Execution tasklist (Generated next step)
```

### Source Code (repository root)

```text
src/databricks/
├── lib/
│   └── streaming_utils.py       # (Existing) Stream ingestion configurations
└── notebooks/
    ├── bronze_ingestion.py      # (Existing)
    ├── silver_transformations.py # Multiplexes Bronze blob -> 4 Dedicated Silver Delta Tables
    └── gold_aggregations.py      # Creates Gold datamarts (Driver Gaps, Tyre Deg, Health)

tests/databricks/
└── test_aggregations.py         # PySpark local validation of sliding calculations
```

**Structure Decision**: Retaining the existing 3-tier medallion directory structure inside the databricks notebooks folder representing the explicit ETL path.

## Complexity Tracking

N/A - Standard Medallion routing without major logic divergence.
