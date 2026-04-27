from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType

def get_kafka_read_stream(spark: SparkSession, connection_string: str, topic: str):
    """
    Returns a streaming DataFrame reading from Event Hubs.
    """
    # Extract the broker URL (namespace.servicebus.windows.net:9093) from the connection string
    namespace = connection_string.split("Endpoint=sb://")[1].split("/")[0]
    broker = f"{namespace}:9093"
    
    # Event Hubs requires 'kafkashaded' Prefix only on Databricks Native, 
    # but for Community Edition standard kafka works better sometimes. 
    # We will use the correct module:
    jaas_config = f'kafkashaded.org.apache.kafka.common.security.plain.PlainLoginModule required username="$ConnectionString" password="{connection_string}";'
    
    return spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", broker) \
        .option("subscribe", topic) \
        .option("kafka.sasl.mechanism", "PLAIN") \
        .option("kafka.security.protocol", "SASL_SSL") \
        .option("kafka.sasl.jaas.config", jaas_config) \
        .option("startingOffsets", "latest") \
        .load()

def parse_kafka_json(df, schema: StructType):
    """
    Parses the binary 'value' payload from Kafka into structured columns.
    """
    return df.select(
        col("key").cast("string").alias("partition_key"),
        from_json(col("value").cast("string"), schema).alias("data"),
        col("timestamp").alias("kafka_timestamp")
    ).select("partition_key", "data.*", "kafka_timestamp")
