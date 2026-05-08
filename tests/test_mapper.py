"""
tests/test_mapper.py — Unit tests para CoordinateMapper.

Verifica que la interpolación de coordenadas sea matemáticamente
correcta para todos los casos límite relevantes.

Ejecutar con:
    pytest tests/test_mapper.py -v
"""

import pytest
from core.mapper import CoordinateMapper


SCREEN_W = 1920
SCREEN_H = 1080


class TestCoordinateMapperInit:
    """Tests de inicialización y validación."""

    def test_valid_initialization(self):
        mapper = CoordinateMapper(SCREEN_W, SCREEN_H, dead_zone_margin=0.1)
        assert mapper.screen_size == (SCREEN_W, SCREEN_H)
        assert mapper.dead_zone_margin == pytest.approx(0.1)

    def test_zero_margin_is_valid(self):
        mapper = CoordinateMapper(SCREEN_W, SCREEN_H, dead_zone_margin=0.0)
        assert mapper.dead_zone_margin == pytest.approx(0.0)

    def test_invalid_margin_raises(self):
        with pytest.raises(ValueError):
            CoordinateMapper(SCREEN_W, SCREEN_H, dead_zone_margin=0.5)

    def test_negative_margin_raises(self):
        with pytest.raises(ValueError):
            CoordinateMapper(SCREEN_W, SCREEN_H, dead_zone_margin=-0.1)


class TestCoordinateMapperMapping:
    """Tests del mapeo de coordenadas."""

    def setup_method(self):
        """Mapper sin zona muerta para simplificar las matemáticas."""
        self.mapper = CoordinateMapper(SCREEN_W, SCREEN_H, dead_zone_margin=0.0)

    def test_center_maps_to_center(self):
        """El centro del frame debe mapearse al centro de la pantalla."""
        sx, sy = self.mapper.map(0.5, 0.5)
        assert sx == pytest.approx(SCREEN_W // 2, abs=2)
        assert sy == pytest.approx(SCREEN_H // 2, abs=2)

    def test_x_axis_is_flipped(self):
        """
        La cámara está espejada: norm_x=0 (izquierda del frame)
        debe mapearse al lado DERECHO de la pantalla.
        """
        sx_left, _  = self.mapper.map(0.0, 0.5)   # norm_x=0 → flipped=1 → screen derecha
        sx_right, _ = self.mapper.map(1.0, 0.5)   # norm_x=1 → flipped=0 → screen izquierda
        assert sx_left  > sx_right

    def test_y_axis_not_flipped(self):
        """El eje Y NO se invierte: norm_y=0 → arriba de pantalla."""
        _, sy_top    = self.mapper.map(0.5, 0.0)
        _, sy_bottom = self.mapper.map(0.5, 1.0)
        assert sy_top < sy_bottom

    def test_output_clamped_to_screen(self):
        """Las coordenadas siempre deben estar dentro del rango de la pantalla."""
        sx, sy = self.mapper.map(2.0, -1.0)   # Fuera del rango [0,1]
        assert 0 <= sx < SCREEN_W
        assert 0 <= sy < SCREEN_H

    def test_full_range_maps_to_full_screen(self):
        """Sin zona muerta, [0,1] debe cubrir toda la pantalla."""
        sx_max, _ = self.mapper.map(0.0, 0.5)   # flipped → x_screen máximo
        sx_min, _ = self.mapper.map(1.0, 0.5)   # flipped → x_screen mínimo
        _, sy_min = self.mapper.map(0.5, 0.0)
        _, sy_max = self.mapper.map(0.5, 1.0)

        assert sx_max >= SCREEN_W - 2
        assert sx_min <= 1
        assert sy_min <= 1
        assert sy_max >= SCREEN_H - 2


class TestCoordinateMapperDeadZone:
    """Tests del comportamiento de la zona muerta."""

    def test_dead_zone_reduces_effective_range(self):
        """
        Con un 10% de zona muerta, las posiciones en el borde del frame
        deben mapearse igual que las posiciones dentro de la zona muerta.
        """
        margin = 0.10
        mapper = CoordinateMapper(SCREEN_W, SCREEN_H, dead_zone_margin=margin)

        # norm_x = 0.05 está dentro de la zona muerta (< margin=0.10)
        # flipped = 0.95, que está fuera de [margin, 1-margin] en el eje X flipped
        # Debe quedar clampeado al borde de la pantalla
        sx_at_edge, _ = mapper.map(0.05, 0.5)
        sx_outside,  _ = mapper.map(0.0,  0.5)

        # Ambos deberían estar en el extremo derecho de la pantalla
        assert sx_at_edge == sx_outside

    def test_dead_zone_center_still_maps_to_center(self):
        """La zona muerta no debe desplazar el centro de la imagen."""
        mapper = CoordinateMapper(SCREEN_W, SCREEN_H, dead_zone_margin=0.15)
        sx, sy = mapper.map(0.5, 0.5)
        assert sx == pytest.approx(SCREEN_W // 2, abs=5)
        assert sy == pytest.approx(SCREEN_H // 2, abs=5)

    def test_map_from_pixel(self):
        """map_from_pixel debe producir el mismo resultado que map con normalización."""
        mapper = CoordinateMapper(SCREEN_W, SCREEN_H, dead_zone_margin=0.0)
        frame_w, frame_h = 640, 480

        norm_x, norm_y = 0.3, 0.6
        pixel_x = int(norm_x * frame_w)
        pixel_y = int(norm_y * frame_h)

        result_norm  = mapper.map(norm_x, norm_y)
        result_pixel = mapper.map_from_pixel(pixel_x, pixel_y, frame_w, frame_h)

        assert result_norm[0] == pytest.approx(result_pixel[0], abs=2)
        assert result_norm[1] == pytest.approx(result_pixel[1], abs=2)
