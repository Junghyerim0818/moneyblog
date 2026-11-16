"""블로그 조회수 기록 (GitHub Actions '블로그 조회수' 워크플로에서 실행).
블로거 API pageviews(7DAYS·30DAYS·all)를 받아 tools/data/stats/pageviews.csv 에 하루 한 줄 추가.
하루 조회수 = 오늘 누적(all) − 직전 기록 누적. 블로거 API는 글별 조회수를 주지 않아요."""
import csv
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from publish import API, access_token, call  # noqa: E402

KST = timezone(timedelta(hours=9))
OUT = Path(__file__).resolve().parents[1] / "tools" / "data" / "stats"
CSV = OUT / "pageviews.csv"


def main():
    token = access_token()
    blog = os.environ["BLOGGER_BLOG_ID"].strip().strip("\"'")
    pv = call("GET", f"{API}/blogs/{blog}/pageviews?range=7DAYS&range=30DAYS&range=all", None, token)
    counts = {c["timeRange"]: int(c["count"]) for c in pv.get("counts", [])}
    info = call("GET", f"{API}/blogs/{blog}?fields=posts/totalItems", None, token)
    now = datetime.now(KST)
    row = {"date": now.strftime("%Y-%m-%d"), "time": now.strftime("%H:%M"),
           "all": counts.get("ALL_TIME", 0), "d7": counts.get("SEVEN_DAYS", 0),
           "d30": counts.get("THIRTY_DAYS", 0), "posts": info.get("posts", {}).get("totalItems", "")}
    OUT.mkdir(parents=True, exist_ok=True)
    rows = list(csv.DictReader(open(CSV, encoding="utf-8"))) if CSV.exists() else []
    prev = next((r for r in reversed(rows) if r["date"] != row["date"]), None)
    row["day"] = row["all"] - int(prev["all"]) if prev else ""
    rows = [r for r in rows if r["date"] != row["date"]] + [row]  # 같은 날 다시 돌면 덮어쓰기
    with open(CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["date", "time", "day", "all", "d7", "d30", "posts"])
        w.writeheader()
        w.writerows(rows)
    (OUT / "latest.json").write_text(json.dumps(row, ensure_ascii=False, indent=1), encoding="utf-8")
    print("조회수:", row)


if __name__ == "__main__":
    main()
