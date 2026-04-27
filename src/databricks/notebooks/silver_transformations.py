# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Transformations
# MAGIC Multiplexes Bronze stream into 4 Dedicated Silver Delta Tables

# COMMAND ----------

from pyspark.sql.functions import col, to_timestamp, from_json
from pyspark.sql.types import *

# COMMAND ----------

# Read from Unity Catalog governed table
bronze_stream = spark.readStream.table("f1_catalog.bronze.bronze_telemetry")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Dedicated Silver Filtering

# 1. Events (Packet 3)
events_schema = StructType([StructField("eventStringCode", StringType())])

silver_events = bronze_stream.filter(col("m_packetId") == 3) \
    .withColumn("parsed", from_json(col("data"), events_schema)) \
    .select(
        col("m_packetId").alias("packet_id"),
        col("m_playerCarIndex").alias("car_index"),
        to_timestamp("timestamp").alias("timestamp"),
        col("parsed.eventStringCode").alias("event_code")
    )

query_events = silver_events.writeStream \
    .format("delta").outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/silver_events") \
    .start("/tmp/tables/silver_events")

# COMMAND ----------
# 2. Telemetry (Packet 6)
telemetry_schema = StructType([
    StructField("speed", IntegerType()),
    StructField("engineRPM", IntegerType()),
    StructField("gear", IntegerType()),
    StructField("throttle", FloatType()),
    StructField("brake", FloatType()),
    StructField("engineTemperature", IntegerType())
])

silver_telemetry = bronze_stream.filter(col("m_packetId") == 6) \
    .withColumn("parsed", from_json(col("data"), telemetry_schema)) \
    .select(
        col("m_packetId").alias("packet_id"),
        col("m_playerCarIndex").alias("car_index"),
        to_timestamp("timestamp").alias("timestamp"),
        col("parsed.speed").alias("speed_kmh"),
        (col("parsed.engineRPM") / 15000.0).alias("engine_rpm_normalized"),
        col("parsed.gear").alias("gear"),
        col("parsed.throttle").alias("throttle"),
        col("parsed.brake").alias("brake"),
        col("parsed.engineTemperature").alias("engine_temperature")
    )

query_telemetry = silver_telemetry.writeStream \
    .format("delta").outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/silver_telemetry") \
    .start("/tmp/tables/silver_telemetry")

# COMMAND ----------
# 3. Status (Packet 7)
status_schema = StructType([
    StructField("fuelInTank", FloatType()),
    StructField("ersStoreEnergy", FloatType()),
    StructField("actualTyreCompound", IntegerType()),
    StructField("tyresAgeLaps", IntegerType()),
    StructField("drsActivation", IntegerType())
])

silver_status = bronze_stream.filter(col("m_packetId") == 7) \
    .withColumn("parsed", from_json(col("data"), status_schema)) \
    .select(
        col("m_packetId").alias("packet_id"),
        col("m_playerCarIndex").alias("car_index"),
        to_timestamp("timestamp").alias("timestamp"),
        col("parsed.fuelInTank").alias("fuel_in_tank"),
        col("parsed.ersStoreEnergy").alias("ers_energy"),
        col("parsed.actualTyreCompound").cast("string").alias("tyre_compound"),
        col("parsed.tyresAgeLaps").alias("tyre_age_laps"),
        col("parsed.drsActivation").cast("boolean").alias("drs_activation")
    )

query_status = silver_status.writeStream \
    .format("delta").outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/silver_status") \
    .start("/tmp/tables/silver_status")

# COMMAND ----------
# 4. Damage (Packet 10)
damage_schema = StructType([
    StructField("frontLeftWingDamage", FloatType()),
    StructField("rearWingDamage", FloatType()),
    StructField("engineDamage", FloatType()),
    StructField("tyresDamage", ArrayType(FloatType()))
])

silver_damage = bronze_stream.filter(col("m_packetId") == 10) \
    .withColumn("parsed", from_json(col("data"), damage_schema)) \
    .select(
        col("m_packetId").alias("packet_id"),
        col("m_playerCarIndex").alias("car_index"),
        to_timestamp("timestamp").alias("timestamp"),
        col("parsed.frontLeftWingDamage").alias("front_wing_damage"), 
        col("parsed.rearWingDamage").alias("rear_wing_damage"),
        col("parsed.engineDamage").alias("engine_wear"),
        col("parsed.tyresDamage").getItem(0).alias("tyre_wear") 
    )

query_damage = silver_damage.writeStream \
    .format("delta").outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/silver_damage") \
    .start("/tmp/tables/silver_damage")
