# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Transformations
# MAGIC Multiplexes Bronze stream into 4 Dedicated Silver Delta Tables

# COMMAND ----------

from pyspark.sql.functions import col, to_timestamp
from pyspark.sql.types import *

# COMMAND ----------

# Read from Local Community Edition Path (bypassing Unity Catalog and DBFS root locks)
bronze_stream = spark.readStream.format("delta").load("/tmp/tables/bronze_telemetry")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Dedicated Silver Filtering

# 1. Events (Packet 3)
silver_events = bronze_stream.filter(col("m_packetId") == 3) \
    .select(
        col("m_packetId").alias("packet_id"),
        col("m_playerCarIndex").alias("car_index"),
        to_timestamp("timestamp").alias("timestamp"),
        col("data.eventStringCode").alias("event_code")
    )

query_events = silver_events.writeStream \
    .format("delta").outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/silver_events") \
    .start("/tmp/tables/silver_events")

# COMMAND ----------
# 2. Telemetry (Packet 6)
silver_telemetry = bronze_stream.filter(col("m_packetId") == 6) \
    .select(
        col("m_packetId").alias("packet_id"),
        col("m_playerCarIndex").alias("car_index"),
        to_timestamp("timestamp").alias("timestamp"),
        col("data.speed").alias("speed_kmh"),
        (col("data.engineRPM") / 15000.0).alias("engine_rpm_normalized"),
        col("data.gear").alias("gear"),
        col("data.throttle").alias("throttle"),
        col("data.brake").alias("brake"),
        col("data.engineTemperature").alias("engine_temperature")
    )

query_telemetry = silver_telemetry.writeStream \
    .format("delta").outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/silver_telemetry") \
    .start("/tmp/tables/silver_telemetry")

# COMMAND ----------
# 3. Status (Packet 7)
silver_status = bronze_stream.filter(col("m_packetId") == 7) \
    .select(
        col("m_packetId").alias("packet_id"),
        col("m_playerCarIndex").alias("car_index"),
        to_timestamp("timestamp").alias("timestamp"),
        col("data.fuelInTank").alias("fuel_in_tank"),
        col("data.ersStoreEnergy").alias("ers_energy"),
        col("data.actualTyreCompound").cast("string").alias("tyre_compound"),
        col("data.tyresAgeLaps").alias("tyre_age_laps"),
        col("data.drsActivation").cast("boolean").alias("drs_activation")
    )

query_status = silver_status.writeStream \
    .format("delta").outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/silver_status") \
    .start("/tmp/tables/silver_status")

# COMMAND ----------
# 4. Damage (Packet 10)
silver_damage = bronze_stream.filter(col("m_packetId") == 10) \
    .select(
        col("m_packetId").alias("packet_id"),
        col("m_playerCarIndex").alias("car_index"),
        to_timestamp("timestamp").alias("timestamp"),
        col("data.frontLeftWingDamage").alias("front_wing_damage"), 
        col("data.rearWingDamage").alias("rear_wing_damage"),
        col("data.engineDamage").alias("engine_wear"),
        col("data.tyresDamage").getItem(0).alias("tyre_wear") 
    )

query_damage = silver_damage.writeStream \
    .format("delta").outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/silver_damage") \
    .start("/tmp/tables/silver_damage")
