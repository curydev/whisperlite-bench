from whisperlite.runners.whisper_cpp import WhisperCppRunner, model_filename, parse_load_ms
from whisperlite.sysinfo import cgroup_memory_limit, collect


def test_cgroup_limit(tmp_path):
    f = tmp_path / "memory.max"
    f.write_text("max\n")
    assert cgroup_memory_limit([f]) is None
    f.write_text("4294967296\n")
    assert cgroup_memory_limit([f]) == 4 * 2**30
    assert cgroup_memory_limit([tmp_path / "missing"]) is None


def test_collect_has_core_fields():
    info = collect()
    assert info["total_ram_gb"] > 0 and "docker" in info


def test_ggml_model_names():
    assert model_filename("small", "f16") == "ggml-small.bin"
    assert model_filename("small", "q8_0") == "ggml-small-q8_0.bin"


def test_parse_load_time():
    stderr = "whisper_print_timings:     load time =   123.45 ms\nwhisper_print_timings:    total time =  900.00 ms"
    assert parse_load_ms(stderr) == 123.45
    assert parse_load_ms("no timings") is None


def test_whisper_cli_command_is_cpu_only():
    r = WhisperCppRunner()
    r.binary, r.model_path, r.threads = "whisper-cli", "m.bin", 4
    r.decoding = {"language": "ko", "beam_size": 5}
    cmd = r.command("a.wav")
    assert "-ng" in cmd and cmd[cmd.index("-l") + 1] == "ko" and cmd[cmd.index("-t") + 1] == "4"
