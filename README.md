# Whisper-Diarization-Pipeline für Experteninterviews (Ausgabe für MAXQDA)

Lokale Pipeline, die Interviewaufnahmen in ein Transkript mit Sprecherlabels und Zeitstempeln umwandelt, das sich direkt in MAXQDA importieren lässt. Sie entstand für die Transkription der Experteninterviews einer Masterarbeit (TU Braunschweig, 2026) und ist ein Fork von [MahmoudAshraf97/whisper-diarization](https://github.com/MahmoudAshraf97/whisper-diarization) (Ashraf 2024), das seinerseits auf [OpenAI Whisper](https://github.com/openai/whisper) aufbaut.

Alles läuft lokal. Es werden weder Audiodateien noch Transkripte an externe Dienste gesendet.

## Was dieses Repository ergänzt

Der Kern (Sprachmodell, Forced Alignment, Diarisierung) stammt unverändert aus dem Original. Ergänzt wurde:

| Datei | Zweck |
|---|---|
| `diarize.py` (angepasst) | neue Optionen `--num-speakers` (feste Sprecherzahl, nur MSDD), `--hotwords` und `--prompt-file` (Kontextbegriffe, die Whisper beim Transkribieren bevorzugt) |
| `diarization/msdd/msdd.py` (angepasst) | gibt die feste Sprecherzahl an das MSDD-Modell weiter |
| `marketing_terms.txt` | rund 140 englische Fachbegriffe aus MarTech und AdTech (z. B. Walled Garden, Contextual Targeting, Third-Party Cookies), damit sie im deutschen Redefluss richtig geschrieben werden |
| `convert2maxqda.py` | wandelt die `.srt`-Ausgabe in das MAXQDA-Format `#HH:MM:SS# Sprecher: Text` um und korrigiert typische Verhörer (z. B. „JGPT“ → „ChatGPT“) |
| `m4a2maxqda.py`, `audio2maxqda.py` | führen beide Schritte in einem Aufruf aus (`audio2maxqda.py` ist nur ein anders benannter Einstieg) |
| `mp42mp3.py` | optionale Umwandlung von mp4/anderen Formaten in mp3 ohne System-ffmpeg |

Die Dokumentation des Originals steht unverändert in [`README_UPSTREAM.md`](README_UPSTREAM.md).

## Ablauf

1. optional Stimmtrennung (Demucs), damit die Sprecher besser unterschieden werden
2. Transkription mit Whisper (faster-whisper, Standard `large-v3`, Sprache Deutsch) mit Kontextbegriffen aus `marketing_terms.txt`
3. zeitliches Ausrichten der Wörter (`ctc-forced-aligner`)
4. Sprecher-Diarisierung (NVIDIA NeMo, MSDD oder Sortformer) und Zuordnung der Sprecher zu den Wörtern
5. Ausgabe als `.srt` und `.txt`, danach Umwandlung in `<name>_maxqda.txt`

## Installation

Voraussetzungen und Installation wie im Original (Python 3.10 oder neuer, FFmpeg, Cython), siehe [`README_UPSTREAM.md`](README_UPSTREAM.md):

```
pip install cython
pip install -c constraints.txt -r requirements.txt
```

## Benutzung

Aufnahme in MAXQDA-Format (Standard: Deutsch, `large-v3`, zwei Sprecher, `marketing_terms.txt` wird automatisch verwendet):

```
python m4a2maxqda.py interview.m4a
```

Weitere Optionen:

```
python m4a2maxqda.py interview.m4a --whisper-model large-v3-turbo --device cpu
python m4a2maxqda.py interview.m4a --language en
python m4a2maxqda.py interview.m4a --num-speakers 0        # Sprecherzahl automatisch schätzen
python m4a2maxqda.py interview.m4a --prompt-file eigene_begriffe.txt
```

Nicht aufgeführte Optionen (z. B. `--no-stem`, `--batch-size`, `--diarizer msdd|sortformer`) werden an `diarize.py` weitergereicht. Die Schritte lassen sich auch einzeln ausführen:

```
python diarize.py -a interview.m4a --language de --num-speakers 2 --prompt-file marketing_terms.txt
python convert2maxqda.py interview.srt
```

Ausgabe: `interview.srt`, `interview.txt` und `interview_maxqda.txt`. Die letzte Datei lässt sich in MAXQDA als Transkript importieren (Zeitstempel im Format `#HH:MM:SS#`).

## Grenzen und Hinweise

- Automatische Transkripte müssen mit der Tonspur gegengelesen werden. In den Interviews der Masterarbeit fehlten pro Gespräch einzelne kurze Passagen, die zu Wiederholungen wie „Google, Google, Google“ transkribiert wurden. Alle Transkripte sollten deshalb vollständig geprüft und korrigiert werden.
- Die Sprecherzahl `--num-speakers` wirkt nur beim MSDD-Diarizer, nicht bei Sortformer. Gleichzeitiges Sprechen wird nicht gelöst (siehe Original).
- Die Verhörer-Liste in `convert2maxqda.py` (`CORRECTIONS`) und die Begriffsliste `marketing_terms.txt` sind auf die Interviews dieser Arbeit zugeschnitten und sollten für andere Themen angepasst werden. Whisper nutzt von der Begriffsliste nur etwa die ersten 200 Tokens, das Wichtigste gehört deshalb nach oben.

## Datenschutz

Aufnahmen und Transkripte gehören nicht in dieses Repository. `.gitignore` schließt Audio- und Videodateien sowie `.srt`/`.txt`-Ausgaben aus (die Begriffsliste `marketing_terms.txt` ist davon ausgenommen).

## Lizenz und Quellen

BSD 2-Clause, siehe [`LICENSE`](LICENSE) (Copyright des Originalautors Mahmoud Ashraf; Ergänzungen unter derselben Lizenz).

- Ashraf, Mahmoud (2024): Whisper Diarization: Speaker Diarization Using OpenAI Whisper. https://github.com/MahmoudAshraf97/whisper-diarization
- OpenAI Whisper: https://github.com/openai/whisper
- Faster Whisper, NVIDIA NeMo, Demucs, `ctc-forced-aligner` (siehe `requirements.txt` und `README_UPSTREAM.md`)
