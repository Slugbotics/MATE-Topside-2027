import sys
from PySide6.QtWidgets import QApplication, QDialog, QLineEdit, QPushButton, QVBoxLayout, QMainWindow, QLabel, QWidget, QSlider
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, Signal, Slot, QThread
import cv2

pyqtSignal = Signal
pyqtSlot = Slot

class Thread(QThread):
    changePixmap = pyqtSignal(QImage)

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

                #convert image to QImage
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(640, 480, Qt.KeepAspectRatio)
                self.changePixmap.emit(p) #Emit signal 



            else:
                break
        
    def stop(self):
        self.isRunning=False
        self.quit()
        self.terminate()

class VideoContainer(QWidget):
    def __init__(self):
        super().__init__()
        self.title = 'PySide Video'
        self.left = 100
        self.top = 100
        self.fwidth = 640
        self.fheight = 480
        self.initUI()

    @pyqtSlot(QImage)
    def setImage(self, image):
        #update image    
        self.label.setPixmap(QPixmap.fromImage(image)) #Emitted signal is sent to this slot
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.fwidth, self.fheight)
        self.resize(1200, 800)
        
        # create a label
        self.label = QLabel(self)        
        self.label.resize(640, 480)
        self.th = Thread(self) 
        self.th.changePixmap.connect(self.setImage) #Thread is connected to Widget
        self.th.start()
        self.show()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = VideoContainer()
    sys.exit(app.exec())