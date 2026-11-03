# 문제 해결 기록

수업 평가는 "실패 → 원인 분석 → 해결 → 기록" 과정을 봅니다. 오류를 만나면 먼저 GitHub 이슈("설치·실행 오류" 템플릿)로 남기고, 해결되면 여기에 한 줄로 요약합니다.

| 날짜 | 환경 | 증상 | 원인 | 해결 | 이슈 |
|---|---|---|---|---|---|
| 2026-11-03 | Docker (Ubuntu 22.04) | 이미지 빌드 중 `pip install -e` 실패: "build backend is missing the 'build_editable' hook" | Ubuntu 22.04 기본 pip가 오래되어 pyproject.toml만 있는 패키지의 개발 모드 설치(PEP 660)를 지원하지 않음 | pip를 먼저 업그레이드하고, 이미지 안에서는 일반 설치 사용 | |
| 2026-11-03 | Docker | `prepare-data`가 데이터를 다 쓴 뒤 "Fatal Python error: PyGILState_Release"로 비정상 종료 | datasets 스트리밍 스레드가 Python 종료 과정에서 충돌 | 작업 완료 후 `os._exit(0)`으로 종료 단계 생략 | |
| 2026-11-03 | Docker | openai small 측정 실패: "SHA256 checksum does not match" | 모델 다운로드 파일 손상 | 캐시의 `small.pt`를 지우고 다시 측정 | |
| 2026-11-03 | Docker (VM 5.9GB, 스왑 없음) | openai medium 최대 메모리가 7,851MB로 VM 전체보다 크게 나옴 | openai/whisper가 파일마다 ffmpeg를 띄우는데, fork 직후 exec 전의 자식은 부모 메모리를 그대로 공유함. 부모와 자식을 차례로 읽는 사이에 fork가 일어나면 부모는 전부, 자식은 공유분 절반이 집계됨 | 1차 수정(PSS 사용)으로는 해결 안 됨(재측정 7,679MB). cgroup으로 실제값 5,077MB 확인 후, exec 전 복제 프로세스(부모와 명령줄이 같은 자식)를 제외하도록 2차 수정 → 5,004MB로 일치. 테스트 2개 추가 | |
| 2026-11-03 | Docker | 결과 파일의 PC 이름이 매번 다름 | 컨테이너 호스트 이름은 무작위 컨테이너 ID | `WHISPERLITE_HOST`로 실제 PC 이름 전달 | |
| 2026-11-03 | Docker | 같은 조합을 다시 재니 CER은 똑같은데 RTF가 20~55% 달라짐 (예: whisper.cpp tiny Q8_0 0.156 → 0.067) | 첫 측정은 Docker 설치·이미지 빌드 직후로 맥에 다른 작업이 있었던 것으로 추정 (확인 불가) | 측정 규칙대로 같은 조합을 두 번 재고, 측정 중 다른 작업을 하지 않기 | |
| 2026-11-03 | 맥 재시작 후 | 측정 시작 직후 "docker-run.sh: No such file" | 실행 스크립트를 임시 폴더에 두었는데 재시작으로 비워짐 | 저장소 `scripts/docker-run.sh`로 이동 | |
| 2026-11-03 | 데이터 | 앞에서부터 50개를 받으니 화자가 2명뿐 | 테스트셋이 화자 순서로 정렬됨 | `--stride` 옵션으로 고르게 추출 (10명) | |
