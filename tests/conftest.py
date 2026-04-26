import pytest

@pytest.fixture
def mock_eventhub_connection_string(monkeypatch):
    monkeypatch.setenv("EVENTHUB_NAMESPACE", "mock-namespace")
    monkeypatch.setenv("EVENTHUB_NAME", "mock-topic")
    monkeypatch.setenv("EVENTHUB_CONNECTION_STRING", "Endpoint=sb://mock.servicebus.windows.net/;SharedAccessKeyName=mock;SharedAccessKey=mock")
