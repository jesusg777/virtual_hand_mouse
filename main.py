"""
main.py — Entry point del Virtual Hand Mouse.

Orquesta todos los módulos del proyecto en el loop principal.
Sigue el patrón de composición: no contiene lógica de negocio,
solo conecta las capas entre sí.

Flujo por frame:
  1. Capturar frame de la webcam          (OpenCV)
  2. Detectar landmarks de la mano        (core/detector)
  3. Extraer coordenadas del índice
  4. Suavizar las coordenadas             (core/smoother)
  5. Mapear a resolución de pantalla      (core/mapper)
  6. Reconocer el gesto actual            (core/gesture_engine)
  7. Ejecutar la acción en el SO          (controllers/mouse_controller)
  8. Renderizar overlay y mostrar frame   (ui/overlay)

Salida:
  - Presiona 'q' para salir limpiamente.
  - Mueve el cursor a la esquina superior izquierda (failsafe de PyAutoGUI).
"""

import sys
import cv2
import pyautogui

from config import CAMERA, OVERLAY
from core.detector      import HandDetector, LandmarkIndex
from core.smoother      import MovingAverageSmoother
from core.mapper        import CoordinateMapper
from core.gesture_engine import GestureEngine, GestureState, _euclidean
from controllers.mouse_controller import MouseController
from ui.overlay         import Overlay
from utils.fps_counter  import FPSCounter


def main() -> None:
    # ------------------------------------------------------------------
    # Obtener resolución real del monitor
    # ------------------------------------------------------------------
    screen_w, screen_h = pyautogui.size()
    print(f"[INFO] Resolución detectada: {screen_w}x{screen_h}")

    # ------------------------------------------------------------------
    # Inicializar módulos
    # ------------------------------------------------------------------
    cap = cv2.VideoCapture(CAMERA.device_index)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,  CAMERA.frame_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA.frame_height)
    cap.set(cv2.CAP_PROP_FPS,          CAMERA.fps)

    if not cap.isOpened():
        print(f"[ERROR] No se pudo abrir la cámara con índice {CAMERA.device_index}")
        sys.exit(1)

    detector  = HandDetector()
    smoother  = MovingAverageSmoother(n_dimensions=2)
    mapper    = CoordinateMapper(screen_width=screen_w, screen_height=screen_h)
    engine    = GestureEngine()
    mouse     = MouseController()
    overlay   = Overlay()
    fps_counter = FPSCounter()

    print("[INFO] Virtual Hand Mouse iniciado. Presiona 'q' para salir.")
    print("[INFO] Gestos disponibles:")
    print("         Mover cursor  → dedo índice")
    print("         Clic izquierdo → pinza índice + pulgar")
    print("         Clic derecho  → pinza medio  + pulgar")
    print("         Scroll        → índice + medio levantados")
    print("         Pausar        → puño cerrado")

    try:
        while True:
            # 1. Capturar frame
            ret, frame = cap.read()
            if not ret:
                print("[WARN] Frame no leído, reintentando...")
                continue

            # Espejo horizontal para visualización natural
            frame = cv2.flip(frame, 1)

            fps_counter.tick()

            # 2. Detectar landmarks
            landmarks = detector.process(frame)

            if landmarks is not None:
                # 3. Extraer coordenadas del dedo índice (landmark 8)
                raw_x, raw_y = landmarks.get_2d(LandmarkIndex.INDEX_FINGER_TIP)

                # 4. Suavizar
                smooth_x, smooth_y = smoother.update(raw_x, raw_y)

                # 5. Mapear a pantalla
                screen_x, screen_y = mapper.map(smooth_x, smooth_y)

                # 6. Reconocer gesto
                # DEBUG TEMPORAL — eliminar después de calibrar
                thumb  = landmarks.get_2d(LandmarkIndex.THUMB_TIP)
                index  = landmarks.get_2d(LandmarkIndex.INDEX_FINGER_TIP)
                middle = landmarks.get_2d(LandmarkIndex.MIDDLE_FINGER_TIP)
                wrist  = landmarks.get_2d(LandmarkIndex.WRIST)
                mcp    = landmarks.get_2d(LandmarkIndex.INDEX_FINGER_MCP)
                hand_size = _euclidean(wrist, mcp) or 1e-6
                print(f"idx-thumb: {_euclidean(index, thumb)/hand_size:.3f}  |  mid-thumb: {_euclidean(middle, thumb)/hand_size:.3f}")
                gesture = engine.update(landmarks)

                # 7. Actuar sobre el SO
                if gesture.cursor_active:
                    mouse.move(screen_x, screen_y)

                if gesture.state == GestureState.LEFT_CLICK:
                    mouse.left_click_down()
                else:
                    mouse.left_click_up()

                if gesture.state == GestureState.RIGHT_CLICK:
                    mouse.right_click_down()
                else:
                    mouse.right_click_up()

                if gesture.state == GestureState.SCROLL:
                    mouse.scroll(gesture.scroll_delta)

            else:
                # Sin mano detectada: soltar botones y resetear suavizado
                mouse.release_all()
                smoother.reset()
                engine.reset()

            # 8. Overlay y visualización
            frame = overlay.draw(
                frame,
                landmarks,
                engine.current_state,
                fps_counter.get(),
            )

            cv2.imshow("Virtual Hand Mouse — presiona Q para salir", frame)

            # Salida con 'q'
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break

    except pyautogui.FailSafeException:
        print("\n[INFO] FailSafe activado: cursor en esquina superior izquierda.")

    except KeyboardInterrupt:
        print("\n[INFO] Interrumpido por el usuario.")

    finally:
        print("[INFO] Cerrando recursos...")
        mouse.release_all()
        detector.close()
        cap.release()
        cv2.destroyAllWindows()
        print("[INFO] Virtual Hand Mouse finalizado.")


if __name__ == "__main__":
    main()
