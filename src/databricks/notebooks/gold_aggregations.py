# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Layer Aggregations
# MAGIC Reads from the four Silver Delta tables and produces 4 Gold datamarts for dashboard widgets.
# MAGIC
# MAGIC | Gold table              | Source(s)                       | Metric                             |
# MAGIC |-------------------------|---------------------------------|------------------------------------|
# MAGIC | `gold_distances`        | silver_telemetry                | Distance + avg speed per 1s window |
# MAGIC | `gold_vehicle_health`   | silver_status + silver_damage   | Latest health snapshot             |
# MAGIC | `gold_tyre_degradation` | silver_telemetry + silver_damage| Wear vs distance per compound      |
# MAGIC | `gold_driver_gaps`      | silver_telemetry                | Gap to race leader in meters       |

# COMMAND ----------

CHECKPOINT_BASE  = "/tmp/checkpoints/gold"

SILVER_TELEMETRY = "f1_catalog.silver.silver_telemetry"
SILVER_STATUS    = "f1_catalog.silver.silver_status"
SILVER_DAMAGE    = "f1_catalog.silver.silver_damage"

GOLD_DISTANCES   = "f1_catalog.gold.gold_distances"
GOLD_HEALTH      = "f1_catalog.gold.gold_vehicle_health"
GOLD_TYRE_DEG    = "f1_catalog.gold.gold_tyre_degradation"
GOLD_GAPS        = "f1_catalog.gold.gold_driver_gaps"

# 60 Hz sampling → dt ≈ 0.01667 s per packet
DT_SECONDS = 1 / 60.0

# COMMAND ----------

from pyspark.sql.functions import col, window, sum as _sum, avg, max as _max
import pyspark.sql.functions as F
from pyspark.sql.window import Window

s_telemetry = spark.readStream.table(SILVER_TELEMETRY)
s_status    = spark.readStream.table(SILVER_STATUS)
s_damage    = spark.readStream.table(SILVER_DAMAGE)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Gold: Driver Distances

# COMMAND ----------

distances = (
    s_telemetry
    .withWatermark("timestamp", "2 seconds")
    .withColumn("distance_delta_m", (col("speed_kmh") / 3.6) * DT_SECONDS)
    .groupBy(window(col("timestamp"), "1 second"), col("car_index"))
    .agg(
        _sum("distance_delta_m").alias("segment_distance"),
        avg("speed_kmh").alias("avg_speed"),
    )
)

query_distances = (
    distances.writeStream
             .format("delta")
             .outputMode("append")
             .option("checkpointLocation", f"{CHECKPOINT_BASE}/distances")
             .toTable(GOLD_DISTANCES)
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Gold: Vehicle Health

# COMMAND ----------

status_agg = (
    s_status
    .withWatermark("timestamp", "2 seconds")
    .groupBy(window(col("timestamp"), "1 second"), col("car_index"))
    .agg(
        _max("fuel_in_tank").alias("fuel_in_tank"),
        _max("ers_energy").alias("ers_energy"),
        _max("drs_activation").alias("drs_activation"),
        _max("tyre_compound").alias("tyre_compound"),
        _max("tyre_age_laps").alias("tyre_age_laps"),
    )
)

damage_agg = (
    s_damage
    .withWatermark("timestamp", "2 seconds")
    .groupBy(window(col("timestamp"), "1 second"), col("car_index"))
    .agg(
        _max("tyre_wear").alias("tyre_wear"),
        _max("engine_wear").alias("engine_wear"),
        _max("front_wing_damage").alias("front_wing_damage"),
        _max("rear_wing_damage").alias("rear_wing_damage"),
    )
)

vehicle_health = (
    status_agg
    .join(damage_agg, on=["window", "car_index"], how="inner")
    .select(
        col("car_index"),
        col("window.end").alias("last_updated"),
        col("tyre_wear"),
        col("engine_wear"),
        col("front_wing_damage"),
        col("rear_wing_damage"),
        col("fuel_in_tank"),
        col("ers_energy"),
        col("drs_activation"),
    )
)

query_health = (
    vehicle_health.writeStream
                  .format("delta")
                  .outputMode("append")
                  .option("checkpointLocation", f"{CHECKPOINT_BASE}/vehicle_health")
                  .toTable(GOLD_HEALTH)
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Gold: Tyre Degradation

# COMMAND ----------

telem_dist = (
    s_telemetry
    .withWatermark("timestamp", "2 seconds")
    .withColumn("distance_delta_m", (col("speed_kmh") / 3.6) * DT_SECONDS)
    .groupBy(window(col("timestamp"), "1 second"), col("car_index"))
    .agg(_sum("distance_delta_m").alias("distance_traveled_m"))
)

status_compound = (
    s_status
    .withWatermark("timestamp", "2 seconds")
    .groupBy(window(col("timestamp"), "1 second"), col("car_index"))
    .agg(_max("tyre_compound").alias("tyre_compound"))
)

damage_wear = (
    s_damage
    .withWatermark("timestamp", "2 seconds")
    .groupBy(window(col("timestamp"), "1 second"), col("car_index"))
    .agg(avg("tyre_wear").alias("average_wear_pct"))
)

tyre_deg = (
    telem_dist
    .join(damage_wear,     on=["window", "car_index"], how="inner")
    .join(status_compound, on=["window", "car_index"], how="left")
    .select(
        col("window"),
        col("tyre_compound"),
        col("car_index"),
        col("distance_traveled_m"),
        col("average_wear_pct"),
    )
)

query_tyre_deg = (
    tyre_deg.writeStream
            .format("delta")
            .outputMode("append")
            .option("checkpointLocation", f"{CHECKPOINT_BASE}/tyre_degradation")
            .toTable(GOLD_TYRE_DEG)
)

# COMMAND ----------
# MAGIC %md
# MAGIC ## Gold: Head-to-Head Driver Gaps
# MAGIC
# MAGIC Structured Streaming does not support stream-stream self-joins, so we use
# MAGIC `foreachBatch` to compute the gap to the race leader within each micro-batch.

# COMMAND ----------

from pyspark.sql import DataFrame

def compute_gaps(batch_df: DataFrame, batch_id: int):
    if batch_df.rdd.isEmpty():
        return

    w = Window.partitionBy("window").orderBy(F.desc("segment_distance"))

    gaps = (
        batch_df
        .withColumn("leader_distance", F.first("segment_distance").over(w))
        .withColumn("gap_to_leader_m", col("leader_distance") - col("segment_distance"))
        .select(
            col("window"),
            col("car_index"),
            col("segment_distance"),
            col("gap_to_leader_m"),
        )
    )

    gaps.write.format("delta").mode("append").saveAsTable(GOLD_GAPS)


distances_for_gaps = (
    s_telemetry
    .withWatermark("timestamp", "2 seconds")
    .withColumn("distance_delta_m", (col("speed_kmh") / 3.6) * DT_SECONDS)
    .groupBy(window(col("timestamp"), "1 second"), col("car_index"))
    .agg(_sum("distance_delta_m").alias("segment_distance"))
)

query_gaps = (
    distances_for_gaps.writeStream
                      .foreachBatch(compute_gaps)
                      .option("checkpointLocation", f"{CHECKPOINT_BASE}/driver_gaps")
                      .trigger(processingTime="1 second")
                      .start()
)

# COMMAND ----------

print("All 4 Gold streams started:")
print(f"  Distances        → {GOLD_DISTANCES}")
print(f"  Vehicle Health   → {GOLD_HEALTH}")
print(f"  Tyre Degradation → {GOLD_TYRE_DEG}")
print(f"  Driver Gaps      → {GOLD_GAPS}")
