import serial
import serial.tools.list_ports
import time
import csv
import os
import sys

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
            print("⏳ No devices found. Please plug in your ESP32 and press Enter to refresh.")
        else:
            for i, (dev, desc) in enumerate(ports):
                print(f"[{i}] {dev} — {desc}")
            print("\nType the number of the port to select it, or press Enter to refresh:")

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

def extract_data_from_esp32(port, baudrate):
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"esp32_impact_data_{timestamp}.csv"

    try:
        with serial.Serial(port, baudrate, timeout=TIMEOUT) as ser:
            time.sleep(2)
            ser.write(b'b')
            print("🛰️  Command sent to ESP32. Reading data...")

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
                    print("📝 Header line found:", headers)
                    continue

                if not header_found or line.startswith("#") or not any(c.isdigit() for c in line):
                    continue

                values = line.split(",")
                if len(values) >= 6:
                    csv_data.append(values)

            if csv_data:
                with open(output_file, "w", newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(headers)
                    writer.writerows(csv_data)
                print(f"📁 Data written to: {output_file}")
            else:
                print("⚠️ No data received from ESP32.")

    except serial.SerialException as e:
        print(f"❌ Serial connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def send_delete_command(port, baudrate):
    try:
        confirm = input("⚠️ Are you sure you want to delete all data on the ESP32? Type 'yes' to confirm: ").strip().lower()
        if confirm != 'yes':
            print("❌ Delete command cancelled.")
            return

        with serial.Serial(port, baudrate, timeout=TIMEOUT) as ser:
            time.sleep(2)
            ser.write(b'd')
            print("🧹 Delete command ('d') sent. Check device for confirmation.")

    except serial.SerialException as e:
        print(f"❌ Serial connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def send_format_command(port, baudrate):
    try:
        confirm = input("⚠️ Are you absolutely sure you want to format SPIFFS (this will erase ALL data)? Type 'CONFIRM' to proceed: ").strip().upper()
        if confirm != 'CONFIRM':
            print("❌ Format command cancelled.")
            return

        with serial.Serial(port, baudrate, timeout=TIMEOUT) as ser:
            time.sleep(2)
            ser.write(b'c')
            print("💣 Format command ('c') sent. Watch the ESP32 serial output for confirmation.")

    except serial.SerialException as e:
        print(f"❌ Serial connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

def send_charge_mode_toggle(port, baudrate):
    try:
        with serial.Serial(port, baudrate, timeout=TIMEOUT) as ser:
            time.sleep(2)
            ser.write(b'p')
            print("🔋 Charge mode toggle command ('p') sent.")
    except serial.SerialException as e:
        print(f"❌ Serial connection error: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


def main():
    port = prompt_for_port()

    while True:
        print("\n📋 Choose an action:")
        print("[1] Read data file from ESP32")
        print("[2] Toggle charge mode (pause/resume logging)")
        print("[3] Delete data file only")
        print("[4] FORMAT SPIFFS (full wipe)")
        print("[5] Cancel / Exit")

        action = input("> ").strip()
        if action == "1":
            extract_data_from_esp32(port, BAUD_RATE)
            break
        elif action == "2":
            send_charge_mode_toggle(port, BAUD_RATE)
            break
        elif action == "3":
            send_delete_command(port, BAUD_RATE)
            break
        elif action == "4":
            send_format_command(port, BAUD_RATE)
            break
        elif action == "5":
            print("🚪 Exiting.")
            break
        else:
            print("❌ Invalid option. Try again.")

if __name__ == "__main__":
    main()
