import cv2

class Camera:
    def __init__(self, source, cam_type):
        self.cam_type = cam_type
        self.cap = cv2.VideoCapture(source)
        
    def get_frame(self):
        success, frame = self.cap.read()
        if not success:
            return b''
        ret, jpeg = cv2.imencode('.jpg', frame)
        return jpeg.tobytes()
    
    def release(self):
        self.cap.release()