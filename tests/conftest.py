import struct
import wave

import pytest

from whisperlite.data import write_manifest


def write_silence(path, seconds=1.0, rate=16000):
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(rate)
        w.writeframes(struct.pack("<h", 0) * int(seconds * rate))


@pytest.fixture
def manifest(tmp_path):
    (tmp_path / "wav").mkdir()
    rows = []
    for i, text in enumerate(["안녕하세요", "안녕하세요."]):
        write_silence(tmp_path / "wav" / f"{i}.wav", seconds=2.0)
        rows.append({"id": str(i), "wav": f"wav/{i}.wav", "duration": 2.0, "text": text})
    path = tmp_path / "manifest.csv"
    write_manifest(path, rows)
    return path
