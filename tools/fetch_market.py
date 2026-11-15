"""GitHub Actions에서 돌림: 지수·환율 일별 종가를 tools/data/market/<이름>.csv 로 저장.
작업 환경(클라우드)에서는 시세 사이트 접속이 막혀 있어서, 데이터는 이 워크플로가 받아 커밋해요.
자료: Yahoo Finance (일별 종가, 최근 1년)"""
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent / "data" / "market"
KST = timezone(timedelta(hours=9))
SYMBOLS = {
    "KOSPI": "^KS11", "KOSDAQ": "^KQ11", "USDKRW": "KRW=X",
    "SP500": "^GSPC", "NASDAQ": "^IXIC", "DOW": "^DJI",
    "DXY": "DX-Y.NYB", "US10Y": "^TNX", "WTI": "CL=F",
}


def fetch(sym):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{urllib.parse.quote(sym)}?range=1y&interval=1d"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        res = json.load(r)["chart"]["result"][0]
    tz = timezone(timedelta(seconds=res["meta"].get("gmtoffset", 0)))
    rows = []
    for t, c in zip(res["timestamp"], res["indicators"]["quote"][0]["close"]):
        if c is not None:
            rows.append((datetime.fromtimestamp(t, tz).strftime("%Y-%m-%d"), round(c, 4)))
    # 같은 날짜 중복(장중 갱신분)은 마지막 값만
    return list(dict(rows).items())


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ok = 0
    for name, sym in SYMBOLS.items():
        try:
            rows = fetch(sym)
        except Exception as e:  # 하나 실패해도 나머지는 저장
            print(f"! {name} ({sym}) 실패: {e}")
            continue
        with open(OUT / f"{name}.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["date", "close"])
            w.writerows(rows)
        print(f"✓ {name}: {len(rows)}일, 마지막 {rows[-1]}")
        ok += 1
        time.sleep(1)
    (OUT / "_updated.txt").write_text(datetime.now(KST).strftime("%Y-%m-%d %H:%M KST") + " · Yahoo Finance\n")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
