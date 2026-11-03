"""Combine pre-measured CER (bench table) with this PC's short measurement
(RTF, peak RAM) and pick the fastest configuration that meets the user's limits."""

from dataclasses import dataclass, field


def _key(row) -> str:
    return f"{row['runner']}/{row['model']}/{row['precision']}"


def _ok(row) -> bool:
    return not row.get("error") and row.get("rtf") not in ("", None)


@dataclass
class Candidate:
    key: str
    rtf: float
    cer: float
    peak_ram_mb: float
    rejected: list = field(default_factory=list)


def ram_estimates(bench_rows) -> dict:
    """Peak RAM per configuration from the bench table, used to skip models
    that cannot fit before spending time measuring them."""
    return {_key(r): float(r["peak_ram_mb"]) for r in bench_rows if r.get("peak_ram_mb")}


def fits_in_memory(configs, bench_rows, available_mb, margin=1.2):
    est = ram_estimates(bench_rows)
    return [c for c in configs if est.get(c.key, 0) * margin <= available_mb]


def recommend(bench_rows, quick_rows, max_cer, max_rtf=None, available_mb=None):
    """Returns (best Candidate or None, all candidates sorted by RTF)."""
    cer_by_key = {_key(r): float(r["cer"]) for r in bench_rows if _ok(r) and r.get("cer")}
    candidates = []
    for r in quick_rows:
        if not _ok(r):
            continue
        key = _key(r)
        if key not in cer_by_key:
            continue
        c = Candidate(key, float(r["rtf"]), cer_by_key[key], float(r["peak_ram_mb"]))
        if c.cer > max_cer:
            c.rejected.append(f"CER {c.cer:.3f} > {max_cer}")
        if max_rtf is not None and c.rtf > max_rtf:
            c.rejected.append(f"RTF {c.rtf:.3f} > {max_rtf}")
        if available_mb is not None and c.peak_ram_mb > available_mb:
            c.rejected.append(f"RAM {c.peak_ram_mb:.0f}MB > {available_mb:.0f}MB")
        candidates.append(c)
    candidates.sort(key=lambda c: c.rtf)
    best = next((c for c in candidates if not c.rejected), None)
    return best, candidates
