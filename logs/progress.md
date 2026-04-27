# TheWordForum 프로젝트 진행 로그

업데이트: 2026-04-27

---

## Phase 1 — 크롤링 ✅ 완료

- 완료일시: 2026-04-27 10:50
- 수집 영상 수: **2,968개**
- 카테고리별: Asia 1,992 / LatinAmerica 608 / Africa 337 / Europe 15 / USCanada 12 / Oceania 4
- 저장 파일: `data/video_list.csv`, `data/urls.txt`

**핵심 발견**: thewordforum.org는 Next.js App Router (JS 렌더링)라 Selenium 불필요.
JS 번들에서 YouTube 플레이리스트 ID를 직접 추출해 yt-dlp로 수집 (쿠키 불필요).

---

## Phase 2a — 자막 다운로드 ⏳ 진행 중

- 시작: 2026-04-27 10:51
- 방법: yt-dlp 자동자막(ko) 일괄 다운로드
- 저장 위치: `data/subs/*.ko.vtt`
- 프로세스: PID 7665 (백그라운드)
- 확인: `ls data/subs/ | wc -l`

---

## Phase 2b — Whisper 전사 ⏳ 진행 중

- 시작: 2026-04-27 11:07
- 방법: faster-whisper large-v3 (CUDA / RTX A2000 12GB)
- 저장 위치: `data/whisper/*.txt`, `data/whisper_dataset.csv`
- 진행 추적: `logs/whisper_progress.json`
- 프로세스: PID 14484 (백그라운드)
- 영상당 소요: ~45초 → 전체 예상 약 37시간
- 확인: `cat logs/whisper_progress.json | python3 -c "import sys,json; d=json.load(sys.stdin); print(f'완료: {len(d[chr(34)+\"done\"+chr(34)])}개')"`

---

## Phase 3~5 — 분석 ⏸ 대기 중

- Phase 2b 완료 후 시작
- 지리분석 / 관계도 / 말씀 포인트
- 스크립트: `.claude/analyze.md` 참고
