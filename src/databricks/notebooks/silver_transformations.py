# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Transformations
# MAGIC Parses specific packet types and normalizes metrics (MinMax).

# COMMAND ----------

from pyspark.sql.functions import col, when
import pyspark.sql.functions as F

# COMMAND ----------

bronze_df = spark.readStream.table("f1_catalog.bronze.telemetry")

# COMMAND ----------
# MAGIC %md
# MAGIC ## Normalization (Packet ID 6: Car Telemetry)

telemetry_df = bronze_df.filter(col("m_packetId") == 6)

# Example Min-Max scaling for Engine RPM (assuming max 15000)
# RPM scaled to 0.0 - 1.0 logic
silver_telemetry = telemetry_df \
    .withColumn("engine_rpm_normalized", col("data.engine_rpm") / 15000.0) \
    .withColumn("timestamp", F.to_timestamp("timestamp"))

# COMMAND ----------
# MAGIC %md
# MAGIC ## Stateful Stream Processing for Active Status
# MAGIC Identifying RTMT (Retirement) from Packet 3 Event stream and combining it.
# MAGIC (Using Databricks transformWithState - Conceptual mapping as defined in research)

# In pyspark (Runtime 16.2+), this is achieved using applyInPandasWithState or the new native transformWithState
def process_retirement_state(key, pdfs, state):
    # Dummy logic to represent retirement tracking
    # If RTMT seen for playerCarIndex, flag as retired
    pass

# COMMAND ----------

query = silver_telemetry.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "/mnt/datalake/checkpoints/silver_telemetry") \
    .table("f1_catalog.silver.car_telemetry")

# COMMAND ----------
