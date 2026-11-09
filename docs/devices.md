# 측정 기기

`whisperlite sysinfo` 결과를 기기마다 남깁니다. 기기 간 비교(검증 지표 ④)와 Docker·직접 실행 비교(⑥)의 근거가 됩니다.

| 담당 | 기기 | OS | CPU (물리/논리 코어) | RAM | Docker 메모리 할당 | 비고 |
|---|---|---|---|---|---|---|
| curydev | 자작 데스크톱 (ASRock A520M-ITX/ac) | Windows 11 Education 26200, Docker Desktop 4.98 (WSL2) | AMD Ryzen 7 5700X3D (8/16) | 16GB | 7.7GB (WSL2 기본값: RAM의 50%) | 노트북 아님. `WHISPERLITE_HOST=amd-5700x3d-desktop`, 스레드 8 |
