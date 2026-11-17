import sys
from PySide6.QtWidgets import QApplication, QMainWindow

from videoContainer import VideoContainer

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
