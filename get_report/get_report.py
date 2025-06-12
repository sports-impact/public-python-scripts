import serial
import serial.tools.list_ports
import time
import csv
import os

BAUD_RATE = 115200
TIMEOUT = 5

def list_serial_ports():
    ports = serial.tools.list_ports.comports()
    return [(p.device, p.description) for p in ports]

def prompt_for_port():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        ports = list_serial_ports()
        print("🔌 Available USB Serial Ports:\n")

        if not ports:
            print("⏳ No devices found. Plug in ESP32 and press Enter to refresh.")
        else:
            for i, (dev, desc) in enumerate(ports):
                print(f"[{i}] {dev} — {desc}")
            print("\nEnter number to select port, or press Enter to refresh:")

        choice = input("> ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(ports):
                selected_port = ports[idx][0]
                print(f"\n✅ Selected port: {selected_port}")
                return selected_port
        elif choice == "":
            continue
        else:
            print("❌ Invalid selection. Try again.")

def before_flight(port):
    try:
        with serial.Serial(port, BAUD_RATE, timeout=TIMEOUT) as ser:
            time.sleep(2)
            print("💣 Formatting SPIFFS...")
            ser.write(b'c')
            time.sleep(2)
            print("🔋 Enabling charge mode (pause logging)...")
            ser.write(b'p')
            print("✅ Device prepared for flight.")
    except Exception as e:
        print(f"❌ Error: {e}")

def after_flight(port):
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"esp32_impact_data_{timestamp}.csv"
    try:
        with serial.Serial(port, BAUD_RATE, timeout=TIMEOUT) as ser:
            time.sleep(2)
            ser.write(b'b')
            print("🛰️  Requesting data from ESP32...")

            header_found = False
            csv_data = []

            while True:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                if "End of binary file dump." in line:
                    print("✅ Data dump completed.")
                    break
                if "timestamp_ms" in line and not header_found:
                    headers = line.split(",")
                    header_found = True
                    print("📝 Header found.")
                    continue
                if not header_found or line.startswith("#"):
                    continue
                values = line.split(",")
                if len(values) >= 6:
                    csv_data.append(values)

        if csv_data:
            with open(output_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(csv_data)
            print(f"📁 Data saved to: {output_file}")
        else:
            print("⚠️ No data received.")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    port = prompt_for_port()
    print("\n📋 Choose mode:")
    print("[1] 🛫 Before Flight (Format + Charge Mode)")
    print("[2] 🛬 After Flight (Download CSV)")
    print("[3] ❌ Exit")

    choice = input("> ").strip()
    if choice == "1":
        before_flight(port)
    elif choice == "2":
        after_flight(port)
    else:
        print("🚪 Exiting.")

if __name__ == "__main__":
    main()
