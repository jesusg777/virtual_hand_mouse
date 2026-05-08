# 🖱️ Virtual Hand Mouse

> Control tu cursor con gestos de mano usando Computer Vision en tiempo real, sin tocar ningún hardware físico.

Construido con **MediaPipe Tasks**, **OpenCV** y **PyAutoGUI** sobre Python 3.10+.

![Python](https://img.shields.io/badge/Python-3.10+-blue?logo=python&logoColor=white)
![MediaPipe](https://img.shields.io/badge/MediaPipe-0.10.9+-green?logo=google&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-4.9+-red?logo=opencv&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows%2010%2F11-lightgrey?logo=windows&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📋 Tabla de Contenidos

- [¿Qué hace este proyecto?](#-qué-hace-este-proyecto)
- [Demo](#-demo)
- [Gestos disponibles](#-gestos-disponibles)
- [Arquitectura del proyecto](#-arquitectura-del-proyecto)
- [Decisiones de diseño](#-decisiones-de-diseño)
- [Instalación](#-instalación)
- [Calibración](#-calibración)
- [Tests](#-tests)
- [Requisitos del sistema](#-requisitos-del-sistema)
- [Preguntas frecuentes](#-preguntas-frecuentes)

---

## 🎯 ¿Qué hace este proyecto?

Virtual Hand Mouse captura el video de tu webcam en tiempo real, detecta los **21 puntos clave (landmarks) de tu mano** usando una red neuronal (MediaPipe Hand Landmarker), y traduce la posición y forma de tu mano en comandos del ratón del sistema operativo.

**Caso de uso principal:** herramienta de accesibilidad para personas que no pueden utilizar un ratón físico convencional, permitiéndoles controlar el computador únicamente con movimientos de la mano frente a una cámara.

### ¿Cómo funciona internamente?

Cada frame del video pasa por un pipeline de 8 pasos:

```
Webcam → Detector → Extracción → Suavizado → Mapeo → Gestos → Acción → Overlay
  (1)      (2)         (3)          (4)         (5)     (6)      (7)      (8)
```

1. **Captura** — OpenCV abre la webcam y captura frames a ~30 FPS.
2. **Detección** — MediaPipe Hand Landmarker localiza los 21 puntos de la mano en el frame.
3. **Extracción** — Se extraen las coordenadas normalizadas del nudillo base del índice (landmark 5).
4. **Suavizado** — Una Media Móvil de 7 frames elimina el temblor natural de la mano.
5. **Mapeo** — Interpolación lineal convierte coordenadas de cámara (640×480) a coordenadas de pantalla (ej. 1920×1080), aplicando una zona muerta en los bordes.
6. **Gestos** — Una máquina de estados con histéresis detecta el gesto actual (clic, scroll, pausa).
7. **Acción** — PyAutoGUI ejecuta el comando correspondiente en el sistema operativo.
8. **Overlay** — OpenCV dibuja los landmarks, estado del gesto y FPS sobre el frame en vivo.

---

## 🎬 Demo

```
[INFO] Resolución detectada: 1920x1080
[INFO] Virtual Hand Mouse iniciado. Presiona 'q' para salir.
[INFO] Gestos disponibles:
         Mover cursor   → nudillo del índice
         Clic izquierdo → pinza índice + pulgar
         Clic derecho   → pinza medio  + pulgar
         Scroll         → índice + medio levantados
         Pausar         → puño cerrado
```

La ventana de OpenCV muestra la cámara en vivo con:
- Esqueleto de la mano dibujado en blanco
- Puntos verdes en los landmarks clave (índice, pulgar, medio)
- Estado del gesto actual en la esquina superior izquierda
- FPS en la esquina superior derecha
- Rectángulo gris indicando la zona activa (excluyendo la zona muerta)

---

## 🤚 Gestos disponibles

| Gesto | Descripción visual | Acción |
|---|---|---|
| **Mover cursor** | Mano abierta, dedos extendidos | El cursor sigue el nudillo del índice |
| **Clic izquierdo** | Punta del índice toca la punta del pulgar (pinza) | Clic izquierdo sostenido mientras dure la pinza |
| **Clic derecho** | Punta del dedo medio toca la punta del pulgar | Clic derecho |
| **Scroll** | Índice y medio levantados juntos (signo de paz / V) | Mover la mano arriba/abajo desplaza la página |
| **Pausar** | Puño completamente cerrado | El cursor se congela en su posición actual |

### ¿Por qué el cursor se controla con el nudillo y no con la punta del índice?

Esta es una de las decisiones de diseño más importantes del proyecto. Si el cursor siguiera la **punta** del índice, al hacer la pinza (bajar el dedo para tocarlo con el pulgar), el cursor se desplazaría justo antes de registrar el clic, haciendo que el clic caiga en el lugar equivocado.

La solución es controlar el cursor desde el **nudillo base del índice (landmark 5 — MCP)**, que permanece casi completamente estático cuando doblas el dedo. Así, la posición del cursor no cambia al hacer la pinza, y el clic cae exactamente donde el usuario apuntaba.

---

## 🏗️ Arquitectura del proyecto

```
virtual_hand_mouse/
│
├── main.py                  # Entry point — orquesta todas las capas
├── config.py                # Single source of truth de parámetros
├── requirements.txt         # Dependencias para pip install
├── pyproject.toml           # Metadata moderna del proyecto (PEP 517)
├── .gitignore               # Excluye venv, __pycache__, modelos binarios
├── README.md                # Este archivo
│
├── models/                  # Modelos de MediaPipe (NO versionados en git)
│   └── .gitkeep             # Mantiene el directorio en el repositorio
│
├── core/                    # Lógica de negocio pura — sin dependencias de IO
│   ├── __init__.py
│   ├── detector.py          # Wrapper sobre MediaPipe Hand Landmarker
│   ├── smoother.py          # Algoritmo de Media Móvil (Moving Average)
│   ├── mapper.py            # Interpolación lineal cámara → pantalla
│   └── gesture_engine.py   # Máquina de estados de gestos con histéresis
│
├── controllers/             # Capa que actúa sobre el sistema operativo
│   ├── __init__.py
│   └── mouse_controller.py  # Abstracción sobre PyAutoGUI
│
├── ui/                      # Capa de visualización
│   ├── __init__.py
│   └── overlay.py           # Dibuja landmarks, estado y FPS sobre el frame
│
├── utils/                   # Herramientas transversales
│   ├── __init__.py
│   └── fps_counter.py       # Contador de FPS con Media Móvil
│
└── tests/                   # Unit tests — corren sin cámara ni hardware
    ├── __init__.py
    ├── test_smoother.py     # 8 tests del algoritmo de suavizado
    └── test_mapper.py       # 8 tests de la interpolación de coordenadas
```

### Responsabilidad de cada módulo

| Módulo | Responsabilidad | Dependencias externas |
|---|---|---|
| `config.py` | Centraliza todos los parámetros en un solo lugar. Cero números mágicos en el código. | Ninguna |
| `core/detector.py` | Recibe un frame BGR y devuelve los 21 landmarks. No sabe nada de pantalla ni gestos. | MediaPipe |
| `core/smoother.py` | Recibe coordenadas ruidosas y devuelve el promedio de los últimos N frames. | NumPy |
| `core/mapper.py` | Convierte coordenadas normalizadas [0,1] a píxeles de pantalla, aplicando zona muerta e inversión del eje X. | NumPy |
| `core/gesture_engine.py` | Mantiene la máquina de estados y detecta el gesto actual con histéresis. | NumPy |
| `controllers/mouse_controller.py` | Traduce comandos de alto nivel (mover, clic, scroll) a llamadas al SO. | PyAutoGUI |
| `ui/overlay.py` | Dibuja el esqueleto, estado y FPS sobre el frame. | OpenCV |
| `utils/fps_counter.py` | Mide cuadros por segundo con una ventana deslizante. | Ninguna |
| `main.py` | Conecta todas las capas en el loop principal. No contiene lógica de negocio. | Todo lo anterior |

---

## 🧠 Decisiones de diseño

### 1. Layered Architecture + Single Responsibility

El proyecto está dividido en capas con responsabilidades estrictas:

- `core/` — no tiene ninguna dependencia de IO. Es matemática pura y totalmente testeable sin hardware.
- `controllers/` — es la única capa que habla con el sistema operativo. Si mañana quieres cambiar PyAutoGUI por `pynput`, solo modificas este archivo.
- `ui/` — es la única capa que habla con OpenCV para mostrar cosas. Si quieres agregar una GUI en Tkinter, solo agregas un archivo aquí.

### 2. Histéresis en la detección de clics

Un sistema ingenuo haría clic cuando `distancia < umbral` y lo soltaría cuando `distancia >= umbral`. El problema es que la mano tiembla y la distancia oscila alrededor del umbral, generando múltiples clics en menos de un segundo.

La solución es usar **dos umbrales distintos**:
- `click_threshold_enter` → umbral para **activar** el clic (más bajo)
- `click_threshold_exit` → umbral para **desactivar** el clic (más alto)

La zona entre ambos umbrales es la "zona de histéresis". El clic permanece activo mientras la distancia no supere el umbral de salida, aunque momentáneamente supere el de entrada. Esto elimina completamente el efecto de "chattering".

```
distancia:  ──────╮    ╭──────────────╮    ╭──────
                  │    │              │    │
threshold_exit:  ─┼────┼──────────────┼────┼──
                  │    │              │    │
threshold_enter: ─┼────┼──────────────┼────┼──
                  ╰────╯              ╰────╯
clic:        OFF  [  ON              ON  ] OFF
```

### 3. Máquina de estados con orden de prioridad

Los gestos se evalúan en orden de prioridad estricto:

```
PAUSE → LEFT_CLICK → RIGHT_CLICK → SCROLL → IDLE
```

Esto garantiza que si el usuario está haciendo un clic y accidentalmente levanta el dedo medio, el estado no salte a SCROLL. El gesto de mayor prioridad siempre gana.

### 4. Punto de control del cursor

El cursor se controla desde el **landmark 5 (MCP — nudillo base del índice)** en lugar de la punta del dedo (landmark 8). La razón es que la punta del índice se desplaza significativamente al doblarse para hacer la pinza, moviendo el cursor justo antes del clic. El nudillo base permanece estático durante la pinza, garantizando que el clic caiga exactamente donde el usuario apuntaba.

### 5. Suavizado por Media Móvil

Las coordenadas de la mano tienen ruido frame a frame por el movimiento natural y el ruido de la cámara. Sin suavizado, el cursor "tiembla" constantemente. La solución es promediar las últimas N coordenadas:

```
posición_suavizada = (pos[t] + pos[t-1] + ... + pos[t-N+1]) / N
```

- **N bajo (3–5):** respuesta rápida, algo de temblor visible.
- **N alto (10–15):** muy suave, pero con lag perceptible al mover rápido.
- **N = 7 (default):** balance óptimo para uso general.

### 6. Zona muerta en bordes

Sin zona muerta, el usuario debe llevar la mano al extremo físico del frame para mover el cursor al borde de la pantalla, lo que genera fatiga. La zona muerta recorta un porcentaje de cada borde del frame:

```
zona activa = frame central sin el X% de cada lado
```

Esto hace que el rango de movimiento útil de la mano sea más cómodo y centrado.

### 7. Modelo binario fuera del repositorio

El archivo `hand_landmarker.task` (~10 MB) no se versiona en git. En su lugar:
- `.gitignore` lo excluye explícitamente.
- `models/.gitkeep` mantiene el directorio versionado.
- El README (esta sección de instalación) explica cómo descargarlo.

Esto sigue la práctica estándar de la industria para proyectos de ML.

---

## 🚀 Instalación

### Requisitos previos

- Python 3.10 o superior
- pip
- Git
- Webcam (integrada o USB)

### Paso 1 — Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/virtual-hand-mouse.git
cd virtual-hand-mouse
```

### Paso 2 — Crear entorno virtual

```bash
python -m venv venv
venv\Scripts\activate
```

Verifica que el entorno esté activo: el prompt debería mostrar `(venv)` al inicio.

### Paso 3 — Instalar dependencias

```bash
pip install -r requirements.txt
```

Las dependencias instaladas son:

| Librería | Versión mínima | Uso |
|---|---|---|
| `mediapipe` | 0.10.9 | Detección de landmarks de la mano |
| `opencv-python` | 4.9.0 | Captura de video y renderizado del overlay |
| `pyautogui` | 0.9.54 | Control del ratón del sistema operativo |
| `numpy` | 1.26.0 | Cálculos matriciales y mapeo de coordenadas |
| `pytest` | 8.0.0 | Ejecución de tests unitarios |

### Paso 4 — Descargar el modelo de MediaPipe

El modelo de red neuronal no está incluido en el repositorio. Descárgalo ejecutando:

```bash
python -c "
import urllib.request, pathlib
url = 'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task'
pathlib.Path('models').mkdir(exist_ok=True)
urllib.request.urlretrieve(url, 'models/hand_landmarker.task')
print('Modelo descargado correctamente.')
"
```

Esto descarga el archivo `hand_landmarker.task` (~10 MB) en la carpeta `models/`.

### Paso 5 — Ejecutar

```bash
python main.py
```

**Para salir:** presiona `Q` en la ventana de la cámara, o mueve el cursor a la **esquina superior izquierda** de la pantalla (failsafe de seguridad de PyAutoGUI).

---

## ⚙️ Calibración

Todos los parámetros ajustables están centralizados en **`config.py`**. No necesitas modificar ningún otro archivo para calibrar el proyecto a tu hardware.

### ¿Por qué necesito calibrar?

Los umbrales de gestos dependen del **tamaño de tu mano** y de la **distancia a la cámara**. Los valores por defecto son un punto de partida razonable, pero cada persona necesita ajustarlos.

### Cómo encontrar tus umbrales personales

Agrega temporalmente estas líneas en `main.py` justo antes de `engine.update(landmarks)`:

```python
from core.gesture_engine import _euclidean, LandmarkIndex
thumb  = landmarks.get_2d(LandmarkIndex.THUMB_TIP)
index  = landmarks.get_2d(LandmarkIndex.INDEX_FINGER_TIP)
wrist  = landmarks.get_2d(LandmarkIndex.WRIST)
mcp    = landmarks.get_2d(LandmarkIndex.INDEX_FINGER_MCP)
hand_size = _euclidean(wrist, mcp) or 1e-6
print(f"idx-thumb: {_euclidean(index, thumb)/hand_size:.3f}")
```

Ejecuta el programa y observa los valores en consola:
1. Con la **mano abierta** (modo mover cursor): anota el valor mínimo que ves.
2. Haciendo la **pinza** (modo clic): anota el valor máximo que alcanzas.

Esos dos valores son los límites de tu zona de histéresis. El `click_threshold_enter` debe estar entre ambos, más cerca del valor de pinza. El `click_threshold_exit` debe ser notablemente mayor, más cerca del valor de mano abierta.

### Parámetros disponibles

```python
# ── config.py ──────────────────────────────────────────────────────────

# Cámara
CAMERA = CameraConfig(
    device_index=0,      # Índice de la webcam. Cámbialo a 1, 2... si tienes varias.
    frame_width=640,     # Resolución de captura.
    frame_height=480,
    fps=30,
)

# Suavizado del cursor
SMOOTHER = SmootherConfig(
    buffer_size=7,       # Frames a promediar. Sube para más suavidad, baja para más respuesta.
)

# Mapeo de coordenadas
MAPPER = MapperConfig(
    dead_zone_margin=0.10,  # Porcentaje de borde ignorado. 0.10 = 10% por lado.
)

# Gestos y umbrales (los más importantes de calibrar)
GESTURE = GestureConfig(
    click_threshold_enter=0.200,       # Umbral de ACTIVACIÓN del clic izquierdo.
    click_threshold_exit=0.600,        # Umbral de DESACTIVACIÓN. Siempre mayor que enter.
    right_click_threshold_enter=0.200, # Igual para el clic derecho.
    right_click_threshold_exit=0.600,
    scroll_speed=30,                   # Velocidad del scroll. Sube si va muy lento.
)
```

### Guía rápida de síntomas y soluciones

| Síntoma | Causa probable | Solución |
|---|---|---|
| El clic se activa solo | `click_threshold_enter` muy alto | Bajarlo |
| No puedo activar el clic | `click_threshold_enter` muy bajo | Subirlo |
| El clic parpadea (se activa y desactiva rápido) | Zona de histéresis muy pequeña | Aumentar la diferencia entre `enter` y `exit` |
| El cursor tiembla mucho | `buffer_size` muy bajo | Subirlo a 10–12 |
| El cursor va con lag notable | `buffer_size` muy alto | Bajarlo a 5 |
| Debo estirar el brazo hasta el borde | `dead_zone_margin` muy grande | Bajarlo a 0.05 |
| El cursor llega al borde sin esfuerzo | `dead_zone_margin` muy pequeño | Subirlo a 0.15 |

---

## 🧪 Tests

El proyecto incluye tests unitarios que verifican la matemática pura de los módulos críticos, sin necesidad de cámara ni hardware.

```bash
pytest tests/ -v
```

Salida esperada:

```
tests/test_smoother.py::TestMovingAverageSmootherInit::test_default_initialization PASSED
tests/test_smoother.py::TestMovingAverageSmootherInit::test_custom_buffer_size PASSED
tests/test_smoother.py::TestMovingAverageSmootherInit::test_invalid_buffer_size_raises PASSED
tests/test_smoother.py::TestMovingAverageSmootherBehavior::test_single_value_returns_itself PASSED
tests/test_smoother.py::TestMovingAverageSmootherBehavior::test_smoothing_reduces_noise PASSED
tests/test_smoother.py::TestMovingAverageSmootherBehavior::test_constant_signal_returns_constant PASSED
...
tests/test_mapper.py::TestCoordinateMapperMapping::test_center_maps_to_center PASSED
tests/test_mapper.py::TestCoordinateMapperMapping::test_x_axis_is_flipped PASSED
tests/test_mapper.py::TestCoordinateMapperDeadZone::test_dead_zone_reduces_effective_range PASSED
...

16 passed in 0.42s
```

### ¿Qué se testea?

**`test_smoother.py`** — Verifica que el algoritmo de Media Móvil:
- Devuelve el propio valor cuando el buffer tiene un solo elemento.
- Promedia correctamente N valores.
- Atenúa spikes de ruido correctamente.
- Se comporta bien al llenarse el buffer y al resetearse.
- Maneja múltiples dimensiones de forma independiente.

**`test_mapper.py`** — Verifica que la interpolación de coordenadas:
- Mapea el centro del frame al centro de la pantalla.
- Invierte correctamente el eje X (compensación del espejo de la cámara).
- No invierte el eje Y.
- Clampea coordenadas fuera del rango [0,1] al borde de la pantalla.
- La zona muerta no desplaza el centro de la imagen.

---

## 💻 Requisitos del sistema

| Componente | Mínimo | Recomendado |
|---|---|---|
| Sistema operativo | Windows 10 | Windows 11 |
| Python | 3.10 | 3.11 o 3.12 |
| CPU | Intel Core i5 4ª gen / AMD Ryzen 5 | Intel Core i5 8ª gen o superior |
| RAM | 4 GB | 8 GB |
| Webcam | 480p a 30 FPS | 720p a 30 FPS |
| Iluminación | Luz ambiente normal | Luz directa sobre la mano |

### Nota sobre el rendimiento

MediaPipe corre el modelo de detección de landmarks en CPU por defecto. En equipos modernos se obtienen fácilmente 25–30 FPS. Si el rendimiento es bajo, prueba reducir la resolución de captura en `config.py`:

```python
CAMERA = CameraConfig(frame_width=320, frame_height=240)
```

---

## ❓ Preguntas frecuentes

**¿Por qué el cursor se mueve al revés horizontalmente?**
La cámara captura el video como un espejo. El `CoordinateMapper` invierte el eje X por defecto para que el movimiento sea intuitivo. Si tu cámara ya está configurada sin espejo, cambia la línea `flipped_x = 1.0 - norm_x` a `flipped_x = norm_x` en `core/mapper.py`.

**¿Por qué los mensajes de warning de TensorFlow Lite en la consola?**
Son mensajes informativos de MediaPipe sobre el backend de inferencia, no errores. No afectan el funcionamiento del programa. No es posible suprimirlos sin modificar la librería.

**¿Puedo usar esto en Mac o Linux?**
El código es compatible, pero PyAutoGUI requiere configuración adicional en macOS (permisos de accesibilidad) y en Linux (dependencias de `python3-xlib`). El proyecto fue desarrollado y probado en Windows.

**¿Funciona con dos manos a la vez?**
El detector está configurado para detectar una sola mano (`num_hands=1` en `config.py`). Puedes aumentarlo a 2, pero necesitarías extender la lógica de `main.py` para manejar múltiples landmarks simultáneamente.

**¿Por qué el modelo no está en el repositorio?**
Los archivos binarios de modelos de ML no deben versionarse en git porque son grandes (~10 MB), no son código legible, y pueden cambiar de versión. La práctica estándar es documentar cómo descargarlo y excluirlo del repositorio.

---

## 📄 Licencia

MIT — Libre para uso personal, educativo y comercial.