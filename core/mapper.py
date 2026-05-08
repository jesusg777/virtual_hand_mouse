"""
core/mapper.py — Interpolación lineal de coordenadas cámara → pantalla.

Responsabilidad única: convertir coordenadas normalizadas del frame
(0.0–1.0) a píxeles de la pantalla, aplicando la zona muerta en bordes.

No sabe nada de MediaPipe, gestos ni del ratón.
"""

from __future__ import annotations

import numpy as np

from config import MAPPER


class CoordinateMapper:
    """
    Mapea coordenadas normalizadas [0, 1] del espacio de la cámara
    al espacio de píxeles de la pantalla, con zona muerta configurable.

    La zona muerta (dead zone) recorta los bordes del frame para que
    el usuario no tenga que llevar la mano a los extremos físicos.

    Fórmula:
        x_screen = interp(x_cam_clipped, [margin, 1-margin], [0, screen_w])

    Uso:
        mapper = CoordinateMapper(screen_width=1920, screen_height=1080)
        sx, sy = mapper.map(0.5, 0.3)   # → (960, 324)
    """

    def __init__(
        self,
        screen_width:      int,
        screen_height:     int,
        dead_zone_margin:  float = MAPPER.dead_zone_margin,
    ) -> None:
        """
        Args:
            screen_width:     resolución horizontal del monitor en píxeles.
            screen_height:    resolución vertical del monitor en píxeles.
            dead_zone_margin: fracción [0.0–0.4] del frame ignorada en cada borde.
        """
        if not (0.0 <= dead_zone_margin < 0.5):
            raise ValueError(
                f"dead_zone_margin debe estar en [0.0, 0.5), recibido: {dead_zone_margin}"
            )

        self._sw  = screen_width
        self._sh  = screen_height
        self._dz  = dead_zone_margin

        # Rango efectivo del frame tras aplicar la zona muerta
        self._cam_x_min = dead_zone_margin
        self._cam_x_max = 1.0 - dead_zone_margin
        self._cam_y_min = dead_zone_margin
        self._cam_y_max = 1.0 - dead_zone_margin

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def map(self, norm_x: float, norm_y: float) -> tuple[int, int]:
        """
        Convierte coordenadas normalizadas a píxeles de pantalla.

        La cámara está espejada horizontalmente respecto a la pantalla,
        por lo que se invierte el eje X (1 - x) para un comportamiento intuitivo.

        Args:
            norm_x: coordenada X normalizada [0.0, 1.0].
            norm_y: coordenada Y normalizada [0.0, 1.0].

        Returns:
            (screen_x, screen_y) en píxeles, clampeados al tamaño de pantalla.
        """
        # Invertir X: el frame de la cámara está espejado
        flipped_x = norm_x

        screen_x = int(np.interp(
            flipped_x,
            [self._cam_x_min, self._cam_x_max],
            [0, self._sw],
        ))
        screen_y = int(np.interp(
            norm_y,
            [self._cam_y_min, self._cam_y_max],
            [0, self._sh],
        ))

        # Clamp para no salir de la pantalla
        screen_x = max(0, min(screen_x, self._sw - 1))
        screen_y = max(0, min(screen_y, self._sh - 1))

        return screen_x, screen_y

    def map_from_pixel(
        self, pixel_x: int, pixel_y: int,
        frame_width: int, frame_height: int,
    ) -> tuple[int, int]:
        """
        Variante: recibe coordenadas en píxeles del frame (no normalizadas).
        Útil si ya tienes las coordenadas en píxeles directamente.
        """
        norm_x = pixel_x / frame_width
        norm_y = pixel_y / frame_height
        return self.map(norm_x, norm_y)

    @property
    def screen_size(self) -> tuple[int, int]:
        return self._sw, self._sh

    @property
    def dead_zone_margin(self) -> float:
        return self._dz
