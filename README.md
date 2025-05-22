# Surreal Touch Device Scanner

This is a Python program for scanning and connecting to specific Surreal Touch devices. The program scans and displays Surreal Touch devices, allowing users to connect and communicate with them.

## Features

- Scan and display Surreal Touch devices
- Double-click devices in the list to connect
- Automatically subscribe to specific characteristics
- Display received data in real-time

## Requirements

- Python 3.7+
- PyQt6
- bleak

## Installation

1. Clone or download this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the program:
```bash
python surreal_scanner.py
```

2. Click the "Scan Devices" button to start scanning
3. Find the target device in the list
4. Double-click the device to connect
5. After successful connection, the program will automatically subscribe to characteristics and display Pose data and button data
6. After connection, you can input amplitude, frequency, and duration parameters, then click the "Send Vibration" button to control device vibration

## Notes

- Ensure your system supports Bluetooth functionality
- Ensure the target Surreal Touch device is within range and powered on
- The program requires appropriate system permissions to access Bluetooth functionality 