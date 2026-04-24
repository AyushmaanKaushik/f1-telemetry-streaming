import pytest
from src.ingestion.models import EventPacket

def test_event_packet_parsing():
    packet = EventPacket(m_packetId=3, m_playerCarIndex=0, timestamp="2026-04-24T12:00:00Z", eventCode="SSTA")
    assert packet.m_packetId == 3
    assert packet.eventCode == "SSTA"
