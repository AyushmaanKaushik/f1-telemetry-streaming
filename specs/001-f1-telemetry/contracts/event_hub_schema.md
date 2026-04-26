# Event Hub Telemetry Contract

The data sent to Azure Event Hubs must be formatted as JSON with the following overarching schema:

```json
{
  "m_packetId": 6,
  "m_playerCarIndex": 1,
  "timestamp": "2026-04-24T12:00:00Z",
  "payload": {
    "speed": 312,
    "rpm": 11500,
    "throttle": 1.0,
    "brake": 0.0,
    "gear": 8
  }
}
```

The consumer (Databricks) expects `m_playerCarIndex` as the Kafka partition key.
