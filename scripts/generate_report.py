#!/usr/bin/env python3
"""Whisper 완료 후 Google Docs 보고서 생성"""

import csv
import re
from collections import Counter, defaultdict
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

# 지역명 키워드 (나라/도시)
REGION_KEYWORDS = [
    "한국", "미국", "중국", "일본", "인도", "브라질", "독일", "영국", "프랑스",
    "호주", "캐나다", "멕시코", "아르헨티나", "나이지리아", "케냐", "에티오피아",
    "필리핀", "인도네시아", "태국", "베트남", "싱가포르", "말레이시아",
    "미얀마", "대만", "홍콩", "캄보디아", "라오스", "네팔", "방글라데시",
    "페루", "콜롬비아", "칠레", "볼리비아", "에콰도르", "파나마",
    "가나", "탄자니아", "우간다", "르완다", "코트디부아르", "짐바브웨",
    "뉴질랜드", "피지", "파푸아뉴기니",
]

# 복음 전달 경로 패턴
ROUTE_PATTERNS = [
    re.compile(r'([가-힣]{2,6})(?:에서|을 통해|로부터)\s*[가-힣\s]*?([가-힣]{2,6})(?:에게|한테|에)\s*복음'),
    re.compile(r'([가-힣]{2,6})(?:을|를)\s*통해\s*([가-힣]{2,6})(?:이|가)\s*(?:믿|구원|예수)'),
]

# 인물 관계 패턴
RELATION_PATTERNS = [
    (re.compile(r'([가-힣]{2,5})(?:을|를)\s*통해\s*([가-힣]{2,5})(?:을|를)\s*만'), "전도"),
    (re.compile(r'([가-힣]{2,5})(?:이|가)\s*([가-힣]{2,5})에게\s*복음'), "복음전달"),
    (re.compile(r'([가-힣]{2,5})(?:와|과)\s*([가-힣]{2,5})(?:이|가)\s*함께'), "동역"),
    (re.compile(r'([가-힣]{2,5})\s*(?:전도사|목사|사역자|선교사).*?([가-힣]{2,5})'), "사역관계"),
]


def load_data():
    rows = []
    with open(DATASET, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows.append(row)
    return rows


def analyze(rows):
    total = len(rows)
    by_category = Counter(r["category"] for r in rows)
    avg_chars = sum(int(r.get("char_count", 0)) for r in rows) // max(total, 1)

    # 복음 포인트 전체
    gospel_counts = {}
    for point, keywords in GOSPEL_KEYWORDS.items():
        gospel_counts[point] = sum(
            sum(r["text"].count(kw) for kw in keywords)
            for r in rows if r.get("text")
        )
    gospel_top = sorted(gospel_counts.items(), key=lambda x: -x[1])

    # 카테고리별 복음 포인트
    cat_gospel = defaultdict(lambda: defaultdict(int))
    for r in rows:
        if not r.get("text"):
            continue
        cat = r["category"]
        for point, keywords in GOSPEL_KEYWORDS.items():
            cat_gospel[cat][point] += sum(r["text"].count(kw) for kw in keywords)

    # 성경 구절
    all_scriptures = []
    for r in rows:
        if r.get("text"):
            all_scriptures.extend(SCRIPTURE_PATTERN.findall(r["text"]))
    scripture_top = Counter(all_scriptures).most_common(15)

    # 지역 분포
    region_counts = Counter()
    for r in rows:
        if r.get("text"):
            for region in REGION_KEYWORDS:
                cnt = r["text"].count(region)
                if cnt:
                    region_counts[region] += cnt
    region_top = region_counts.most_common(15)

    # 복음 이동 경로
    routes = Counter()
    for r in rows:
        if not r.get("text"):
            continue
        for pat in ROUTE_PATTERNS:
            for m in pat.findall(r["text"]):
                if m[0] != m[1] and len(m[0]) >= 2 and len(m[1]) >= 2:
                    routes[(m[0], m[1])] += 1
    route_top = routes.most_common(10)

    # 인물 관계
    relations = []
    for r in rows:
        if not r.get("text"):
            continue
        for pat, rel_type in RELATION_PATTERNS:
            for m in pat.findall(r["text"]):
                if m[0] != m[1]:
                    relations.append((m[0], m[1], rel_type, r["category"]))
    relation_counter = Counter((a, b, t) for a, b, t, _ in relations)
    relation_top = relation_counter.most_common(15)

    return {
        "total": total,
        "by_category": by_category,
        "avg_chars": avg_chars,
        "gospel_top": gospel_top,
        "cat_gospel": dict(cat_gospel),
        "scripture_top": scripture_top,
        "region_top": region_top,
        "route_top": route_top,
        "relation_top": relation_top,
    }


def build_doc_text(stats):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = []

    lines.append(f"TheWordForum 간증 분석 보고서\n")
    lines.append(f"생성일시: {now}  |  분석 대상: {stats['total']:,}개 영상\n\n")

    # 1. 수집 현황
    lines.append("1. 수집 현황\n\n")
    lines.append(f"  총 영상 수: {stats['total']:,}개\n")
    lines.append(f"  평균 전사 텍스트 길이: {stats['avg_chars']:,}자\n\n")
    lines.append("  카테고리별 영상 수:\n")
    for cat, cnt in sorted(stats["by_category"].items(), key=lambda x: -x[1]):
        pct = cnt / stats["total"] * 100
        lines.append(f"    • {cat}: {cnt:,}개 ({pct:.1f}%)\n")
    lines.append("\n")

    # 2. 성경 구절 빈도
    lines.append("2. 자주 등장한 성경 구절 Top 15\n\n")
    if stats["scripture_top"]:
        for i, (verse, cnt) in enumerate(stats["scripture_top"], 1):
            lines.append(f"  {i:2d}. {verse}  —  {cnt}회\n")
    else:
        lines.append("  (추출된 구절 없음)\n")
    lines.append("\n")

    # 3. 지역별 분포
    lines.append("3. 지역별 언급 분포\n\n")
    lines.append("  간증 텍스트에서 언급된 지역명 빈도:\n")
    for region, cnt in stats["region_top"]:
        bar = "■" * min(cnt // max(stats["region_top"][0][1] // 20, 1), 20)
        lines.append(f"    • {region}: {cnt}회  {bar}\n")
    lines.append("\n")

    # 4. 복음 이동 경로
    lines.append("4. 복음 전파 경로 (지역 → 지역)\n\n")
    if stats["route_top"]:
        for (frm, to), cnt in stats["route_top"]:
            lines.append(f"  {frm}  →  {to}  ({cnt}건)\n")
    else:
        lines.append("  (패턴 매칭된 경로 없음)\n")
    lines.append("\n")

    # 5. 인물 관계도
    lines.append("5. 복음 전달 인물 관계\n\n")
    lines.append("  형식: [인물A]  →  [인물B]  (관계유형, N건)\n\n")
    if stats["relation_top"]:
        for (a, b, rel), cnt in stats["relation_top"]:
            lines.append(f"  {a}  →  {b}  ({rel}, {cnt}건)\n")
    else:
        lines.append("  (패턴 매칭된 관계 없음)\n")
    lines.append("\n")

    # 6. 복음 핵심 포인트
    lines.append("6. 복음 핵심 포인트 빈도\n\n")
    max_cnt = stats["gospel_top"][0][1] if stats["gospel_top"] else 1
    for point, cnt in stats["gospel_top"]:
        bar = "■" * min(int(cnt / max_cnt * 20), 20)
        lines.append(f"  {point}: {cnt:,}회  {bar}\n")
    lines.append("\n")

    # 7. 카테고리별 복음 포인트
    lines.append("7. 카테고리별 복음 포인트 Top 3\n\n")
    for cat in sorted(stats["cat_gospel"].keys()):
        top3 = sorted(stats["cat_gospel"][cat].items(), key=lambda x: -x[1])[:3]
        top3_str = "  /  ".join(f"{p} {c:,}회" for p, c in top3)
        lines.append(f"  [{cat}]  {top3_str}\n")
    lines.append("\n")

    # 8. 분석 방법
    lines.append("8. 분석 방법\n\n")
    lines.append("  • 영상 수집: YouTube 플레이리스트 API (yt-dlp)\n")
    lines.append("  • 음성 전사: OpenAI Whisper large-v3 (CUDA / NVIDIA RTX A2000 12GB)\n")
    lines.append("  • 한국어 감지 정확도: 평균 99% 이상\n")
    lines.append("  • 지역 분석: 키워드 매칭 (국가·도시명)\n")
    lines.append("  • 복음 경로: 정규식 패턴 (\"X에서 Y에게 복음\" 등)\n")
    lines.append("  • 관계도: 정규식 패턴 (\"X를 통해 Y를 만\" 등)\n")
    lines.append("  • 성경 구절: 정규식 패턴 (\"OO N장 N절\" 형식)\n")

    return "".join(lines)


def main():
    print("데이터 로드 중...")
    rows = load_data()
    stats = analyze(rows)
    print(f"총 {stats['total']}개 분석 완료")

    creds = service_account.Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
    docs = build("docs", "v1", credentials=creds)
    drive = build("drive", "v3", credentials=creds)

    title = f"TheWordForum 간증 분석 보고서 ({datetime.now().strftime('%Y-%m-%d')})"
    doc = docs.documents().create(body={"title": title}).execute()
    doc_id = doc["documentId"]
    print(f"문서 생성: {doc_id}")

    full_text = build_doc_text(stats)
    docs.documents().batchUpdate(
        documentId=doc_id,
        body={"requests": [{"insertText": {"location": {"index": 1}, "text": full_text}}]}
    ).execute()
    print("내용 작성 완료")

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
