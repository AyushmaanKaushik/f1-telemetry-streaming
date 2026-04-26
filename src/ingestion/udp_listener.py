import socket
import struct
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from src.ingestion.logger import get_logger
from src.ingestion.eventhub_producer import EventHubProducer

logger = get_logger(__name__)

PORT = 20777
HOST = "0.0.0.0"

def process_and_send(data: bytes, producer: EventHubProducer):
    """
    Decodes the F1 UDP packet header and routes to Kafka.
    """
    if len(data) < 29:
        return
        
    try:
        # Assuming F1 2023 Header format: 
        # uint16 (packetFormat), uint8 (gameYear), uint8 (gameMajorVersion), uint8 (gameMinorVersion), uint8 (packetVersion), uint8 (packetId), uint64 (sessionUID), float (sessionTime), uint32 (frameIdentifier), uint32 (overallFrameIdentifier), uint8 (playerCarIndex), uint8 (secondaryPlayerCarIndex)
        header_format = '<HBBBBBQfIIBB'
        
        # We only really need packetId (index 5) and playerCarIndex (index 10)
        unpacked = struct.unpack_from(header_format, data, 0)
        packet_id = unpacked[5]
        player_car_index = unpacked[10]
        
        if packet_id in [3, 6, 7, 10]:
            payload = {
                "m_packetId": packet_id,
                "m_playerCarIndex": player_car_index,
                "timestamp": datetime.utcnow().isoformat(),
                "raw_size": len(data)
            }
            
            # Unpack specific bodies if they match our synthetic lengths
            if packet_id == 6 and len(data) >= 29 + 14:
                # Unpack CarTelemetry Format: <H H b f f H
                body_data = struct.unpack_from('<HHbffH', data, 29)
                payload.update({
                    "speed_kmh": body_data[0],
                    "engine_rpm": body_data[1],
                    "gear": body_data[2],
                    "throttle": body_data[3],
                    "brake": body_data[4],
                    "engine_temperature": body_data[5]
                })
            elif packet_id == 3 and len(data) >= 29 + 4:
                # Unpack Event Format: <4s
                body_data = struct.unpack_from('<4s', data, 29)
                payload.update({
                    "eventCode": body_data[0].decode('utf-8', errors='ignore')
                })
            elif packet_id == 7 and len(data) >= 29 + 11:
                # Unpack CarStatus Format: <ffBBB
                body_data = struct.unpack_from('<ffBBB', data, 29)
                payload.update({
                    "fuel_in_tank": body_data[0],
                    "ers_energy": body_data[1],
                    "tyre_compound": f"C{body_data[2]}", # Integer to String mapping locally
                    "tyre_age_laps": body_data[3],
                    "drs_activation": bool(body_data[4])
                })
            elif packet_id == 10 and len(data) >= 29 + 16:
                # Unpack CarDamage Format: <ffff
                body_data = struct.unpack_from('<ffff', data, 29)
                payload.update({
                    "front_wing_damage": body_data[0],
                    "rear_wing_damage": body_data[1],
                    "engine_wear": body_data[2],
                    "tyre_wear": body_data[3]
                })
                
            producer.send_telemetry(partition_key=player_car_index, payload=payload)
    except Exception as e:
        logger.error(f"Failed to process packet: {e}")

def main():
    producer = EventHubProducer()
    
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
        udp_socket.bind((HOST, PORT))
        udp_socket.settimeout(1.0)
        logger.info(f"Listening for UDP telemetry on {HOST}:{PORT}...")
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            try:
                while True:
                    try:
                        data, addr = udp_socket.recvfrom(2048)
                        executor.submit(process_and_send, data, producer)
                    except socket.timeout:
                        continue
            except KeyboardInterrupt:
                logger.info("Interrupt received, shutting down.")
            finally:
                producer.flush()

if __name__ == "__main__":
    main()
