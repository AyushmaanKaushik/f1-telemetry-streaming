# F1 Telemetry Streaming Platform

A real-time telemetry processing pipeline bridging the raw UDP outputs from the Formula 1 game into an enterprise-grade analytics platform using Azure Event Hubs and Databricks.

## Architecture

1. **Edge Ingestion (Python)**: Subscribes to F1 Game UDP packets (Port 20777). Uses struct unpacking to pick out Core Packets (Event, Car Telemetry, Car Status, Car Damage) and concurrently pushes them to Azure Event Hubs via a Kafka connection.
2. **Broker (Azure Event Hubs)**: Acts as the Kafka topic `telemetry_topic`.
3. **Data Processing (Databricks / PySpark)**: Structured streaming clusters applying Medallion tier transformations (Bronze raw payload -> Silver normalizations -> Gold aggregation/distance computing).

---

## Codebase Structure
- `src/ingestion/`: The Python Edge UDP listener, configuration, data structures, and Kafka producer.
- `src/databricks/notebooks/`: The Databricks notebooks to deploy for your medallion architecture.
- `src/databricks/lib/`: Reusable PySpark utility functions.
- `tests/ingestion/`: Pytest configuration for the Edge python ingestion application.

---

## 1. Setup & Installation (Edge Component)

**Prerequisites:**
- Python 3.11+
- An active Azure subscription with an Event Hubs namespace provisioned.

**Installation Steps**:
1. Clone the repository and navigate into the folder.
2. Ensure you have a virtual environment set up:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

**Environment Variables**:
Create a `.env` file or export the following variables in your terminal:
```bash
export EVENTHUB_NAMESPACE="your-namespace"
export EVENTHUB_NAME="telemetry_topic"
export EVENTHUB_CONNECTION_STRING="Endpoint=sb://your-namespace.servicebus.windows.net/;SharedAccessKeyName=RootManageSharedAccessKey;SharedAccessKey=YOUR_KEY"
```

---

## 2. Usage

### Starting the Ingestion Stream
Launch your Formula 1 Game and configure the Telemetry settings to broadcast to `127.0.0.1` on Port `20777` at a rate of 60Hz.

Run the listener script:
```bash
python -m src.ingestion.udp_listener
```
*The script will bind to the port and you will see logs indicating successful connections and message deliveries.*

### Running the Databricks Streams
1. Package the `src/databricks/lib/` folder and upload it to your Databricks workspace path.
2. Import the `src/databricks/notebooks/` files as Databricks Notebooks.
3. Configure `EVENTHUB_BROKER` inside your `bronze_ingestion` tracking using Databricks secrets.
4. Run the notebooks concurrently in the following order:
   - `bronze_ingestion`
   - `silver_transformations`
   - `gold_aggregations`

---

## 3. Testing 

The repository utilizes `pytest` for the Python ingestion components.

### Running Edge tests

Execute the test suite to validate the UDP structure mapping and the Kafka producer mocks:
```bash
python -m pytest tests/
```

Expected output should show `test_parser.py` and `test_producer.py` passing cleanly without attempting to hit live Azure credentials (handled by `tests/conftest.py`).

---

## Azure Monitoring & Operational Health

To ensure the ingestor does not drop the 60Hz telemetry, configure **Azure Monitor** alerts against your Event Hubs namespace:
- **`IncomingMessages` (Sum)**: Ensure this stays > 0 during an active session.
- **`ThrottledRequests` (Sum)**: Alert if this is > 0. Throttled requests indicate that the Premium Processing Units (PUs) or Standard Throughput Units (TUs) allocated to the namespace are insufficient for the 20-car packet volume.
