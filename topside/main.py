import os
from pathlib import Path
import sys
from PySide6.QtWidgets import QApplication, QMainWindow

from videoContainer import VideoContainer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("MATE Frontend")
        self.setCentralWidget(VideoContainer(0))

if __name__ == '__main__':
    script_dir = Path(__file__).resolve().parent
    os.chdir(script_dir)
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showFullScreen()
    sys.exit(app.exec())
