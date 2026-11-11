import sys
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QMainWindow, QLabel, QWidget, QSlider, QSizePolicy
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, Signal, Slot, QThread
import cv2
import numpy as np

class Thread(QThread):
    newFrame = Signal(np.ndarray)

    def run(self):
        self.isRunning = True
        cap = cv2.VideoCapture(0)

        while self.isRunning:
            ret, frame = cap.read()
            if ret:
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



            else:
                break
        
    def stop(self):
        self.isRunning=False
        self.quit()
        self.terminate()

class VideoContainer(QLabel):
    def __init__(self):
        super().__init__()
        self.title = 'Video stream'
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
        
        self.th = Thread(self)
        self.th.newFrame.connect(self.setImage) # Thread is connected to Widget
        self.th.start()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MATE Frontend")
        self.setCentralWidget(VideoContainer())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec())
