"""Measure one configuration: RTF, CER and peak memory, as one CSV row."""

import csv
import json
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

import psutil

from . import sysinfo
from .data import load_manifest
from .metrics import cer, rtf
from .textnorm import has_digits

FIELDS = [
    "runner", "model", "precision", "threads", "n_files", "audio_seconds",
    "load_seconds", "transcribe_seconds", "rtf", "cer", "peak_ram_mb",
    "hyps_with_digits", "docker", "hostname", "error",
]


def process_memory(p) -> int:
    """Memory of one process without double counting shared pages.

    A child that has just been forked (openai/whisper starts ffmpeg for every
    file) shares all of its parent's pages until exec, so summing RSS over the
    tree can report up to twice the real usage. PSS splits shared pages
    between the processes that map them; it is available on Linux (Docker).
    """
    if sys.platform.startswith("linux"):
        return p.memory_full_info().pss
    return p.memory_info().rss


class PeakMemory:
    """Polls the memory of a process and its children (whisper-cli runs as a child)."""

    def __init__(self, pid: int, interval: float = 0.05):
        self.proc = psutil.Process(pid)
        self.interval = interval
        self.peak = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._poll, daemon=True)

    def _poll(self):
        while not self._stop.is_set():
            try:
                procs = [self.proc] + self.proc.children(recursive=True)
                total = 0
                for p in procs:
                    try:
                        total += process_memory(p)
                    except psutil.Error:
                        pass
                self.peak = max(self.peak, total)
            except psutil.Error:
                break
            self._stop.wait(self.interval)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join()


def measure(config, manifest, threads, timeout=None) -> dict:
    items = load_manifest(manifest)
    audio_seconds = sum(i["duration"] for i in items)
    row = {
        "runner": config.runner, "model": config.model, "precision": config.precision,
        "threads": threads, "n_files": len(items), "audio_seconds": round(audio_seconds, 2),
        "docker": sysinfo.in_docker(), "hostname": sysinfo.hostname(), "error": "",
    }
    with tempfile.TemporaryDirectory() as tmp:
        job_path, out_path = Path(tmp) / "job.json", Path(tmp) / "result.json"
        job_path.write_text(json.dumps({
            "runner": config.runner, "model": config.model, "precision": config.precision,
            "threads": threads, "manifest": str(Path(manifest).resolve()),
        }))
        proc = subprocess.Popen(
            [sys.executable, "-m", "whisperlite.worker", str(job_path), str(out_path)],
            stderr=subprocess.PIPE, text=True,
        )
        with PeakMemory(proc.pid) as mem:
            try:
                _, stderr = proc.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                proc.kill()
                _, stderr = proc.communicate()
                stderr = f"timeout after {timeout}s"
        row["peak_ram_mb"] = round(mem.peak / 2**20, 1)
        if proc.returncode != 0 or not out_path.exists():
            # last line is usually the exception (e.g. MemoryError, missing library)
            lines = [line for line in (stderr or "").strip().splitlines() if line.strip()]
            row["error"] = lines[-1] if lines else f"exit code {proc.returncode}"
            return row
        result = json.loads(out_path.read_text(encoding="utf-8"))

    by_id = {r["id"]: r for r in result["items"]}
    hyps = [by_id[i["id"]]["hyp"] for i in items]
    transcribe_seconds = sum(r["seconds"] for r in result["items"])
    row.update({
        "load_seconds": round(result["load_seconds"], 3),
        "transcribe_seconds": round(transcribe_seconds, 3),
        "rtf": round(rtf(transcribe_seconds, audio_seconds), 4),
        "cer": round(cer([i["text"] for i in items], hyps), 4),
        "hyps_with_digits": sum(has_digits(h) for h in hyps),
    })
    return row


def read_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def append_row(path, row) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in FIELDS})
