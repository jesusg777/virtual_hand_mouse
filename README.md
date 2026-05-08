# 🖱️ Virtual Hand Mouse

Control tu cursor con gestos de mano usando Computer Vision en tiempo real.

Construido con **MediaPipe Tasks**, **OpenCV** y **PyAutoGUI** sobre Python 3.10+.

---

## ¿Qué hace este proyecto?

Captura video de tu webcam, detecta los 21 landmarks de tu mano usando una red neuronal
(MediaPipe Hand Landmarker) y traduce la posición y forma de tu mano en comandos del ratón,
sin tocar ningún hardware físico.

**Caso de uso principal:** herramienta de accesibilidad para personas que no pueden
utilizar un ratón convencional.

---

## Gestos disponibles

| Gesto | Acción |
|---|---|
| Dedo índice extendido | Mover cursor |
| Pinza índice + pulgar | Clic izquierdo |
| Pinza medio + pulgar | Clic derecho |
| Índice + medio levantados | Scroll (movimiento vertical) |
| Puño cerrado | Pausar cursor |

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/virtual-hand-mouse.git
cd virtual-hand-mouse
```

### 2. Crear entorno virtual e instalar dependencias

```bash
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
```

### 3. Descargar el modelo de MediaPipe

```bash
python -c "
import urllib.request, pathlib
url = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task'
pathlib.Path('models').mkdir(exist_ok=True)
urllib.request.urlretrieve(url, 'models/hand_landmarker.task')
print('Modelo descargado correctamente.')
"
```

### 4. Ejecutar

```bash
python main.py
```

Presiona **Q** para salir. Mueve el cursor a la **esquina superior izquierda** para activar el failsafe de seguridad.

---

## Calibración

Todos los parámetros ajustables están en **`config.py`**. No necesitas tocar ningún otro archivo:

```python
# Sensibilidad del suavizado
SMOOTHER = SmootherConfig(buffer_size=7)   # Aumenta para más suavidad

# Umbral de clic (distancia normalizada por el tamaño de la mano)
GESTURE = GestureConfig(
    click_threshold_enter=0.040,   # Reducir → más fácil hacer clic
    click_threshold_exit=0.060,    # Siempre mayor que enter (histéresis)
)

# Zona muerta en bordes del frame
MAPPER = MapperConfig(dead_zone_margin=0.10)   # 10% de margen por lado
```

---

## Arquitectura

```
virtual_hand_mouse/
│
├── main.py                  # Entry point — orquesta las capas
├── config.py                # Single source of truth de parámetros
│
├── core/                    # Lógica de negocio pura (sin IO)
│   ├── detector.py          # MediaPipe Hand Landmarker wrapper
│   ├── smoother.py          # Moving Average (elimina temblor)
│   ├── mapper.py            # Interpolación cámara → pantalla
│   └── gesture_engine.py   # Máquina de estados de gestos
│
├── controllers/
│   └── mouse_controller.py  # Abstracción sobre PyAutoGUI
│
├── ui/
│   └── overlay.py           # Renderizado del overlay en OpenCV
│
├── utils/
│   └── fps_counter.py       # Contador de FPS desacoplado
│
├── models/                  # Modelo de MediaPipe (no versionado)
└── tests/                   # Unit tests (pytest)
    ├── test_smoother.py
    └── test_mapper.py
```

**Decisiones de diseño:**
- `core/` no tiene dependencias de IO — es 100% testeable sin hardware.
- `GestureEngine` usa una máquina de estados con histéresis para evitar clics dobles.
- `CoordinateMapper` invierte el eje X para compensar el espejo natural de la cámara.
- `MouseController` implementa un guardián de estado para no enviar comandos redundantes al SO.

---

## Tests

```bash
pytest tests/ -v
```

Los tests cubren `smoother.py` y `mapper.py` con matemática pura, sin necesidad de cámara.

---

## Requisitos del sistema

- Python 3.10 o superior
- Windows 10/11
- Webcam (integrada o USB)
- ~250 MB de RAM en ejecución

---

## Licencia

Hecho para uso personal, educativo y comercial.
