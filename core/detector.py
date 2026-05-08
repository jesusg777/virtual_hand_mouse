"""
core/detector.py — Wrapper sobre MediaPipe Tasks Hand Landmarker.

Responsabilidad única: recibir un frame BGR de OpenCV y devolver
los landmarks normalizados de la mano detectada.

No sabe nada de pantalla, gestos ni cursor.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision
import numpy as np

from config import DETECTOR, MODEL_PATH


# ---------------------------------------------------------------------------
# Índices de landmarks (MediaPipe Hand Landmarker)
# https://developers.google.com/mediapipe/solutions/vision/hand_landmarker
# ---------------------------------------------------------------------------
class LandmarkIndex:
    WRIST            = 0
    THUMB_TIP        = 4
    INDEX_FINGER_MCP = 5
    INDEX_FINGER_TIP = 8
    MIDDLE_FINGER_TIP = 12
    RING_FINGER_TIP  = 16
    PINKY_TIP        = 20


@dataclass
class HandLandmarks:
    """
    Contenedor de los 21 landmarks de una mano.

    Atributos:
        points: array (21, 3) con coordenadas normalizadas (x, y, z).
                x, y ∈ [0.0, 1.0] — fracción del frame.
                z es profundidad relativa (negativo = más cerca).
        handedness: 'Left' o 'Right' según MediaPipe.
    """
    points:     np.ndarray   # shape (21, 3), dtype float32
    handedness: str          # 'Left' | 'Right'

    def get(self, index: int) -> np.ndarray:
        """Devuelve (x, y, z) del landmark indicado."""
        return self.points[index]

    def get_2d(self, index: int) -> tuple[float, float]:
        """Devuelve (x, y) del landmark indicado (ignora z)."""
        p = self.points[index]
        return float(p[0]), float(p[1])


class HandDetector:
    """
    Encapsula MediaPipe Tasks Hand Landmarker en modo VIDEO.

    Uso:
        detector = HandDetector()
        landmarks = detector.process(bgr_frame)
        if landmarks:
            x, y = landmarks.get_2d(LandmarkIndex.INDEX_FINGER_TIP)
    """

    def __init__(self, model_path: Path = MODEL_PATH) -> None:
        if not model_path.exists():
            raise FileNotFoundError(
                f"Modelo no encontrado en: {model_path}\n"
                "Descárgalo desde:\n"
                "  https://storage.googleapis.com/mediapipe-models/"
                "hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task\n"
                f"y colócalo en: {model_path}"
            )

        base_options = mp_python.BaseOptions(model_asset_path=str(model_path))
        options = mp_vision.HandLandmarkerOptions(
            base_options=base_options,
            running_mode=mp_vision.RunningMode.VIDEO,
            num_hands=DETECTOR.num_hands,
            min_hand_detection_confidence=DETECTOR.min_hand_detection_conf,
            min_hand_presence_confidence=DETECTOR.min_hand_presence_conf,
            min_tracking_confidence=DETECTOR.min_tracking_conf,
        )
        self._landmarker = mp_vision.HandLandmarker.create_from_options(options)
        self._frame_timestamp_ms: int = 0

    def process(self, bgr_frame: np.ndarray) -> Optional[HandLandmarks]:
        """
        Procesa un frame BGR y devuelve los landmarks de la primera mano
        detectada, o None si no hay ninguna.

        Args:
            bgr_frame: frame capturado por OpenCV (np.ndarray, uint8, BGR).

        Returns:
            HandLandmarks o None.
        """
        # MediaPipe Tasks espera RGB
        rgb_frame = bgr_frame[:, :, ::-1].copy()
        mp_image  = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)

        # Incrementar timestamp para el modo VIDEO
        self._frame_timestamp_ms += 33   # ~30 fps
        result = self._landmarker.detect_for_video(
            mp_image, self._frame_timestamp_ms
        )

        if not result.hand_landmarks:
            return None

        # Tomar la primera mano detectada
        raw_landmarks = result.hand_landmarks[0]
        points = np.array(
            [[lm.x, lm.y, lm.z] for lm in raw_landmarks],
            dtype=np.float32,
        )

        handedness = (
            result.handedness[0][0].display_name
            if result.handedness
            else "Unknown"
        )

        return HandLandmarks(points=points, handedness=handedness)

    def close(self) -> None:
        """Libera los recursos de MediaPipe."""
        self._landmarker.close()

    # Permitir uso como context manager
    def __enter__(self) -> "HandDetector":
        return self

    def __exit__(self, *_) -> None:
        self.close()
