# F1 Telemetry Streaming Quickstart

## Prerequisites
- Python 3.11 installed locally.
- Access to an Azure subscription (Event Hubs creation permission).
- A Databricks Premium workspace deployed.
- Formula 1 game or telemetry simulator outputting 2023+ spec UDP packets on port `20777`.

## Local Setup

1. **Install python requirements**:
   ```bash
   pip install confluent-kafka pytest pydantic
   ```

2. **Configure Azure Event Hub**:
   - Create a resource group and deploy Event Hubs (Premium tier).
   - Ensure the "Kafka Surface" allows connection.
   - Note the Primary Connection String and configure it in your dot-env.

3. **Start the local listener**:
   ```bash
   python src/ingestion/udp_listener.py
   ```
   *The system is now listening on 20777 and writing to the Event Hub.*

## Databricks Setup

1. Configure Databricks cluster (recommended version Databricks Runtime 16.2+).
2. Attach ADLS storage for checkpoints.
3. Import the `bronze_ingestion.py` notebook.
4. Mount the stream pointing pointing to the Event Hub SASL address.
