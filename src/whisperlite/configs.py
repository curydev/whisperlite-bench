"""The measurement matrix and the decoding settings every runner must use.

Keeping these in one place is what makes the comparison fair: runners read
DECODING instead of relying on each library's own defaults, which differ.
"""

from dataclasses import dataclass

MODEL_SIZES = ["tiny", "base", "small", "medium"]

# precision labels per runner. openai/whisper on CPU only runs FP32.
# whisper.cpp's unquantized ggml models are F16, not FP32.
PRECISIONS = {
    "openai": ["fp32"],
    "faster": ["fp32", "int8"],
    "whispercpp": ["f16", "q8_0"],
}

DECODING = {
    "language": "ko",
    "beam_size": 5,
    "temperature": 0.0,
    "vad": False,
    "condition_on_previous_text": False,
}


@dataclass(frozen=True)
class Config:
    runner: str
    model: str
    precision: str

    @property
    def key(self) -> str:
        return f"{self.runner}/{self.model}/{self.precision}"


def all_configs(runners=None, models=None):
    runners = runners or list(PRECISIONS)
    models = models or MODEL_SIZES
    return [
        Config(r, m, p)
        for r in runners
        for m in models
        for p in PRECISIONS[r]
    ]
