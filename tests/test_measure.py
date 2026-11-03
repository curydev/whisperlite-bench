from whisperlite.configs import Config
from whisperlite.measure import append_row, measure, read_rows


def test_measure_with_dummy_runner(manifest, tmp_path, monkeypatch):
    monkeypatch.setenv("WHISPERLITE_DUMMY_TEXT", "안녕하세요")
    monkeypatch.setenv("WHISPERLITE_DUMMY_DELAY", "0.2")
    r = measure(Config("dummy", "tiny", "fp32"), manifest, threads=1)

    assert r["error"] == ""
    assert r["n_files"] == 2 and r["audio_seconds"] == 4.0
    assert r["cer"] == 0.0
    assert 0.08 < r["rtf"] < 0.5  # 2 x 0.2s over 4s of audio
    assert r["peak_ram_mb"] > 0

    out = tmp_path / "out.csv"
    append_row(out, r)
    append_row(out, r)
    assert len(read_rows(out)) == 2


def test_measure_reports_runner_failure(manifest):
    r = measure(Config("openai", "tiny", "int8"), manifest, threads=1)
    assert r["error"]  # openai/whisper rejects INT8 (or is not installed)
    assert "rtf" not in r
