# 측정 규칙

세 실행기를 공정하게 비교하기 위한 규칙입니다. 바꿀 때는 이슈로 합의하고 이 문서와 `src/whisperlite/configs.py`를 함께 고칩니다.

## 측정 조합 (총 20개)

| 실행기 | 정밀도 | 비고 |
|---|---|---|
| openai/whisper | `fp32` | CPU에서는 FP32만 지원 |
| faster-whisper | `fp32`, `int8` | `compute_type` 값 |
| whisper.cpp | `f16`, `q8_0` | 기본 ggml 모델은 F16(FP32 아님). `q8_0`은 ggml 자체 8비트 양자화로 faster-whisper의 `int8`과 같은 방식이 아님 |

모델 크기: tiny, base, small, medium. openai 4 + faster-whisper 8 + whisper.cpp 8 = 20개.

## 디코딩 옵션 (모든 실행기 공통)

라이브러리마다 기본값이 달라서, 기본값을 쓰지 않고 아래 값을 명시합니다.

- 언어 `ko` 고정 (언어 자동 감지 끔)
- beam size 5
- temperature 0 (온도 fallback 끔)
- VAD 끔
- 이전 문장 조건부 디코딩 끔

## CPU 전용

- openai/whisper: `device="cpu"`
- faster-whisper: `device="cpu"`
- whisper.cpp: `-ng` (Apple Silicon에서 Metal GPU 사용을 막음)

## 시간 측정

- **RTF = 전사 시간 ÷ 음성 길이.** 모델 로딩 시간은 `load_seconds`에 따로 기록하고 RTF에서 뺍니다. 음성이 3~21초로 짧아서 로딩 시간을 섞으면 RTF가 왜곡됩니다.
- whisper.cpp는 파일마다 프로세스를 새로 띄우므로, whisper-cli가 출력하는 `load time`을 빼서 전사 시간을 구합니다.
- 스레드 수는 기본값으로 물리 코어 수를 쓰고 결과에 기록합니다. 기기 간 비교에서는 같은 값으로 맞춥니다.

## 메모리 측정

- 조합마다 새 프로세스(`whisperlite.worker`)를 띄워 다른 조합의 메모리가 섞이지 않게 합니다.
- 0.05초 간격으로 프로세스와 자식 프로세스의 RSS 합을 재서 최댓값을 기록합니다.
- Docker 안에서는 컨테이너 메모리 제한(cgroup)을 사용 가능한 메모리로 봅니다.

## CER 정규화

정답과 전사 결과에 똑같이 적용합니다 (`src/whisperlite/textnorm.py`).

1. 유니코드 NFKC 정규화, 소문자화
2. 문장부호·기호 제거
3. 공백 모두 제거 (띄어쓰기 차이를 오류로 세지 않음)

**숫자 표기는 아직 정하지 않았습니다.** Whisper는 "3시"처럼 숫자로 쓰는데 정답은 "세 시"처럼 한글일 수 있고, 고유어·한자어 읽기가 달라 자동 변환이 어렵습니다. `hyps_with_digits` 열로 빈도를 먼저 보고 규칙을 정합니다.

## 측정 환경 기록

- 측정 전에 `whisperlite sysinfo` 결과를 이슈나 `docs/devices.md`에 남깁니다.
- 노트북은 전원을 연결하고, 다른 프로그램을 닫고 측정합니다.
- 팬이 없는 노트북(예: MacBook Air)은 오래 돌리면 발열로 느려질 수 있으니, 같은 조합을 두 번 재서 차이를 확인합니다.
