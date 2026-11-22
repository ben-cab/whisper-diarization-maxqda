"""
Konverter: WhisperX-JSON oder SRT (mit Sprecherlabels) -> MAXQDA/f4analyse-Format
===================================================================================

Wandelt die Ausgabe von WhisperX (--output_format json) oder whisper-diarization
(erzeugt .srt mit "Sprecher: Text") in ein Zeitstempel-Format um, das MAXQDA und
f4analyse importieren können: #HH:MM:SS# Sprecher: Text

Nutzung:
    python convert2maxqda.py transkript.json
    python convert2maxqda.py transkript.srt
    python convert2maxqda.py transkript.json --output ergebnis.txt
"""

import argparse
import json
import os
import re
import sys


# Haeufige Fehlerkennungen von Whisper -> Korrektur.
# Schluessel = Regex (Wortgrenzen, wird case-insensitive gesucht), Wert = korrekte Schreibweise.
# Hier bei Bedarf weitere haeufige Verhoerer ergaenzen.
CORRECTIONS = {
    r"\bJCPT\b": "ChatGPT",
    r"\bJGPT\b": "ChatGPT",
    r"\bChat\s?GPT\b": "ChatGPT",
    r"\bTschantt?\s?GPT\b": "ChatGPT",
}


def apply_corrections(text: str) -> str:
    """Wendet die CORRECTIONS-Ersetzungen auf einen Textabschnitt an."""
    for pattern, replacement in CORRECTIONS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


def format_timestamp(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def srt_timestamp_to_seconds(ts: str) -> float:
    # Format: 00:01:23,456
    ts = ts.replace(",", ".")
    h, m, s = ts.split(":")
    return int(h) * 3600 + int(m) * 60 + float(s)


def convert_whisperx_json(path: str) -> list[tuple[float, str, str]]:
    """Erwartet WhisperX --output_format json mit 'segments' (jeweils speaker, start, text)."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    segments = data.get("segments", data if isinstance(data, list) else [])
    result = []
    for seg in segments:
        start = seg.get("start", 0.0)
        speaker = seg.get("speaker", "Unbekannt")
        text = seg.get("text", "").strip()
        if text:
            result.append((start, speaker, text))
    return result


def convert_srt(path: str) -> list[tuple[float, str, str]]:
    """
    Erwartet ein SRT mit Blöcken wie:
        1
        00:00:01,000 --> 00:00:04,000
        SPEAKER_00: Hallo und herzlich willkommen.

    Fällt auf 'Unbekannt' zurück, falls kein 'Sprecher:' Präfix erkannt wird.
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    blocks = re.split(r"\n\s*\n", content.strip())
    result = []
    time_pattern = re.compile(r"(\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[,.]\d{3})")

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) < 2:
            continue

        time_line = next((l for l in lines if time_pattern.search(l)), None)
        if not time_line:
            continue

        match = time_pattern.search(time_line)
        start_seconds = srt_timestamp_to_seconds(match.group(1))

        text_lines = lines[lines.index(time_line) + 1:]
        full_text = " ".join(text_lines).strip()

        speaker_match = re.match(r"^([\w\s]+?):\s*(.*)$", full_text)
        if speaker_match:
            speaker, text = speaker_match.group(1).strip(), speaker_match.group(2).strip()
        else:
            speaker, text = "Unbekannt", full_text

        if text:
            result.append((start_seconds, speaker, text))

    return result


def merge_consecutive(segments: list[tuple[float, str, str]]) -> list[tuple[float, str, str]]:
    """Fasst aufeinanderfolgende Segmente desselben Sprechers zusammen."""
    if not segments:
        return []

    merged = [list(segments[0])]
    for start, speaker, text in segments[1:]:
        if speaker == merged[-1][1]:
            merged[-1][2] = f"{merged[-1][2]} {text}"
        else:
            merged.append([start, speaker, text])
    return [tuple(m) for m in merged]


def write_maxqda_format(segments: list[tuple[float, str, str]], out_path: str):
    with open(out_path, "w", encoding="utf-8") as f:
        for start, speaker, text in segments:
            ts = format_timestamp(start)
            f.write(f"#{ts}# {speaker}: {text}\n\n")
    print(f"-> Gespeichert: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Konvertiert WhisperX-JSON oder SRT ins MAXQDA/f4analyse-Format")
    parser.add_argument("input", help="Pfad zur .json (WhisperX) oder .srt Datei")
    parser.add_argument("--output", default=None, help="Ausgabedatei (Standard: <input>_maxqda.txt)")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Datei nicht gefunden: {args.input}")
        sys.exit(1)

    ext = os.path.splitext(args.input)[1].lower()
    if ext == ".json":
        segments = convert_whisperx_json(args.input)
    elif ext == ".srt":
        segments = convert_srt(args.input)
    else:
        print("Nicht unterstütztes Format. Bitte .json (WhisperX) oder .srt verwenden.")
        sys.exit(1)

    segments = merge_consecutive(segments)
    segments = [(start, speaker, apply_corrections(text)) for start, speaker, text in segments]

    out_path = args.output or f"{os.path.splitext(args.input)[0]}_maxqda.txt"
    write_maxqda_format(segments, out_path)


if __name__ == "__main__":
    main()