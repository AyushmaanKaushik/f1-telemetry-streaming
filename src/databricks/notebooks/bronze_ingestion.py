# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Ingestion: Raw Telemetry Stream
# MAGIC Ingests UDP packets sent to Azure Event Hub via our Python Edge Script.

# COMMAND ----------

import sys
sys.path.append("/Workspace/Repos/your_repo/f1-telemetry-streaming")

from src.databricks.lib.streaming_utils import get_kafka_read_stream, parse_kafka_json
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, FloatType

# Assuming widgets or secrets are configured for credentials
EVENTHUB_BROKER = dbutils.secrets.get(scope="f1_scope", key="eventhub_broker")
TOPIC = "telemetry_topic"

# COMMAND ----------

# Schema defining the core envelope shared by all packets
base_schema = StructType([
    StructField("m_packetId", IntegerType(), True),
    StructField("m_playerCarIndex", IntegerType(), True),
    StructField("timestamp", StringType(), True),
    StructField("raw_size", IntegerType(), True)
])

# COMMAND ----------

raw_df = get_kafka_read_stream(spark, EVENTHUB_BROKER, TOPIC)
bronze_df = parse_kafka_json(raw_df, base_schema)

# Write to bronze delta table with append mode
query = bronze_df.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "/mnt/datalake/checkpoints/bronze_telemetry") \
    .table("f1_catalog.bronze.telemetry")

# COMMAND ----------
