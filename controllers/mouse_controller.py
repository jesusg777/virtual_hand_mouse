"""
controllers/mouse_controller.py — Abstracción sobre PyAutoGUI para controlar el ratón.

Responsabilidad única: traducir los comandos de alto nivel
(mover, clic, scroll) a llamadas concretas al sistema operativo.

¿Por qué una clase y no llamar PyAutoGUI directamente?
  - Si mañana cambias de PyAutoGUI a pynput, solo modificas este archivo.
  - Permite mockear fácilmente en tests (sin mover el ratón real durante CI).
  - Centraliza el manejo de la failsafe de PyAutoGUI.

No sabe nada de MediaPipe, gestos ni OpenCV.
"""

from __future__ import annotations

import pyautogui

from config import GESTURE


# Desactivar la pausa automática de PyAutoGUI entre comandos
# (el throttling lo manejamos nosotros vía el loop de frames)
pyautogui.PAUSE = 0.0

# Failsafe: mover el ratón a la esquina superior izquierda detiene el programa.
# MANTENER ACTIVO en desarrollo; considera desactivarlo solo en producción controlada.
pyautogui.FAILSAFE = True


class MouseController:
    """
    Controlador del ratón del sistema operativo.

    Implementa un guardián de estado para:
    - No enviar clics repetidos mientras el gesto sigue activo (left_held).
    - No enviar scroll si el delta es 0.

    Uso:
        mouse = MouseController()
        mouse.move(960, 540)
        mouse.left_click_down()
        mouse.left_click_up()
    """

    def __init__(self) -> None:
        self._left_held:  bool = False
        self._right_held: bool = False

    # ------------------------------------------------------------------
    # Movimiento
    # ------------------------------------------------------------------

    def move(self, x: int, y: int) -> None:
        """
        Mueve el cursor a la posición absoluta (x, y).
        duration=0 → sin animación, movimiento instantáneo.
        """
        try:
            pyautogui.moveTo(x, y, duration=0)
        except pyautogui.FailSafeException:
            raise   # Propagar: la failsafe es intencional

    # ------------------------------------------------------------------
    # Clic izquierdo (con guardián de estado)
    # ------------------------------------------------------------------

    def left_click_down(self) -> None:
        """Presiona el botón izquierdo si no estaba ya presionado."""
        if not self._left_held:
            pyautogui.mouseDown(button="left")
            self._left_held = True

    def left_click_up(self) -> None:
        """Suelta el botón izquierdo si estaba presionado."""
        if self._left_held:
            pyautogui.mouseUp(button="left")
            self._left_held = False

    # ------------------------------------------------------------------
    # Clic derecho (con guardián de estado)
    # ------------------------------------------------------------------

    def right_click_down(self) -> None:
        if not self._right_held:
            pyautogui.mouseDown(button="right")
            self._right_held = True

    def right_click_up(self) -> None:
        if self._right_held:
            pyautogui.mouseUp(button="right")
            self._right_held = False

    # ------------------------------------------------------------------
    # Scroll
    # ------------------------------------------------------------------

    def scroll(self, delta: int) -> None:
        """
        Desplaza la rueda del ratón.
        delta > 0 → scroll arriba
        delta < 0 → scroll abajo
        """
        if delta != 0:
            pyautogui.scroll(delta)

    # ------------------------------------------------------------------
    # Release all (seguridad)
    # ------------------------------------------------------------------

    def release_all(self) -> None:
        """
        Suelta todos los botones. Llamar en el cierre del programa
        para evitar dejar botones presionados al salir.
        """
        self.left_click_up()
        self.right_click_up()

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "MouseController":
        return self

    def __exit__(self, *_) -> None:
        self.release_all()
