# Databricks Setup Guide — F1 Telemetry Pipeline

Complete, step-by-step setup for running the F1 telemetry Medallion pipeline on Databricks Community Edition.

---

## Prerequisites

- Databricks Community Edition account active at `https://community.cloud.databricks.com`
- Azure Event Hub namespace created and running (`telemetry_topic` hub exists)
- Databricks CLI installed and authenticated (see Step 1)
- `udp_listener.py` / `synthetic_generator.py` running locally

---

## Step 1 — Authenticate the Databricks CLI

```powershell
pip install databricks-cli

databricks configure --token
# Host:  https://community.cloud.databricks.com
# Token: (generate one from Databricks UI → User Settings → Access Tokens)
```

Verify it works:
```powershell
databricks workspace ls /
```

---

## Step 2 — Create a Cluster

> Community Edition only gives you **1 cluster at a time**, max 6h runtime.

1. Go to **Compute → Create Compute**
2. Settings:
   - **Cluster name**: `f1-pipeline`
   - **Databricks Runtime**: `14.3 LTS` (includes Spark 3.5, Python 3.11)
   - **Node type**: Community default (single node)
3. Under **Advanced Options → Spark Config**, add:
   ```
   spark.databricks.delta.preview.enabled true
   ```
4. Under **Advanced Options → Maven Libraries**, click **Add Library**:
   - **Coordinates**: `com.microsoft.azure:azure-eventhubs-spark_2.12:2.3.22`
   
   > This is the Spark–Event Hub Kafka connector. Without it, `format("kafka")` cannot talk to Azure Event Hubs.

5. Click **Create**. Wait for the cluster to reach **Running** status.

---

## Step 3 — Create the Catalog and Schemas

Open a new notebook attached to your cluster and run this **one-time setup cell**:

```python
# === One-time Databricks setup — run once, then delete this notebook ===

# 1. Create Unity Catalog catalog
spark.sql("CREATE CATALOG IF NOT EXISTS f1_catalog")

# 2. Create the three Medallion schemas
spark.sql("CREATE SCHEMA IF NOT EXISTS f1_catalog.bronze")
spark.sql("CREATE SCHEMA IF NOT EXISTS f1_catalog.silver")
spark.sql("CREATE SCHEMA IF NOT EXISTS f1_catalog.gold")

# 3. Verify
display(spark.sql("SHOW SCHEMAS IN f1_catalog"))
```

> **Note**: Community Edition may not have Unity Catalog enabled. If the above fails with a
> `catalog not found` error, replace all table references in the notebooks with path-based writes:
> ```python
> # Instead of: .toTable("f1_catalog.bronze.bronze_telemetry")
> # Use:        .start("/FileStore/tables/bronze_telemetry")
> ```
> And read with:
> ```python
> spark.readStream.format("delta").load("/FileStore/tables/bronze_telemetry")
> ```

---

## Step 4 — Register Secrets

> ✅ Already completed — your `f1_scope` has all 3 keys. Skip if done.

```powershell
# Create the scope
databricks secrets create-scope --scope f1_scope

# Add the three secrets
databricks secrets put --scope f1_scope --key eventhub_namespace
# Paste: <your-namespace>.servicebus.windows.net:9093

databricks secrets put --scope f1_scope --key eventhub_name
# Paste: telemetry_topic

databricks secrets put --scope f1_scope --key eventhub_conn_str
# Paste: Endpoint=sb://<namespace>.servicebus.windows.net/;SharedAccessKeyName=...

# Verify
databricks secrets list --scope f1_scope
```

#### Where to find these values in Azure Portal

| Secret | Location in Azure |
|---|---|
| `eventhub_namespace` | Event Hub Namespace → **Overview** → hostname (add `:9093`) |
| `eventhub_name` | Event Hub Namespace → **Event Hubs** → hub name |
| `eventhub_conn_str` | Event Hub Namespace → **Shared Access Policies** → `RootManageSharedAccessKey` → **Connection string–primary key** |

---

## Step 5 — Upload the Notebooks

1. In Databricks UI, go to **Workspace → your username folder**
2. Click **⋮ → Import**
3. Upload each file via **File** import mode:
   - `src/databricks/notebooks/bronze_ingestion.py`
   - `src/databricks/notebooks/silver_transformations.py`
   - `src/databricks/notebooks/gold_aggregations.py`
4. Attach all three notebooks to the `f1-pipeline` cluster

---

## Step 6 — Start the Local Packet Generator

In your local terminal, start the UDP packet simulator before running any notebook:

```powershell
# Option A: Real game (F1 24 running with UDP telemetry enabled on port 20777)
# Just run the game — udp_listener.py will catch packets automatically

# Option B: Synthetic generator (no game required)
python -m src.ingestion.synthetic_generator
```

Confirm `udp_listener.py` is forwarding to Event Hub:
```powershell
python -m src.ingestion.udp_listener
# Should print: Listening for UDP telemetry on 0.0.0.0:20777
```

---

## Step 7 — Run the Notebooks in Order

Run each notebook **top to bottom** using **Run All**. Each must be running before starting the next.

### 7a. `bronze_ingestion.py`
- Connects to Event Hub via Kafka
- Parses the flat JSON payload
- Streams to `f1_catalog.bronze.bronze_telemetry`
- **Expected**: Last cell prints `Bronze stream started → f1_catalog.bronze.bronze_telemetry`

Validate in a new cell:
```python
display(spark.readStream.table("f1_catalog.bronze.bronze_telemetry"))
```

### 7b. `silver_transformations.py`
- Reads from `bronze_telemetry`
- Filters by `m_packetId` into 4 typed Silver tables (Events, Telemetry, Status, Damage)
- **Expected**: Last cell prints all 4 Silver stream paths

Validate:
```python
display(spark.readStream.table("f1_catalog.silver.silver_telemetry"))
```

### 7c. `gold_aggregations.py`
- Reads from Silver tables
- Produces 4 Gold datamarts (Distances, Vehicle Health, Tyre Degradation, Driver Gaps)
- **Expected**: Last cell prints all 4 Gold stream paths

Validate:
```python
display(spark.readStream.table("f1_catalog.gold.gold_driver_gaps"))
```

---

## Step 8 — Verify Data is Flowing

Run this in any notebook cell while the streams are active:

```python
# Quick row count check across all tables
for tbl in [
    "f1_catalog.bronze.bronze_telemetry",
    "f1_catalog.silver.silver_telemetry",
    "f1_catalog.silver.silver_status",
    "f1_catalog.silver.silver_damage",
    "f1_catalog.gold.gold_distances",
    "f1_catalog.gold.gold_driver_gaps",
]:
    count = spark.read.table(tbl).count()
    print(f"{tbl}: {count} rows")
```

---

## Troubleshooting

| Error | Cause | Fix |
|---|---|---|
| `CATALOG_NOT_FOUND: f1_catalog` | Unity Catalog not enabled on CE | Use path-based writes to `/FileStore/tables/` (see Step 3 note) |
| `DBFS_DISABLED` on `/FileStore/checkpoints/` | Public DBFS root blocked | Use `/tmp/checkpoints/` instead |
| `ClassNotFound: kafkashaded...` | Kafka connector JAR not installed | Add Maven library in cluster config (Step 2) |
| `Secret does not exist` | Scope/key mismatch | Run `databricks secrets list --scope f1_scope` to verify keys |
| Bronze stream starts but Silver tables empty | `m_packetId` filter not matching | Run `display(spark.read.table("f1_catalog.bronze.bronze_telemetry"))` and check `m_packetId` column values |
| `COMMAND_CANCELED` / timeout | Community Edition 6h cluster limit | Restart the cluster and re-run all notebooks |
