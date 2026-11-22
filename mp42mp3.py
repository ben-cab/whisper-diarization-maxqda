"""
Konverter: mp4 (oder jedes andere A/V-Format) -> mp3
====================================================

Nutzt das bereits installierte PyAV (mit gebundeltem ffmpeg/libmp3lame), damit
KEIN System-ffmpeg im PATH noetig ist. Sample-Rate und Kanaele (mono/stereo)
werden beibehalten.

Nutzung:
    python mp42mp3.py aufnahme.mp4
    python mp42mp3.py aufnahme.mp4 --output ton.mp3
    python mp42mp3.py aufnahme.mp4 --bitrate 320k

Hinweis: Fuer die Transkription ist eine Konvertierung meist gar nicht noetig -
m4a2maxqda.py / audio2maxqda.py koennen die mp4 auch direkt verarbeiten.
"""

import argparse
import os
import sys

import av


def parse_bitrate(value: str) -> int:
    """'192k' / '192000' / '320k' -> int (bit/s)."""
    v = value.strip().lower()
    if v.endswith("k"):
        return int(float(v[:-1]) * 1000)
    return int(v)


def convert(in_path: str, out_path: str, bitrate: int = 192000):
    with av.open(in_path) as inp:
        if not inp.streams.audio:
            print(f"Keine Audiospur gefunden in: {in_path}")
            sys.exit(1)
        in_stream = inp.streams.audio[0]

        with av.open(out_path, "w") as out:
            # mp3 unterstuetzt nur mono/stereo -> bei mehr Kanaelen auf stereo mischen
            layout = "mono" if in_stream.layout.name == "mono" else "stereo"
            out_stream = out.add_stream("libmp3lame", rate=in_stream.rate)
            out_stream.bit_rate = bitrate

            # Frames ins vom Encoder erwartete Format bringen (Sample-Format/Layout/Rate)
            resampler = av.AudioResampler(
                format=out_stream.format,
                layout=layout,
                rate=in_stream.rate,
            )

            def mux(frames):
                for frame in frames:
                    for packet in out_stream.encode(frame):
                        out.mux(packet)

            for frame in inp.decode(in_stream):
                frame.pts = None
                mux(resampler.resample(frame))

            # Resampler und Encoder leeren (flush)
            mux(resampler.resample(None))
            for packet in out_stream.encode(None):
                out.mux(packet)


def main():
    parser = argparse.ArgumentParser(description="Konvertiert mp4 (o. a.) nach mp3 via PyAV")
    parser.add_argument("input", help="Eingabedatei (z.B. .mp4)")
    parser.add_argument("--output", default=None, help="Ausgabe-mp3 (Standard: <input>.mp3)")
    parser.add_argument("--bitrate", default="192k", help="mp3-Bitrate, z.B. 192k oder 320k")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Datei nicht gefunden: {args.input}")
        sys.exit(1)

    out_path = args.output or f"{os.path.splitext(args.input)[0]}.mp3"
    print(f">> Konvertiere: {args.input} -> {out_path}  ({args.bitrate})")
    convert(args.input, out_path, parse_bitrate(args.bitrate))
    print("Fertig.")


if __name__ == "__main__":
    main()
