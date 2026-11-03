# 원본 저장소 구조 분석

수업 최소 요구사항인 "GitHub 저장소 구조 분석"을 정리하는 문서입니다. 실행기 담당자가 각자 채웁니다.

## openai/whisper (담당: )

- 저장소: https://github.com/openai/whisper (MIT)
- 주요 디렉터리와 역할:
- 우리가 호출하는 부분: `whisper.load_model()`, `model.transcribe()`
- 디코딩 옵션이 정의된 곳:
- 설치·실행 중 겪은 문제 (이슈 링크):

## faster-whisper (담당: )

- 저장소: https://github.com/SYSTRAN/faster-whisper (MIT), 엔진 https://github.com/OpenNMT/CTranslate2 (MIT)
- 주요 디렉터리와 역할:
- 우리가 호출하는 부분: `WhisperModel(...)`, `model.transcribe()`
- 모델 변환과 다운로드 방식:
- 설치·실행 중 겪은 문제 (이슈 링크):

## whisper.cpp (담당: )

- 저장소: https://github.com/ggml-org/whisper.cpp (MIT)
- 주요 디렉터리와 역할:
- 우리가 호출하는 부분: `whisper-cli` 실행 파일
- 양자화 도구와 지원 형식 (`quantize` 실행 결과):
- 설치·실행 중 겪은 문제 (이슈 링크):

## 비교 대상으로 고른 이유

두 경량화 구현은 Python 패키지 방식(faster-whisper)과 네이티브 실행 방식(whisper.cpp)을 대표합니다. 검토했지만 제외한 대안이 있으면 이유와 함께 적습니다.
