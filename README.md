# WhisperLite Bench

외장 GPU가 없는 노트북에서 오픈소스 음성인식 모델 Whisper를 쓰려는 사람을 위해, 세 가지 실행 방식을 같은 조건에서 비교하고 **내 PC에 맞는 설정을 추천**하는 도구입니다.

| 실행기 | 역할 | 정밀도 |
|---|---|---|
| [openai/whisper](https://github.com/openai/whisper) | 기준선 (원본 재현) | FP32 |
| [faster-whisper](https://github.com/SYSTRAN/faster-whisper) | 경량화 ① (CTranslate2) | FP32, INT8 |
| [whisper.cpp](https://github.com/ggml-org/whisper.cpp) | 경량화 ② (C/C++) | F16, Q8_0 |

모델 크기 tiny, base, small, medium을 합쳐 20개 조합의 **속도(RTF)**, **한국어 정확도(CER)**, **최대 메모리**를 잽니다.

## 동작 방식

1. **사전 측정 (팀, Docker):** 공개 한국어 데이터 Zeroth-Korean 테스트셋 전체로 20개 조합을 측정해 CER 표를 만듭니다. Docker로 누구나 같은 소프트웨어 환경에서 재현할 수 있습니다.
2. **사용자 PC 측정 (직접 실행):** 사용자 PC에서 사용 가능한 메모리에 들어가는 조합만 골라 짧은 샘플로 속도와 메모리를 잽니다.
3. **추천:** 사전 측정한 CER과 내 PC의 측정값을 합쳐, 허용 오류율과 목표 속도를 만족하는 가장 빠른 조합을 고릅니다.
4. **검증:** 같은 PC에서 Docker와 직접 실행의 차이를 비교하고, 추천 결과가 전체 측정의 최적 조합과 일치하는지 확인합니다.

측정 규칙(디코딩 옵션 고정, CPU 전용, 로딩 시간 분리, CER 정규화)은 [docs/measurement-rules.md](docs/measurement-rules.md)에 있습니다.

## 현재 상태

- [x] 측정 파이프라인, CER·RTF 계산, 메모리 측정, 추천 로직, CLI
- [x] 단위 테스트 (Whisper 없이 가짜 실행기로 파이프라인 검증), GitHub Actions
- [ ] 세 실행기를 실제 모델로 실행해 확인 (실행기 담당)
- [ ] Docker 이미지 빌드 확인, whisper.cpp 버전 고정
- [ ] 데이터 준비 스크립트를 실제 데이터셋으로 확인
- [ ] 숫자 표기 정규화 규칙 결정

## 설치

### A. Docker (사전 측정, 재현용)

```bash
docker build -f docker/Dockerfile -t whisperlite .
```

```bash
docker run --rm -v "$PWD/data:/app/data" -v "$PWD/results:/app/results" -v whisperlite-cache:/cache whisperlite sysinfo
```

macOS·Windows의 Docker Desktop은 VM 안에서 돌아가므로, 설정에서 메모리를 충분히(medium까지 재려면 6GB 이상 권장) 할당하세요.

### B. 직접 실행 (Ubuntu 기본)

```bash
sudo apt install ffmpeg python3-venv cmake build-essential
```

```bash
python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[faster,data,dev]"
```

whisper.cpp는 소스에서 빌드하고 `whisper-cli`를 PATH에 두거나 `WHISPER_CPP_BIN`으로 경로를 지정합니다.

```bash
git clone https://github.com/ggml-org/whisper.cpp && cmake -S whisper.cpp -B whisper.cpp/build && cmake --build whisper.cpp/build -j --config Release
```

```bash
export WHISPER_CPP_BIN="$PWD/whisper.cpp/build/bin/whisper-cli"
```

openai/whisper까지 직접 실행하려면 `pip install -e ".[openai]"`를 추가합니다 (PyTorch 설치로 용량이 큽니다). macOS·Windows 직접 실행은 확장 기능으로, 동작이 확인되면 여기에 추가합니다.

## 사용법

```bash
whisperlite prepare-data --out data/zeroth_test
```

```bash
whisperlite prepare-data --out data/sample --limit 20
```

```bash
whisperlite bench --manifest data/zeroth_test/manifest.csv
```

```bash
whisperlite recommend --reference results/reference.csv --max-cer 0.15 --max-rtf 0.5
```

```bash
whisperlite compare results/bench_mypc.csv results/bench_mypc_docker.csv
```

```bash
whisperlite plot results/reference.csv --out results/rtf_cer.png
```

- `prepare-data`: Zeroth-Korean 테스트셋(457개, 약 1.2시간)을 16kHz WAV와 `manifest.csv`로 준비합니다. `--limit`으로 앞에서부터 일부만 받아 내장 샘플로 씁니다.
- `bench`: 20개 조합 전체 측정. 결과 파일에 이미 있는 조합은 건너뛰므로 중간에 멈춰도 이어서 돌릴 수 있습니다. 개발 중에는 `--runners faster --models tiny`처럼 좁혀서 돌리세요.
- `recommend`: 이 PC에서 후보를 짧게 재고 추천합니다. `--max-rtf 0.5`는 "음성 길이의 절반 시간 안에 처리"라는 뜻입니다.
- `compare`: 같은 PC에서 잰 두 결과(예: 직접 실행 vs Docker)의 RTF 비율과 메모리 차이.

결과 CSV 형식은 [results/README.md](results/README.md)를 보세요.

## 저장소 구조

```text
├── src/whisperlite/
│   ├── cli.py            명령어
│   ├── configs.py        측정 조합(20개)과 공통 디코딩 옵션
│   ├── data.py           데이터셋 → WAV + manifest
│   ├── worker.py         조합 하나를 별도 프로세스에서 실행
│   ├── measure.py        RTF·CER·최대 메모리 측정
│   ├── recommend.py      추천 로직
│   ├── sysinfo.py        CPU·RAM·Docker 메모리 제한
│   ├── textnorm.py       CER 정규화
│   └── runners/          실행기별 어댑터 (openai, faster, whispercpp)
├── tests/                단위 테스트
├── docker/Dockerfile     사전 측정용 Ubuntu 22.04 환경
├── docs/                 측정 규칙, 저장소 구조 분석, 기기 목록, 문제 해결 기록
└── results/              측정 결과 CSV와 그래프
```

## 역할 분담

| 담당 | 파일 |
|---|---|
| openai/whisper | `runners/openai_whisper.py`, `docs/repo-analysis.md` 해당 절 |
| faster-whisper | `runners/faster_whisper.py`, `docs/repo-analysis.md` 해당 절 |
| whisper.cpp | `runners/whisper_cpp.py`, `docker/Dockerfile`의 빌드, `docs/repo-analysis.md` 해당 절 |
| 측정·추천 | `measure.py`, `recommend.py`, `textnorm.py`, `cli.py` |

작업은 이슈로 만들고 브랜치에서 PR로 합칩니다. 오류는 "설치·실행 오류" 이슈 템플릿으로 기록합니다.

## 라이선스와 출처

- 이 저장소의 코드: MIT ([LICENSE](LICENSE))
- openai/whisper (MIT), faster-whisper (MIT), CTranslate2 (MIT), whisper.cpp (MIT), jiwer (Apache-2.0)
- 데이터: [Zeroth-Korean Speech Corpus (OpenSLR SLR40)](https://www.openslr.org/40/), CC BY 4.0. Hugging Face의 [`kresnik/zeroth_korean`](https://huggingface.co/datasets/kresnik/zeroth_korean)으로 받습니다. 데이터와 모델 파일은 저장소에 포함하지 않습니다.
- A. Radford et al., "Robust Speech Recognition via Large-Scale Weak Supervision," ICML 2023.
