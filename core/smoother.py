"""
core/smoother.py — Algoritmo de suavizado por Media Móvil (Moving Average).

Responsabilidad única: recibir coordenadas ruidosas frame a frame
y devolver una versión suavizada que elimine el temblor natural de la mano.

No sabe nada de MediaPipe, OpenCV ni del ratón.
"""

from __future__ import annotations

from collections import deque
from typing import Sequence

import numpy as np

from config import SMOOTHER


class MovingAverageSmoother:
    """
    Implementa una Media Móvil Simple (SMA) sobre N dimensiones.

    ¿Por qué Media Móvil y no Kalman?
    - La Media Móvil es determinista, simple de entender y de testear unitariamente.
    - Para un portafolio educativo, demuestra comprensión del problema sin
      oscurecer la lógica con la matemática matricial de Kalman.
    - Si el proyecto crece, basta con sustituir esta clase por KalmanSmoother
      sin cambiar ningún otro módulo (Open/Closed Principle).

    Uso:
        smoother = MovingAverageSmoother(n_dimensions=2)
        smooth_x, smooth_y = smoother.update(raw_x, raw_y)
    """

    def __init__(
        self,
        n_dimensions: int = 2,
        buffer_size:  int = SMOOTHER.buffer_size,
    ) -> None:
        """
        Args:
            n_dimensions: número de coordenadas a suavizar (2 = x, y).
            buffer_size:  ventana de la media móvil.
        """
        if buffer_size < 1:
            raise ValueError(f"buffer_size debe ser ≥ 1, recibido: {buffer_size}")
        if n_dimensions < 1:
            raise ValueError(f"n_dimensions debe ser ≥ 1, recibido: {n_dimensions}")

        self._n  = n_dimensions
        self._sz = buffer_size
        # Una deque por dimensión; maxlen hace el "pop" automático
        self._buffers: list[deque[float]] = [
            deque(maxlen=buffer_size) for _ in range(n_dimensions)
        ]

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def update(self, *values: float) -> tuple[float, ...]:
        """
        Agrega nuevas coordenadas al buffer y devuelve el promedio actual.

        Args:
            *values: una coordenada por dimensión.
                     Ejemplo: smoother.update(x, y)

        Returns:
            Tupla con las coordenadas suavizadas.

        Raises:
            ValueError: si el número de valores no coincide con n_dimensions.
        """
        if len(values) != self._n:
            raise ValueError(
                f"Se esperaban {self._n} valores, se recibieron {len(values)}"
            )

        result: list[float] = []
        for buf, val in zip(self._buffers, values):
            buf.append(float(val))
            result.append(float(np.mean(buf)))

        return tuple(result)

    def reset(self) -> None:
        """Vacía todos los buffers (útil al perder el tracking de la mano)."""
        for buf in self._buffers:
            buf.clear()

    @property
    def is_ready(self) -> bool:
        """
        Devuelve True cuando el buffer está al menos a la mitad de capacidad.
        Útil para ignorar los primeros frames donde el promedio aún no es estable.
        """
        return all(len(buf) >= self._sz // 2 for buf in self._buffers)

    @property
    def buffer_size(self) -> int:
        return self._sz

    @property
    def n_dimensions(self) -> int:
        return self._n
