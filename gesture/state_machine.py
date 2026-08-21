"""
Gesture State Machine & Priority Resolution Engine.
Implements candidate frame debouncing, priority ordering, cooldowns, and event generation.
"""
import time
from enum import Enum, auto
from typing import Optional, Dict, Any, Tuple, List
from .config import GestureConfig
from .classifier import GestureType
from .landmark_processor import LandmarkProcessor

class State(Enum):
    IDLE = auto()
    HAND_DETECTED = auto()
    GESTURE_CANDIDATE = auto()
    GESTURE_CONFIRMED = auto()
    ACTION_ACTIVE = auto()
    COOLDOWN = auto()

class GestureEvent(Enum):
    NONE = auto()
    CURSOR_MOVE = auto()
    LEFT_CLICK = auto()
    RIGHT_CLICK = auto()
    DOUBLE_CLICK = auto()
    DRAG_START = auto()
    DRAG_MOVE = auto()
    DRAG_END = auto()
    SCROLL = auto()
    ZOOM_IN = auto()
    ZOOM_OUT = auto()

class GestureStateMachine:
    """Manages gesture state transitions, debouncing, priority, and cooldowns."""

    def __init__(self, config: GestureConfig):
        self.config = config
        self.state = State.IDLE
        
        self.candidate_gesture = GestureType.NONE
        self.candidate_count = 0
        
        self.last_confirmed_gesture = GestureType.NONE
        self.last_action_time = 0.0
        
        self.is_dragging = False
        
        self.prev_hand_pos: Optional[Tuple[float, float]] = None
        self.prev_pinch_dist: Optional[float] = None
        
        self.last_click_time = 0.0

    def process_frame(
        self,
        landmarks: List[Tuple[float, float, float]],
        gesture: GestureType,
        confidence: float,
        metadata: Dict[str, Any]
    ) -> Tuple[GestureEvent, Dict[str, Any]]:
        """
        Processes camera frame data and returns an actionable GestureEvent with payload details.
        """
        now = time.time()
        
        if not landmarks or gesture == GestureType.NONE or confidence < self.config.gesture_confidence:
            # If hand left frame while dragging, release drag
            if self.is_dragging:
                self.is_dragging = False
                self.state = State.IDLE
                self.candidate_count = 0
                return GestureEvent.DRAG_END, {}
            
            self.state = State.IDLE
            self.candidate_gesture = GestureType.NONE
            self.candidate_count = 0
            self.prev_hand_pos = None
            self.prev_pinch_dist = None
            return GestureEvent.NONE, {}

        # Hand detected!
        hand_pos = LandmarkProcessor.get_hand_center(landmarks)
        index_tip = (landmarks[8][0], landmarks[8][1])

        # Candidate debouncing logic
        if gesture == self.candidate_gesture:
            self.candidate_count += 1
        else:
            self.candidate_gesture = gesture
            self.candidate_count = 1

        is_confirmed = self.candidate_count >= self.config.debounce_frames

        # Handle Drag State Machine Priority (FIST)
        if self.is_dragging:
            if gesture == GestureType.OPEN_HAND:
                self.is_dragging = False
                self.state = State.IDLE
                return GestureEvent.DRAG_END, {"pos": index_tip}
            else:
                return GestureEvent.DRAG_MOVE, {"pos": index_tip}

        if is_confirmed and gesture == GestureType.FIST and not self.is_dragging:
            self.is_dragging = True
            self.state = State.ACTION_ACTIVE
            return GestureEvent.DRAG_START, {"pos": index_tip}

        # Handle Pinch Zoom Priority
        if gesture == GestureType.PINCH:
            pinch_dist = metadata.get("pinch_dist", LandmarkProcessor.get_pinch_distance(landmarks))
            event = GestureEvent.NONE
            payload = {}

            if self.prev_pinch_dist is not None:
                dist_delta = pinch_dist - self.prev_pinch_dist
                if (now - self.last_action_time) > self.config.zoom_cooldown_sec:
                    if dist_delta < -0.008:
                        event = GestureEvent.ZOOM_IN
                        payload = {"scale_delta": abs(dist_delta) * self.config.pinch_sensitivity * 10}
                        self.last_action_time = now
                    elif dist_delta > 0.008:
                        event = GestureEvent.ZOOM_OUT
                        payload = {"scale_delta": abs(dist_delta) * self.config.pinch_sensitivity * 10}
                        self.last_action_time = now

            self.prev_pinch_dist = pinch_dist
            self.prev_hand_pos = hand_pos
            return event, payload

        self.prev_pinch_dist = None

        # Handle Click Gestures (Index, Middle, Two Fingers) with Cooldown
        if is_confirmed and (now - self.last_click_time) > self.config.click_cooldown_sec:
            if gesture == GestureType.MIDDLE_ONLY:
                self.last_click_time = now
                return GestureEvent.LEFT_CLICK, {"pos": index_tip}
            elif gesture == GestureType.INDEX_ONLY:
                self.last_click_time = now
                return GestureEvent.RIGHT_CLICK, {"pos": index_tip}
            elif gesture == GestureType.TWO_FINGERS:
                # Distinguish between Double Click and Scroll based on vertical movement delta
                if self.prev_hand_pos is not None:
                    dy = hand_pos[1] - self.prev_hand_pos[1]
                    if abs(dy) > 0.03:
                        scroll_amount = -dy * self.config.scroll_sensitivity
                        self.prev_hand_pos = hand_pos
                        return GestureEvent.SCROLL, {"delta": scroll_amount}
                
                # Stationary two-finger gesture -> Double Click
                self.last_click_time = now
                return GestureEvent.DOUBLE_CLICK, {"pos": index_tip}

        # Default Open Hand -> Cursor Movement
        if gesture in [GestureType.OPEN_HAND, GestureType.TWO_FINGERS]:
            event_payload = {"pos": index_tip, "hand_center": hand_pos}
            self.prev_hand_pos = hand_pos
            return GestureEvent.CURSOR_MOVE, event_payload

        self.prev_hand_pos = hand_pos
        return GestureEvent.NONE, {}
