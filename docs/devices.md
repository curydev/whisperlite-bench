# 측정 기기

`whisperlite sysinfo` 결과를 기기마다 남깁니다. 기기 간 비교(검증 지표 ④)와 Docker·직접 실행 비교(⑥)의 근거가 됩니다.

| 담당 | 기기 | OS | CPU (물리/논리 코어) | RAM | Docker 메모리 할당 | 비고 |
|---|---|---|---|---|---|---|
| curydev | 자작 데스크톱 (ASRock A520M-ITX/ac) | Windows 11 Education 26200, Docker Desktop 4.98 (WSL2) | AMD Ryzen 7 5700X3D (8/16) | 16GB | 7.7GB (WSL2 기본값: RAM의 50%) | 노트북 아님. `WHISPERLITE_HOST=amd-5700x3d-desktop`, 스레드 8 |
| curydev | MacBook Air 13 (M3, 2024, Mac15,12) | macOS 27.0.1 (medium 직접 실행은 27.2), Colima 0.10.3 + Docker 29.9.2 | Apple M3 (8/8, 성능 4 + 효율 4) | 8GB | 6GB (Colima VM, 8 CPU) | 노트북, 팬 없음. `WHISPERLITE_HOST=macbookair-m3`, 스레드 8. 직접 실행: Python 3.10.22 venv(Docker와 같은 패키지 버전), whisper.cpp 482279b8를 macOS 기본 설정(Accelerate)으로 빌드, 측정 중 Colima 끔. Docker는 medium 미측정 |
