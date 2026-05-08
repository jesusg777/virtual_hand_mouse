"""
core/gesture_engine.py — Motor de reconocimiento de gestos con máquina de estados.

Responsabilidad única: analizar los landmarks de la mano y determinar
qué gesto se está realizando, manteniendo estado entre frames.

Por qué una máquina de estados y no simples if/else:
  - Permite implementar histéresis (umbrales de entrada/salida distintos)
    para evitar clics dobles accidentales.
  - El estado actual es explícito y testeable.
  - Agregar un nuevo gesto (ej. clic derecho) solo requiere añadir
    un nuevo estado, sin modificar los existentes (Open/Closed Principle).

No sabe nada de OpenCV, ratón ni pantalla.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import NamedTuple

import numpy as np

from config import GESTURE
from core.detector import HandLandmarks, LandmarkIndex


# ---------------------------------------------------------------------------
# Definición de gestos
# ---------------------------------------------------------------------------
class GestureState(Enum):
    """Estados posibles del motor de gestos."""
    IDLE         = auto()   # Sin gesto especial → mover cursor
    LEFT_CLICK   = auto()   # Pinza índice–pulgar
    RIGHT_CLICK  = auto()   # Pinza medio–pulgar
    SCROLL       = auto()   # Índice + medio levantados
    PAUSE        = auto()   # Puño cerrado → no mover cursor


class GestureResult(NamedTuple):
    """Resultado devuelto por el motor en cada frame."""
    state:        GestureState
    scroll_delta: int    # > 0 → scroll arriba, < 0 → scroll abajo, 0 → sin scroll
    cursor_active: bool  # False cuando el cursor NO debe moverse (PAUSE)


# ---------------------------------------------------------------------------
# Motor principal
# ---------------------------------------------------------------------------
class GestureEngine:
    """
    Analiza HandLandmarks y devuelve el GestureResult correspondiente.

    Histéresis implementada para left_click y right_click:
      - Para ACTIVAR el clic, la distancia debe bajar de threshold_enter.
      - Para DESACTIVAR el clic, la distancia debe subir de threshold_exit.
      - threshold_exit > threshold_enter → zona de histéresis.

    Uso:
        engine = GestureEngine()
        result = engine.update(landmarks)
        if result.state == GestureState.LEFT_CLICK:
            ...
    """

    def __init__(self) -> None:
        self._state = GestureState.IDLE

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def update(self, landmarks: HandLandmarks) -> GestureResult:
        """
        Procesa los landmarks del frame actual y actualiza el estado interno.

        Args:
            landmarks: HandLandmarks del frame actual.

        Returns:
            GestureResult con el estado y datos adicionales.
        """
        # --- Extraer puntos clave ---
        thumb_tip   = landmarks.get_2d(LandmarkIndex.THUMB_TIP)
        index_tip   = landmarks.get_2d(LandmarkIndex.INDEX_FINGER_TIP)
        middle_tip  = landmarks.get_2d(LandmarkIndex.MIDDLE_FINGER_TIP)
        ring_tip    = landmarks.get_2d(LandmarkIndex.RING_FINGER_TIP)
        pinky_tip   = landmarks.get_2d(LandmarkIndex.PINKY_TIP)
        wrist       = landmarks.get_2d(LandmarkIndex.WRIST)
        index_mcp   = landmarks.get_2d(LandmarkIndex.INDEX_FINGER_MCP)

        # --- Calcular distancias normalizadas ---
        hand_size          = _euclidean(wrist, index_mcp) or 1e-6  # evitar div/0
        d_index_thumb      = _euclidean(index_tip, thumb_tip)  / hand_size
        d_middle_thumb     = _euclidean(middle_tip, thumb_tip) / hand_size

        # --- Detectar dedos levantados ---
        index_up  = _finger_is_up(index_tip,  index_mcp,  wrist)
        middle_up = _finger_is_up(middle_tip, index_mcp,  wrist)
        ring_up   = _finger_is_up(ring_tip,   index_mcp,  wrist)
        pinky_up  = _finger_is_up(pinky_tip,  index_mcp,  wrist)

        # --- Máquina de estados ---
        new_state = self._evaluate_state(
            d_index_thumb, d_middle_thumb,
            index_up, middle_up, ring_up, pinky_up,
        )
        self._state = new_state

        # --- Calcular scroll delta ---
        scroll_delta = 0
        if new_state == GestureState.SCROLL:
            # Usar la posición Y del índice para determinar dirección
            # (el movimiento vertical de los dedos controla el scroll)
            scroll_delta = self._compute_scroll(index_tip)

        cursor_active = new_state != GestureState.PAUSE

        return GestureResult(
            state=new_state,
            scroll_delta=scroll_delta,
            cursor_active=cursor_active,
        )

    def reset(self) -> None:
        """Reinicia la máquina de estados al estado inicial."""
        self._state = GestureState.IDLE

    @property
    def current_state(self) -> GestureState:
        return self._state

    # ------------------------------------------------------------------
    # Lógica interna
    # ------------------------------------------------------------------

    def _evaluate_state(
        self,
        d_index_thumb:  float,
        d_middle_thumb: float,
        index_up:  bool,
        middle_up: bool,
        ring_up:   bool,
        pinky_up:  bool,
    ) -> GestureState:
        """Evalúa transiciones de estado con histéresis."""
    
        # Puño cerrado → PAUSE (ningún dedo levantado)
        if not index_up and not middle_up and not ring_up and not pinky_up:
            return GestureState.PAUSE
    
        # LEFT_CLICK primero — tiene prioridad sobre todo
        if self._state == GestureState.LEFT_CLICK:
            if d_index_thumb > GESTURE.click_threshold_exit:
                return GestureState.IDLE
            return GestureState.LEFT_CLICK
        else:
            if d_index_thumb < GESTURE.click_threshold_enter:
                return GestureState.LEFT_CLICK
    
        # RIGHT_CLICK
        if self._state == GestureState.RIGHT_CLICK:
            if d_middle_thumb > GESTURE.right_click_threshold_exit:
                return GestureState.IDLE
            return GestureState.RIGHT_CLICK
        else:
            if d_middle_thumb < GESTURE.right_click_threshold_enter:
                return GestureState.RIGHT_CLICK
    
        # SCROLL al final — solo si no hay pinza activa
        if index_up and middle_up and not ring_up and not pinky_up:
            if d_index_thumb > GESTURE.click_threshold_exit:
                return GestureState.SCROLL
    
        return GestureState.IDLE
    # Posición Y previa para calcular delta de scroll
    _prev_scroll_y: float = 0.5

    def _compute_scroll(self, index_tip: tuple[float, float]) -> int:
        """
        Calcula la velocidad y dirección del scroll basándose en el movimiento
        vertical del dedo índice.
        """
        current_y = index_tip[1]
        delta_y   = self._prev_scroll_y - current_y   # positivo → mano sube → scroll arriba
        self._prev_scroll_y = current_y

        if abs(delta_y) < 0.005:   # umbral mínimo de movimiento
            return 0

        return int(delta_y * GESTURE.scroll_speed * 100)


# ---------------------------------------------------------------------------
# Funciones de ayuda (puras, sin estado)
# ---------------------------------------------------------------------------

def _euclidean(p1: tuple[float, float], p2: tuple[float, float]) -> float:
    """Distancia euclidiana entre dos puntos 2D."""
    return float(np.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2))


def _finger_is_up(
    tip:   tuple[float, float],
    mcp:   tuple[float, float],
    wrist: tuple[float, float],
) -> bool:
    """
    Heurístico simple: un dedo está levantado si su punta está más lejos
    de la muñeca que el MCP (nudillo base).
    Funciona para todos los dedos excepto el pulgar (que se maneja por pinza).
    """
    dist_tip   = _euclidean(tip,  wrist)
    dist_mcp   = _euclidean(mcp,  wrist)
    return dist_tip > dist_mcp * 1.15   # 15% de margen para robustez
