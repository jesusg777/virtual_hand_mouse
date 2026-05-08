"""
utils/fps_counter.py — Contador de FPS desacoplado del loop principal.

Responsabilidad única: calcular los cuadros por segundo del loop de video
usando una media móvil sobre los últimos N intervalos de tiempo.
"""

from __future__ import annotations

import time
from collections import deque


class FPSCounter:
    """
    Calcula FPS en tiempo real usando una media móvil sobre los
    intervalos entre frames consecutivos.

    Uso:
        fps_counter = FPSCounter()
        while True:
            fps_counter.tick()
            fps = fps_counter.get()
    """

    def __init__(self, window: int = 30) -> None:
        """
        Args:
            window: número de frames sobre los que promediar.
        """
        self._times:    deque[float] = deque(maxlen=window)
        self._last_tick: float       = time.perf_counter()

    def tick(self) -> None:
        """Registra el timestamp del frame actual."""
        now = time.perf_counter()
        self._times.append(now - self._last_tick)
        self._last_tick = now

    def get(self) -> float:
        """
        Devuelve los FPS actuales.
        Devuelve 0.0 si aún no hay datos suficientes.
        """
        if not self._times:
            return 0.0
        avg_interval = sum(self._times) / len(self._times)
        return 1.0 / avg_interval if avg_interval > 0 else 0.0

    def reset(self) -> None:
        """Reinicia el contador."""
        self._times.clear()
        self._last_tick = time.perf_counter()
