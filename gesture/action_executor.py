"""
Native OS Action Executor Layer.
Executes smoothed cursor movements, clicks, drag & drop, scrolling, and zooming using PyAutoGUI.
"""
import math
from typing import Tuple, Optional, Dict, Any
from .config import GestureConfig
from .state_machine import GestureEvent

try:
    import pyautogui
    # Configure PyAutoGUI safety & performance
    pyautogui.FAILSAFE = False
    pyautogui.PAUSE = 0.001
    HAS_PYAUTOGUI = True
except ImportError:
    pyautogui = None
    HAS_PYAUTOGUI = False

class ActionExecutor:
    """Executes smooth native OS actions based on incoming GestureEvent payloads."""

    def __init__(self, config: GestureConfig):
        self.config = config
        self.prev_x: Optional[float] = None
        self.prev_y: Optional[float] = None
        self.screen_w, self.screen_h = (1920, 1080)
        
        if HAS_PYAUTOGUI:
            try:
                self.screen_w, self.screen_h = pyautogui.size()
            except Exception:
                pass

    def _normalize_to_screen(self, norm_x: float, norm_y: float) -> Tuple[float, float]:
        """
        Maps normalized camera coordinates (0..1) to screen pixel coordinates (0..screen_width).
        Inverts X axis for natural mirror webcam interaction.
        Applies screen margins for comfortable corner reach.
        """
        margin = self.config.screen_margin
        
        # Clamp within margin boundaries
        clamped_x = max(margin, min(1.0 - margin, 1.0 - norm_x))  # Mirrored X
        clamped_y = max(margin, min(1.0 - margin, norm_y))
        
        # Scale to 0..1 range after margins
        scaled_x = (clamped_x - margin) / (1.0 - 2 * margin)
        scaled_y = (clamped_y - margin) / (1.0 - 2 * margin)
        
        target_x = scaled_x * self.screen_w
        target_y = scaled_y * self.screen_h
        
        return target_x, target_y

    def _smooth_coordinates(self, target_x: float, target_y: float) -> Tuple[float, float]:
        """
        Applies Exponential Moving Average (EMA) smoothing to prevent landmark jitter.
        `smoothed = alpha * current + (1 - alpha) * previous`
        """
        if self.prev_x is None or self.prev_y is None:
            self.prev_x, self.prev_y = target_x, target_y
            return target_x, target_y

        alpha = max(0.05, min(0.95, self.config.cursor_smoothing))
        
        dx = target_x - self.prev_x
        dy = target_y - self.prev_y
        dist = math.hypot(dx, dy)

        # Apply deadzone check
        if dist < self.config.cursor_deadzone_px:
            return self.prev_x, self.prev_y

        smoothed_x = alpha * target_x + (1.0 - alpha) * self.prev_x
        smoothed_y = alpha * target_y + (1.0 - alpha) * self.prev_y

        self.prev_x, self.prev_y = smoothed_x, smoothed_y
        return smoothed_x, smoothed_y

    def execute(self, event: GestureEvent, payload: Dict[str, Any]) -> None:
        """Executes the corresponding native OS input action for the given GestureEvent."""
        if not HAS_PYAUTOGUI or event == GestureEvent.NONE:
            return

        try:
            if event == GestureEvent.CURSOR_MOVE:
                pos = payload.get("pos")
                if pos:
                    tx, ty = self._normalize_to_screen(pos[0], pos[1])
                    sx, sy = self._smooth_coordinates(tx, ty)
                    pyautogui.moveTo(int(sx), int(sy))

            elif event == GestureEvent.LEFT_CLICK:
                pos = payload.get("pos")
                if pos:
                    tx, ty = self._normalize_to_screen(pos[0], pos[1])
                    sx, sy = self._smooth_coordinates(tx, ty)
                    pyautogui.click(int(sx), int(sy), button='left')

            elif event == GestureEvent.RIGHT_CLICK:
                pos = payload.get("pos")
                if pos:
                    tx, ty = self._normalize_to_screen(pos[0], pos[1])
                    sx, sy = self._smooth_coordinates(tx, ty)
                    pyautogui.click(int(sx), int(sy), button='right')

            elif event == GestureEvent.DOUBLE_CLICK:
                pos = payload.get("pos")
                if pos:
                    tx, ty = self._normalize_to_screen(pos[0], pos[1])
                    sx, sy = self._smooth_coordinates(tx, ty)
                    pyautogui.doubleClick(int(sx), int(sy))

            elif event == GestureEvent.DRAG_START:
                pos = payload.get("pos")
                if pos:
                    tx, ty = self._normalize_to_screen(pos[0], pos[1])
                    sx, sy = self._smooth_coordinates(tx, ty)
                    pyautogui.mouseDown(int(sx), int(sy), button='left')

            elif event == GestureEvent.DRAG_MOVE:
                pos = payload.get("pos")
                if pos:
                    tx, ty = self._normalize_to_screen(pos[0], pos[1])
                    sx, sy = self._smooth_coordinates(tx, ty)
                    pyautogui.moveTo(int(sx), int(sy))

            elif event == GestureEvent.DRAG_END:
                pyautogui.mouseUp(button='left')

            elif event == GestureEvent.SCROLL:
                delta = payload.get("delta", 0)
                if delta != 0:
                    pyautogui.scroll(int(delta))

            elif event == GestureEvent.ZOOM_IN:
                # Hotkey Ctrl + '+' or wheel up
                pyautogui.hotkey('ctrl', '=')

            elif event == GestureEvent.ZOOM_OUT:
                # Hotkey Ctrl + '-' or wheel down
                pyautogui.hotkey('ctrl', '-')

        except Exception as err:
            pass  # Fail gracefully to preserve system stability
