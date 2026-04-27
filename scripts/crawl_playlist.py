#!/usr/bin/env python3
"""Phase 1 - YouTube 플레이리스트에서 영상 목록 수집 (yt-dlp 사용)"""

import subprocess
import json
import csv
import os
from datetime import datetime

# 한국어(ko) 플레이리스트 ID (JS 번들에서 추출)
KO_PLAYLISTS = {
    "Asia":         "PLLBA8oKJsd0Q6uODmr5BHVJbeIoMpiTSx",
    "Europe":       "PLLBA8oKJsd0TWmDzNnTLvbql9jzyfcZ2D",
    "LatinAmerica": "PLLBA8oKJsd0QXNQsf-U1znazDE2f_30OX",
    "Africa":       "PLLBA8oKJsd0S0JeHr6aFoOo7xw2axu7lJ",
    "USCanada":     "PLLBA8oKJsd0R3zM-ztDVtkrgjzlzX2xyn",
    "Oceania":      "PLLBA8oKJsd0T6Df3EAVMg_CeYCjYLbhFQ",
}

def fetch_playlist(playlist_id, cat_name):
    """yt-dlp로 플레이리스트 영상 목록 가져오기"""
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    cmd = [
        "yt-dlp",
        "--flat-playlist",
        "--print", "%(id)s\t%(title)s",
        "--no-warnings",
        url
    ]
    print(f"[{cat_name}] 플레이리스트 수집 중...")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        videos = []
        for line in result.stdout.strip().splitlines():
            if "\t" in line:
                vid_id, title = line.split("\t", 1)
                videos.append({
                    "category": cat_name,
                    "title": title.strip(),
                    "video_id": vid_id.strip(),
                    "youtube_url": f"https://www.youtube.com/watch?v={vid_id.strip()}"
                })
        if result.returncode != 0 and result.stderr:
            print(f"  경고: {result.stderr[:200]}")
        return videos
    except subprocess.TimeoutExpired:
        print(f"  [{cat_name}] 타임아웃!")
        return []
    except Exception as e:
        print(f"  [{cat_name}] 오류: {e}")
        return []

def main():
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)

    all_results = []
    log = {"start": str(datetime.now()), "categories": {}}

    for cat_name, playlist_id in KO_PLAYLISTS.items():
        videos = fetch_playlist(playlist_id, cat_name)
        all_results.extend(videos)
        log["categories"][cat_name] = len(videos)
        print(f"  [{cat_name}] {len(videos)}개 수집")

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
    for cat, cnt in log["categories"].items():
        print(f"  {cat}: {cnt}개")
    print(f"저장: data/video_list.csv, data/urls.txt")

    # logs/progress.md 업데이트
    with open("logs/progress.md", "w", encoding="utf-8") as f:
        f.write("# TheWordForum 진행 로그\n\n")
        f.write("## Phase 1 완료\n")
        f.write(f"- 완료일시: {log['end']}\n")
        f.write(f"- 수집 영상 수: {len(all_results)}개\n")
        f.write("- 카테고리별:\n")
        for cat, cnt in log["categories"].items():
            f.write(f"  - {cat}: {cnt}개\n")

if __name__ == "__main__":
    main()
