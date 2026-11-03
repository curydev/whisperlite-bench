# results

측정 결과 CSV와 그래프를 둡니다. 발표·보고서에 쓸 결과만 커밋하고, 시험 실행은 `results/scratch/`에 두세요(커밋되지 않음).

| 파일 | 만드는 명령 | 용도 |
|---|---|---|
| `bench_<PC>.csv`, `bench_<PC>_docker.csv` | `whisperlite bench` | 전체 측정. 팀이 정한 하나를 `reference.csv`로 복사해 CER 표로 사용 |
| `quick_<PC>.csv` | `whisperlite recommend` | 사용자 PC의 짧은 측정 |
| `rtf_cer.png` | `whisperlite plot` | RTF–CER 산점도 |

## CSV 열

| 열 | 의미 |
|---|---|
| `runner`, `model`, `precision` | 설정 (예: `faster`, `small`, `int8`) |
| `threads` | 사용한 CPU 스레드 수 |
| `n_files`, `audio_seconds` | 측정한 음성 개수와 총 길이 |
| `load_seconds` | 모델 로딩 시간 (RTF에서 제외) |
| `transcribe_seconds`, `rtf` | 전사 시간, RTF = 전사 시간 ÷ 음성 길이 |
| `cer` | 정규화 후 문자 오류율 |
| `peak_ram_mb` | 측정 프로세스(자식 포함)의 최대 메모리 |
| `hyps_with_digits` | 숫자가 들어간 전사 결과 수 (숫자 표기 차이 점검용) |
| `docker`, `hostname` | 측정 환경 |
| `error` | 실패 사유 (메모리 부족, 미설치 등). 실패도 결과로 남깁니다 |
