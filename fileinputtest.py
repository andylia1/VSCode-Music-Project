import sounddevice as sd
import librosa
import matplotlib.pyplot as plt
import numpy as np

def record():
    fs = 44100
    length = 30
    recording = sd.rec(frames=fs*length, samplerate=fs, blocking=True, channels=1)
    recording = recording.squeeze()          # (1323000, 1) → (1323000,)
    recording = recording.astype(np.float32) # librosa prefers float32
    create_spectro(recording, fs)



def create_spectro(recording, fs):
    spectro = librosa.feature.melspectrogram(y=recording, sr=fs)
    spectro_db = librosa.power_to_db(spectro, ref=np.max)
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(spectro_db, sr=fs, x_axis="time", y_axis="mel")
    plt.colorbar(format="%+2.0f dB")
    plt.title("Mel Spectro")
    plt.show()



record()