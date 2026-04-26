import json
from confluent_kafka import Producer
from src.ingestion.config import config
from src.ingestion.logger import get_logger

logger = get_logger(__name__)

class EventHubProducer:
    def __init__(self):
        conf = {
            'bootstrap.servers': config.kafka_broker,
            'security.protocol': 'SASL_SSL',
            'sasl.mechanisms': 'PLAIN',
            'sasl.username': '$ConnectionString',
            'sasl.password': config.eventhub_connection_string,
        }
        try:
            self.producer = Producer(conf)
            logger.info("Successfully connected to Event Hub.")
        except Exception as e:
            logger.error(f"Failed to create producer: {e}")
            self.producer = None

    def delivery_report(self, err, msg):
        """ Called once for each message produced to indicate delivery result """
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def send_telemetry(self, partition_key: int, payload: dict):
        if not self.producer:
            return

        try:
            data = json.dumps(payload)
            self.producer.produce(
                topic=config.eventhub_name,
                key=str(partition_key).encode('utf-8'),
                value=data.encode('utf-8'),
                callback=self.delivery_report
            )
            self.producer.poll(0) # trigger callbacks
        except Exception as e:
            logger.error(f"Error producing message: {e}")
            
    def flush(self):
        if self.producer:
            self.producer.flush()
