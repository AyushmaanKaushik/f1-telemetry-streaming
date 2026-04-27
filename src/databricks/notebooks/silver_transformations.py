# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Transformations
# MAGIC Reads `f1_catalog.bronze.bronze_telemetry` and fans out into 4 typed Silver Delta tables.
# MAGIC
# MAGIC | Packet ID | Silver table         | Freq  |
# MAGIC |-----------|----------------------|-------|
# MAGIC | 3         | silver_events        | Event |
# MAGIC | 6         | silver_telemetry     | ~60Hz |
# MAGIC | 7         | silver_status        | ~2Hz  |
# MAGIC | 10        | silver_damage        | ~2Hz  |

# COMMAND ----------

CHECKPOINT_BASE  = "/tmp/checkpoints/silver"
BRONZE_TABLE     = "f1_catalog.bronze.bronze_telemetry"

SILVER_EVENTS    = "f1_catalog.silver.silver_events"
SILVER_TELEMETRY = "f1_catalog.silver.silver_telemetry"
SILVER_STATUS    = "f1_catalog.silver.silver_status"
SILVER_DAMAGE    = "f1_catalog.silver.silver_damage"

# COMMAND ----------

from pyspark.sql.functions import col

bronze_stream = spark.readStream.table(BRONZE_TABLE)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Packet 3 — Events

# COMMAND ----------

silver_events = (
    bronze_stream
    .filter(col("m_packetId") == 3)
    .select(
        col("m_packetId").cast("int").alias("packet_id"),
        col("m_playerCarIndex").cast("int").alias("car_index"),
        col("timestamp"),
        col("eventCode").alias("event_code"),
    )
)

query_events = (
    silver_events.writeStream
                 .format("delta")
                 .outputMode("append")
                 .option("checkpointLocation", f"{CHECKPOINT_BASE}/events")
                 .toTable(SILVER_EVENTS)
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Packet 6 — Car Telemetry (~60 Hz)

# COMMAND ----------

silver_telemetry = (
    bronze_stream
    .filter(col("m_packetId") == 6)
    .select(
        col("m_packetId").cast("int").alias("packet_id"),
        col("m_playerCarIndex").cast("int").alias("car_index"),
        col("timestamp"),
        col("speed_kmh").cast("float"),
        (col("engine_rpm") / 15000.0).alias("engine_rpm_normalized"),
        col("gear").cast("int"),
        col("throttle").cast("float"),
        col("brake").cast("float"),
        col("engine_temperature").cast("int"),
    )
)

query_telemetry = (
    silver_telemetry.writeStream
                    .format("delta")
                    .outputMode("append")
                    .option("checkpointLocation", f"{CHECKPOINT_BASE}/telemetry")
                    .toTable(SILVER_TELEMETRY)
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Packet 7 — Car Status (~2 Hz)

# COMMAND ----------

silver_status = (
    bronze_stream
    .filter(col("m_packetId") == 7)
    .select(
        col("m_packetId").cast("int").alias("packet_id"),
        col("m_playerCarIndex").cast("int").alias("car_index"),
        col("timestamp"),
        col("fuel_in_tank").cast("float"),
        col("ers_energy").cast("float"),
        col("tyre_compound"),
        col("tyre_age_laps").cast("int"),
        col("drs_activation").cast("boolean"),
    )
)

query_status = (
    silver_status.writeStream
                 .format("delta")
                 .outputMode("append")
                 .option("checkpointLocation", f"{CHECKPOINT_BASE}/status")
                 .toTable(SILVER_STATUS)
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Packet 10 — Car Damage (~2 Hz)

# COMMAND ----------

silver_damage = (
    bronze_stream
    .filter(col("m_packetId") == 10)
    .select(
        col("m_packetId").cast("int").alias("packet_id"),
        col("m_playerCarIndex").cast("int").alias("car_index"),
        col("timestamp"),
        col("front_wing_damage").cast("float"),
        col("rear_wing_damage").cast("float"),
        col("engine_wear").cast("float"),
        col("tyre_wear").cast("float"),
    )
)

query_damage = (
    silver_damage.writeStream
                 .format("delta")
                 .outputMode("append")
                 .option("checkpointLocation", f"{CHECKPOINT_BASE}/damage")
                 .toTable(SILVER_DAMAGE)
)

# COMMAND ----------

print("All 4 Silver streams started:")
print(f"  Events    → {SILVER_EVENTS}")
print(f"  Telemetry → {SILVER_TELEMETRY}")
print(f"  Status    → {SILVER_STATUS}")
print(f"  Damage    → {SILVER_DAMAGE}")
