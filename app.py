from flask import Flask, render_template, Response, request
import cv2

app = Flask(__name__)

# Захват видео с камеры (0 — это индекс камеры по умолчанию)
camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()  # Чтение кадра с камеры
        if not success:
            break
        else:
            # Преобразуем кадр в JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

# Добавляем маршрут для обработки POST-запросов от кнопок
@app.route('/relay', methods=['POST'])
def control_relay():
    relay_number = request.form.get('relay')  # Получаем номер реле из запроса
    print(f"реле{relay_number}")  # Выводим в терминал
    return f"реле{relay_number} активировано", 200  # Возвращаем ответ

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')