"""CER and RTF."""

import jiwer

from .textnorm import normalize


def cer(references, hypotheses) -> float:
    """Corpus-level character error rate after normalization."""
    refs = [normalize(r) for r in references]
    hyps = [normalize(h) for h in hypotheses]
    pairs = [(r, h) for r, h in zip(refs, hyps) if r]
    if not pairs:
        raise ValueError("no non-empty references")
    return jiwer.cer([r for r, _ in pairs], [h for _, h in pairs])


def rtf(transcribe_seconds: float, audio_seconds: float) -> float:
    """Real-time factor: processing time / audio length. Model loading is excluded."""
    if audio_seconds <= 0:
        raise ValueError("audio_seconds must be positive")
    return transcribe_seconds / audio_seconds
