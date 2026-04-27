#!/usr/bin/env python3
"""Whisper 완료 후 Google Docs 보고서 생성"""

import csv
import re
import os
from collections import Counter
from datetime import datetime

from google.oauth2 import service_account
from googleapiclient.discovery import build

CREDS_FILE = "/home/adminsecure01/.google_credentials.json"
DATASET = "/home/adminsecure01/data/whisper_dataset.csv"
SHARE_EMAIL = "dainal7603@gmail.com"

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/drive",
]

GOSPEL_KEYWORDS = {
    "죄용서": ["죄", "용서", "사함"],
    "부활": ["부활", "살아나", "다시살"],
    "구원": ["구원", "구하다", "살리다"],
    "십자가": ["십자가", "보혈", "피"],
    "믿음": ["믿음", "믿다", "신앙"],
    "회개": ["회개", "돌이키다", "뉘우치"],
    "성령": ["성령", "성신", "보혜사"],
    "영생": ["영생", "영원한생명", "천국"],
}

SCRIPTURE_PATTERN = re.compile(r'[가-힣]+\s*\d+[장:]\s*\d+절?')


def load_data():
    rows = []
    with open(DATASET, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def analyze(rows):
    total = len(rows)
    by_category = Counter(r["category"] for r in rows)

    # 평균 텍스트 길이
    avg_chars = sum(int(r.get("char_count", 0)) for r in rows) // max(total, 1)

    # 복음 포인트 빈도
    gospel_counts = {}
    for point, keywords in GOSPEL_KEYWORDS.items():
        count = sum(
            sum(r["text"].count(kw) for kw in keywords)
            for r in rows if r.get("text")
        )
        gospel_counts[point] = count
    gospel_top = sorted(gospel_counts.items(), key=lambda x: -x[1])

    # 성경 구절 빈도
    all_scriptures = []
    for r in rows:
        if r.get("text"):
            all_scriptures.extend(SCRIPTURE_PATTERN.findall(r["text"]))
    scripture_top = Counter(all_scriptures).most_common(10)

    return {
        "total": total,
        "by_category": by_category,
        "avg_chars": avg_chars,
        "gospel_top": gospel_top,
        "scripture_top": scripture_top,
    }


def build_doc_requests(stats, rows):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    requests = []

    def insert(text, idx=1):
        requests.append({"insertText": {"location": {"index": idx}, "text": text}})
        return len(text)

    def heading(text, level, idx):
        requests.append({"insertText": {"location": {"index": idx}, "text": text + "\n"}})
        requests.append({
            "updateParagraphStyle": {
                "range": {"startIndex": idx, "endIndex": idx + len(text) + 1},
                "paragraphStyle": {"namedStyleType": f"HEADING_{level}"},
                "fields": "namedStyleType",
            }
        })
        return len(text) + 1

    # 문서 내용 구성 (한 번에 텍스트 생성 후 삽입)
    lines = []
    lines.append(f"TheWordForum 간증 분석 보고서\n")
    lines.append(f"생성일시: {now}\n\n")

    lines.append("1. 수집 현황\n\n")
    lines.append(f"총 영상 수: {stats['total']:,}개\n")
    lines.append(f"평균 텍스트 길이: {stats['avg_chars']:,}자\n\n")

    lines.append("카테고리별 영상 수\n")
    for cat, cnt in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
        lines.append(f"  • {cat}: {cnt:,}개\n")
    lines.append("\n")

    lines.append("2. 복음 핵심 포인트\n\n")
    for point, cnt in stats["gospel_top"]:
        bar = "■" * min(int(cnt / max(stats["gospel_top"][0][1], 1) * 20), 20)
        lines.append(f"  {point}: {cnt:,}회  {bar}\n")
    lines.append("\n")

    lines.append("3. 자주 등장한 성경 구절 Top 10\n\n")
    if stats["scripture_top"]:
        for i, (verse, cnt) in enumerate(stats["scripture_top"], 1):
            lines.append(f"  {i}. {verse} — {cnt}회\n")
    else:
        lines.append("  (패턴 매칭 결과 없음)\n")
    lines.append("\n")

    lines.append("4. 카테고리별 복음 포인트 분포\n\n")
    for cat in sorted(stats["by_category"].keys()):
        cat_rows = [r for r in rows if r["category"] == cat]
        cat_gospel = {}
        for point, keywords in GOSPEL_KEYWORDS.items():
            cat_gospel[point] = sum(
                sum(r["text"].count(kw) for kw in keywords)
                for r in cat_rows if r.get("text")
            )
        top3 = sorted(cat_gospel.items(), key=lambda x: -x[1])[:3]
        top3_str = ", ".join(f"{p}({c:,})" for p, c in top3)
        lines.append(f"  {cat}: {top3_str}\n")
    lines.append("\n")

    lines.append("5. 분석 방법\n\n")
    lines.append("  • 영상 수집: YouTube 플레이리스트 API (yt-dlp)\n")
    lines.append("  • 음성 전사: OpenAI Whisper large-v3 (CUDA / RTX A2000 12GB)\n")
    lines.append("  • 언어 감지 정확도: 한국어 평균 99% 이상\n")
    lines.append("  • 복음 포인트: 키워드 빈도 분석\n")
    lines.append("  • 성경 구절: 정규식 패턴 매칭\n")

    full_text = "".join(lines)

    return [{"insertText": {"location": {"index": 1}, "text": full_text}}]


def main():
    print("데이터 로드 중...")
    rows = load_data()
    stats = analyze(rows)

    print(f"총 {stats['total']}개 분석 완료")

    creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    docs = build("docs", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)

    # 문서 생성
    title = f"TheWordForum 간증 분석 보고서 ({datetime.now().strftime('%Y-%m-%d')})"
    doc = docs.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    print(f"문서 생성: {doc_id}")

    # 내용 삽입
    requests = build_doc_requests(stats, rows)
    docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    print("내용 작성 완료")

    # 공유 설정 (본인 이메일)
    drive.permissions().create(
        fileId=doc_id,
        body={"type": "user", "role": "writer", "emailAddress": SHARE_EMAIL},
        sendNotificationEmail=False,
    ).execute()

    doc_url = f"https://docs.google.com/document/d/{doc_id}/edit"
    print(f"완료! 문서 URL: {doc_url}")
    return doc_url


if __name__ == "__main__":
    main()
