"""
Pipeline: Audio (z.B. .m4a) -> Diarisierung + Transkription -> MAXQDA/f4-Format
==============================================================================

Verkettet die beiden Schritte:
  1. diarize.py        (Whisper + Sprecher-Diarisierung -> .srt / .txt)
  2. convert2maxqda.py (.srt -> #HH:MM:SS# Sprecher: Text -> _maxqda.txt)

Nutzung (Standard: deutsch, large-v3):
    python m4a2maxqda.py ex02.m4a

Mit anderen Optionen:
    python m4a2maxqda.py interview.m4a --whisper-model large-v3-turbo --device cpu
    python m4a2maxqda.py interview.m4a --language en

Alle nicht aufgeführten Argumente werden unveraendert an diarize.py durchgereicht.
"""

import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    parser = argparse.ArgumentParser(
        description="Audio -> Diarisierung -> MAXQDA-Format in einem Schritt",
    )
    parser.add_argument("audio", help="Pfad zur Audiodatei (.m4a, .wav, .mp3, ...)")
    parser.add_argument(
        "--whisper-model",
        default="large-v3",
        help="Whisper-Modell (Standard: large-v3, mehrsprachig)",
    )
    parser.add_argument(
        "--language",
        default="de",
        help="Sprache des Audios (Standard: de). 'None' fuer Auto-Erkennung.",
    )
    parser.add_argument(
        "--num-speakers",
        type=int,
        default=2,
        help="Feste Sprecherzahl (Standard: 2). 0 = automatisch schaetzen.",
    )
    parser.add_argument(
        "--prompt-file",
        default=None,
        help="Kontextdatei mit Begriffen (z.B. engl. Marketingbegriffe). "
        "Standard: marketing_terms.txt, falls vorhanden.",
    )
    # Restliche Argumente (z.B. --device, --batch-size, --no-stem, --diarizer)
    # werden unveraendert an diarize.py weitergereicht.
    args, passthrough = parser.parse_known_args()

    if not os.path.exists(args.audio):
        print(f"Datei nicht gefunden: {args.audio}")
        sys.exit(1)

    diarize_cmd = [
        sys.executable,
        os.path.join(HERE, "diarize.py"),
        "-a", args.audio,
        "--whisper-model", args.whisper_model,
    ]
    # 'None' bedeutet: kein --language -> diarize.py macht Auto-Erkennung
    if args.language and args.language.lower() != "none":
        diarize_cmd += ["--language", args.language]

    # Feste Sprecherzahl erzwingen (0 = automatisch)
    if args.num_speakers and args.num_speakers > 0:
        diarize_cmd += ["--num-speakers", str(args.num_speakers)]

    # Kontextdatei: explizit angegeben oder Standard marketing_terms.txt
    prompt_file = args.prompt_file
    if prompt_file is None:
        default_prompt = os.path.join(HERE, "marketing_terms.txt")
        if os.path.exists(default_prompt):
            prompt_file = default_prompt
            print(f"   (nutze Kontextdatei: {default_prompt})")
    if prompt_file:
        diarize_cmd += ["--prompt-file", prompt_file]

    diarize_cmd += passthrough

    print(">> Schritt 1/2: Diarisierung + Transkription")
    print("   " + " ".join(diarize_cmd))
    result = subprocess.run(diarize_cmd)
    if result.returncode != 0:
        print("diarize.py ist fehlgeschlagen, Abbruch.")
        sys.exit(result.returncode)

    srt_path = f"{os.path.splitext(args.audio)[0]}.srt"
    if not os.path.exists(srt_path):
        print(f"Erwartetes SRT nicht gefunden: {srt_path}")
        sys.exit(1)

    print(f"\n>> Schritt 2/2: Konvertierung -> MAXQDA-Format ({srt_path})")
    convert_cmd = [sys.executable, os.path.join(HERE, "convert2maxqda.py"), srt_path]
    result = subprocess.run(convert_cmd)
    if result.returncode != 0:
        print("convert2maxqda.py ist fehlgeschlagen.")
        sys.exit(result.returncode)

    out_path = f"{os.path.splitext(args.audio)[0]}_maxqda.txt"
    print(f"\nFertig. In MAXQDA importierbar: {out_path}")


if __name__ == "__main__":
    main()
