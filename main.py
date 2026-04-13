import librosa
import librosa.display
import numpy as np
import sys
import sounddevice as sd
import matplotlib.pyplot as plt
from fileinputpage import FileInputterPage
from PyQt6.QtWidgets import QWidget, QApplication, QStackedWidget

myApp = QApplication(sys.argv)
pageOne = FileInputterPage()

pages = QStackedWidget()
pages.addWidget(pageOne)



with open("fileinputpage.qss", 'r') as f:
    pages.setStyleSheet(f.read())
pages.setCurrentIndex(0)
pages.show()

sys.exit(myApp.exec())