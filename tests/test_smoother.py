"""
tests/test_smoother.py — Unit tests para MovingAverageSmoother.

Verifica que el algoritmo de suavizado funciona correctamente
con matemática pura, sin necesidad de cámara ni hardware.

Ejecutar con:
    pytest tests/test_smoother.py -v
"""

import pytest
from core.smoother import MovingAverageSmoother


class TestMovingAverageSmootherInit:
    """Tests de inicialización y validación de parámetros."""

    def test_default_initialization(self):
        smoother = MovingAverageSmoother(n_dimensions=2)
        assert smoother.n_dimensions == 2
        assert smoother.buffer_size > 0

    def test_custom_buffer_size(self):
        smoother = MovingAverageSmoother(n_dimensions=2, buffer_size=10)
        assert smoother.buffer_size == 10

    def test_invalid_buffer_size_raises(self):
        with pytest.raises(ValueError):
            MovingAverageSmoother(n_dimensions=2, buffer_size=0)

    def test_invalid_n_dimensions_raises(self):
        with pytest.raises(ValueError):
            MovingAverageSmoother(n_dimensions=0, buffer_size=5)

    def test_wrong_number_of_values_raises(self):
        smoother = MovingAverageSmoother(n_dimensions=2, buffer_size=5)
        with pytest.raises(ValueError):
            smoother.update(1.0)   # Solo 1 valor para 2 dimensiones


class TestMovingAverageSmootherBehavior:
    """Tests del comportamiento del suavizado."""

    def test_single_value_returns_itself(self):
        """Con un solo valor en el buffer, el promedio es el propio valor."""
        smoother = MovingAverageSmoother(n_dimensions=2, buffer_size=5)
        result = smoother.update(100.0, 200.0)
        assert result == (100.0, 200.0)

    def test_average_of_two_values(self):
        """Dos valores idénticos deben promediar a sí mismos."""
        smoother = MovingAverageSmoother(n_dimensions=1, buffer_size=2)
        smoother.update(10.0)
        result = smoother.update(20.0)
        assert result == (15.0,)

    def test_smoothing_reduces_noise(self):
        """
        El suavizado debe acercar el resultado al promedio real,
        no al último valor ruidoso.
        """
        smoother = MovingAverageSmoother(n_dimensions=1, buffer_size=5)
        # Llenar el buffer con valores estables
        for _ in range(4):
            smoother.update(100.0)
        # Agregar un valor atípico (spike de ruido)
        result = smoother.update(200.0)
        # El resultado debe ser mucho menor que 200 (el ruido fue atenuado)
        assert result[0] < 150.0, f"El ruido no fue suavizado: {result[0]}"

    def test_buffer_saturates_at_max_size(self):
        """Insertar más valores que el buffer no debe causar error."""
        smoother = MovingAverageSmoother(n_dimensions=1, buffer_size=3)
        for i in range(10):
            result = smoother.update(float(i))
        # Con buffer_size=3, los últimos 3 valores son 7, 8, 9 → promedio 8.0
        assert result[0] == pytest.approx(8.0)

    def test_constant_signal_returns_constant(self):
        """Una señal constante debe permanecer constante tras el suavizado."""
        smoother = MovingAverageSmoother(n_dimensions=2, buffer_size=7)
        for _ in range(10):
            result = smoother.update(0.5, 0.3)
        assert result[0] == pytest.approx(0.5)
        assert result[1] == pytest.approx(0.3)

    def test_reset_clears_buffer(self):
        """Después de reset, el primer valor debe comportarse como el primero."""
        smoother = MovingAverageSmoother(n_dimensions=1, buffer_size=5)
        for _ in range(5):
            smoother.update(100.0)
        smoother.reset()
        result = smoother.update(50.0)
        # Buffer vacío → el promedio es solo el nuevo valor
        assert result == (50.0,)

    def test_is_ready_false_initially(self):
        """El smoother no debe estar 'listo' con muy pocos datos."""
        smoother = MovingAverageSmoother(n_dimensions=1, buffer_size=10)
        smoother.update(1.0)
        assert not smoother.is_ready

    def test_is_ready_true_after_enough_data(self):
        """El smoother debe estar listo cuando el buffer supera el 50%."""
        smoother = MovingAverageSmoother(n_dimensions=1, buffer_size=4)
        for _ in range(3):
            smoother.update(1.0)
        assert smoother.is_ready

    def test_two_dimensional_independence(self):
        """Las dos dimensiones deben ser independientes entre sí."""
        smoother = MovingAverageSmoother(n_dimensions=2, buffer_size=2)
        smoother.update(10.0, 100.0)
        result = smoother.update(20.0, 200.0)
        assert result[0] == pytest.approx(15.0)   # (10+20)/2
        assert result[1] == pytest.approx(150.0)  # (100+200)/2
