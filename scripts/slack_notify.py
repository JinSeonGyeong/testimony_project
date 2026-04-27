#!/usr/bin/env python3
"""Whisper 진행 상황 Slack 알림"""

import json
import subprocess
import time
import urllib.request

with open("/home/adminsecure01/.slack_webhook") as _f:
    WEBHOOK = _f.read().strip()
PROGRESS_FILE = "/home/adminsecure01/logs/whisper_progress.json"
TOTAL = 2968
CHECK_INTERVAL = 1800  # 30분마다 체크
MILESTONES = {25, 50, 75, 100}


def git_push():
    base = "/home/adminsecure01"
    subprocess.run(["git", "-C", base, "add",
                    "data/whisper_dataset.csv", "logs/progress.md", "logs/whisper_progress.json"], check=False)
    subprocess.run(["git", "-C", base, "commit", "-m",
                    "Phase 2b 완료: Whisper 전사 결과 업로드 (2,968개)"], check=False)
    subprocess.run(["git", "-C", base, "push", "-u", "origin", "main"], check=False)


def send_slack(msg):
    data = json.dumps({"text": msg}).encode()
    req = urllib.request.Request(WEBHOOK, data=data, headers={"Content-type": "application/json"})
    urllib.request.urlopen(req, timeout=10)


def get_progress():
    with open(PROGRESS_FILE) as f:
        d = json.load(f)
    return len(d["done"]), len(d["failed"])


def main():
    notified_milestones = set()

    while True:
        try:
            done, failed = get_progress()
            pct = done / TOTAL * 100
            eta_hours = (TOTAL - done) * 45 / 3600

            # 마일스톤 알림
            for m in MILESTONES:
                if pct >= m and m not in notified_milestones:
                    notified_milestones.add(m)
                    if m == 100:
                        git_push()
                        send_slack(
                            f"🎉 *Whisper 전사 완료!*\n"
                            f"완료: {done}개 / 실패: {failed}개\n"
                            f"결과: `data/whisper_dataset.csv`\n"
                            f"📦 GitHub에 자동 업로드 완료!"
                        )
                    else:
                        send_slack(
                            f"📊 *Whisper 진행률 {m}% 달성*\n"
                            f"완료: {done}/{TOTAL}개 | 실패: {failed}개\n"
                            f"남은 예상 시간: {eta_hours:.1f}시간"
                        )

            # 완료 시 종료
            if done >= TOTAL:
                break

        except Exception as e:
            pass

        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
