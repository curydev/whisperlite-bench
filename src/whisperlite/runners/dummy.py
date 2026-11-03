"""Test runner: returns a fixed transcript without any model, so the
measurement pipeline can be tested without installing Whisper."""

import os
import time

from .base import Runner


class DummyRunner(Runner):
    def load(self, model, precision, threads, decoding):
        self.text = os.environ.get("WHISPERLITE_DUMMY_TEXT", "안녕하세요")
        self.delay = float(os.environ.get("WHISPERLITE_DUMMY_DELAY", "0.01"))

    def transcribe(self, wav_path):
        time.sleep(self.delay)
        return self.text
