import sys
from PySide6.QtWidgets import QApplication, QMainWindow

from controlThread import ControlThread
from videoContainer import VideoContainer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MATE Frontend")
        # TODO: use camera stream instead of laptop and add more video containers
        videoContainers = [VideoContainer(0)]
        # TODO: add a layout for multiple video containers
        self.setCentralWidget(videoContainers[0])
        
        self.controlThread = ControlThread(self)
        QApplication.instance().aboutToQuit.connect(self.controlThread.requestInterruption)
        
        for videoContainer in videoContainers:
            videoContainer.start()
        
        self.controlThread.start()
        QApplication.instance().aboutToQuit.connect(self.controlThread.wait)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec())
