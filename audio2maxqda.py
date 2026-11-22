"""
Alias fuer m4a2maxqda.py mit generischem Namen.
==============================================

Identische Funktion, nur klarer benannt: die Pipeline akzeptiert jedes gaengige
Audio-/Videoformat (mp3, m4a, wav, mp4, flac, ogg, ...), weil faster-whisper die
Datei ueber PyAV dekodiert.

    python audio2maxqda.py interview.mp3
    python audio2maxqda.py interview.mp4 --no-stem

Alle Optionen sind dieselben wie bei m4a2maxqda.py.
"""

from m4a2maxqda import main

if __name__ == "__main__":
    main()
