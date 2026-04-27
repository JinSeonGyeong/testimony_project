#!/usr/bin/env python3
"""Phase 1 - thewordforum.org 크롤링 (Playwright 사용)"""

import re
import csv
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

CATEGORIES = {
    "Asia": "https://www.thewordforum.org/ko/testimonies/Asia",
    "Europe": "https://www.thewordforum.org/ko/testimonies/Europe",
    "Americas": "https://www.thewordforum.org/ko/testimonies/Americas",
    "Oceania": "https://www.thewordforum.org/ko/testimonies/Oceania",
    "LatinAmerica": "https://www.thewordforum.org/ko/testimonies/Latin%20America",
    "Africa": "https://www.thewordforum.org/ko/testimonies/Africa",
}

# YouTube Video ID 패턴 (11자리)
YT_ID_PATTERN = re.compile(r'/([a-zA-Z0-9_-]{11})$')

def scroll_to_bottom(page):
    """페이지 끝까지 스크롤"""
    prev_height = 0
    scroll_count = 0
    while True:
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(2500)
        curr_height = page.evaluate("document.body.scrollHeight")
        if curr_height == prev_height:
            break
        prev_height = curr_height
        scroll_count += 1
        print(f"  스크롤 {scroll_count}회 (높이: {curr_height}px)")
    return scroll_count

def extract_videos(page, cat_name):
    """현재 페이지에서 영상 정보 추출"""
    links = page.query_selector_all("a[href]")
    seen = set()
    videos = []
    for link in links:
        href = link.get_attribute("href") or ""
        title = (link.inner_text() or "").strip()
        # thewordforum.org 내부 링크에서 ID 추출
        if "thewordforum.org" in href or href.startswith("/"):
            match = YT_ID_PATTERN.search(href)
            if match:
                vid_id = match.group(1)
                if vid_id not in seen:
                    seen.add(vid_id)
                    videos.append({
                        "category": cat_name,
                        "title": title or "제목없음",
                        "video_id": vid_id,
                        "youtube_url": f"https://www.youtube.com/watch?v={vid_id}"
                    })
    return videos

def main():
    os.makedirs("data", exist_ok=True)
    all_results = []
    log = {"start": str(datetime.now()), "categories": {}}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        for cat_name, cat_url in CATEGORIES.items():
            print(f"\n[{cat_name}] 크롤링 시작: {cat_url}")
            try:
                page.goto(cat_url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(3000)

                scroll_count = scroll_to_bottom(page)
                videos = extract_videos(page, cat_name)

                all_results.extend(videos)
                log["categories"][cat_name] = len(videos)
                print(f"  [{cat_name}] {len(videos)}개 수집 (스크롤 {scroll_count}회)")
            except Exception as e:
                print(f"  [{cat_name}] 오류: {e}")
                log["categories"][cat_name] = f"ERROR: {e}"

        browser.close()

    # CSV 저장
    with open("data/video_list.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["category", "title", "video_id", "youtube_url"])
        writer.writeheader()
        writer.writerows(all_results)

    # URL 목록 저장
    with open("data/urls.txt", "w", encoding="utf-8") as f:
        for item in all_results:
            f.write(item["youtube_url"] + "\n")

    log["total"] = len(all_results)
    log["end"] = str(datetime.now())

    print(f"\n{'='*50}")
    print(f"총 {len(all_results)}개 수집 완료")
    print(f"카테고리별: {log['categories']}")
    print(f"저장: data/video_list.csv, data/urls.txt")

    # logs/progress.md 업데이트
    os.makedirs("logs", exist_ok=True)
    with open("logs/progress.md", "w", encoding="utf-8") as f:
        f.write(f"# TheWordForum 진행 로그\n\n")
        f.write(f"## Phase 1 완료\n")
        f.write(f"- 완료일시: {log['end']}\n")
        f.write(f"- 수집 영상 수: {len(all_results)}개\n")
        f.write(f"- 카테고리별:\n")
        for cat, cnt in log["categories"].items():
            f.write(f"  - {cat}: {cnt}개\n")

if __name__ == "__main__":
    main()
