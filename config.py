"""
config.py — Single source of truth for all tunable parameters.

Modifica este archivo para calibrar el proyecto a tu hardware
sin tocar ningún otro módulo.
"""

from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
ROOT_DIR   = Path(__file__).parent
MODELS_DIR = ROOT_DIR / "models"
MODEL_PATH = MODELS_DIR / "hand_landmarker.task"

# ---------------------------------------------------------------------------
# Cámara
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class CameraConfig:
    device_index: int   = 0      # Índice de la webcam (0 = primera disponible)
    frame_width:  int   = 640    # Resolución de captura (ancho)
    frame_height: int   = 480    # Resolución de captura (alto)
    fps:          int   = 30     # FPS objetivo


# ---------------------------------------------------------------------------
# MediaPipe Hand Landmarker
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class DetectorConfig:
    num_hands:               int   = 1      # Número máximo de manos a detectar
    min_hand_detection_conf: float = 0.7    # Confianza mínima para detectar una mano
    min_hand_presence_conf:  float = 0.7    # Confianza mínima para mantener el tracking
    min_tracking_conf:       float = 0.5    # Confianza mínima del tracker entre frames


# ---------------------------------------------------------------------------
# Suavizado del cursor (Moving Average)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class SmootherConfig:
    """
    buffer_size controla cuántos frames se promedian.
    - Valor bajo  (3–5)  → respuesta rápida, más temblor.
    - Valor alto (10–15) → muy suave, pero con lag perceptible.
    """
    buffer_size: int = 7


# ---------------------------------------------------------------------------
# Mapeo de coordenadas cámara → pantalla
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class MapperConfig:
    """
    dead_zone_margin: porcentaje del frame que se ignora en los bordes.
    Esto evita que el usuario tenga que estirar el brazo a los extremos.
    Ejemplo: 0.1 ignora el 10% de cada lado.
    """
    dead_zone_margin: float = 0.10   # 10% de margen en cada borde
    cam_width:        int   = 640
    cam_height:       int   = 480


# ---------------------------------------------------------------------------
# Gestos y umbrales
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class GestureConfig:
    """
    Histéresis de clic:
      - click_threshold_enter: la pinza debe estar MÁS CERCA que este valor para ACTIVAR el clic.
      - click_threshold_exit:  la pinza debe estar MÁS LEJOS  que este valor para DESACTIVAR el clic.
    Tener dos umbrales distintos evita clics dobles accidentales (efecto "chattering").

    Distancias expresadas como fracción del ancho del frame (0.0 – 1.0).
    """
    click_threshold_enter:  float = 0.040   # Activar clic
    click_threshold_exit:   float = 0.060   # Desactivar clic

    right_click_threshold_enter: float = 0.040
    right_click_threshold_exit:  float = 0.060

    scroll_speed:           int   = 30      # Píxeles por frame en modo scroll


# ---------------------------------------------------------------------------
# Overlay de OpenCV
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class OverlayConfig:
    show_fps:        bool  = True
    show_landmarks:  bool  = True
    show_gesture:    bool  = True
    font_scale:      float = 0.6
    # Colores en formato BGR (OpenCV)
    color_active:    tuple = (0,   255, 100)   # Verde neón → gesto activo
    color_inactive:  tuple = (200, 200, 200)   # Gris       → sin gesto
    color_pause:     tuple = (0,   100, 255)   # Naranja    → pausado
    color_fps:       tuple = (255, 255,   0)   # Amarillo   → FPS


# ---------------------------------------------------------------------------
# Instancias globales (importa estas, no las dataclasses)
# ---------------------------------------------------------------------------
CAMERA   = CameraConfig()
DETECTOR = DetectorConfig()
SMOOTHER = SmootherConfig()
MAPPER   = MapperConfig()
GESTURE  = GestureConfig()
OVERLAY  = OverlayConfig()
