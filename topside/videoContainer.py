import cv2
import numpy as np
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import QLabel, QSizePolicy, QApplication
from PySide6.QtGui import QPixmap, QImage

from cameraThread import CameraThread

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
