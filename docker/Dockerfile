# Reference environment for the full benchmark (사전 측정).
# Ubuntu 22.04 ships Python 3.10, which both openai-whisper and faster-whisper support.
FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
# Pin to a tag or commit after the first successful build, and record it in README.
ARG WHISPER_CPP_REF=master

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 python3-pip python3-venv ffmpeg git cmake build-essential ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

# whisper.cpp, CPU build
RUN git clone https://github.com/ggml-org/whisper.cpp /opt/whisper.cpp \
    && cd /opt/whisper.cpp && git checkout "$WHISPER_CPP_REF" \
    && cmake -B build -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build -j --config Release \
    && ln -s /opt/whisper.cpp/build/bin/whisper-cli /usr/local/bin/whisper-cli

WORKDIR /app
# CPU-only PyTorch wheel avoids downloading CUDA libraries
RUN pip3 install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip3 install --no-cache-dir -e ".[all,dev]"
COPY tests ./tests

# models are cached here; mount a volume to keep them between runs
ENV XDG_CACHE_HOME=/cache HF_HOME=/cache/huggingface WHISPER_CPP_MODELS=/cache/whisperlite/ggml
ENTRYPOINT ["whisperlite"]
CMD ["--help"]
