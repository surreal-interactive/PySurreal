import asyncio
import logging
import struct
from typing import Callable, List, Dict, Optional
from bleak import BleakScanner, BleakClient
from dataclasses import dataclass
from surreal_data_model import PoseData, ButtonStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# BLE Service and Characteristic UUIDs
TARGET_SERVICE = "6e401001-b5a3-f393-e0a9-e50e24dcca9e"
POSE_CHARACTERISTIC = "6e401002-b5a3-f393-e0a9-e50e24dcca9e"
BUTTON_CHARACTERISTIC = "6e401003-b5a3-f393-e0a9-e50e24dcca9e"
VIBRATION_CHARACTERISTIC = "6e401004-b5a3-f393-e0a9-e50e24dcca9e"

@dataclass
class BLEDevice:
    """BLE device information class"""
    name: str
    address: str

class SurrealSdk:
    """SurrealSdk class, encapsulates SurrealSdk related functionality"""
    
    def __init__(self):
        """Initialize SurrealSdk"""
        self.target_service = TARGET_SERVICE
        self.pose_characteristic = POSE_CHARACTERISTIC
        self.button_characteristic = BUTTON_CHARACTERISTIC
        self.vibration_characteristic = VIBRATION_CHARACTERISTIC
        self.client: Optional[BleakClient] = None
        self.is_connected = False
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.data_callback: Optional[Callable[[PoseData], None]] = None
        self.button_callback: Optional[Callable[[ButtonStatus], None]] = None
        self._vibration_sequence = 0  # Vibration message sequence number
        self._setup_event_loop()

    def _setup_event_loop(self):
        """Set up event loop"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

    def set_data_callback(self, callback: Callable[[PoseData], None]):
        """
        Set data reception callback function
        
        Args:
            callback: Callback function for receiving data, parameter is parsed PoseData object
        """
        self.data_callback = callback

    def set_button_callback(self, callback: Callable[[ButtonStatus], None]):
        """
        Set button data reception callback function
        
        Args:
            callback: Callback function for receiving button data, parameter is parsed ButtonStatus object
        """
        self.button_callback = callback

    async def scan_devices(self) -> List[BLEDevice]:
        """
        Scan for devices
        
        Returns:
            List[BLEDevice]: List of matching devices
        """
        try:
            logger.info("Starting device scan...")
            devices = await BleakScanner.discover()
            filtered_devices = []
            
            for device in devices:
                if device.metadata.get('uuids'):
                    if self.target_service in device.metadata['uuids']:
                        filtered_devices.append(
                            BLEDevice(
                                name=device.name or "Unknown",
                                address=device.address
                            )
                        )
                        logger.info(f"Found device: {device.name or 'Unknown'} ({device.address})")
            
            logger.info(f"Scan complete, found {len(filtered_devices)} devices")
            return filtered_devices
        except Exception as e:
            logger.error(f"Error scanning devices: {str(e)}")
            return []

    async def connect_device(self, device: BLEDevice) -> bool:
        """
        Connect to device and subscribe to characteristics
        
        Args:
            device: Device to connect to
            
        Returns:
            bool: Whether connection was successful
        """
        max_retries = 3
        retry_count = 0
        connection_timeout = 30.0  # Increase timeout to 30 seconds

        while retry_count < max_retries:
            try:
                logger.info(f"Connecting to device: {device.name} ({device.address}) - Attempt {retry_count + 1}/{max_retries}")
                
                # If previous connection exists, disconnect first
                if self.client and self.is_connected:
                    await self.disconnect()
                
                self.client = BleakClient(device.address)
                
                # Set connection timeout
                await asyncio.wait_for(self.client.connect(), timeout=connection_timeout)
                self.is_connected = True
                logger.info("Device connected successfully")
                
                # Subscribe to Pose data characteristic
                logger.info(f"Subscribing to Pose data characteristic: {self.pose_characteristic}")
                await self.client.start_notify(
                    self.pose_characteristic,
                    self._notification_handler
                )
                logger.info("Pose data characteristic subscription successful")

                # Subscribe to button data characteristic
                logger.info(f"Subscribing to button data characteristic: {self.button_characteristic}")
                await self.client.start_notify(
                    self.button_characteristic,
                    self._notification_handler
                )
                logger.info("Button data characteristic subscription successful")
                return True
                
            except asyncio.TimeoutError:
                retry_count += 1
                error_msg = f"Device connection timeout (Attempt {retry_count}/{max_retries})"
                logger.error(error_msg)
                if retry_count < max_retries:
                    await asyncio.sleep(2)  # Wait 2 seconds before retry
                    continue
                return False
                
            except Exception as e:
                retry_count += 1
                error_msg = f"Connection error: {str(e)} (Attempt {retry_count}/{max_retries})"
                logger.error(error_msg)
                if retry_count < max_retries:
                    await asyncio.sleep(2)  # Wait 2 seconds before retry
                    continue
                return False

    def _notification_handler(self, sender, data):
        """Handle received data"""
        # Get characteristic UUID string
        sender_uuid = str(sender.uuid)
        # logger.info(f"Received data, characteristic: {sender_uuid}")
        # logger.info(f"Target Pose characteristic: {self.pose_characteristic}")
        # logger.info(f"Target button characteristic: {self.button_characteristic}")
        
        if sender_uuid == self.pose_characteristic and self.data_callback:
            try:
                # Parse data into PoseData object
                pose_data = PoseData.from_bytes(data)
                # logger.debug(f"Received Pose data: {pose_data}")
                self.data_callback(pose_data)
            except Exception as e:
                logger.error(f"Pose data parsing error: {str(e)}")
        elif sender_uuid == self.button_characteristic and self.button_callback:
            try:
                # Parse data into ButtonStatus object
                button_status = ButtonStatus.from_bytes(data)
                logger.debug(f"Received button data: {button_status}")
                self.button_callback(button_status)
            except Exception as e:
                logger.error(f"Button data parsing error: {str(e)}")
        else:
            logger.warning(f"No matching characteristic, data length: {len(data)} bytes")

    async def disconnect(self):
        """Disconnect from device"""
        if self.client and self.is_connected:
            try:
                logger.info("Disconnecting from device...")
                await self.client.disconnect()
                self.is_connected = False
                self.client = None
                logger.info("Device disconnected")
            except Exception as e:
                logger.error(f"Error disconnecting: {str(e)}")

    def stop(self):
        """Stop SDK"""
        if self.loop and self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)
        if self.client and self.is_connected:
            asyncio.run_coroutine_threadsafe(self.disconnect(), self.loop)

    async def send_vibration(self, amplitude: int, frequency: int, duration_ms: int) -> bool:
        """
        Send vibration message to device
        
        Args:
            amplitude: Vibration amplitude (0-10000)
            frequency: Vibration frequency (20-300 Hz)
            duration_ms: Vibration duration (>= 30ms)
            
        Returns:
            bool: Whether send was successful
        """
        if not self.client or not self.is_connected:
            logger.error("Device not connected, cannot send vibration message")
            return False
            
        try:
            # Parameter validation
            if not (0 <= amplitude <= 10000):
                logger.error(f"Vibration amplitude out of range (0-10000): {amplitude}")
                return False
            if not (20 <= frequency <= 300):
                logger.error(f"Vibration frequency out of range (20-300Hz): {frequency}")
                return False
            if duration_ms < 30:
                logger.error(f"Vibration duration too short (>= 30ms): {duration_ms}")
                return False
                
            # Construct vibration message data
            # Pack data using little-endian
            data = struct.pack('<BHHHHI',
                0x18,                  # Fixed value 0x18 (uint8_t)
                0x000a,               # Fixed value 0x000a (uint16_t)
                self._vibration_sequence,  # Sequence number (uint16_t)
                amplitude,                 # Amplitude (uint16_t)
                frequency,                 # Frequency (uint16_t)
                duration_ms               # Duration (uint32_t)
            )
            
            # Send data
            await self.client.write_gatt_char(
                self.vibration_characteristic,
                data
            )
            
            # Update sequence number
            self._vibration_sequence = (self._vibration_sequence + 1) % 65536
            
            logger.info(f"Vibration message sent successfully: Amplitude={amplitude}, Frequency={frequency}Hz, Duration={duration_ms}ms")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send vibration message: {str(e)}")
            return False 