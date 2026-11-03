"""Lightweight ①: faster-whisper (CTranslate2) on CPU."""

from .base import Runner

_COMPUTE_TYPE = {"fp32": "float32", "int8": "int8"}


class FasterWhisperRunner(Runner):
    def load(self, model, precision, threads, decoding):
        from faster_whisper import WhisperModel

        self.decoding = decoding
        self.model = WhisperModel(
            model,
            device="cpu",
            compute_type=_COMPUTE_TYPE[precision],
            cpu_threads=threads,
        )

    def transcribe(self, wav_path):
        d = self.decoding
        segments, _info = self.model.transcribe(
            wav_path,
            language=d["language"],
            beam_size=d["beam_size"],
            temperature=d["temperature"],
            condition_on_previous_text=d["condition_on_previous_text"],
            vad_filter=d["vad"],
        )
        # segments is a lazy generator: decoding happens while joining
        return "".join(s.text for s in segments).strip()
