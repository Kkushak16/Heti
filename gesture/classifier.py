"""
Hand Gesture Classifier.
Classifies normalized hand landmarks into abstract gesture categories.
Inspired by kinivi/hand-gesture-recognition-mediapipe and ahmed-0egy cursor controller.
"""
from enum import Enum, auto
from typing import Dict, Any, Tuple, List
from .landmark_processor import LandmarkProcessor

class GestureType(Enum):
    NONE = auto()
    OPEN_HAND = auto()     # Cursor Movement
    FIST = auto()          # Drag
    INDEX_ONLY = auto()    # Right Click
    MIDDLE_ONLY = auto()   # Left Click
    TWO_FINGERS = auto()    # Double Click / Scroll
    PINCH = auto()         # Zoom

class GestureClassifier:
    """Classifies hand pose and calculates confidence scores."""

    @staticmethod
    def classify(landmarks: List[Tuple[float, float, float]]) -> Tuple[GestureType, float, Dict[str, Any]]:
        """
        Analyzes 21 3D hand landmarks and returns (GestureType, confidence, metadata).
        """
        if not landmarks or len(landmarks) < 21:
            return GestureType.NONE, 0.0, {}

        states = LandmarkProcessor.extract_finger_states(landmarks)
        pinch_dist = LandmarkProcessor.get_pinch_distance(landmarks)
        
        t_open = states["thumb_open"]
        i_open = states["index_open"]
        m_open = states["middle_open"]
        r_open = states["ring_open"]
        p_open = states["pinky_open"]

        open_count = sum([i_open, m_open, r_open, p_open])
        
        # 1. PINCH DETECTION (Thumb + Index close together)
        if pinch_dist < 0.06 and i_open:
            confidence = max(0.6, 1.0 - (pinch_dist / 0.06))
            return GestureType.PINCH, confidence, {"pinch_dist": pinch_dist}

        # 2. FIST (All fingers closed)
        if not i_open and not m_open and not r_open and not p_open:
            return GestureType.FIST, 0.90, {"fist": True}

        # 3. OPEN HAND (At least 3-4 fingers open)
        if open_count >= 3:
            return GestureType.OPEN_HAND, 0.88, {"open_count": open_count}

        # 4. INDEX ONLY (Right click gesture)
        if i_open and not m_open and not r_open and not p_open:
            return GestureType.INDEX_ONLY, 0.85, {"finger": "index"}

        # 5. MIDDLE ONLY (Left click gesture)
        if m_open and not i_open and not r_open and not p_open:
            return GestureType.MIDDLE_ONLY, 0.85, {"finger": "middle"}

        # 6. TWO FINGERS (Index + Middle open, Ring + Pinky closed)
        if i_open and m_open and not r_open and not p_open:
            return GestureType.TWO_FINGERS, 0.87, {"two_fingers": True}

        # Fallback to OPEN_HAND if mostly open
        if open_count >= 2:
            return GestureType.OPEN_HAND, 0.70, {}

        return GestureType.NONE, 0.0, {}
