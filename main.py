import librosa
import librosa.display
import numpy as np
import sys
import matplotlib.pyplot as plt
from fileinputpage import FileInputterPage
from PyQt6.QtWidgets import QWidget, QApplication, QStackedWidget
from database import create_database
from pathlib import Path

style_path = Path(__file__).resolve().parent / "fileinputpage.qss"

myApp = QApplication(sys.argv)

create_database()

pageOne = FileInputterPage()

pages = QStackedWidget()
pages.addWidget(pageOne)


with open(style_path, encoding="utf-8") as f:
    pages.setStyleSheet(f.read())

pages.setCurrentIndex(0)

myApp.aboutToQuit.connect(pageOne.cleanup)

pages.show()


sys.exit(myApp.exec())


