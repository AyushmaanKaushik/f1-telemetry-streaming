from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class F1Packet(BaseModel):
    m_packetId: int
    m_playerCarIndex: int
    timestamp: str

class EventPacket(F1Packet):
    eventCode: str

class CarTelemetryPacket(F1Packet):
    speed_kmh: int
    engine_rpm: int
    gear: int
    throttle: float
    brake: float
    engine_temperature: int

class CarStatusPacket(F1Packet):
    fuel_in_tank: float
    ers_energy: float
    tyre_compound: str
    tyre_age_laps: int
    drs_activation: bool

class CarDamagePacket(F1Packet):
    front_wing_damage: float
    rear_wing_damage: float
    engine_wear: float
    tyre_wear: float
