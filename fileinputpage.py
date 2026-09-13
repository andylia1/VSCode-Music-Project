import librosa
import librosa.display
import queue
import numpy as np
import scipy.ndimage as sp
import pyaudiowpatch as pyaudio
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QWidget, QPushButton, QFileDialog, QApplication, QVBoxLayout, QFileDialog, QMessageBox
import hashlib
from database import DB_PATH
import sqlite3
from pathlib import Path

class FileInputterPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Input A File")
        layout = QVBoxLayout()
        fileButton = QPushButton("Select a File")
        recordButton = QPushButton("Match Song")
        stopButton = QPushButton("Stop Matching")
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


    def callback(self, in_data, frame_count, time_info, status_flags):
        if (status_flags):
            print(status_flags)
        audio_data = np.frombuffer(in_data, dtype=np.int32).astype(np.float32)
        audio_data /= 2147483648.0
        self.handler.put(audio_data)

        return(None, pyaudio.paContinue)


    def find_device(self):
        print(self.p.get_default_wasapi_loopback())

    
    def on_click_record(self):
        if self.stream is not None:
            print("A recording is already running")
            return

        self.handler = queue.Queue()
        
        self.stream = self.p.open(stream_callback=self.callback, input_device_index=self.p.get_default_wasapi_loopback()["index"], channels=1, input=True, rate=48000, format=2)
        print("Running")
        print(self.p.get_default_wasapi_loopback()["index"])


    def on_click_stop(self):
        
        self.stream.stop_stream()
        self.stream.close()
        self.stream = None
        print("Recording stopped")
        audioData = []
        
        while (not (self.handler.empty())):
            slice = self.handler.get()
            audioData.append(slice)
            self.handler.task_done()

        y = np.concatenate(audioData)
        
        spectro = librosa.feature.melspectrogram(y=y, sr=48000)
        spectro_db = librosa.power_to_db(spectro, ref = np.max)

        #Creates peaks of spectrogram to generate fingerprints
        peaks = sp.maximum_filter(spectro_db, size=(10, 10)) == spectro_db
        threshold = spectro_db > -40
        peak_indexes = np.argwhere(peaks & threshold)
        print(np.shape(peak_indexes))
        fingerprints = self.fingerprint_creation(peak_indexes[:, [1,0]])


        #Plots spectrogram
        # plt.figure(figsize=(10,4))
        # librosa.display.specshow(spectro_db, x_axis="time", y_axis="mel", sr=48000)
        # plt.colorbar(format="%+2.0f dB")
        # plt.title("Mel Spectro")
        # plt.show()

        results = self.match_fingerprints(fingerprints)

        song_id, song_name, offset_difference, matches = results

        QMessageBox.information(self, "Song Name", f"The song is {song_name}")

        print(f"{song_id}, {song_name}, {offset_difference}, {matches}")


    def match_fingerprints(self, fingerprints):
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute(
            """
            CREATE TEMP TABLE external_fingerprints (
                hash BLOB NOT NULL,
                offset INTEGER NOT NULL,
                PRIMARY KEY (hash, offset)
            )
            """
        )

        cursor.executemany(
            """
            INSERT OR IGNORE INTO external_fingerprints (hash, offset)
            VALUES(?, ?)
            """,
            fingerprints
        )


        cursor.execute(
            """
            SELECT
                songs.song_id,
                songs.song_name,
                fingerprints.offset - external_fingerprints.offset as time_diff,
                COUNT(*) as matches
            FROM external_fingerprints
            JOIN fingerprints 
                on fingerprints.hash = external_fingerprints.hash
            JOIN songs
                on songs.song_id = fingerprints.song_id
            GROUP BY
                songs.song_id,
                songs.song_name,
                fingerprints.offset - external_fingerprints.offset
            ORDER BY matches DESC
            LIMIT 1
            """
        )

        result = cursor.fetchone()

        connection.commit()
        connection.close()

        if result is None:
            return None

        return result

    def create_spectro(self, audio): 
        audio_paths = audio
        for audio_path in audio_paths:

            #Creating spectrogram
            y, sr = librosa.load(audio_path, sr=48000)
            spectro = librosa.feature.melspectrogram(y=y, sr=sr)
            spectro_db = librosa.power_to_db(spectro, ref=np.max)
            print(np.shape(spectro_db))

            #Creating peaks of spectrogram
            peaks = sp.maximum_filter(spectro_db, size=(10, 10)) == spectro_db
            threshold = spectro_db > -40
            peak_indexes = np.argwhere(peaks & threshold)
            print(np.shape(peak_indexes))

            #Creates entry into song table
            song_id = self.save_song_to_database(Path(audio_path).stem)

            #Hash
            fingerprints = self.fingerprint_creation(peak_indexes[:, [1,0]])

            #Saves to database of a known song
            rows = {(hash_value, song_id, offset)
                    for hash_value, offset in fingerprints}
            self.save_fingerprint_to_database(rows)


            #Plotting spectrogram
            # plt.figure(figsize=(10,4))
            # librosa.display.specshow(spectro_db, x_axis="time", y_axis="mel", sr=sr)
            # plt.colorbar(format="%+2.0f dB")
            # plt.title("Mel Spectro")

            # #Plotting peaks
            # x_axis_time = peak_indexes[:, 1]
            # y_axis_freq = peak_indexes[:, 0]

            # true_x_time = librosa.frames_to_time(x_axis_time, sr=sr)
            # true_y_freq = librosa.mel_frequencies(n_mels=spectro_db.shape[0])[y_axis_freq]

            # plt.scatter(true_x_time, true_y_freq, color='yellow', s=10)

            # plt.show()

    def fingerprint_creation(self, peaks):
        #Number of other points that will be hashed to the original point
        connections = 5
        sorted_peaks = peaks[np.argsort(peaks[:, 0])]
        fingerprints = set()

        for i in range(len(sorted_peaks)):
            anchor_time, anchor_freq = sorted_peaks[i]
            for j in range(1, connections+1): 
                if i + j >= len(sorted_peaks): 
                    break

                surrounding_time, surrounding_freq = sorted_peaks[i+j]

                time_diff = surrounding_time - anchor_time

                raw_hash_value = f"{anchor_freq},{surrounding_freq},{time_diff}"

                hash_value = hashlib.sha1(raw_hash_value.encode("utf-8")).digest()[:10]

                fingerprints.add((hash_value, int(anchor_time)))

        return fingerprints


    def save_fingerprint_to_database(self, fingerprints):
        if not fingerprints:
            return

        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.executemany(
            """
            INSERT OR IGNORE into fingerprints (hash, song_id, offset)
            VALUES(?, ?, ?)
            """,
            fingerprints
        )

        connection.commit()
        connection.close()

    def save_song_to_database(self, song_name):
        connection = sqlite3.connect(DB_PATH)
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE into songs (song_name)
            VALUES (?)
            """,
            (song_name,)
        )

        cursor.execute(
            """
            SELECT song_id
            FROM songs
            WHERE song_name = ?
            """,
            (song_name,)
        )

        song_id = cursor.fetchone()


        connection.commit()
        connection.close()

        return song_id[0]


    def on_click_file(self):
        audio_paths = self.open_file()
        self.create_spectro(audio_paths)



    def open_file(self):
        audio_path, _ = QFileDialog.getOpenFileNames(self, "Select Audio File", r"C:\Users\andyl\VSCode Music Project\assets", "Audio Files (*.mp3)")
        return audio_path
    
        
    def cleanup(self):
        if self.stream is not None:
            if self.stream.is_active():
                self.stream.stop_stream
            self.stream.close()

        if self.p is not None:
            self.p.terminate()
