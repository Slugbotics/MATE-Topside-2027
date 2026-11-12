import sys
import time
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QMainWindow, QLabel, QWidget, QSlider, QSizePolicy
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, Signal, Slot, QThread
import cv2
import numpy as np

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
            #workshop code
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower = (25, 50, 50)
            upper = (35, 255, 255)
            mask = cv2.inRange(hsv, lower, upper)
            contours, _  = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for contour in contours:
                if cv2.contourArea(contour) > 500:
                    x, y, w, h = cv2.boundingRect(contour)
                    cv2.rectangle(frame, (x,y), (x+w, y+h), (0, 0, 255), 3) #apply rectangle to image

            self.newFrame.emit(frame) #Emit signal
        
        if self.cap is not None:
            self.cap.release()

    def stop(self):
        self.requestInterruption()

class VideoContainer(QLabel):
    def __init__(self, camera=0):
        super().__init__()
        self.title = f'Video stream ({camera})'
        self.camera = camera
        self.initUI()

    @Slot(np.ndarray)
    def setImage(self, image):
        #convert image to QImage
        rgbImage = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        h, w, ch = rgbImage.shape
        bytesPerLine = ch * w
        qImage = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
        
        # convert to pixmap
        pixmap = QPixmap.fromImage(qImage)
        scaledPixmap = pixmap.scaled(
            self.size(), 
            Qt.AspectRatioMode.KeepAspectRatio, 
            Qt.TransformationMode.SmoothTransformation
        )

        #update image    
        self.setPixmap(scaledPixmap)
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.resize(1200, 800)
        
        # create a label
        self.setAlignment(Qt.AlignCenter)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        self.th = CameraThread(self.camera, self)
        self.th.newFrame.connect(self.setImage) # Thread is connected to Widget
        self.th.start()

        QApplication.instance().aboutToQuit.connect(self.stop)
    
    def stop(self):
        self.th.stop()
        self.th.wait()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MATE Frontend")
        self.setCentralWidget(VideoContainer(0))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec())
