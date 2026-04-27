# 집에서 이어서 하기 가이드

## 현재 상태 확인 (먼저 실행)

```bash
cd /home/adminsecure01

# 1. 프로세스 살아있는지 확인
ps aux | grep -E "yt-dlp|whisper_transcribe" | grep -v grep

# 2. 자막 다운로드 진행률
ls data/subs/ | wc -l
# → 2968에 가까우면 완료

# 3. Whisper 전사 진행률
cat logs/whisper_progress.json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(f'완료: {len(d[\"done\"])}개 / 실패: {len(d[\"failed\"])}개 / 남은: {2968 - len(d[\"done\"])}개')
"
```

---

## 케이스별 대응

### 케이스 A — 두 프로세스 모두 살아있음
아무것도 안 해도 됨. 그냥 기다리면 됨.

### 케이스 B — yt-dlp (자막 다운로드)가 죽어있음

```bash
export PATH="$HOME/.local/bin:$PATH"
cd /home/adminsecure01

# 이미 받은 파일은 자동 스킵됨
nohup yt-dlp \
  --write-sub --write-auto-sub --sub-lang ko \
  --skip-download --ignore-errors --sleep-interval 1 \
  --no-warnings \
  -o "data/subs/%(id)s.%(ext)s" \
  --batch-file data/urls.txt \
  > logs/subtitle_download.log 2>&1 &
echo "yt-dlp PID: $!"
```

### 케이스 C — Whisper가 죽어있음

```bash
export PATH="$HOME/.local/bin:$PATH"
cd /home/adminsecure01

# 자동으로 이어서 실행 (whisper_progress.json 기반 재시작)
nohup python3 scripts/whisper_transcribe.py \
  > logs/whisper_run.log 2>&1 &
echo "Whisper PID: $!"
```

### 케이스 D — Whisper까지 완료됨
Phase 3~5 분석 시작:

```bash
export PATH="$HOME/.local/bin:$PATH"
cd /home/adminsecure01
pip install spacy scikit-learn --break-system-packages
python3 -m spacy download ko_core_news_sm

python3 scripts/geo_analysis.py
python3 scripts/relations.py
python3 scripts/gospel_analysis.py
```

---

## 파일 구조 요약

```
/home/adminsecure01/
├── data/
│   ├── video_list.csv       # 2,968개 영상 목록
│   ├── urls.txt             # YouTube URL 목록
│   ├── subs/                # yt-dlp 자동자막 (.ko.vtt)
│   ├── whisper/             # Whisper 전사 결과 (.txt)
│   └── whisper_dataset.csv  # Whisper 전체 결과 CSV
├── logs/
│   ├── progress.md          # 진행 현황
│   ├── whisper_progress.json # Whisper 완료/실패 목록
│   ├── subtitle_download.log
│   └── whisper_run.log
└── scripts/
    ├── crawl_playlist.py    # Phase 1 (완료)
    ├── whisper_transcribe.py # Phase 2b (진행 중)
    └── parse_subtitles.py   # Phase 2a 파싱용
```

---

## 중요 정보

- **GPU**: NVIDIA RTX A2000 12GB / CUDA 12.4
- **Whisper 모델**: large-v3 (float16)
- **Python 패키지 경로**: `~/.local/bin` (항상 PATH에 추가 필요)
- **자막 방식**: Whisper 전사 결과(`whisper_dataset.csv`)를 최종 데이터로 사용
- **YouTube 플레이리스트 ID** (한국어):
  - Asia: `PLLBA8oKJsd0Q6uODmr5BHVJbeIoMpiTSx`
  - Europe: `PLLBA8oKJsd0TWmDzNnTLvbql9jzyfcZ2D`
  - LatinAmerica: `PLLBA8oKJsd0QXNQsf-U1znazDE2f_30OX`
  - Africa: `PLLBA8oKJsd0S0JeHr6aFoOo7xw2axu7lJ`
  - USCanada: `PLLBA8oKJsd0R3zM-ztDVtkrgjzlzX2xyn`
  - Oceania: `PLLBA8oKJsd0T6Df3EAVMg_CeYCjYLbhFQ`
