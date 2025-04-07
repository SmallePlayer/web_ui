from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import cv2
import threading
import numpy as np
from queue import Queue
import time

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Очереди для кадров
frame_queues = {
    "camera1": Queue(maxsize=1),
    "camera2": Queue(maxsize=1)
}

# Состояния кнопок
button_states = {
    "panel_btn1": False,
    "panel_btn2": False,
    "panel_btn3": False,
    "video1_btn": False,
    "video2_btn": False
}


def camera_thread(camera_id, source):
    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        print(f"Camera {camera_id} (source {source}) not available - skipping")
        return

    print(f"Camera {camera_id} started with source {source}")
    while True:
        try:
            ret, frame = cap.read()
            if not ret:
                time.sleep(0.1)
                continue

            frame = cv2.resize(frame, (640, 480))
            _, buffer = cv2.imencode('.jpg', frame)
            if frame_queues[camera_id].full():
                frame_queues[camera_id].get()
            frame_queues[camera_id].put(buffer.tobytes())
            time.sleep(0.033)  # ~30 FPS

        except Exception as e:
            print(f"Error in {camera_id}: {str(e)}")
            time.sleep(1)


# Проверка доступности камер перед запуском
available_cameras = []
for i in range(2):  # Проверяем первые 2 камеры
    cap = cv2.VideoCapture(i)
    if cap.isOpened():
        available_cameras.append(i)
        cap.release()

print(f"Available cameras: {available_cameras}")

# Запускаем потоки только для доступных камер
if len(available_cameras) >= 1:
    threading.Thread(target=camera_thread, args=("camera1", available_cameras[0]), daemon=True).start()
if len(available_cameras) >= 2:
    threading.Thread(target=camera_thread, args=("camera2", available_cameras[1]), daemon=True).start()
else:
    # Если вторая камера недоступна, создаем черный экран
    def black_frame_generator():
        while True:
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            _, buffer = cv2.imencode('.jpg', frame)
            if frame_queues["camera2"].full():
                frame_queues["camera2"].get()
            frame_queues["camera2"].put(buffer.tobytes())


    threading.Thread(target=black_frame_generator, daemon=True).start()


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "camera2_available": len(available_cameras) >= 2
    })


@app.get("/video_feed/{camera_id}")
async def video_feed(camera_id: str):
    async def generate():
        while True:
            frame = frame_queues[camera_id].get()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


@app.post("/toggle_button/{btn_id}")
async def toggle_button(btn_id: str):
    if btn_id in button_states:
        button_states[btn_id] = not button_states[btn_id]
        print(f"{btn_id} state: {button_states[btn_id]}")
    return {"state": button_states.get(btn_id, False)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=5000)
