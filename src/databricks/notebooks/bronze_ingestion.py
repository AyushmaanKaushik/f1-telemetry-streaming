# Databricks notebook source
# MAGIC %md
# MAGIC # Bronze Ingestion: Raw Telemetry Stream
# MAGIC Ingests UDP packets sent to Azure Event Hub via our Python Edge Script.

# COMMAND ----------

import sys
sys.path.append("/Workspace/Repos/your_repo/f1-telemetry-streaming")

from src.databricks.lib.streaming_utils import get_kafka_read_stream, parse_kafka_json
from pyspark.sql.types import StructType, StructField, IntegerType, StringType, FloatType

# Community Edition workaround: Define connection string directly as a string or via Databricks Widgets
# Replace this fallback string with your actual Event Hub string from your .env file
CONNECTION_STRING = "Endpoint=sb://f1-car-telemetry-data.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=8xkZP1VO7NWQTOnynIoxUVIb2/XnkcEex+AEhAN3Vbk=;EntityPath=telemetry-topic"

TOPIC = "telemetry-topic"

# COMMAND ----------

# Schema defining the core envelope shared by all packets
base_schema = StructType([
    StructField("m_packetId", IntegerType(), True),
    StructField("m_playerCarIndex", IntegerType(), True),
    StructField("timestamp", StringType(), True),
    StructField("raw_size", IntegerType(), True)
])

# COMMAND ----------

raw_df = get_kafka_read_stream(spark, CONNECTION_STRING, TOPIC)
bronze_df = parse_kafka_json(raw_df, base_schema)

# Community Edition: Write to internal DBFS rather than external mounted Datalakes / Unity Catalog
query = bronze_df.writeStream \
    .format("delta") \
    .outputMode("append") \
    .option("checkpointLocation", "/FileStore/checkpoints/bronze_telemetry") \
    .table("default.bronze_telemetry")

# COMMAND ----------
