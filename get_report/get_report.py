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
        print("Available USB Serial Ports:\n")

        if not ports:
            print("No devices found. Plug in ESP32 and press Enter to refresh.")
        else:
            for i, (dev, desc) in enumerate(ports):
                print(f"[{i}] {dev} — {desc}")
            print("\nEnter number to select port, or press Enter to refresh:")

        choice = input("> ").strip()
        if choice.isdigit():
            idx = int(choice)
            if 0 <= idx < len(ports):
                selected_port = ports[idx][0]
                print(f"\nSelected port: {selected_port}")
                return selected_port
        elif choice == "":
            continue
        else:
            print("Invalid selection. Try again.")

def before_flight(port):
    print("\nWARNING: This will ERASE all existing data on the device.")
    confirm = input("Are you sure you want to continue? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Operation cancelled.")
        return

    double_check = input("Please type 'ERASE' to confirm: ").strip().upper()
    if double_check != "ERASE":
        print("Confirmation failed. Operation cancelled.")
        return

    try:
        with serial.Serial(port, BAUD_RATE, timeout=TIMEOUT) as ser:
            time.sleep(2)
            print("Sending erase command...")
            ser.write(b'c')
            time.sleep(2)
            print("Sending pause logging command...")
            ser.write(b'p')
            print("Device successfully prepared for flight.")

        print("\nNext Steps:")
        print("- Ensure the power switch is ON while charging (towards the USB-C port).")
        print("- Leave the device charging for at least 4 hours.")
        print("- Before unplugging, switch the device OFF to avoid draining the battery.")
    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")

def after_flight(port):
    timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
    output_file = f"esp32_impact_data_{timestamp}.csv"
    try:
        with serial.Serial(port, BAUD_RATE, timeout=TIMEOUT) as ser:
            time.sleep(2)
            ser.write(b'b')
            print("Requesting data from ESP32...")

            header_found = False
            csv_data = []
            line_count = 0
            spinner = ["|", "/", "-", "\\"]
            spin_idx = 0

            while True:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                if "End of binary file dump." in line:
                    print("\nData dump completed.")
                    break
                if "timestamp_ms" in line and not header_found:
                    headers = line.split(",")
                    header_found = True
                    print("Header found. Starting data collection...")
                    continue
                if not header_found or line.startswith("#"):
                    continue

                values = line.split(",")
                if len(values) >= 6:
                    csv_data.append(values)
                    line_count += 1

                    if line_count % 100 == 0:
                        print(f"\rReading data: {line_count} {spinner[spin_idx % 4]}", end="", flush=True)
                        spin_idx += 1

        if csv_data:
            with open(output_file, "w", newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(csv_data)
            print(f"\nData successfully saved to: {output_file}")
            print("You can now open the CSV in Excel, Google Sheets, or your preferred analysis tool.")
        else:
            print("No data received from device. Please ensure the device is powered on and logging has occurred.")
    except serial.SerialException as e:
        print(f"Serial communication error: {e}")
    except UnicodeDecodeError:
        print("Received non-text data or corrupt serial data. Please ensure the firmware outputs proper CSV-formatted lines.")
    except Exception as e:
        print(f"Unexpected error: {e}")

def main():
    port = prompt_for_port()
    while True:
        print("\nChoose mode:")
        print("[1] Before Flight (Format + Charge Mode)")
        print("[2] After Flight (Download CSV)")
        print("[3] Exit")

        choice = input("> ").strip()
        if choice == "1":
            before_flight(port)
        elif choice == "2":
            after_flight(port)
        elif choice == "3":
            print("Exiting.")
            break
        else:
            print("Invalid option. Try again.")

if __name__ == "__main__":
    main()
