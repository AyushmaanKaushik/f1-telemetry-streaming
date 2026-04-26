import os
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

class Config(BaseModel):
    eventhub_namespace: str = Field(default_factory=lambda: os.getenv("EVENTHUB_NAMESPACE", ""))
    eventhub_name: str = Field(default_factory=lambda: os.getenv("EVENTHUB_NAME", "telemetry_topic"))
    eventhub_connection_string: str = Field(default_factory=lambda: os.getenv("EVENTHUB_CONNECTION_STRING", ""))
    
    @property
    def kafka_broker(self) -> str:
        return f"{self.eventhub_namespace}.servicebus.windows.net:9093"

# Singleton instance
config = Config()
