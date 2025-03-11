from flask import Flask, render_template, Response, request, jsonify  # Добавлен jsonify
import cv2
from camera import Camera

app = Flask(__name__)

relays = {
    'relay1': False,
    'relay_row': False,
    'relay_common': False
}

# Инициализация камеры 
current_camera = Camera(source=0, cam_type='usb')

def gen_frames():
    while True:
        frame = current_camera.get_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/get_relays')
def get_relays():
    return jsonify(relays)  # Теперь работает с правильным импортом

@app.route('/control', methods=['POST'])
def control():
    relay = request.form.get('relay')
    if relay in relays:
        relays[relay] = not relays[relay]
        print(f"{relay} state: {relays[relay]}")
        return jsonify({relay: relays[relay]})
    return jsonify({'error': 'Relay not found'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)