import cv2
import numpy as np
import time
from PySide6.QtCore import QThread, Signal

class CameraThread(QThread):
    newFrame = Signal(np.ndarray)

    def __init__(self, camera=0, parent=None):
        super().__init__(parent)
        self.camera = camera
        self.cap = None
        self.reconnectTime = time.time() - 100
    
    def reconnect(self):
        if time.time() - self.reconnectTime < 1:
            time.sleep(1 - (time.time() - self.reconnectTime))
        self.reconnectTime = time.time()
        if self.cap is not None:
            self.cap.release()
        self.cap = cv2.VideoCapture(self.camera)
        if not self.cap.isOpened():
            print(f"ERROR: failed to connect to video: {self.camera}")
            self.cap = None

    def run(self):
        self.reconnect()

        while not self.isInterruptionRequested():
            if self.cap is None:
                self.reconnect()
                continue
            ret, frame = self.cap.read()
            if not ret:
                self.reconnect()
                continue

            self.newFrame.emit(frame) #Emit signal
        
        if self.cap is not None:
            self.cap.release()

    def stop(self):
        self.requestInterruption()
