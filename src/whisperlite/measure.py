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
    """Memory of one process; on Linux PSS, which splits shared libraries
    between the processes that map them."""
    if sys.platform.startswith("linux"):
        return p.memory_full_info().pss
    return p.memory_info().rss


class PeakMemory:
    """Polls the memory of a process and its children (whisper-cli runs as a child).

    openai/whisper forks ffmpeg for every file. Between fork and exec the child
    is a copy of the worker sharing all its pages, and because parent and child
    are read one after the other, a fork in between makes the parent count in
    full while the child counts half its pages (pilot: 7.7GB reported, 5.1GB
    real). Children whose command line is still the parent's are therefore
    skipped; once they exec (ffmpeg, whisper-cli) they are counted.
    """

    def __init__(self, pid: int, interval: float = 0.05):
        self.proc = psutil.Process(pid)
        self.interval = interval
        self.peak = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._poll, daemon=True)

    def _poll(self):
        try:
            own_cmdline = self.proc.cmdline()
        except psutil.Error:
            return
        while not self._stop.is_set():
            try:
                total = process_memory(self.proc)
                for p in self.proc.children(recursive=True):
                    try:
                        if p.cmdline() == own_cmdline:
                            continue  # forked copy that has not exec'd yet
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


def hyps_dir(out_csv) -> Path:
    """Where bench keeps transcripts next to its CSV: results/x.csv → results/x_hyps/."""
    out_csv = Path(out_csv)
    return out_csv.with_name(out_csv.stem + "_hyps")


def hyps_path(out_csv, config) -> Path:
    return hyps_dir(out_csv) / (config.key.replace("/", "_") + ".jsonl")


def write_hyps(path, items, hyps) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for item, hyp in zip(items, hyps):
            f.write(json.dumps({"id": item["id"], "ref": item["text"], "hyp": hyp}, ensure_ascii=False) + "\n")


def read_hyps(path) -> list:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def measure(config, manifest, threads, timeout=None, save_hyps=None) -> dict:
    """Run one configuration. save_hyps: optional .jsonl path for the transcripts."""
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
    if save_hyps:
        write_hyps(save_hyps, items, hyps)
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
