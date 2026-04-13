import librosa
import librosa.display
import queue
import numpy as np
import scipy.signal as sp
import pyaudiowpatch as pyaudio
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QWidget, QPushButton, QFileDialog, QApplication, QVBoxLayout, QFileDialog

class FileInputterPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Input A File")
        layout = QVBoxLayout()
        fileButton = QPushButton("Select a File")
        recordButton = QPushButton("Record")
        stopButton = QPushButton("Stop")
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.handler = queue.Queue() 
        self.find_device()
        
        layout.addWidget(fileButton)
        layout.addWidget(recordButton)
        layout.addWidget(stopButton)
        fileButton.clicked.connect(self.on_click_file)
        recordButton.clicked.connect(self.on_click_record)
        stopButton.clicked.connect(self.on_click_stop)

        self.setLayout(layout)
    
    def on_click_record(self):
        self.stream = self.p.open(stream_callback=self.callback, input_device_index=17, channels=1, input=True, rate=48000, format=2)
        print("Running")



        

    def callback(self, in_data, frame_count, time_info, status_flags):
        if (status_flags):
            print(status_flags)
        audio_data = np.frombuffer(in_data, dtype=np.int32).astype(np.float32)
        audio_data /= 32768.0
        self.handler.put(audio_data)

        return(None, pyaudio.paContinue)



    def on_click_stop(self):
        
        self.stream.stop_stream()
        self.stream.close()
        print("Recording stopped")
        audioData = []
        
        while (not (self.handler.empty())):
            slice = self.handler.get()
            audioData.append(slice)
            self.handler.task_done()

        y = np.concatenate(audioData)
        
        spectro = librosa.feature.melspectrogram(y=y, sr=48000)
        spectro_db = librosa.power_to_db(spectro, ref = np.max)
        plt.figure(figsize=(10,4))
        librosa.display.specshow(spectro_db, x_axis="time", y_axis="mel", sr=48000)
        plt.colorbar(format="%+2.0f dB")
        plt.title("Mel Spectro")
        plt.show()

        self.p.terminate()


    def find_device(self):
        print(self.p.get_default_wasapi_loopback())




    def create_spectro(self, audio): 
        audio_paths = audio
        for audio_path in audio_paths:
            y, sr = librosa.load(audio_path)
            print(np.shape(y))
            spectro = librosa.feature.melspectrogram(y=y, sr=sr)
            print(spectro.shape())
            spectro_db = librosa.power_to_db(spectro, ref=np.max)
            print(spectro_db.shape())
            # peaks = sp.find_peaks(spectro_db)
            plt.figure(figsize=(10,4))
            librosa.display.specshow(spectro_db, x_axis="time", y_axis="mel", sr=sr)
            # plt.plot(peaks, y[peaks])
            plt.colorbar(format="%+2.0f dB")
            plt.title("Mel Spectro")
            plt.show()




    def on_click_file(self):
        audio_paths = self.open_file()
        self.create_spectro(audio_paths)

    

    def open_file(self):
        audio_path, _ = QFileDialog.getOpenFileNames(self, "Select Audio File", r"C:\Users\andyl\VSCode Music Project\assets", "Audio Files (*.mp3)")
        return audio_path
    

