# W.I.P


# Intro
This is a song recognition app that is inspired by the methodology described in this article [https://willdrevo.com/fingerprinting-and-audio-recognition-with-python/](url) by Will Drevo built for Windows Wasapi devices

# Usage Guidelines
To use this program, go to the releases tab and download the latest release. You will be shown three selections: "Select a File", "Match Song", and "Stop Matching".

# "Select a File"
This button will allows an user to add mp3 files to a local database stored on their device. You are able to select files in batches.

# "Match Song" and "Stop Matching"
When you are playing a song and want to know the name of the song, press "Match Song". Give the software 4-5 seconds to properly assess what song it is. Afterwards, press "Stop Matching" to get returned the song name, which is the name of the audio file that you inputted into the database.

# Modifications
If you want to use this for audio analysis tools, you can uncomment the code that plots mel spectrograms with their local peaks.
