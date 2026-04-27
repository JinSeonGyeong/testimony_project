# TheWordForum 프로젝트 진행 로그

업데이트: 2026-04-27

---

## Phase 1 — 크롤링 ✅ 완료

- 완료일시: 2026-04-27 10:50
- 수집 영상 수: **2,968개**
- 카테고리별: Asia 1,992 / LatinAmerica 608 / Africa 337 / Europe 15 / USCanada 12 / Oceania 4
- 저장 파일: `data/video_list.csv`, `data/urls.txt`

---

## Phase 2a — yt-dlp 자막 다운로드 ❌ 중단

- Whisper 전사와 동시 실행 시 YouTube rate limit 발생 → 중단 결정
- Whisper 전사 결과가 더 정확하므로 대체 사용

---

## Phase 2b — Whisper 전사 ⏳ 진행 중

- 시작: 2026-04-27 11:07
- 모델: faster-whisper large-v3 (CUDA / RTX A2000 12GB)
- 현재: **58개 완료 / 실패 0개** (2026-04-27 기준)
- 저장 위치: `data/whisper/*.txt`, `data/whisper_dataset.csv`
- 진행 추적: `logs/whisper_progress.json`
- 예상 완료: 약 37시간 소요

---

## Phase 3~5 — 분석 ⏸ 대기 중

Whisper 완료 시 자동 실행:
- Google Docs 보고서 자동 생성 → `dainal7603@gmail.com` 공유
- GitHub 자동 push
- Slack 알림 (완료 링크 포함)

보고서 구성:
- 카테고리별 영상 수 및 비율
- 자주 등장한 성경 구절 Top 15
- 지역별 언급 분포
- 복음 전파 경로 (지역 → 지역)
- 복음 전달 인물 관계도
- 카테고리별 복음 핵심 포인트
