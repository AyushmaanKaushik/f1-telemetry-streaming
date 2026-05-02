# Databricks notebook source
# MAGIC %md
# MAGIC # F1 Telemetry: Serverless Real-time Pipeline
# MAGIC Serverless compute prevents infinite streaming triggers. To bypass this and achieve 
# MAGIC real-time latency, this notebook runs a `while True` loop that continuously executes 
# MAGIC `AvailableNow` micro-batches sequentially (Bronze -> Silver -> Gold).

# COMMAND ----------

# MAGIC %sql
# MAGIC CREATE SCHEMA IF NOT EXISTS f1_catalog.bronze;
# MAGIC CREATE VOLUME IF NOT EXISTS f1_catalog.bronze.checkpoints;
# MAGIC CREATE SCHEMA IF NOT EXISTS f1_catalog.silver;
# MAGIC CREATE VOLUME IF NOT EXISTS f1_catalog.silver.checkpoints;
# MAGIC CREATE SCHEMA IF NOT EXISTS f1_catalog.gold;
# MAGIC CREATE VOLUME IF NOT EXISTS f1_catalog.gold.checkpoints;

# COMMAND ----------

import time
import pyspark.sql.functions as F
from pyspark.sql.types import *
from pyspark.sql.functions import col, from_json, to_timestamp, window, sum as _sum, avg, max as _max
from pyspark.sql.window import Window
from pyspark.sql import DataFrame

# Configuration & Secrets
EH_NAMESPACE = dbutils.secrets.get(scope="f1_scope", key="eventhub_namespace")
EH_NAME      = dbutils.secrets.get(scope="f1_scope", key="eventhub_name")
EH_CONN_STR  = dbutils.secrets.get(scope="f1_scope", key="eventhub_conn_str")

# Tables
BRONZE_TABLE     = "f1_catalog.bronze.bronze_telemetry"
SILVER_EVENTS    = "f1_catalog.silver.silver_events"
SILVER_TELEMETRY = "f1_catalog.silver.silver_telemetry"
SILVER_STATUS    = "f1_catalog.silver.silver_status"
SILVER_DAMAGE    = "f1_catalog.silver.silver_damage"
GOLD_DISTANCES   = "f1_catalog.gold.gold_distances"
GOLD_HEALTH      = "f1_catalog.gold.gold_vehicle_health"
GOLD_TYRE_DEG    = "f1_catalog.gold.gold_tyre_degradation"
GOLD_GAPS        = "f1_catalog.gold.gold_driver_gaps"

# Checkpoints
CHK_BRONZE = "/Volumes/f1_catalog/bronze/checkpoints/bronze_telemetry"
CHK_SILVER = "/Volumes/f1_catalog/silver/checkpoints"
CHK_GOLD   = "/Volumes/f1_catalog/gold/checkpoints"

DT_SECONDS = 1 / 60.0

print("Configurations loaded.")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Define DataFrame Plans
# MAGIC We build the Spark execution plans once. The `while True` loop will execute them.

# COMMAND ----------

# =========================
# BRONZE LAYER
# =========================
eh_sasl = (
    'kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule required '
    'username="$ConnectionString" '
    f'password="{EH_CONN_STR}";'
)
kafka_options = {
    "kafka.bootstrap.servers":  EH_NAMESPACE,
    "kafka.security.protocol":  "SASL_SSL",
    "kafka.sasl.mechanism":     "PLAIN",
    "kafka.sasl.jaas.config":   eh_sasl,
    "kafka.request.timeout.ms": "60000",
    "kafka.session.timeout.ms": "30000",
    "subscribe":                EH_NAME,
    "startingOffsets":          "latest",
    "failOnDataLoss":           "false",
}
bronze_schema = StructType([
    StructField("m_packetId", IntegerType(), True), StructField("m_playerCarIndex", IntegerType(), True),
    StructField("timestamp", StringType(), True), StructField("raw_size", IntegerType(), True),
    StructField("speed_kmh", IntegerType(), True), StructField("engine_rpm", IntegerType(), True),
    StructField("gear", IntegerType(), True), StructField("throttle", FloatType(), True),
    StructField("brake", FloatType(), True), StructField("engine_temperature", IntegerType(), True),
    StructField("eventCode", StringType(), True), StructField("fuel_in_tank", FloatType(), True),
    StructField("ers_energy", FloatType(), True), StructField("tyre_compound", StringType(), True),
    StructField("tyre_age_laps", IntegerType(), True), StructField("drs_activation", BooleanType(), True),
    StructField("front_wing_damage", FloatType(), True), StructField("rear_wing_damage", FloatType(), True),
    StructField("engine_wear", FloatType(), True), StructField("tyre_wear", FloatType(), True),
])

raw_stream = spark.readStream.format("kafka").options(**kafka_options).load()
bronze_df = raw_stream.select(from_json(col("value").cast("string"), bronze_schema).alias("d")).select("d.*").withColumn("timestamp", to_timestamp(col("timestamp")))

# =========================
# SILVER LAYER
# =========================
bronze_stream = spark.readStream.table(BRONZE_TABLE)

silver_events = bronze_stream.filter(col("m_packetId") == 3).select(col("m_packetId").cast("int").alias("packet_id"), col("m_playerCarIndex").cast("int").alias("car_index"), col("timestamp"), col("eventCode").alias("event_code"))
silver_telemetry = bronze_stream.filter(col("m_packetId") == 6).select(
    col("m_packetId").cast("int").alias("packet_id"), col("m_playerCarIndex").cast("int").alias("car_index"), col("timestamp"),
    col("speed_kmh").cast("float"), (col("engine_rpm") / 15000.0).alias("engine_rpm_normalized"), col("gear").cast("int"),
    col("throttle").cast("float"), col("brake").cast("float"), col("engine_temperature").cast("int")
)
silver_status = bronze_stream.filter(col("m_packetId") == 7).select(
    col("m_packetId").cast("int").alias("packet_id"), col("m_playerCarIndex").cast("int").alias("car_index"), col("timestamp"),
    col("fuel_in_tank").cast("float"), col("ers_energy").cast("float"), col("tyre_compound"), col("tyre_age_laps").cast("int"), col("drs_activation").cast("boolean")
)
silver_damage = bronze_stream.filter(col("m_packetId") == 10).select(
    col("m_packetId").cast("int").alias("packet_id"), col("m_playerCarIndex").cast("int").alias("car_index"), col("timestamp"),
    col("front_wing_damage").cast("float"), col("rear_wing_damage").cast("float"), col("engine_wear").cast("float"), col("tyre_wear").cast("float")
)

# =========================
# GOLD LAYER
# =========================
s_telemetry = spark.readStream.table(SILVER_TELEMETRY)
s_status    = spark.readStream.table(SILVER_STATUS)
s_damage    = spark.readStream.table(SILVER_DAMAGE)

distances = s_telemetry.withColumn("timestamp", col("timestamp").cast("timestamp")).withWatermark("timestamp", "2 seconds").withColumn("distance_delta_m", (col("speed_kmh") / 3.6) * DT_SECONDS).groupBy(window(col("timestamp"), "1 second"), col("car_index")).agg(_sum("distance_delta_m").alias("segment_distance"), avg("speed_kmh").alias("avg_speed"))

status_agg = s_status.withColumn("timestamp", col("timestamp").cast("timestamp")).withWatermark("timestamp", "2 seconds").groupBy(window(col("timestamp"), "1 second"), col("car_index")).agg(_max("fuel_in_tank").alias("fuel_in_tank"), _max("ers_energy").alias("ers_energy"), _max("drs_activation").alias("drs_activation"), _max("tyre_compound").alias("tyre_compound"), _max("tyre_age_laps").alias("tyre_age_laps"))
damage_agg = s_damage.withColumn("timestamp", col("timestamp").cast("timestamp")).withWatermark("timestamp", "2 seconds").groupBy(window(col("timestamp"), "1 second"), col("car_index")).agg(_max("tyre_wear").alias("tyre_wear"), _max("engine_wear").alias("engine_wear"), _max("front_wing_damage").alias("front_wing_damage"), _max("rear_wing_damage").alias("rear_wing_damage"))
vehicle_health = status_agg.join(damage_agg, on=["window", "car_index"], how="inner").select(col("car_index"), col("window.end").alias("last_updated"), col("tyre_wear"), col("engine_wear"), col("front_wing_damage"), col("rear_wing_damage"), col("fuel_in_tank"), col("ers_energy"), col("drs_activation"))

# Re-use existing aggregated streams (distances, damage_agg, status_agg) to avoid duplicating state stores
tyre_deg = distances.join(damage_agg, on=["window", "car_index"], how="inner") \
                    .join(status_agg, on=["window", "car_index"], how="left") \
                    .select(
                        col("window"), 
                        col("tyre_compound"), 
                        col("car_index"), 
                        col("segment_distance").alias("distance_traveled_m"), 
                        col("tyre_wear").alias("average_wear_pct")
                    )

def compute_gaps(batch_df: DataFrame, batch_id: int):
    w = Window.partitionBy("window").orderBy(F.desc("segment_distance"))
    gaps = batch_df.withColumn("leader_distance", F.first("segment_distance").over(w)).withColumn("gap_to_leader_m", col("leader_distance") - col("segment_distance")).select(col("window"), col("car_index"), col("segment_distance"), col("gap_to_leader_m"))
    gaps.write.format("delta").mode("append").saveAsTable(GOLD_GAPS)
distances_for_gaps = s_telemetry.withColumn("timestamp", col("timestamp").cast("timestamp")).withWatermark("timestamp", "2 seconds").withColumn("distance_delta_m", (col("speed_kmh") / 3.6) * DT_SECONDS).groupBy(window(col("timestamp"), "1 second"), col("car_index")).agg(_sum("distance_delta_m").alias("segment_distance"))

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Start Continuous Streams
# MAGIC Using `processingTime` trigger to run streams concurrently.

# COMMAND ----------

TRIGGER_INTERVAL = "2 seconds"

print("🚀 Starting Sequential Micro-Batch Pipeline...")

# 1. BRONZE
print("Processing Bronze layer...")
q_bronze = bronze_df.writeStream.format("delta").outputMode("append").option("checkpointLocation", CHK_BRONZE).option("mergeSchema", "true").trigger(availableNow=True).toTable(BRONZE_TABLE)
q_bronze.awaitTermination()

# 2. SILVER
print("Processing Silver layer...")
q_events = silver_events.writeStream.format("delta").outputMode("append").option("checkpointLocation", f"{CHK_SILVER}/events").trigger(availableNow=True).toTable(SILVER_EVENTS)
q_telem = silver_telemetry.writeStream.format("delta").outputMode("append").option("checkpointLocation", f"{CHK_SILVER}/telemetry").trigger(availableNow=True).toTable(SILVER_TELEMETRY)
q_status = silver_status.writeStream.format("delta").outputMode("append").option("checkpointLocation", f"{CHK_SILVER}/status").trigger(availableNow=True).toTable(SILVER_STATUS)
q_damage = silver_damage.writeStream.format("delta").outputMode("append").option("checkpointLocation", f"{CHK_SILVER}/damage").trigger(availableNow=True).toTable(SILVER_DAMAGE)

q_events.awaitTermination()
q_telem.awaitTermination()
q_status.awaitTermination()
q_damage.awaitTermination()

# 3. GOLD
print("Processing Gold layer...")
q_dist = distances.writeStream.format("delta").outputMode("append").option("checkpointLocation", f"{CHK_GOLD}/distances").trigger(availableNow=True).toTable(GOLD_DISTANCES)
q_hlth = vehicle_health.writeStream.format("delta").outputMode("append").option("checkpointLocation", f"{CHK_GOLD}/vehicle_health").trigger(availableNow=True).toTable(GOLD_HEALTH)
q_gaps = distances_for_gaps.writeStream.foreachBatch(compute_gaps).option("checkpointLocation", f"{CHK_GOLD}/driver_gaps").trigger(availableNow=True).start()
q_tyre = tyre_deg.writeStream.format("delta").outputMode("append").option("checkpointLocation", f"{CHK_GOLD}/tyre_degradation_v2").trigger(availableNow=True).toTable(GOLD_TYRE_DEG)

q_dist.awaitTermination()
q_hlth.awaitTermination()
q_tyre.awaitTermination()
q_gaps.awaitTermination()

print("✅ Pipeline batch completed successfully.")
