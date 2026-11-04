"""Lightweight ②: whisper.cpp through its whisper-cli binary, CPU only (-ng).

Each file runs in its own whisper-cli process, so the model is loaded every
time. The load time whisper-cli prints is subtracted to get transcription time.

Environment:
  WHISPER_CPP_BIN     path to whisper-cli (default: whisper-cli on PATH)
  WHISPER_CPP_MODELS  directory for ggml model files
"""

import os
import re
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path

from .base import Runner

MODEL_URL = "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/{name}"
_LOAD = re.compile(r"load time\s*=\s*([\d.]+)\s*ms")


def model_filename(model: str, precision: str) -> str:
    return f"ggml-{model}.bin" if precision == "f16" else f"ggml-{model}-{precision}.bin"


def models_dir() -> Path:
    default = Path.home() / ".cache" / "whisperlite" / "ggml"
    return Path(os.environ.get("WHISPER_CPP_MODELS", default))


def ensure_model(model: str, precision: str) -> Path:
    path = models_dir() / model_filename(model, precision)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".part")
        urllib.request.urlretrieve(MODEL_URL.format(name=path.name), tmp)
        tmp.rename(path)
    return path


def parse_stdout(data: bytes) -> str:
    """Join whisper-cli's segment lines into one string.

    whisper.cpp splits segments on token boundaries, and a token can end in the
    middle of a multibyte character (common for Korean). The rest of that
    character then starts the next line. Such lines are glued back without a
    space; any bytes that are still invalid become U+FFFD.
    """
    out = b""
    for line in data.splitlines():
        line = line.strip()
        if not line:
            continue
        if out and 0x80 <= line[0] <= 0xBF:  # UTF-8 continuation byte
            out += line
        else:
            out += (b" " if out else b"") + line
    return out.decode("utf-8", errors="replace")


def parse_load_ms(stderr: str):
    m = _LOAD.search(stderr)
    return float(m.group(1)) if m else None


class WhisperCppRunner(Runner):
    def load(self, model, precision, threads, decoding):
        binary = os.environ.get("WHISPER_CPP_BIN", "whisper-cli")
        self.binary = shutil.which(binary) or binary
        self.model_path = ensure_model(model, precision)
        self.threads = threads
        self.decoding = decoding
        self._seconds = None

    def command(self, wav_path):
        d = self.decoding
        return [
            self.binary,
            "-m", str(self.model_path),
            "-f", wav_path,
            "-l", d["language"],
            "-bs", str(d["beam_size"]),
            "-t", str(self.threads),
            "-ng",  # no GPU: keeps Apple Silicon (Metal) runs CPU-only
            "-nt",  # no timestamps: stdout is plain text
        ]

    def transcribe(self, wav_path):
        start = time.perf_counter()
        proc = subprocess.run(self.command(wav_path), capture_output=True, check=True)
        wall = time.perf_counter() - start
        load_ms = parse_load_ms(proc.stderr.decode("utf-8", errors="replace"))
        self._seconds = wall - load_ms / 1000 if load_ms is not None else wall
        return parse_stdout(proc.stdout)

    def last_transcribe_seconds(self):
        return self._seconds
