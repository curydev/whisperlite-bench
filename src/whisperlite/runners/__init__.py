"""Runner registry. Each runner is imported lazily so a missing library only
breaks the runner that needs it."""

import importlib

_RUNNERS = {
    "openai": "whisperlite.runners.openai_whisper:OpenAIWhisperRunner",
    "faster": "whisperlite.runners.faster_whisper:FasterWhisperRunner",
    "whispercpp": "whisperlite.runners.whisper_cpp:WhisperCppRunner",
    "dummy": "whisperlite.runners.dummy:DummyRunner",
}


def get_runner(name: str):
    module, cls = _RUNNERS[name].split(":")
    return getattr(importlib.import_module(module), cls)()
