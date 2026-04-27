# Databricks notebook source
# /// script
# [tool.databricks.environment]
# environment_version = "2"
# ///
# MAGIC %md
# MAGIC # Bronze Ingestion: Raw Telemetry Stream
# MAGIC Ingests UDP packets sent to Azure Event Hub via our Python Edge Script.

# COMMAND ----------

import sys
sys.path.append("/Workspace/Users/ayushmaan1362@gmail.com/f1-telemetry-streaming")

from src.databricks.lib.streaming_utils import get_kafka_read_stream, parse_kafka_json
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, FloatType

# Community Edition workaround: Define connection string directly as a string or via Databricks Widgets
# Replace this fallback string with your actual Event Hub string from your .env file
CONNECTION_STRING = ">REDACTED_EVENT_HUB_CONNECTION_STRING"

TOPIC = "telemetry-topic"

# COMMAND ----------

base_schema = StructType([
    StructField("m_packetId", IntegerType(), True),
    StructField("m_playerCarIndex", IntegerType(), True),
    StructField("timestamp", StringType(), True),
    StructField("raw_size", IntegerType(), True)
])

# COMMAND ----------

raw_df = get_kafka_read_stream(spark, CONNECTION_STRING, TOPIC)
bronze_df = parse_kafka_json(raw_df, base_schema)

# Write to f1_catalog.bronze schema
query = bronze_df.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "/Workspace/Users/ayushmaan1362@gmail.com/f1-telemetry-streaming/checkpoints/bronze_telemetry") \
    .trigger(availableNow=True) \
    .table("f1_catalog.bronze.bronze_telemetry")
