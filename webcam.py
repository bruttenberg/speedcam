import time

import cv2


# TODO: Clear frame buffer if in live mode

class Webcam:
    def __init__(self, source, frame_rate):
        self.camera = cv2.VideoCapture(source)
        self.frame_rate = frame_rate
        self.live = True
        if type(source) is str:
            self.live = False

    def get_image(self):
        ret, frame = self.camera.read()
        if self.live is False:
            time.sleep(1 / self.frame_rate)
        return frame

    def cleanup(self):
        self.camera.release()
