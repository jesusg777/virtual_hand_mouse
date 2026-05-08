"""
ui/overlay.py — Renderizado del overlay informativo sobre el frame de OpenCV.

Responsabilidad única: dibujar sobre el frame de OpenCV la información
de landmarks, estado del gesto actual, FPS y zona muerta.

No sabe nada de MediaPipe Tasks directamente, solo trabaja con
HandLandmarks (el DTO de core/detector.py).
"""

from __future__ import annotations

import cv2
import numpy as np

from config import OVERLAY, MAPPER
from core.detector import HandLandmarks, LandmarkIndex
from core.gesture_engine import GestureState


# Conexiones entre landmarks para dibujar el esqueleto de la mano
# (pares de índices según la topología de MediaPipe)
_HAND_CONNECTIONS: list[tuple[int, int]] = [
    (0, 1), (1, 2), (2, 3), (3, 4),       # Pulgar
    (0, 5), (5, 6), (6, 7), (7, 8),       # Índice
    (0, 9), (9, 10), (10, 11), (11, 12),  # Medio
    (0, 13), (13, 14), (14, 15), (15, 16), # Anular
    (0, 17), (17, 18), (18, 19), (19, 20), # Meñique
    (5, 9), (9, 13), (13, 17),             # Palma
]


class Overlay:
    """
    Dibuja información de diagnóstico sobre el frame BGR de OpenCV.

    Uso:
        overlay = Overlay()
        frame = overlay.draw(frame, landmarks, gesture_state, fps)
        cv2.imshow("Virtual Hand Mouse", frame)
    """

    def draw(
        self,
        frame:          np.ndarray,
        landmarks:      HandLandmarks | None,
        gesture_state:  GestureState,
        fps:            float,
    ) -> np.ndarray:
        """
        Aplica el overlay al frame y lo devuelve modificado (in-place).

        Args:
            frame:         frame BGR capturado por OpenCV.
            landmarks:     landmarks detectados (None si no hay mano).
            gesture_state: estado actual del motor de gestos.
            fps:           cuadros por segundo del loop principal.

        Returns:
            El mismo frame con los elementos visuales añadidos.
        """
        h, w = frame.shape[:2]

        if OVERLAY.show_landmarks and landmarks is not None:
            self._draw_skeleton(frame, landmarks, w, h)
            self._draw_key_points(frame, landmarks, w, h)

        if OVERLAY.show_gesture:
            self._draw_gesture_label(frame, gesture_state)

        if OVERLAY.show_fps:
            self._draw_fps(frame, fps)

        self._draw_dead_zone(frame, w, h)

        return frame

    # ------------------------------------------------------------------
    # Métodos de dibujo internos
    # ------------------------------------------------------------------

    def _draw_skeleton(
        self, frame: np.ndarray,
        landmarks: HandLandmarks,
        w: int, h: int,
    ) -> None:
        """Dibuja las conexiones entre landmarks (esqueleto de la mano)."""
        for start_idx, end_idx in _HAND_CONNECTIONS:
            x1, y1 = landmarks.get_2d(start_idx)
            x2, y2 = landmarks.get_2d(end_idx)
            pt1 = (int(x1 * w), int(y1 * h))
            pt2 = (int(x2 * w), int(y2 * h))
            cv2.line(frame, pt1, pt2, (180, 180, 180), 1, cv2.LINE_AA)

    def _draw_key_points(
        self, frame: np.ndarray,
        landmarks: HandLandmarks,
        w: int, h: int,
    ) -> None:
        """Resalta los landmarks clave usados en los gestos."""
        key_points = {
            LandmarkIndex.INDEX_FINGER_TIP: (OVERLAY.color_active, 8, "8"),
            LandmarkIndex.THUMB_TIP:        (OVERLAY.color_active, 8, "4"),
            LandmarkIndex.MIDDLE_FINGER_TIP:(OVERLAY.color_inactive, 6, "12"),
        }
        for idx, (color, radius, label) in key_points.items():
            x, y = landmarks.get_2d(idx)
            px, py = int(x * w), int(y * h)
            cv2.circle(frame, (px, py), radius, color, -1, cv2.LINE_AA)
            cv2.putText(
                frame, label,
                (px + 8, py - 4),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.35, color, 1, cv2.LINE_AA,
            )

    def _draw_gesture_label(
        self, frame: np.ndarray, state: GestureState,
    ) -> None:
        """Muestra el estado del gesto en la esquina superior izquierda."""
        labels = {
            GestureState.IDLE:       ("MOVING",      OVERLAY.color_inactive),
            GestureState.LEFT_CLICK: ("LEFT CLICK",  OVERLAY.color_active),
            GestureState.RIGHT_CLICK:("RIGHT CLICK", OVERLAY.color_active),
            GestureState.SCROLL:     ("SCROLL",       OVERLAY.color_active),
            GestureState.PAUSE:      ("PAUSED",       OVERLAY.color_pause),
        }
        text, color = labels.get(state, ("UNKNOWN", OVERLAY.color_inactive))

        # Fondo semitransparente
        (tw, th), _ = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, OVERLAY.font_scale, 2
        )
        cv2.rectangle(frame, (8, 8), (tw + 20, th + 20), (0, 0, 0), -1)
        cv2.putText(
            frame, text,
            (14, th + 14),
            cv2.FONT_HERSHEY_SIMPLEX,
            OVERLAY.font_scale, color, 2, cv2.LINE_AA,
        )

    def _draw_fps(self, frame: np.ndarray, fps: float) -> None:
        """Muestra los FPS en la esquina superior derecha."""
        h, w = frame.shape[:2]
        text = f"FPS: {fps:.1f}"
        (tw, th), _ = cv2.getTextSize(
            text, cv2.FONT_HERSHEY_SIMPLEX, OVERLAY.font_scale, 1
        )
        x = w - tw - 14
        cv2.putText(
            frame, text,
            (x, th + 14),
            cv2.FONT_HERSHEY_SIMPLEX,
            OVERLAY.font_scale, OVERLAY.color_fps, 1, cv2.LINE_AA,
        )

    def _draw_dead_zone(self, frame: np.ndarray, w: int, h: int) -> None:
        """Dibuja el rectángulo de la zona activa (excluyendo dead zone)."""
        margin = MAPPER.dead_zone_margin
        x1 = int(w * margin)
        y1 = int(h * margin)
        x2 = int(w * (1 - margin))
        y2 = int(h * (1 - margin))
        cv2.rectangle(frame, (x1, y1), (x2, y2), (80, 80, 80), 1, cv2.LINE_AA)
