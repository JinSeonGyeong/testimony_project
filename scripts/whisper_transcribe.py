#!/usr/bin/env python3
"""Phase 2b - Whisper로 음성 직접 전사 (GPU 가속)"""

import subprocess
import csv
import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

import imageio_ffmpeg
from faster_whisper import WhisperModel

FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
VIDEO_LIST = "data/video_list.csv"
OUTPUT_DIR = "data/whisper"
AUDIO_TMP = "/tmp/twf_audio"
PROGRESS_FILE = "logs/whisper_progress.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(AUDIO_TMP, exist_ok=True)
os.makedirs("logs", exist_ok=True)


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"done": [], "failed": []}


def save_progress(progress):
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f)


def download_audio(video_id, youtube_url):
    out_path = os.path.join(AUDIO_TMP, f"{video_id}.%(ext)s")
    mp3_path = os.path.join(AUDIO_TMP, f"{video_id}.mp3")
    cmd = [
        "yt-dlp",
        "--extract-audio",
        "--audio-format", "mp3",
        "--audio-quality", "5",
        "--no-warnings",
        "--ffmpeg-location", FFMPEG_PATH,
        "-o", out_path,
        youtube_url,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        return None
    return mp3_path if os.path.exists(mp3_path) else None


def transcribe(model, audio_path):
    segments, info = model.transcribe(
        audio_path,
        language="ko",
        beam_size=5,
        vad_filter=True,
    )
    text = " ".join([s.text.strip() for s in segments])
    return text, info.language, info.language_probability


def main():
    # 비디오 목록 로드
    with open(VIDEO_LIST, encoding="utf-8") as f:
        videos = list(csv.DictReader(f))
    total = len(videos)

    # 진행 상황 복원
    progress = load_progress()
    done_ids = set(progress["done"])
    remaining = [v for v in videos if v["video_id"] not in done_ids]

    print(f"총 {total}개 / 완료 {len(done_ids)}개 / 남은 {len(remaining)}개")

    # 모델 로드 (1회)
    print("Whisper large-v3 모델 로딩 중...")
    model = WhisperModel("large-v3", device="cuda", compute_type="float16")
    print("모델 로딩 완료\n")

    results = []
    start_total = time.time()

    for i, row in enumerate(remaining, 1):
        vid_id = row["video_id"]
        title = row["title"]
        category = row["category"]
        url = row["youtube_url"]

        print(f"[{i}/{len(remaining)}] {title[:40]} ({category})")

        # 오디오 다운로드
        t0 = time.time()
        audio_path = download_audio(vid_id, url)
        if not audio_path:
            print(f"  오디오 다운로드 실패 → 건너뜀")
            progress["failed"].append(vid_id)
            save_progress(progress)
            continue

        # Whisper 전사
        try:
            text, lang, lang_prob = transcribe(model, audio_path)
            elapsed = time.time() - t0
            print(f"  완료 ({elapsed:.1f}초) 언어:{lang}({lang_prob:.2f}) {len(text)}자")

            # 결과 저장 (개별 txt)
            txt_path = os.path.join(OUTPUT_DIR, f"{vid_id}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(text)

            results.append({
                "video_id": vid_id,
                "title": title,
                "category": category,
                "youtube_url": url,
                "text": text,
                "char_count": len(text),
                "lang_detected": lang,
                "lang_prob": f"{lang_prob:.3f}",
            })

            progress["done"].append(vid_id)

        except Exception as e:
            print(f"  전사 오류: {e}")
            progress["failed"].append(vid_id)

        finally:
            # 오디오 삭제 (공간 절약)
            if audio_path and os.path.exists(audio_path):
                os.remove(audio_path)

        save_progress(progress)

        # 진행률 표시
        done_count = len(progress["done"])
        elapsed_total = time.time() - start_total
        avg = elapsed_total / i
        eta = avg * (len(remaining) - i)
        print(f"  진행: {done_count}/{total} | 예상 남은 시간: {eta/3600:.1f}시간\n")

        # 중간 CSV 저장 (100개마다)
        if i % 100 == 0:
            save_csv(results)

    save_csv(results)
    print(f"\n완료! {len(progress['done'])}개 전사 / {len(progress['failed'])}개 실패")


def save_csv(results):
    if not results:
        return
    out_path = "data/whisper_dataset.csv"
    fieldnames = ["video_id", "title", "category", "youtube_url", "text", "char_count", "lang_detected", "lang_prob"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"  중간 저장: {out_path} ({len(results)}개)")


if __name__ == "__main__":
    main()
