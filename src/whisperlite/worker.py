"""Runs one configuration in its own process so its peak memory is isolated.

Usage (called by measure.py): python -m whisperlite.worker job.json result.json
"""

import json
import sys
import time

from .configs import DECODING
from .data import load_manifest
from .runners import get_runner


def run(job: dict) -> dict:
    items = load_manifest(job["manifest"])
    runner = get_runner(job["runner"])

    start = time.perf_counter()
    runner.load(job["model"], job["precision"], job["threads"], DECODING)
    load_seconds = time.perf_counter() - start

    results = []
    for item in items:
        start = time.perf_counter()
        hyp = runner.transcribe(item["wav"])
        seconds = runner.last_transcribe_seconds()
        if seconds is None:
            seconds = time.perf_counter() - start
        results.append({"id": item["id"], "seconds": seconds, "hyp": hyp})
    return {"load_seconds": load_seconds, "items": results}


def main(argv=None):
    job_path, out_path = (argv or sys.argv[1:])[:2]
    with open(job_path, encoding="utf-8") as f:
        job = json.load(f)
    result = run(job)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
