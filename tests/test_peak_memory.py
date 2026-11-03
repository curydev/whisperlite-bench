import subprocess
import sys

from whisperlite.measure import PeakMemory

# parent holds ~300MB, then forks a child that never execs. Reading parent and
# child one after the other used to count the shared pages up to twice.
FORKING_PARENT = """
import os, time
data = bytearray(300 * 2**20)
for i in range(0, len(data), 4096):
    data[i] = 1
time.sleep(0.3)
for _ in range(5):
    pid = os.fork()
    if pid == 0:
        time.sleep(0.3)
        os._exit(0)
    os.waitpid(pid, 0)
"""

# parent holds ~100MB and runs a different program that allocates ~200MB:
# both must be counted (this is the whisper-cli case)
EXECING_PARENT = """
import subprocess, sys
data = bytearray(100 * 2**20)
for i in range(0, len(data), 4096):
    data[i] = 1
child = "import time; d = bytearray(200 * 2**20)\\nfor i in range(0, len(d), 4096): d[i] = 1\\ntime.sleep(1.0)"
subprocess.run([sys.executable, "-c", child])
"""


def peak_mb(script):
    proc = subprocess.Popen([sys.executable, "-c", script])
    with PeakMemory(proc.pid) as mem:
        proc.wait()
    return mem.peak / 2**20


def test_forked_copy_is_not_counted():
    assert 250 < peak_mb(FORKING_PARENT) < 450


def test_execed_child_is_counted():
    assert 270 < peak_mb(EXECING_PARENT) < 450
