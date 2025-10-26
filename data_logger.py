import serial
import sqlite3
import re
import sys
import time

# --- Configuration ---
DEFAULT_COM_PORT = 'COM5' # <-- IMPORTANT: Change this to your ESP32's COM port
BAUD_RATE = 115200
DB_FILE = 'scan_data.db'
# ---------------------

# Regex to find our new, structured data line
# It looks for "Angle: [number] | Distance: [number] m."
# [number] can be an integer or float, and positive or negative
DATA_REGEX = re.compile(r"Angle: ([-?\d]+) \| Distance: ([-?\d\.]+) m\.")

def init_db():
    """Creates the 'scans' table if it doesn't already exist."""
    print(f"Initializing database at {DB_FILE}...")
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            angle INTEGER,
            distance_m REAL
        )
    ''')
    conn.commit()
    conn.close()
    print("Database ready.")

def start_logging(com_port):
    """Connects to the serial port and logs data to the database."""
    print(f"Attempting to connect to {com_port} at {BAUD_RATE} baud...")
    
    try:
        ser = serial.Serial(com_port, BAUD_RATE, timeout=1)
        print(f"Connected to {com_port}. Waiting for data...")
    except serial.SerialException as e:
        print(f"Error: Could not open port {com_port}.")
        print(f"Details: {e}")
        print("Please check your COM port in Device Manager or Arduino IDE.")
        sys.exit(1)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    try:
        while True:
            try:
                # Read a line from the serial port
                line = ser.readline().decode('utf-8').strip()

                if line:
                    # Check if the line matches our data format
                    match = DATA_REGEX.search(line)
                    
                    if match:
                        # We found a match! Extract the data.
                        angle = int(match.group(1))
                        distance = float(match.group(2))
                        
                        # Insert data into the database
                        c.execute("INSERT INTO scans (angle, distance_m) VALUES (?, ?)", (angle, distance))
                        conn.commit()
                        
                        print(f"Logged: Angle={angle} deg, Distance={distance} m")
                    
                    else:
                        # Print other lines (like "Moving servo...", "Stopped.", etc.)
                        # This is useful for debugging.
                        print(f"Serial (Noise): {line}")

            except serial.SerialException:
                print("Error: Serial port disconnected.")
                break
            except UnicodeDecodeError:
                print("Serial (Decode Error): Skipping malformed line.")
            except KeyboardInterrupt:
                print("\nLogging stopped by user.")
                break

    finally:
        # Clean up
        ser.close()
        conn.close()
        print(f"Serial port {com_port} closed. Database connection closed.")

if __name__ == "_main_":
    init_db()
    
    # Allow user to specify COM port as an argument
    port = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_COM_PORT
    
    start_logging(port)