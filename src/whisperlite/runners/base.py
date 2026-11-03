"""Common interface every runner implements."""

from abc import ABC, abstractmethod


class Runner(ABC):
    @abstractmethod
    def load(self, model: str, precision: str, threads: int, decoding: dict) -> None:
        """Load the model once. Time spent here is reported as load time, not RTF."""

    @abstractmethod
    def transcribe(self, wav_path: str) -> str:
        """Transcribe one 16 kHz mono WAV file and return plain text."""

    def last_transcribe_seconds(self):
        """Override when the runner measures its own transcription time
        (e.g. a subprocess whose wall time includes model loading)."""
        return None
