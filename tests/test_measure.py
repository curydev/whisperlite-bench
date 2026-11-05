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


def test_bench_saves_transcripts_and_rescore_uses_them(manifest, tmp_path, monkeypatch):
    from whisperlite.cli import _measure_all, main
    from whisperlite.measure import hyps_path, read_hyps

    monkeypatch.setenv("WHISPERLITE_DUMMY_TEXT", "3시")
    monkeypatch.setenv("WHISPERLITE_DUMMY_DELAY", "0")
    out = tmp_path / "bench.csv"
    _measure_all([Config("dummy", "tiny", "fp32")], manifest, 1, out, None)
    path = hyps_path(out, Config("dummy", "tiny", "fp32"))
    saved = read_hyps(path)
    assert [s["hyp"] for s in saved] == ["3시", "3시"]
    assert saved[0]["ref"] == "안녕하세요"

    # pretend the transcripts matched the references: rescore must use the file
    path.write_text("".join(
        f'{{"id": "{i}", "ref": "3 시", "hyp": "3시."}}\n' for i in range(2)), encoding="utf-8")
    try:
        main(["rescore", str(out)])
    except SystemExit:
        pass
    assert read_rows(out)[0]["cer"] == "0.0"
