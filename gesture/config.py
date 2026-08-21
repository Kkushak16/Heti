"""
Centralized Configuration for Handless Mode / Camera-Based Gesture Control.
"""
from dataclasses import dataclass

@dataclass
class GestureConfig:
    enabled: bool = False
    camera_index: int = 0
    detection_confidence: float = 0.7
    tracking_confidence: float = 0.7
    gesture_confidence: float = 0.75
    
    # Cursor controls
    cursor_sensitivity: float = 1.8
    cursor_smoothing: float = 0.35  # Exponential Moving Average alpha (0.1 = heavy smooth, 0.9 = fast raw)
    cursor_deadzone_px: float = 3.0
    screen_margin: float = 0.08      # Margin ratio to reach screen edges easily
    
    # Zoom controls
    pinch_sensitivity: float = 1.2
    min_pinch_distance: float = 0.03
    max_pinch_distance: float = 0.25
    zoom_cooldown_sec: float = 0.15
    
    # Scroll controls
    scroll_sensitivity: float = 30.0
    scroll_cooldown_sec: float = 0.1
    
    # State machine & Debounce
    debounce_frames: int = 4
    click_cooldown_sec: float = 0.5
    drag_confirm_frames: int = 5
    
    # IPC / Web Bridge Port
    websocket_port: int = 8765
