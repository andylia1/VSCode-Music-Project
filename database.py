import os
import sqlite3
from pathlib import Path

APP_PATH = Path(os.environ["LocalAppData"])/ "SongRecognizer"
DB_PATH = APP_PATH / "fingerprints.db"




def create_database():
    #Creates a folder in  project directory for a sql db file
    APP_PATH.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS songs (
                song_id INTEGER PRIMARY KEY AUTOINCREMENT,
                song_name TEXT NOT NULL UNIQUE
            )
        """)

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fingerprints (
            hash BLOB NOT NULL,
            song_id INTEGER NOT NULL,
            offset INTEGER NOT NULL,
            PRIMARY KEY (hash, song_id, offset),
            FOREIGN KEY (song_id) REFERENCES songs(song_id)
        )
    """)

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS index_hash_fingerprint ON fingerprints(hash)
        """)

    connection.commit()
    connection.close()
