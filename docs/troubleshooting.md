# 문제 해결 기록

수업 평가는 "실패 → 원인 분석 → 해결 → 기록" 과정을 봅니다. 오류를 만나면 먼저 GitHub 이슈("설치·실행 오류" 템플릿)로 남기고, 해결되면 여기에 한 줄로 요약합니다.

| 날짜 | 환경 | 증상 | 원인 | 해결 | 이슈 |
|---|---|---|---|---|---|
| 2026-11-03 | Docker (Ubuntu 22.04) | 이미지 빌드 중 `pip install -e` 실패: "build backend is missing the 'build_editable' hook" | Ubuntu 22.04 기본 pip가 오래되어 pyproject.toml만 있는 패키지의 개발 모드 설치(PEP 660)를 지원하지 않음 | pip를 먼저 업그레이드하고, 이미지 안에서는 일반 설치 사용 | |
| 2026-11-03 | Docker | `prepare-data`가 데이터를 다 쓴 뒤 "Fatal Python error: PyGILState_Release"로 비정상 종료 | datasets 스트리밍 스레드가 Python 종료 과정에서 충돌 | 작업 완료 후 `os._exit(0)`으로 종료 단계 생략 | |
| 2026-11-03 | Docker | openai small 측정 실패: "SHA256 checksum does not match" | 모델 다운로드 파일 손상 | 캐시의 `small.pt`를 지우고 다시 측정 | |
| 2026-11-03 | Docker (VM 5.9GB, 스왑 없음) | openai medium 최대 메모리가 7,851MB로 VM 전체보다 크게 나옴 | openai/whisper가 파일마다 ffmpeg를 띄우는데, fork 직후 자식이 부모 메모리를 공유해 RSS 합산 시 두 번 집계됨 | Linux에서 PSS로 측정하도록 수정, 재현 테스트 추가 (예전 방식 611MB vs 실제 305MB) | |
| 2026-11-03 | Docker | 결과 파일의 PC 이름이 매번 다름 | 컨테이너 호스트 이름은 무작위 컨테이너 ID | `WHISPERLITE_HOST`로 실제 PC 이름 전달 | |
| 2026-11-03 | 데이터 | 앞에서부터 50개를 받으니 화자가 2명뿐 | 테스트셋이 화자 순서로 정렬됨 | `--stride` 옵션으로 고르게 추출 (10명) | |
