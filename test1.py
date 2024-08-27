import serial
import struct
import time

# Constants
BAUD_RATE = 115200
SERIAL_PORT = '/dev/ttyUSB0'  # Replace with your actual serial port
FRAME_START_MASTER = b'\x5A\xA5'
FRAME_START_SLAVE = b'\xAA\x55'
END_IDENTIFIER = b'\x68'
COMMAND_READ_COMPREHENSIVE = b'\x01'
DEVICE_NUMBER = b'\x01'

def calculate_checksum(frame):
    return bytes([sum(frame) & 0xFF])

def build_read_comprehensive_frame():
    length_field = b'\x00\x06'
    frame = FRAME_START_MASTER + length_field + DEVICE_NUMBER + COMMAND_READ_COMPREHENSIVE
    checksum = calculate_checksum(frame)
    return frame + checksum + END_IDENTIFIER

def parse_response(response):
    if response.startswith(FRAME_START_SLAVE) and response.endswith(END_IDENTIFIER):
        length_field = struct.unpack('>H', response[2:4])[0]
        command_word = response[5:6]
        
        # Ensure length matches the expected value
        if len(response) != length_field + 4:  # +4 for start field and end identifier
            print(f'Unexpected length. Expected {length_field}, got {len(response)}')
            return None
        
        if command_word == COMMAND_READ_COMPREHENSIVE:
            data = response[6:-2]  # Extract data field
            checksum_received = response[-2:-1]
            checksum_calculated = calculate_checksum(response[:-2])
            
            if checksum_received == checksum_calculated:
                # Parse the comprehensive information
                total_voltage = struct.unpack('>H', data[0:2])[0] * 0.1
                combined_current = (struct.unpack('>H', data[2:4])[0] - 16000) * 0.1
                highest_voltage = struct.unpack('>H', data[4:6])[0] * 0.001
                lowest_voltage = struct.unpack('>H', data[6:8])[0] * 0.001
                soc = struct.unpack('>H', data[8:10])[0] * 0.1
                highest_temp = (struct.unpack('>H', data[16:18])[0] * 0.1) - 40
                lowest_temp = (struct.unpack('>H', data[18:20])[0] * 0.1) - 40
                relay_status = data[20]
                di_signal_status = data[21]
                battery_status = data[22]
                fault_code = struct.unpack('>H', data[23:25])[0]
                total_power = struct.unpack('>H', data[25:27])[0] * 0.1
                
                return {
                    'total_voltage': total_voltage,
                    'combined_current': combined_current,
                    'highest_voltage': highest_voltage,
                    'lowest_voltage': lowest_voltage,
                    'soc': soc,
                    'highest_temp': highest_temp,
                    'lowest_temp': lowest_temp,
                    'relay_status': relay_status,
                    'di_signal_status': di_signal_status,
                    'battery_status': battery_status,
                    'fault_code': fault_code,
                    'total_power': total_power
                }
            else:
                print(f'Checksum error. Received {checksum_received.hex()}, calculated {checksum_calculated.hex()}')
                return None
        else:
            print(f'Unexpected command word: {command_word.hex()}')
            return None
    else:
        print('Response does not start or end with expected bytes')
        return None

def main():
    with serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1) as ser:
        frame = build_read_comprehensive_frame()
        print(f'Sending frame: {frame.hex()}')
        
        ser.write(frame)
        
        time.sleep(0.1)
        response = ser.read(ser.in_waiting or 1)
        print(f'Received response: {response.hex()}')
        
        if response:
            parsed_data = parse_response(response)
            if parsed_data:
                print('Parsed Data:', parsed_data)
            else:
                print('Failed to parse response')
        else:
            print('No response received')

if __name__ == '__main__':
    main()
