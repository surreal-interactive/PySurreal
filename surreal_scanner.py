import sys
import asyncio
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QPushButton, QListWidget, QLabel, QTextEdit, QGroupBox,
                            QHBoxLayout, QSpinBox, QSlider)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from surreal_sdk import SurrealSdk, BLEDevice
from surreal_data_model import PoseData, ButtonStatus

class BLEWorker(QThread):
    """Thread for handling BLE operations"""
    device_found = pyqtSignal(str, str)  # Device name and address
    pose_data_received = pyqtSignal(str)  # Pose data
    button_data_received = pyqtSignal(str)  # Button data

    def __init__(self):
        super().__init__()
        self.sdk = SurrealSdk()
        self.sdk.set_data_callback(self._on_pose_data_received)
        self.sdk.set_button_callback(self._on_button_data_received)

    def _on_pose_data_received(self, data: PoseData):
        """Handle received Pose data"""
        self.pose_data_received.emit(str(data))

    def _on_button_data_received(self, data: ButtonStatus):
        """Handle received button data"""
        self.button_data_received.emit(str(data))

    async def scan_devices(self):
        """Scan for devices"""
        devices = await self.sdk.scan_devices()
        for device in devices:
            self.device_found.emit(device.name, device.address)

    async def connect_device(self, address: str):
        """Connect to device"""
        device = BLEDevice(name="Unknown", address=address)
        await self.sdk.connect_device(device)

    async def send_vibration(self, amplitude: int, frequency: int, duration_ms: int):
        """Send vibration message"""
        await self.sdk.send_vibration(amplitude, frequency, duration_ms)

    def run(self):
        """Run event loop"""
        self.sdk.loop.run_forever()

    def stop(self):
        """Stop event loop"""
        self.sdk.stop()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Surreal Touch Device Scanner")
        self.setGeometry(100, 100, 1000, 800)
        
        # Create main window widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Create scan button
        self.scan_button = QPushButton("Scan Devices")
        self.scan_button.clicked.connect(self.start_scan)
        layout.addWidget(self.scan_button)
        
        # Create device list
        self.device_list = QListWidget()
        self.device_list.itemDoubleClicked.connect(self.connect_to_device)
        layout.addWidget(self.device_list)
        
        # Create status label
        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)
        
        # Create vibration control group
        vibration_group = QGroupBox("Vibration Control")
        vibration_layout = QVBoxLayout()
        
        # Amplitude control
        amplitude_layout = QHBoxLayout()
        amplitude_label = QLabel("Amplitude (0-10000):")
        self.amplitude_spin = QSpinBox()
        self.amplitude_spin.setRange(0, 10000)
        self.amplitude_spin.setValue(5000)
        self.amplitude_spin.setSingleStep(100)
        amplitude_layout.addWidget(amplitude_label)
        amplitude_layout.addWidget(self.amplitude_spin)
        vibration_layout.addLayout(amplitude_layout)
        
        # Frequency control
        frequency_layout = QHBoxLayout()
        frequency_label = QLabel("Frequency (20-300Hz):")
        self.frequency_spin = QSpinBox()
        self.frequency_spin.setRange(20, 300)
        self.frequency_spin.setValue(100)
        self.frequency_spin.setSingleStep(10)
        frequency_layout.addWidget(frequency_label)
        frequency_layout.addWidget(self.frequency_spin)
        vibration_layout.addLayout(frequency_layout)
        
        # Duration control
        duration_layout = QHBoxLayout()
        duration_label = QLabel("Duration (>=30ms):")
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(30, 10000)
        self.duration_spin.setValue(500)
        self.duration_spin.setSingleStep(50)
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_spin)
        vibration_layout.addLayout(duration_layout)
        
        # Send button
        self.vibration_button = QPushButton("Send Vibration")
        self.vibration_button.clicked.connect(self.send_vibration)
        vibration_layout.addWidget(self.vibration_button)
        
        vibration_group.setLayout(vibration_layout)
        layout.addWidget(vibration_group)
        
        # Create data group
        data_group = QGroupBox("Data Reception")
        data_layout = QVBoxLayout()
        
        # Create Pose data text box
        pose_label = QLabel("Pose Data:")
        data_layout.addWidget(pose_label)
        self.pose_text = QTextEdit()
        self.pose_text.setReadOnly(True)
        data_layout.addWidget(self.pose_text)
        
        # Create button data text box
        button_label = QLabel("Button Data:")
        data_layout.addWidget(button_label)
        self.button_text = QTextEdit()
        self.button_text.setReadOnly(True)
        data_layout.addWidget(self.button_text)
        
        data_group.setLayout(data_layout)
        layout.addWidget(data_group)
        
        # Initialize BLE worker thread
        self.ble_worker = BLEWorker()
        self.ble_worker.device_found.connect(self.add_device)
        self.ble_worker.pose_data_received.connect(self.update_pose_data)
        self.ble_worker.button_data_received.connect(self.update_button_data)
        self.ble_worker.start()
        
        # Store device addresses
        self.devices = {}

    def add_device(self, name, address):
        """Add device to list"""
        device_text = f"{name} ({address})"
        self.device_list.addItem(device_text)
        self.devices[device_text] = address

    def start_scan(self):
        """Start scanning for devices"""
        self.device_list.clear()
        self.devices.clear()
        self.status_label.setText("Scanning...")
        asyncio.run_coroutine_threadsafe(
            self.ble_worker.scan_devices(),
            self.ble_worker.sdk.loop
        )

    def connect_to_device(self, item):
        """Connect to selected device"""
        device_text = item.text()
        if device_text in self.devices:
            address = self.devices[device_text]
            self.status_label.setText(f"Connecting to {device_text}...")
            asyncio.run_coroutine_threadsafe(
                self.ble_worker.connect_device(address),
                self.ble_worker.sdk.loop
            )

    def update_pose_data(self, data):
        """Update Pose data"""
        self.pose_text.append(data)
        # Keep latest data visible
        self.pose_text.verticalScrollBar().setValue(
            self.pose_text.verticalScrollBar().maximum()
        )

    def update_button_data(self, data):
        """Update button data"""
        self.button_text.append(data)
        # Keep latest data visible
        self.button_text.verticalScrollBar().setValue(
            self.button_text.verticalScrollBar().maximum()
        )

    def send_vibration(self):
        """Send vibration message"""
        amplitude = self.amplitude_spin.value()
        frequency = self.frequency_spin.value()
        duration = self.duration_spin.value()
        
        self.status_label.setText(f"Sending vibration: Amplitude={amplitude}, Frequency={frequency}Hz, Duration={duration}ms")
        asyncio.run_coroutine_threadsafe(
            self.ble_worker.send_vibration(amplitude, frequency, duration),
            self.ble_worker.sdk.loop
        )

    def closeEvent(self, event):
        """Clean up resources when window closes"""
        self.ble_worker.stop()
        self.ble_worker.wait()
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 