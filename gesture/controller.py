"""
Handless Gesture Controller.
Main background service managing webcam streaming, MediaPipe hand tracking inference, FPS tracking, and event dispatch.
"""
import time
import threading
from typing import Dict, Any, Optional

from .config import GestureConfig
from .landmark_processor import LandmarkProcessor
from .classifier import GestureClassifier, GestureType
from .state_machine import GestureStateMachine, GestureEvent
from .action_executor import ActionExecutor
from .server import GestureEventServer

try:
    import cv2
    import mediapipe as mp
    HAS_CV_MP = True
except ImportError:
    cv2 = None
    mp = None
    HAS_CV_MP = False

class HandlessGestureController:
    """Singleton background controller for Handless Mode camera processing and gesture control."""

    _instance = None

    def __new__(cls, config: Optional[GestureConfig] = None):
        if cls._instance is None:
            cls._instance = super(HandlessGestureController, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, config: Optional[GestureConfig] = None):
        if self._initialized:
            if config:
                self.config = config
            return
        
        self.config = config or GestureConfig()
        self.state_machine = GestureStateMachine(self.config)
        self.executor = ActionExecutor(self.config)
        self.server = GestureEventServer(port=self.config.websocket_port)
        
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._fps = 0.0
        self._current_gesture = GestureType.NONE
        self._last_event = GestureEvent.NONE
        self._hand_detected = False
        self._initialized = True

    def start(self) -> Dict[str, Any]:
        """Requests webcam access and starts hand landmark gesture tracking."""
        if not HAS_CV_MP:
            return {"status": "error", "message": "MediaPipe or OpenCV not installed in current environment."}

        if self._running:
            return {"status": "success", "message": "Handless Mode is already running."}

        self._running = True
        self.config.enabled = True
        self.server.start()
        
        self._thread = threading.Thread(target=self._processing_loop, daemon=True)
        self._thread.start()

        return {"status": "success", "message": "Handless Mode started. Camera active."}

    def stop(self) -> Dict[str, Any]:
        """Stops webcam processing and releases camera resources immediately."""
        if not self._running:
            return {"status": "success", "message": "Handless Mode is already stopped."}

        self._running = False
        self.config.enabled = False
        
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

        self.server.stop()
        self._hand_detected = False
        self._current_gesture = GestureType.NONE
        self._fps = 0.0

        return {"status": "success", "message": "Handless Mode stopped. Camera resources released."}

    def is_active(self) -> bool:
        return self._running

    def get_status(self) -> Dict[str, Any]:
        """Returns real-time status details of Handless Mode."""
        return {
            "enabled": self._running,
            "hand_detected": self._hand_detected,
            "current_gesture": self._current_gesture.name if self._current_gesture else "NONE",
            "last_event": self._last_event.name if self._last_event else "NONE",
            "fps": round(self._fps, 1),
            "camera_index": self.config.camera_index,
            "websocket_port": self.config.websocket_port
        }

    def _processing_loop(self):
        """Background thread executing webcam capture and MediaPipe gesture classification loop."""
        cap = None
        hands = None
        try:
            cap = cv2.VideoCapture(self.config.camera_index, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(self.config.camera_index)

            if not cap.isOpened():
                self._running = False
                self.config.enabled = False
                return

            mp_hands = mp.solutions.hands
            hands = mp_hands.Hands(
                static_image_mode=False,
                max_num_hands=1,  # Support 1 hand for reliable low-latency control
                min_detection_confidence=self.config.detection_confidence,
                min_tracking_confidence=self.config.tracking_confidence
            )

            prev_time = time.time()

            while self._running:
                ret, frame = cap.read()
                if not ret or frame is None:
                    time.sleep(0.01)
                    continue

                # Calculate FPS
                now_time = time.time()
                dt = now_time - prev_time
                if dt > 0:
                    self._fps = 0.9 * self._fps + 0.1 * (1.0 / dt)
                prev_time = now_time

                # Flip frame horizontally for mirror display
                frame_rgb = cv2.cvtColor(cv2.flip(frame, 1), cv2.COLOR_BGR2RGB)
                results = hands.process(frame_rgb)

                if results.multi_hand_landmarks and len(results.multi_hand_landmarks) > 0:
                    self._hand_detected = True
                    hand_landmarks = results.multi_hand_landmarks[0]
                    
                    # Convert to normalized 3D tuple list
                    landmarks = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
                    
                    # Classify gesture pose
                    gesture, confidence, metadata = GestureClassifier.classify(landmarks)
                    self._current_gesture = gesture

                    # State machine debouncing & event generation
                    event, payload = self.state_machine.process_frame(landmarks, gesture, confidence, metadata)
                    self._last_event = event

                    # Execute native OS action
                    if event != GestureEvent.NONE:
                        self.executor.execute(event, payload)

                    # Broadcast payload to connected WebSocket web clients
                    self.server.broadcast({
                        "type": "GESTURE_FRAME",
                        "gesture": gesture.name,
                        "event": event.name,
                        "hand_center": payload.get("hand_center") or LandmarkProcessor.get_hand_center(landmarks),
                        "fps": round(self._fps, 1),
                        "timestamp": now_time
                    })
                else:
                    self._hand_detected = False
                    self._current_gesture = GestureType.NONE
                    event, payload = self.state_machine.process_frame([], GestureType.NONE, 0.0, {})
                    self._last_event = event

                time.sleep(0.005)  # Yield CPU chunk

        except Exception as err:
            pass
        finally:
            if hands:
                try:
                    hands.close()
                except Exception:
                    pass
            if cap:
                try:
                    cap.release()
                except Exception:
                    pass
            self._running = False
            self.config.enabled = False
