# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "2"
# ///
# MAGIC %md
# MAGIC # Bronze Ingestion: Raw Telemetry Stream
# MAGIC
# MAGIC Reads raw F1 telemetry JSON messages from Azure Event Hub (Kafka endpoint)
# MAGIC and lands them as-is into a Bronze Delta table.
# MAGIC
# MAGIC **Source**: `udp_listener.py` → Event Hub → this notebook
# MAGIC
# MAGIC The payload schema is a FLAT JSON dict. Depending on packet_id, different
# MAGIC fields are present. Bronze preserves all fields as nullable to handle this.

# COMMAND ----------
# MAGIC %md ## 1. Configuration

EH_NAMESPACE   = dbutils.secrets.get(scope="f1_scope", key="eventhub_namespace")   # e.g. "mynamespace.servicebus.windows.net:9093"
EH_NAME        = dbutils.secrets.get(scope="f1_scope", key="eventhub_name")         # e.g. "telemetry_topic"
EH_CONN_STR    = dbutils.secrets.get(scope="f1_scope", key="eventhub_conn_str")     # full connection string

CHECKPOINT_DIR = "/tmp/checkpoints/bronze_telemetry"
BRONZE_TABLE   = "f1_catalog.bronze.bronze_telemetry"

# COMMAND ----------
# MAGIC %md ## 2. Event Hub (Kafka) connection options

eh_sasl = (
    f'kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule required '
    f'username="$ConnectionString" '
    f'password="{EH_CONN_STR}";'
)

kafka_options = {
    "kafka.bootstrap.servers":                    EH_NAMESPACE,
    "kafka.security.protocol":                    "SASL_SSL",
    "kafka.sasl.mechanism":                       "PLAIN",
    "kafka.sasl.jaas.config":                     eh_sasl,
    "kafka.request.timeout.ms":                   "60000",
    "kafka.session.timeout.ms":                   "30000",
    "subscribe":                                   EH_NAME,
    "startingOffsets":                             "latest",
    "failOnDataLoss":                              "false",
}

# COMMAND ----------
# MAGIC %md ## 3. Bronze schema
# MAGIC
# MAGIC This is the UNION of all fields emitted by udp_listener.py across packet IDs 3, 6, 7, 10.
# MAGIC All packet-specific fields are nullable — Bronze captures everything and validates nothing.

from pyspark.sql.types import (
    StructType, StructField,
    IntegerType, StringType, FloatType, BooleanType, TimestampType
)
from pyspark.sql.functions import col, from_json, to_timestamp

bronze_schema = StructType([
    # ── Header fields (present on every packet) ──────────────────────────
    StructField("m_packetId",        IntegerType(),   True),
    StructField("m_playerCarIndex",  IntegerType(),   True),
    StructField("timestamp",         StringType(),    True),
    StructField("raw_size",          IntegerType(),   True),

    # ── Packet 6: Car Telemetry ───────────────────────────────────────────
    StructField("speed_kmh",         IntegerType(),   True),
    StructField("engine_rpm",        IntegerType(),   True),
    StructField("gear",              IntegerType(),   True),
    StructField("throttle",          FloatType(),     True),
    StructField("brake",             FloatType(),     True),
    StructField("engine_temperature",IntegerType(),   True),

    # ── Packet 3: Events ──────────────────────────────────────────────────
    StructField("eventCode",         StringType(),    True),

    # ── Packet 7: Car Status ──────────────────────────────────────────────
    StructField("fuel_in_tank",      FloatType(),     True),
    StructField("ers_energy",        FloatType(),     True),
    StructField("tyre_compound",     StringType(),    True),
    StructField("tyre_age_laps",     IntegerType(),   True),
    StructField("drs_activation",    BooleanType(),   True),

    # ── Packet 10: Car Damage ─────────────────────────────────────────────
    StructField("front_wing_damage", FloatType(),     True),
    StructField("rear_wing_damage",  FloatType(),     True),
    StructField("engine_wear",       FloatType(),     True),
    StructField("tyre_wear",         FloatType(),     True),
])

# COMMAND ----------
# MAGIC %md ## 4. Read stream from Event Hub and parse JSON

raw_stream = (
    spark.readStream
         .format("kafka")
         .options(**kafka_options)
         .load()
)

# Event Hub messages: key=partition_key (bytes), value=JSON payload (bytes)
bronze_df = (
    raw_stream
    .select(from_json(col("value").cast("string"), bronze_schema).alias("d"))
    .select("d.*")
    .withColumn("timestamp", to_timestamp(col("timestamp")))
)

# COMMAND ----------
# MAGIC %md ## 5. Write to Bronze Delta table

query = (
    bronze_df.writeStream
             .format("delta")
             .outputMode("append")
             .option("checkpointLocation", CHECKPOINT_DIR)
             .option("mergeSchema", "true")
             .toTable(BRONZE_TABLE)
)

print(f"Bronze stream started. Writing to {BRONZE_TABLE}")
