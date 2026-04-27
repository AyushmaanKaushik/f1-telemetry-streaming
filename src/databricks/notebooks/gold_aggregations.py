# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer Aggregations
# MAGIC Advanced Datamarts for Dashboards

# COMMAND ----------

from pyspark.sql.functions import col, sum as _sum, avg, window, max as _max
import pyspark.sql.functions as F

# COMMAND ----------

# Load our distinct Silver schemas
silver_telemetry = spark.readStream.format("delta").load("/tmp/tables/silver_telemetry")
silver_damage = spark.readStream.format("delta").load("/tmp/tables/silver_damage")
silver_status = spark.readStream.format("delta").load("/tmp/tables/silver_status")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 1. Head-to-Head Gaps (Distance Traveled)
# MAGIC Distance (meters) = (Speed * (1000/3600)) * dt. 60Hz dt = 0.0166

distance_query = silver_telemetry \
    .withColumn("distance_delta_m", (col("speed_kmh") / 3.6) * 0.0166) \
    .withWatermark("timestamp", "2 seconds") \
    .groupBy(
        window(col("timestamp"), "1 second"),
        col("car_index")
    ) \
    .agg(
        _sum("distance_delta_m").alias("segment_distance")
    )

query_gaps = distance_query.writeStream \
    .format("delta").outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/gold_driver_gaps") \
    .start("/tmp/tables/gold_driver_gaps")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 2. Tyre Degradation (Wear vs Distance)

# Assumes we join telemetry distance with damage wear via watermark windows
telemetry_dist = silver_telemetry \
    .withColumn("distance", (col("speed_kmh") / 3.6) * 0.0166) \
    .withWatermark("timestamp", "2 seconds") \
    .groupBy(window(col("timestamp"), "1 second"), col("car_index")) \
    .agg(_sum("distance").alias("distance_traveled_m"))

damage_wear = silver_damage \
    .withWatermark("timestamp", "2 seconds") \
    .groupBy(window(col("timestamp"), "1 second"), col("car_index")) \
    .agg(avg("tyre_wear").alias("average_wear_pct"))

# Stream-stream join
joined_wear = telemetry_dist.join(
    damage_wear,
    ["car_index", "window"],
    "inner"
)

query_deg = joined_wear.writeStream \
    .format("delta").outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/gold_tyre_degradation") \
    .start("/tmp/tables/gold_tyre_degradation")

# COMMAND ----------
# MAGIC %md
# MAGIC ## 3. Vehicle Health Snapshots

status_snapshot = silver_status \
    .withWatermark("timestamp", "2 seconds") \
    .groupBy(window(col("timestamp"), "1 second"), col("car_index")) \
    .agg(
        _max("fuel_in_tank").alias("fuel_in_tank"),
        _max("ers_energy").alias("ers_energy"),
        _max("drs_activation").alias("drs_activation")
    )

damage_snapshot = silver_damage \
    .withWatermark("timestamp", "2 seconds") \
    .groupBy(window(col("timestamp"), "1 second"), col("car_index")) \
    .agg(
        _max("tyre_wear").alias("tyre_wear"),
        _max("engine_wear").alias("engine_wear"),
        _max("front_wing_damage").alias("front_wing_damage"),
        _max("rear_wing_damage").alias("rear_wing_damage")
    )

health_join = status_snapshot.join(damage_snapshot, ["car_index", "window"], "inner")

query_health = health_join.writeStream \
    .format("delta").outputMode("append") \
    .option("checkpointLocation", "/tmp/checkpoints/gold_vehicle_health") \
    .start("/tmp/tables/gold_vehicle_health")
