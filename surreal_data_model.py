from dataclasses import dataclass
import struct
from typing import Callable, Optional

@dataclass
class PoseData:
    """Pose data model"""
    timestamp: int
    x: float
    y: float
    z: float
    qx: float
    qy: float
    qz: float
    qw: float
    confidence: float
    linear_velocity_x: float
    linear_velocity_y: float
    linear_velocity_z: float
    angular_velocity_x: float
    angular_velocity_y: float
    angular_velocity_z: float
    acceleration_x: float
    acceleration_y: float
    acceleration_z: float

    @classmethod
    def from_bytes(cls, data: bytes) -> 'PoseData':
        """
        Parse bytes data into PoseData object
        
        Args:
            data: Byte data
            
        Returns:
            PoseData: Parsed data object
        """
        # Parse data using little-endian
        # Format: <Qfffffffffffffffff
        # Q: uint64_t (timestamp)
        # f: float (remaining fields)
        fmt = '<Qfffffffffffffffff'
        values = struct.unpack(fmt, data)
        
        return cls(
            timestamp=values[0],
            x=values[1],
            y=values[2],
            z=values[3],
            qx=values[4],
            qy=values[5],
            qz=values[6],
            qw=values[7],
            confidence=values[8],
            linear_velocity_x=values[9],
            linear_velocity_y=values[10],
            linear_velocity_z=values[11],
            angular_velocity_x=values[12],
            angular_velocity_y=values[13],
            angular_velocity_z=values[14],
            acceleration_x=values[15],
            acceleration_y=values[16],
            acceleration_z=values[17]
        )

    def __str__(self) -> str:
        """Return formatted string representation"""
        return (
            f"PoseData(\n"
            f"  timestamp: {self.timestamp}\n"
            f"  position: ({self.x:.3f}, {self.y:.3f}, {self.z:.3f})\n"
            f"  quaternion: ({self.qx:.3f}, {self.qy:.3f}, {self.qz:.3f}, {self.qw:.3f})\n"
            f"  confidence: {self.confidence:.3f}\n"
            f"  linear_velocity: ({self.linear_velocity_x:.3f}, {self.linear_velocity_y:.3f}, {self.linear_velocity_z:.3f})\n"
            f"  angular_velocity: ({self.angular_velocity_x:.3f}, {self.angular_velocity_y:.3f}, {self.angular_velocity_z:.3f})\n"
            f"  acceleration: ({self.acceleration_x:.3f}, {self.acceleration_y:.3f}, {self.acceleration_z:.3f})\n"
            f")"
        )

@dataclass
class ButtonStatus:
    """Controller button status structure"""
    timestamp: int
    btn_xa: bool
    btn_yb: bool
    menu_capture: bool
    joystick_z: bool
    reserve: int
    trigger: int
    grip: int
    joystick_x: int
    joystick_y: int

    @classmethod
    def from_bytes(cls, data: bytes):
        """Parse button status from bytes"""
        # Parse data using little-endian
        timestamp, button_flags, trigger, grip, joystick_x, joystick_y = struct.unpack('<QBBBBB', data)
        
        # Parse button flags
        btn_xa = bool(button_flags & 0x01)
        btn_yb = bool(button_flags & 0x02)
        menu_capture = bool(button_flags & 0x04)
        joystick_z = bool(button_flags & 0x08)
        reserve = (button_flags >> 4) & 0x0F

        return cls(
            timestamp=timestamp,
            btn_xa=btn_xa,
            btn_yb=btn_yb,
            menu_capture=menu_capture,
            joystick_z=joystick_z,
            reserve=reserve,
            trigger=trigger,
            grip=grip,
            joystick_x=joystick_x,
            joystick_y=joystick_y
        )

    def __str__(self):
        """Return string representation of button status"""
        return (f"ButtonStatus(timestamp={self.timestamp}, "
                f"XA={self.btn_xa}, YB={self.btn_yb}, "
                f"Menu/Capture={self.menu_capture}, "
                f"JoystickZ={self.joystick_z}, "
                f"Trigger={self.trigger}, Grip={self.grip}, "
                f"JoystickX={self.joystick_x}, JoystickY={self.joystick_y})") 