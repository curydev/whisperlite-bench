import subprocess
import sys

import pytest

from whisperlite.measure import PeakMemory

# parent holds ~300MB, then forks a short-lived child: RSS summing would see ~600MB
FORKING_PARENT = """
import os, time
data = bytearray(300 * 2**20)
for i in range(0, len(data), 4096):
    data[i] = 1
time.sleep(0.3)
pid = os.fork()
if pid == 0:
    time.sleep(1.0)
    os._exit(0)
os.waitpid(pid, 0)
"""


@pytest.mark.skipif(not sys.platform.startswith("linux"), reason="PSS is Linux-only")
def test_forked_child_is_not_double_counted():
    proc = subprocess.Popen([sys.executable, "-c", FORKING_PARENT])
    with PeakMemory(proc.pid) as mem:
        proc.wait()
    assert 250 < mem.peak / 2**20 < 450
