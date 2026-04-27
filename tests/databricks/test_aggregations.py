import pytest
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder \
        .appName("testing") \
        .master("local[2]") \
        .getOrCreate()

def test_distance_aggregation(spark):
    data = [
        (1, "2023-01-01T12:00:00Z", 360.0), # 100 m/s
        (1, "2023-01-01T12:00:00Z", 360.0)  # 100 m/s
    ]
    df = spark.createDataFrame(data, ["car_index", "timestamp", "speed_kmh"])
    dist_df = df.withColumn("distance_delta_m", (col("speed_kmh") / 3.6) * 0.0166)
    results = dist_df.collect()
    
    # 100 m/s * 0.0166 seconds = 1.66 meters
    assert abs(results[0]["distance_delta_m"] - 1.66) < 0.001
    assert abs(results[1]["distance_delta_m"] - 1.66) < 0.001
