# 이어서 하기 가이드

## 현재 상태 확인

```bash
cd /home/adminsecure01

# 프로세스 살아있는지 확인
ps aux | grep -E "whisper_transcribe|slack_notify" | grep -v grep

# Whisper 진행률
cat logs/whisper_progress.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
left = 2968 - len(d['done'])
print(f'완료: {len(d[\"done\"])}개 / 실패: {len(d[\"failed\"])}개 / 남은: {left}개 / 예상: {left*45/3600:.1f}시간')
"
```

---

## 케이스별 대응

### A — 프로세스 살아있음
그냥 기다리면 됨.

### B — Whisper가 죽어있음

```bash
export PATH="$HOME/.local/bin:$PATH"
cd /home/adminsecure01
nohup python3 scripts/whisper_transcribe.py > logs/whisper_run.log 2>&1 &
echo "Whisper PID: $!"
```

### C — Slack 알림 프로세스가 죽어있음

```bash
cd /home/adminsecure01
nohup python3 scripts/slack_notify.py > /dev/null 2>&1 &
echo "알림 PID: $!"
```

### D — Whisper 완료, 보고서만 다시 생성하고 싶을 때

```bash
export PATH="$HOME/.local/bin:$PATH"
cd /home/adminsecure01
python3 scripts/generate_report.py
```

---

## 파일 구조

```
/home/adminsecure01/
├── data/
│   ├── video_list.csv          # 2,968개 영상 목록
│   ├── urls.txt                # YouTube URL 목록
│   ├── whisper/                # 영상별 전사 텍스트 (.txt)
│   └── whisper_dataset.csv     # 전체 전사 결과 (최종 데이터)
├── logs/
│   ├── progress.md             # 진행 현황 (이 파일)
│   ├── whisper_progress.json   # 완료/실패 영상 ID 목록
│   └── whisper_run.log         # Whisper 실행 로그
└── scripts/
    ├── crawl_playlist.py       # Phase 1 크롤링 (완료)
    ├── whisper_transcribe.py   # Phase 2b 전사 (진행 중)
    ├── slack_notify.py         # 진행 알림 + 완료 시 자동 처리
    └── generate_report.py      # Google Docs 보고서 생성
```

---

## 완료 시 자동 처리 순서

Whisper 100% 완료 → slack_notify.py 가 자동으로:
1. `data/whisper_dataset.csv` GitHub push
2. Google Docs 보고서 생성 및 `dainal7603@gmail.com` 공유
3. Slack으로 문서 링크 전송

---

## 환경 정보

- GPU: NVIDIA RTX A2000 12GB / CUDA 12.4
- Whisper 모델: faster-whisper large-v3 (float16)
- Python 패키지: `~/.local/bin` (PATH 추가 필요)
