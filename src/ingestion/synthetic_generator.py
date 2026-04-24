import socket
import struct
import time
import random
from typing import List

# F1 UDP format string:
# uint16, uint8, uint8, uint8, uint8, uint8 (packetId), uint64, float, uint32, uint32, uint8 (playerCarIndex), uint8
HEADER_FORMAT = '<HBBBBBQfIIBB'

PORT = 20777
HOST = "127.0.0.1"

def generate_header(packet_id: int, car_index: int) -> bytes:
    """Packs the 29-byte binary header required by the listener."""
    
    packet_format = 2023
    game_year = 23
    game_major = 1
    game_minor = 0
    packet_version = 1
    session_uid = random.getrandbits(64)
    session_time = time.time() % 10000.0  # Just a float
    frame_identifier = random.randint(1, 10000)
    overall_frame = frame_identifier
    secondary_car = 255  # indicating invalid
    
    return struct.pack(
        HEADER_FORMAT,
        packet_format, game_year, game_major, game_minor, packet_version,
        packet_id, session_uid, session_time, frame_identifier, overall_frame,
        car_index, secondary_car
    )

def simulate_telemetry(udp_socket: socket.socket, duration_seconds: int = None):
    """Generates 60Hz loop of packets for a specified duration to push to the listener."""
    print(f"Starting F1 Telemetry Simulation -> UDP {HOST}:{PORT}")
    target_fps = 60
    sleep_time = 1.0 / target_fps
    
    start_time = time.time()
    packets_sent = 0
    
    valid_packet_ids = [3, 6, 7, 10]
    
    try:
        while True:
            # Check duration
            if duration_seconds and (time.time() - start_time) > duration_seconds:
                print(f"Simulation ended after {duration_seconds} seconds.")
                break
                
            packet_idx = random.choice(valid_packet_ids)
            car_idx = random.randint(0, 19)
            
            # Generate the raw binary blob
            raw_binary_packet = generate_header(packet_id=packet_idx, car_index=car_idx)
            
            # Append some simulated payload junk to make the bytes > 29 to test bounds
            fuzzy_payload = bytes([random.randint(0, 255) for _ in range(50)])
            final_payload = raw_binary_packet + fuzzy_payload
            
            # Fire packet to the listener
            udp_socket.sendto(final_payload, (HOST, PORT))
            packets_sent += 1
            
            time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        print("\nSimulator stopped by user.")
    
    print(f"Total synthetic packets fired: {packets_sent}")

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        # Run infinitely if executed directly.
        simulate_telemetry(sock)
        
if __name__ == "__main__":
    main()
