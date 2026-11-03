"""Hardware and environment facts recorded with every measurement."""

import os
import platform
from pathlib import Path

import psutil

_CGROUP_FILES = [
    Path("/sys/fs/cgroup/memory.max"),  # cgroup v2
    Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"),  # cgroup v1
]


def cgroup_memory_limit(files=_CGROUP_FILES):
    """Container memory limit in bytes, or None when unlimited / not in a cgroup."""
    for f in files:
        try:
            raw = Path(f).read_text().strip()
        except OSError:
            continue
        if raw == "max":
            return None
        value = int(raw)
        # cgroup v1 reports a huge number when unlimited
        return value if value < 1 << 60 else None
    return None


def in_docker() -> bool:
    return Path("/.dockerenv").exists()


def available_memory() -> int:
    """Memory a new process can use: the smaller of free RAM and the container limit."""
    avail = psutil.virtual_memory().available
    limit = cgroup_memory_limit()
    if limit is not None:
        used = psutil.Process().memory_info().rss
        avail = min(avail, max(limit - used, 0))
    return avail


def hostname() -> str:
    """Name of the physical PC. Inside Docker the hostname is a random
    container id, so the host passes its own name in WHISPERLITE_HOST."""
    return os.environ.get("WHISPERLITE_HOST") or platform.node()


def default_threads() -> int:
    return psutil.cpu_count(logical=False) or os.cpu_count() or 1


def collect() -> dict:
    vm = psutil.virtual_memory()
    return {
        "hostname": hostname(),
        "os": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "cpu": platform.processor() or platform.machine(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "total_ram_gb": round(vm.total / 2**30, 2),
        "available_ram_gb": round(available_memory() / 2**30, 2),
        "docker": in_docker(),
        "python": platform.python_version(),
    }
