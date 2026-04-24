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
    """Generates 1Hz loop of packets for a specified duration to push to the listener."""
    print(f"Starting F1 Telemetry Simulation -> UDP {HOST}:{PORT}")
    target_fps = 1
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
            
            # Generate body based on packet ID
            if packet_idx == 6:
                # Car Telemetry Format: <H H b f f H
                # speed_kmh(uint16), engine_rpm(uint16), gear(int8), throttle(float), brake(float), engine_temp(uint16)
                body = struct.pack(
                    '<HHbffH',
                    random.randint(50, 340),      # speed
                    random.randint(5000, 13000),  # RPM
                    random.randint(1, 8),         # gear
                    random.random(),              # throttle
                    random.random() * 0.5,        # brake
                    random.randint(90, 110)       # temp
                )
            elif packet_idx == 3:
                # Event Packet Format: <4s
                events = [b'SSTA', b'SEND', b'RTMT', b'DRSE', b'DRSD']
                ev_code = random.choice(events)
                body = struct.pack('<4s', ev_code)
            elif packet_idx == 7:
                # Car Status Format: <ffBBB
                # fuel_in_tank(float), ers_energy(float), tyre_compound(uint8), tyre_age_laps(uint8), drs_activation(uint8)
                body = struct.pack(
                    '<ffBBB',
                    random.uniform(10.0, 110.0), # fuel
                    random.uniform(0.0, 4000000.0), # ers
                    random.randint(16, 20),      # compound
                    random.randint(0, 35),       # age
                    random.randint(0, 1)         # drs
                )
            elif packet_idx == 10:
                # Car Damage Format: <ffff
                # front_wing(float), rear_wing(float), engine(float), tyre(float)
                body = struct.pack(
                    '<ffff',
                    random.uniform(0.0, 100.0),
                    random.uniform(0.0, 100.0),
                    random.uniform(0.0, 100.0),
                    random.uniform(0.0, 100.0)
                )
            else:
                body = bytes([random.randint(0, 255) for _ in range(20)])
                
            final_payload = raw_binary_packet + body
            
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
