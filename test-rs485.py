import serial
import struct

class BMS_RS485:
    def __init__(self, port, baudrate=115200):
        self.ser = serial.Serial(port, baudrate, parity=serial.PARITY_NONE,
                                 stopbits=serial.STOPBITS_ONE,
                                 bytesize=serial.EIGHTBITS,
                                 timeout=3)

    def calculate_checksum(self, data):
        return sum(data) & 0xFF

    def read_overall_info(self):
        command = bytearray([0x5A, 0xA5, 0x00, 0x06, 0x01, 0x01, 0x07, 0x68])
        self.ser.write(command)

        response = self.ser.read(30)  # Expected response length based on protocol
        print("Raw response:", response.hex())
        
        # Check for valid start sequence
        if len(response) < 2 or response[:2] != b'\xAA\x55':
            print("Invalid response received")
            return None

        # Validate checksum
        if response[-2] != self.calculate_checksum(response[:-2]):
            print("Checksum validation failed")
            return None

        # Attempt to parse the response data
        try:
            data = struct.unpack('>2H2h2H2hH2B2H2B2H', response[5:-2])

            info = {
                'Battery_Pack_1': {
                    'Total_Voltage': data[0] * 0.1,
                    'Total_Current': (data[1] - 16000) * 0.1,
                    'Highest_Cell_Voltage': data[2] * 0.001,
                    'Lowest_Cell_Voltage': data[3] * 0.001,
                    'SOC': data[4] * 0.1,
                    'Highest_Cell_Temp': (data[6] - 400) * 0.1,
                    'Lowest_Cell_Temp': (data[7] - 400) * 0.1,
                    'Relay_Status': bin(data[8])[2:].zfill(8),
                    'DI_Signal_Status': bin(data[9])[2:].zfill(8)
                },
                'Device_Insulation_Resistance': data[10],
                'BMS3_Relay_Status': bin(data[11])[2:].zfill(8),
                'BMS3_DI_Signal_Status': bin(data[12])[2:].zfill(8),
                'Battery_Status': data[13],
                'Battery_System_Fault_Code': data[14],
                'System_Operating_Mode': data[15],
                'Battery_Pack_Online_Status': data[16]
            }

            return info
        except struct.error as e:
            print("Error parsing data:", e)
            return None

    def close(self):
        self.ser.close()

# Usage example
if __name__ == "__main__":
    bms = BMS_RS485("/dev/ttyUSB0")  # Adjust the port as needed
    try:
        info = bms.read_overall_info()
        if info:
            print(info)
    finally:
        bms.close()
