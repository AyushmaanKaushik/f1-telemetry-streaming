# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer Aggregations
# MAGIC Distance-to-Space Conversion for Driver Gap Analysis

# COMMAND ----------

from pyspark.sql.functions import col, sum as _sum, window
import pyspark.sql.functions as F

# COMMAND ----------

silver_telemetry = spark.readStream.table("f1_catalog.silver.car_telemetry")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Distance Calculation
# MAGIC Assume speed is km/h, freq is ~60Hz (approx 16.6ms spacing).
# MAGIC Distance (meters) = (Speed * (1000/3600)) * dt.
# MAGIC For a real-world scenario, window functions accumulate distance over the session.

distance_query = silver_telemetry \
    .withColumn("distance_delta_m", (col("data.speed_kmh") / 3.6) * 0.0166) \
    .groupBy(
        window(col("timestamp"), "1 second"),
        col("m_playerCarIndex")
    ) \
    .agg(
        _sum("distance_delta_m").alias("segment_distance")
    )

# COMMAND ----------

query = distance_query.writeStream \
    .format("delta") \
    .outputMode("complete") \
    .option("checkpointLocation", "/mnt/datalake/checkpoints/gold_telemetry") \
    .table("f1_catalog.gold.driver_distances")

# COMMAND ----------
