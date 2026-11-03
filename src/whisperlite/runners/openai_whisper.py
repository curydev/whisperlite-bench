"""Baseline: openai/whisper on CPU (FP32 only)."""

from .base import Runner


class OpenAIWhisperRunner(Runner):
    def load(self, model, precision, threads, decoding):
        if precision != "fp32":
            raise ValueError("openai/whisper runs FP32 on CPU")
        import torch
        import whisper

        torch.set_num_threads(threads)
        self.decoding = decoding
        self.model = whisper.load_model(model, device="cpu")

    def transcribe(self, wav_path):
        d = self.decoding
        result = self.model.transcribe(
            wav_path,
            language=d["language"],
            beam_size=d["beam_size"],
            temperature=d["temperature"],
            condition_on_previous_text=d["condition_on_previous_text"],
            fp16=False,
            verbose=None,
        )
        return result["text"].strip()
