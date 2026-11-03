"""Zeroth-Korean test split -> 16 kHz mono 16-bit WAV files + manifest.csv.

The manifest is the single input every runner reads, so all runners see
exactly the same audio (whisper.cpp needs 16-bit WAV anyway).
"""

import csv
import shutil
import subprocess
import tempfile
import wave
from pathlib import Path

DATASET = "kresnik/zeroth_korean"
FIELDS = ["id", "wav", "duration", "text"]


def wav_duration(path) -> float:
    with wave.open(str(path), "rb") as w:
        return w.getnframes() / w.getframerate()


def to_wav(src, dst) -> None:
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg가 필요합니다 (README의 설치 방법 참고)")
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
         "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", str(dst)],
        check=True,
    )


def prepare(out_dir, limit=None) -> Path:
    """Stream the test split (no full-dataset download) and write WAVs + manifest."""
    from datasets import Audio, load_dataset

    out = Path(out_dir)
    (out / "wav").mkdir(parents=True, exist_ok=True)
    ds = load_dataset(DATASET, split="test", streaming=True)
    ds = ds.cast_column("audio", Audio(decode=False))

    rows = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, ex in enumerate(ds):
            if limit is not None and i >= limit:
                break
            uid = str(ex.get("id") or f"{i:05d}")
            src = Path(tmp) / f"{uid}.flac"
            src.write_bytes(ex["audio"]["bytes"])
            wav = out / "wav" / f"{uid}.wav"
            to_wav(src, wav)
            rows.append({"id": uid, "wav": f"wav/{uid}.wav",
                         "duration": round(wav_duration(wav), 3), "text": ex["text"]})

    manifest = out / "manifest.csv"
    write_manifest(manifest, rows)
    return manifest


def write_manifest(path, rows) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)


def load_manifest(path):
    """Rows with absolute wav paths and float durations."""
    base = Path(path).resolve().parent
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        r["wav"] = str(base / r["wav"])
        r["duration"] = float(r["duration"])
    return rows
