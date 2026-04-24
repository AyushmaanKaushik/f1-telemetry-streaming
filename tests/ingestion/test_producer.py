import pytest
from src.ingestion.eventhub_producer import EventHubProducer

def test_producer_initialization(mock_eventhub_connection_string):
    producer = EventHubProducer()
    assert producer is not None
