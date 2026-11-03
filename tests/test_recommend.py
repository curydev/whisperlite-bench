from whisperlite.configs import all_configs
from whisperlite.recommend import fits_in_memory, recommend


def row(runner, model, precision, rtf="", cer="", ram="", error=""):
    return {"runner": runner, "model": model, "precision": precision,
            "rtf": rtf, "cer": cer, "peak_ram_mb": ram, "error": error}


BENCH = [
    row("faster", "small", "int8", rtf="0.3", cer="0.10", ram="900"),
    row("faster", "tiny", "int8", rtf="0.1", cer="0.30", ram="300"),
    row("whispercpp", "small", "q8_0", rtf="0.25", cer="0.11", ram="700"),
    row("faster", "medium", "int8", error="MemoryError"),
]


def test_picks_fastest_that_meets_cer():
    quick = [
        row("faster", "small", "int8", rtf="0.40", ram="950"),
        row("faster", "tiny", "int8", rtf="0.12", ram="320"),
        row("whispercpp", "small", "q8_0", rtf="0.35", ram="720"),
    ]
    best, candidates = recommend(BENCH, quick, max_cer=0.15)
    assert best.key == "whispercpp/small/q8_0"
    assert [c.key for c in candidates][0] == "faster/tiny/int8"
    assert candidates[0].rejected == ["CER 0.300 > 0.15"]


def test_rtf_and_ram_limits():
    quick = [row("faster", "small", "int8", rtf="0.40", ram="950")]
    best, candidates = recommend(BENCH, quick, max_cer=0.2, max_rtf=0.3, available_mb=800)
    assert best is None
    assert len(candidates[0].rejected) == 2


def test_ignores_errors_and_configs_without_cer():
    quick = [
        row("faster", "medium", "int8", rtf="0.9", ram="2000"),
        row("whispercpp", "tiny", "q8_0", rtf="0.05", ram="200"),
        row("faster", "small", "int8", error="killed"),
    ]
    best, candidates = recommend(BENCH, quick, max_cer=0.5)
    assert best is None and candidates == []


def test_fits_in_memory_uses_bench_ram_with_margin():
    configs = all_configs(["faster"], ["tiny", "small"])
    keys = {c.key for c in fits_in_memory(configs, BENCH, available_mb=1000)}
    # small/int8 needs 900 * 1.2 > 1000; unknown estimates (fp32) are kept
    assert keys == {"faster/tiny/int8", "faster/tiny/fp32", "faster/small/fp32"}


def test_matrix_has_20_configs():
    assert len(all_configs()) == 20
