"""기본글 생성 도우미: 원고(HTML) + 그래픽 스펙 → posts/<slug>/ 에 post.html, meta.json, 이미지 생성.
원고 안의 {{img:파일명}} 은 스펙의 alt 와 함께 <figure><img> 로 바뀐다."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from moneygraph.core import render_spec  # noqa: E402

NOTE = ('<p class="mg-note">※ 2026년 11월 기준으로 정리한 글입니다. 세율·제도는 바뀔 수 있으니 '
        '거래 전 증권사·국세청 안내를 한 번 더 확인하세요. 특정 종목·상품의 매수·매도 권유가 아닙니다.</p>')


def source_box(links):
    lis = "\n".join(f'<li><a href="{u}" target="_blank" rel="noopener">{t}</a>{(" " + d) if d else ""}</li>'
                    for t, u, d in links)
    return f'<div class="mg-source">\n<div class="t">참고한 공식 자료</div>\n<ul>\n{lis}\n</ul>\n</div>'


def faq(items):
    body = "\n".join(f"<details><summary>{q}</summary><p>{a}</p></details>" for q, a in items)
    return f'<h2 id="faq">자주 묻는 질문</h2>\n<div class="mg-faq">\n{body}\n</div>'


def make(slug, meta, spec, html, render=True):
    d = ROOT / "posts" / slug
    d.mkdir(parents=True, exist_ok=True)
    spec = {"post": slug, **spec}
    alts = {g["file"]: g["alt"] for g in spec["graphics"]}

    def fig(m):
        f = m.group(1)
        if f not in alts:
            raise KeyError(f"스펙에 없는 그림: {f}")
        return f'<figure><img src="{f}.webp" alt="{alts[f]}"></figure>'

    html = re.sub(r"\{\{img:([^}]+)\}\}", fig, html.strip())
    used = set(re.findall(r'src="([^"]+)\.webp"', html))
    unused = set(alts) - used
    if unused:
        print("  ! 원고에 안 쓴 그림:", ", ".join(sorted(unused)))
    (d / "post.html").write_text(html + "\n", encoding="utf-8")
    (d / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    (d / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8")
    if render:
        render_spec(d / "spec.json", d)
    print(f"✓ {slug}: {len(re.sub('<[^>]+>', '', html)):,}자, 그림 {len(used)}개")
    return d


# ── 시세 추세 그래픽 (데이터: tools/data/market/*.csv, '시세 데이터' 워크플로가 매일 갱신) ──
MARKET = ROOT / "tools" / "data" / "market"
MARKET_NAMES = {"KOSPI": "코스피", "KOSDAQ": "코스닥", "USDKRW": "원·달러 환율", "SP500": "S&P500",
                "NASDAQ": "나스닥", "DOW": "다우", "DXY": "달러인덱스", "US10Y": "미 10년물 금리", "WTI": "WTI 유가"}


def market_series(name, days=60, end=None):
    """(dates, values). end='YYYY-MM-DD'면 그날까지(글 기준일 이후 데이터는 자름)."""
    import csv
    with open(MARKET / f"{name}.csv", encoding="utf-8") as f:
        rows = [(r["date"], float(r["close"])) for r in csv.DictReader(f)]
    from datetime import date
    rows = [r for r in rows if date.fromisoformat(r[0]).weekday() < 5]  # 주말 값(환율 24시간 시세) 제외
    if end:
        rows = [r for r in rows if r[0] <= end]
    rows = rows[-days:]
    return [d for d, _ in rows], [v for _, v in rows]


def trend_graphic(file, name, days=60, end=None, title=None, sub=None, check=None, alt=None, color="blue"):
    """moneygraph trend 스펙 한 개. check=검증한 종가 → 마지막 값과 0.5% 넘게 다르면 멈춤."""
    dates, vals = market_series(name, days, end)
    if not vals:
        raise ValueError(f"{name} 데이터 없음")
    if check is not None and abs(vals[-1] - check) / check > 0.005:
        raise ValueError(f"{name} 차트 마지막 값 {vals[-1]:,.2f}(={dates[-1]})가 확인한 종가 {check:,.2f}와 달라요")
    label = MARKET_NAMES.get(name, name)
    x = [d[5:].replace("-", "/") for d in dates]
    unit = "원" if name == "USDKRW" else ""
    return {"type": "trend", "file": file,
            "title": title or f"{label}\n최근 {len(vals)}거래일",
            "sub": sub or f"{dates[0][5:].replace('-', '/')}~{dates[-1][5:].replace('-', '/')} 일별 종가",
            "x": x, "series": [{"name": label, "values": vals, "color": color}], "unit": unit,
            "source": "Yahoo Finance 일별 종가" + (" (24시간 국제 시세라 서울 종가와 조금 달라요)" if name == "USDKRW" else ""),
            "alt": alt or f"{label} 최근 {len(vals)}거래일 종가 추이 그래프"}
