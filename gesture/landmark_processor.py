"""
MediaPipe Hand Landmark Processor & Preprocessor.
Normalizes 21-point hand landmarks and extracts geometric finger features.
Refactored from kinivi/hand-gesture-recognition-mediapipe architecture.
"""
import math
from typing import List, Tuple, Dict, Any

# MediaPipe Hand Landmark Constants
WRIST = 0
THUMB_CMC = 1
THUMB_MCP = 2
THUMB_IP = 3
THUMB_TIP = 4
INDEX_FINGER_MCP = 5
INDEX_FINGER_PIP = 6
INDEX_FINGER_DIP = 7
INDEX_FINGER_TIP = 8
MIDDLE_FINGER_MCP = 9
MIDDLE_FINGER_PIP = 10
MIDDLE_FINGER_DIP = 11
MIDDLE_FINGER_TIP = 12
RING_FINGER_MCP = 13
RING_FINGER_PIP = 14
RING_FINGER_DIP = 15
RING_FINGER_TIP = 16
PINKY_MCP = 17
PINKY_PIP = 18
PINKY_DIP = 19
PINKY_TIP = 20

class LandmarkProcessor:
    """Processes 21-point MediaPipe hand landmarks into normalized keypoints and finger states."""

    @staticmethod
    def calculate_distance(p1: Tuple[float, float], p2: Tuple[float, float]) -> float:
        """Calculates 2D Euclidean distance between two points."""
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    @staticmethod
    def normalize_landmarks(landmarks: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        Normalizes 21 landmarks relative to the wrist (0, 0) and scaled by maximum distance.
        Reference: kinivi/hand-gesture-recognition-mediapipe preprocessing.
        """
        if not landmarks or len(landmarks) < 21:
            return []

        base_x, base_y = landmarks[WRIST][0], landmarks[WRIST][1]
        relative_landmarks = [(x - base_x, y - base_y) for x, y in landmarks]

        # Calculate max distance for scale normalization
        max_dist = max(math.hypot(x, y) for x, y in relative_landmarks)
        if max_dist == 0:
            max_dist = 1.0

        normalized = [(x / max_dist, y / max_dist) for x, y in relative_landmarks]
        return normalized

    @classmethod
    def extract_finger_states(cls, landmarks: List[Tuple[float, float, float]]) -> Dict[str, bool]:
        """
        Extracts extension states for all 5 fingers based on joint landmarks.
        Returns boolean status: thumb_open, index_open, middle_open, ring_open, pinky_open.
        """
        if not landmarks or len(landmarks) < 21:
            return {
                "thumb_open": False,
                "index_open": False,
                "middle_open": False,
                "ring_open": False,
                "pinky_open": False
            }

        # For index, middle, ring, pinky: check tip position relative to PIP joint and MCP joint
        index_open = landmarks[INDEX_FINGER_TIP][1] < landmarks[INDEX_FINGER_PIP][1]
        middle_open = landmarks[MIDDLE_FINGER_TIP][1] < landmarks[MIDDLE_FINGER_PIP][1]
        ring_open = landmarks[RING_FINGER_TIP][1] < landmarks[RING_FINGER_PIP][1]
        pinky_open = landmarks[PINKY_TIP][1] < landmarks[PINKY_PIP][1]

        # For thumb: distance check between thumb tip and index MCP vs thumb MCP and index MCP
        thumb_tip = (landmarks[THUMB_TIP][0], landmarks[THUMB_TIP][1])
        index_mcp = (landmarks[INDEX_FINGER_MCP][0], landmarks[INDEX_FINGER_MCP][1])
        thumb_ip = (landmarks[THUMB_IP][0], landmarks[THUMB_IP][1])
        
        dist_tip_mcp = cls.calculate_distance(thumb_tip, index_mcp)
        dist_ip_mcp = cls.calculate_distance(thumb_ip, index_mcp)
        thumb_open = dist_tip_mcp > dist_ip_mcp * 1.1

        return {
            "thumb_open": thumb_open,
            "index_open": index_open,
            "middle_open": middle_open,
            "ring_open": ring_open,
            "pinky_open": pinky_open
        }

    @classmethod
    def get_pinch_distance(cls, landmarks: List[Tuple[float, float, float]]) -> float:
        """Returns distance between thumb tip and index finger tip."""
        if not landmarks or len(landmarks) < 21:
            return 1.0
        thumb_tip = (landmarks[THUMB_TIP][0], landmarks[THUMB_TIP][1])
        index_tip = (landmarks[INDEX_FINGER_TIP][0], landmarks[INDEX_FINGER_TIP][1])
        return cls.calculate_distance(thumb_tip, index_tip)

    @classmethod
    def get_hand_center(cls, landmarks: List[Tuple[float, float, float]]) -> Tuple[float, float]:
        """Returns palm/hand center coordinate (average of Wrist, Index MCP, Pinky MCP)."""
        if not landmarks or len(landmarks) < 21:
            return (0.5, 0.5)
        cx = (landmarks[WRIST][0] + landmarks[INDEX_FINGER_MCP][0] + landmarks[PINKY_MCP][0]) / 3.0
        cy = (landmarks[WRIST][1] + landmarks[INDEX_FINGER_MCP][1] + landmarks[PINKY_MCP][1]) / 3.0
        return (cx, cy)
