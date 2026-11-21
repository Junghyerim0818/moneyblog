"""디자인 토큰 + 컴포넌트. 좌표는 전부 픽셀(위→아래), 2배로 그린 뒤 줄여서 선명하게 저장한다."""
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager as fm  # noqa: E402
from matplotlib.patches import Circle, FancyBboxPatch, Wedge  # noqa: E402
from PIL import Image  # noqa: E402

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "brand.json"

# ── 디자인 토큰 ───────────────────────────────────────────────
BRAND = {
    "name": "한눈머니",
    "handle": "숫자로 보는 돈 이야기",
    "font_dir": str(HERE / "fonts"),
}
if CONFIG.exists():
    BRAND.update(json.loads(CONFIG.read_text(encoding="utf-8")))

C = {
    "bg": "#FFFFFF", "card": "#F2F4F6", "card2": "#F9FAFB", "line": "#E5E8EB",
    "text": "#191F28", "sub": "#4E5968", "muted": "#8B95A1",
    "blue": "#3182F6", "blue_l": "#E8F3FF", "blue_d": "#1B64DA",
    "up": "#F04452", "up_l": "#FFEEEE", "down": "#3182F6", "down_l": "#E8F3FF",
    "green": "#15C47E", "green_l": "#E5F8EF", "yellow": "#FFC342", "yellow_l": "#FFF8E1",
    "navy": "#202632",
}
PALETTE = ["#3182F6", "#15C47E", "#FFC342", "#F04452", "#8B5CF6", "#8B95A1"]

WEIGHTS = {"r": "Regular", "m": "Medium", "sb": "SemiBold", "b": "Bold", "xb": "ExtraBold"}
_FP = {}


def font(w="r"):
    if w not in _FP:
        p = Path(BRAND["font_dir"]) / f"Pretendard-{WEIGHTS[w]}.otf"
        if p.exists():
            _FP[w] = fm.FontProperties(fname=str(p))
        else:  # 폰트 폴더가 없으면 시스템 한글 폰트로
            fam = next((f for f in ("Pretendard", "Noto Sans CJK KR", "Malgun Gothic", "AppleGothic", "NanumGothic")
                        if any(f in x.name for x in fm.fontManager.ttflist)), None)
            _FP[w] = fm.FontProperties(family=fam, weight="bold" if w in ("b", "xb", "sb") else "normal")
    return _FP[w]


SCALE = 2  # 2배로 그린 뒤 줄임
BODY_W = 880  # 본문 그래픽 폭: 휴대폰에서 글자가 너무 작아지지 않게


class Canvas:
    def __init__(self, w, h, bg=None):
        self.w, self.h = w, h
        self.fig = plt.figure(figsize=(w / 100, h / 100), dpi=100)
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, w)
        self.ax.set_ylim(h, 0)
        self.ax.axis("off")
        self.rect(0, 0, w, h, bg or C["bg"], r=0)

    # 크기는 픽셀 단위로 받는다
    def text(self, x, y, s, px=28, w="r", color=None, ha="left", va="top", **kw):
        return self.ax.text(x, y, s, fontproperties=font(w), fontsize=px * 0.72, color=color or C["text"],
                            ha=ha, va=va, linespacing=1.35, **kw)

    def rect(self, x, y, w, h, fc, r=24, ec=None, lw=0, z=1):
        self.ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0,rounding_size={r}",
                                         fc=fc, ec=ec or fc, lw=lw, zorder=z, mutation_aspect=1))

    def size(self, artist):
        """그려진 글자의 실제 폭·높이(px)."""
        bb = artist.get_window_extent(renderer=self.fig.canvas.get_renderer())
        return bb.width, bb.height

    def measure(self, s, px, w="r"):
        t = self.text(-9999, -9999, s, px, w)
        size = self.size(t)
        t.remove()
        return size

    def pill(self, x, y, s, px=22, fc=None, color=None, w="sb", pad=(18, 10), ha="left"):
        tw = self.measure(s, px, w)[0]
        bw, bh = tw + pad[0] * 2, px + pad[1] * 2
        x0 = x - bw if ha == "right" else (x - bw / 2 if ha == "center" else x)
        self.rect(x0, y, bw, bh, fc or C["blue_l"], r=bh / 2, z=2)
        self.text(x0 + bw / 2, y + bh / 2, s, px, w, color or C["blue"], ha="center", va="center", zorder=3)
        return bw, bh

    def footer(self, source=None, brand=True, y=None):
        y = y or self.h - 44
        if source:
            self.text(56, y, f"자료: {source}", 18, "r", C["muted"], va="center")
        if brand:
            self.ax.add_patch(Circle((self.w - 56 - self.measure(BRAND["name"], 20, "b")[0] - 18, y), 7, color=C["blue"], zorder=3))
            self.text(self.w - 56, y, BRAND["name"], 20, "b", C["sub"], ha="right", va="center")

    def inset(self, x, y, w, h):
        a = self.fig.add_axes([x / self.w, 1 - (y + h) / self.h, w / self.w, h / self.h])
        a.set_facecolor("none")
        for s in a.spines.values():
            s.set_visible(False)
        a.tick_params(length=0, colors=C["muted"])
        return a

    def save(self, path):
        path = Path(path)
        tmp = path.with_suffix(".tmp.png")
        self.fig.savefig(tmp, dpi=100 * SCALE)
        plt.close(self.fig)
        im = Image.open(tmp).convert("RGB").resize((self.w, self.h), Image.LANCZOS)
        tmp.unlink()
        if path.suffix.lower() == ".webp":
            im.save(path, "WEBP", quality=88, method=6)
        else:
            im.save(path)
        return path


def text_width(s, px, w="r"):
    """대략적인 글자 폭(px). 한글·숫자·영문 폭을 나눠 계산."""
    tot = 0
    for ch in s:
        if "가" <= ch <= "힣" or "ㄱ" <= ch <= "ㆎ":
            tot += 0.96
        elif ch == " ":
            tot += 0.28
        elif ch.isdigit() or ch in ",.%":
            tot += 0.58 if ch.isdigit() else 0.3
        else:
            tot += 0.55
    return tot * px * (1.04 if w in ("b", "xb") else 1)


def header(cv, title, sub=None, eyebrow=None, y=56):
    if eyebrow:
        _, bh = cv.pill(56, y, eyebrow, 20)
        y += bh + 20
    y += cv.size(cv.text(56, y, title, 46, "b"))[1] + 14
    if sub:
        y += cv.size(cv.text(56, y, sub, 24, "r", C["muted"]))[1]
    return y + 40


def header_h(s):
    """캔버스를 만들기 전에 헤더 높이를 미리 잰다."""
    cv = Canvas(BODY_W, 400)
    h = header(cv, s["title"], s.get("sub"), s.get("eyebrow"))
    plt.close(cv.fig)
    return h


def fmt(v, unit=""):
    if isinstance(v, str):
        return v
    s = f"{v:,.0f}" if float(v).is_integer() else f"{v:,.1f}"
    return s + unit


# ── 컴포넌트 ───────────────────────────────────────────────────
def thumbnail(s, out):
    """{title, highlight?, eyebrow?, badge?, number?:{value,label}, size:'wide'|'square'}"""
    sq = s.get("size") == "square"
    W, H = (1080, 1080) if sq else (1200, 630)
    cv = Canvas(W, H, C["card"])
    pad = 80 if sq else 72
    n = s.get("number")
    # 숫자 카드 크기를 먼저 정해서 제목이 쓸 폭을 계산
    if n:
        vpx = 64 if sq else 58
        cw = max(cv.measure(n["value"], vpx, "xb")[0], cv.measure(n["label"], 24, "sb")[0]) + 80
        ch = 190
        nx, ny = (pad, H - pad - ch) if sq else (W - pad - cw, H - pad - ch)
    avail = (W - pad * 2) if (sq or not n) else (W - pad * 2 - cw - 40)
    y = pad
    if s.get("eyebrow"):
        _, bh = cv.pill(pad, y, s["eyebrow"], 26 if sq else 24, fc=C["bg"])
        y += bh + (40 if sq else 32)
    lines = s["title"].split("\n")
    px = 92 if sq else 80
    while px > 40 and max(cv.measure(l, px, "xb")[0] for l in lines) > avail:
        px -= 2
    hl = s.get("highlight", "")
    for ln in lines:
        x = pad
        parts = ((ln.split(hl, 1)[0], C["text"]), (hl, C["blue"]), (ln.split(hl, 1)[1], C["text"])) \
            if hl and hl in ln else ((ln, C["text"]),)
        for part, col in parts:  # 한 줄 안에서 강조 단어만 파랑, 실제 폭으로 이어 붙임
            if part:
                t = cv.text(x, y, part, px, "xb", col)
                x += cv.size(t)[0]
        y += px * 1.28
    if n:
        cv.rect(nx, ny, cw if not sq else W - pad * 2, ch, C["bg"], r=32, z=2)
        cv.text(nx + 40, ny + 38, n["label"], 24, "sb", C["muted"], zorder=3)
        cv.text(nx + 40, ny + 84, n["value"], vpx, "xb", C.get(n.get("color", "blue"), C["blue"]), zorder=3)
    if s.get("badge"):
        cv.pill(pad, H - pad - 58, s["badge"], 28, fc=C["blue"], color="#FFFFFF", w="b", pad=(28, 15))
    cv.text(W - pad, pad + 4, BRAND["name"], 24, "b", C["muted"], ha="right")
    return cv.save(out)


def kpi(s, out):
    """{title, sub?, eyebrow?, cols?:2, items:[{label, value, delta?, dir?:'up'|'down'|'flat', note?}], source?}"""
    W = BODY_W
    items, cols = s["items"], s.get("cols", 2)
    rows = (len(items) + cols - 1) // cols
    ch, gap = 220, 20
    H = int(header_h(s) + rows * (ch + gap) + 90)
    cv = Canvas(W, H)
    y0 = header(cv, s["title"], s.get("sub"), s.get("eyebrow"))
    cw = (W - 112 - gap * (cols - 1)) / cols
    for i, it in enumerate(items):
        x = 56 + (i % cols) * (cw + gap)
        y = y0 + (i // cols) * (ch + gap)
        cv.rect(x, y, cw, ch, C["card"], r=28)
        cv.text(x + 32, y + 32, it["label"], 24, "sb", C["sub"], zorder=3)
        vpx = 56 if len(it["value"]) <= 9 else 44
        cv.text(x + 32, y + 78, it["value"], vpx, "xb", zorder=3)
        if it.get("delta"):
            d = it.get("dir", "up")
            col = {"up": C["up"], "down": C["down"]}.get(d, C["muted"])
            arrow = {"up": "▲ ", "down": "▼ "}.get(d, "")
            cv.text(x + 32, y + ch - 52, arrow + it["delta"], 24, "b", col, zorder=3)
        if it.get("note"):
            cv.text(x + cw - 32, y + ch - 52, it["note"], 20, "r", C["muted"], ha="right", zorder=3)
    cv.footer(s.get("source"))
    return cv.save(out)


def bars(s, out):
    """{title, sub?, items:[{label, value, display?}], highlight?:[idx]|'max'|'min', unit?, signed?:bool, source?}
    가로 막대. signed=True면 0 기준 좌우(상승 빨강/하락 파랑)."""
    W = BODY_W
    items = s["items"]
    rh = 84
    hy = header_h(s)
    H = int(hy + len(items) * rh + 100)
    cv = Canvas(W, H)
    y0 = header(cv, s["title"], s.get("sub"), s.get("eyebrow"))
    vals = [it["value"] for it in items]
    hl = s.get("highlight", [])
    if hl == "max":
        hl = [vals.index(max(vals))]
    elif hl == "min":
        hl = [vals.index(min(vals))]
    unit = s.get("unit", "")
    lx, bx0, bxw = 56, 330, W - 330 - 56 - 170
    if s.get("signed"):
        m = max(abs(v) for v in vals) or 1
        zero = bx0 + bxw / 2 + 60
        for i, it in enumerate(items):
            y = y0 + i * rh
            v = it["value"]
            cv.text(lx, y + rh / 2 - 6, it["label"], 28, "sb", va="center")
            w = (bxw / 2) * abs(v) / m
            col = C["up"] if v > 0 else C["down"]
            x = zero if v >= 0 else zero - w
            cv.rect(x, y + 14, max(w, 6), rh - 40, col, r=10, z=2)
            lab = it.get("display", f"{v:+,.2f}{unit}" if not float(v).is_integer() else f"{v:+,.0f}{unit}")
            cv.text(x + w + 14 if v >= 0 else x - 14, y + rh / 2 - 6, lab, 26, "b", col, ha="left" if v >= 0 else "right", va="center")
        cv.ax.plot([zero, zero], [y0 - 8, y0 + len(items) * rh - 14], color=C["line"], lw=2, zorder=1)
    else:
        m = max(vals) or 1
        for i, it in enumerate(items):
            y = y0 + i * rh
            on = (i in hl) or not hl
            cv.text(lx, y + rh / 2 - 6, it["label"], 28, "sb" if on else "m", C["text"] if on else C["sub"], va="center")
            cv.rect(bx0, y + 14, bxw, rh - 40, C["card"], r=10, z=1)
            w = bxw * it["value"] / m
            cv.rect(bx0, y + 14, max(w, 6), rh - 40, C["blue"] if (i in hl or not hl) else "#B0C9F3", r=10, z=2)
            cv.text(bx0 + bxw + 18, y + rh / 2 - 6, it.get("display", fmt(it["value"], unit)), 28,
                    "b" if on else "sb", C["blue"] if i in hl else C["text"], va="center")
    cv.footer(s.get("source"))
    return cv.save(out)


def trend(s, out):
    """{title, sub?, x:[...], series:[{name, values, color?}], unit?, area?:bool, source?, ymin?}"""
    W = BODY_W
    H = int(header_h(s) + 540)
    cv = Canvas(W, H)
    y0 = header(cv, s["title"], s.get("sub"), s.get("eyebrow"))
    a = cv.inset(56 + 10, y0 + 10, W - 112 - 150, H - y0 - 120)
    xs = list(range(len(s["x"])))
    unit = s.get("unit", "")
    allv = [v for se in s["series"] for v in se["values"] if v is not None]
    lo, hi = min(allv), max(allv)
    padv = (hi - lo) * 0.15 or 1
    small = (hi - lo) < 20  # 금리·지수처럼 범위가 좁으면 소수점 표시
    a.set_ylim(s.get("ymin", lo - padv), hi + padv)
    for k, se in enumerate(s["series"]):
        col = se.get("color") or PALETTE[k]
        col = C.get(col, col)
        a.plot(xs, se["values"], color=col, lw=4, solid_capstyle="round", zorder=3)
        if s.get("area", len(s["series"]) == 1):
            a.fill_between(xs, se["values"], a.get_ylim()[0], color=col, alpha=0.08, zorder=2)
        a.scatter([xs[-1]], [se["values"][-1]], s=140, color=col, zorder=4, edgecolors="white", linewidths=3)
        lab = f"{se['values'][-1]:,.2f}{unit}" if small else f"{fmt(se['values'][-1], unit)}"
        a.annotate(lab + (f"  {se['name']}" if len(s["series"]) > 1 else ""), (xs[-1], se["values"][-1]),
                   xytext=(14, se.get("label_dy", 0)), textcoords="offset points", va="center", fontproperties=font("b"),
                   fontsize=24 * 0.72, color=col, annotation_clip=False)
    a.grid(axis="y", color=C["line"], lw=1.5)
    a.set_axisbelow(True)
    step = max(1, len(xs) // 6)
    ticks = xs[::step]
    if xs[-1] % step:
        if xs[-1] - ticks[-1] < step * 0.6:  # 마지막 눈금과 너무 가까우면 겹치니 바꿔 끼움
            ticks = ticks[:-1]
        ticks = ticks + [xs[-1]]
    a.set_xticks(ticks)
    a.set_xticklabels([s["x"][i] for i in a.get_xticks()], fontproperties=font("m"), fontsize=18 * 0.72)
    for t in a.get_yticklabels():
        t.set_fontproperties(font("m"))
        t.set_fontsize(18 * 0.72)
    a.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(
        (lambda v, _: f"{v:,.2f}") if small else (lambda v, _: f"{v:,.0f}")))
    cv.footer(s.get("source"))
    return cv.save(out)


def checklist(s, out):
    """{title, sub?, rows:[[when, text]], highlight?:[idx], source?}"""
    W = BODY_W
    rows = s["rows"]
    rh, gap = 104, 14
    H = int(header_h(s) + len(rows) * (rh + gap) + 90)
    cv = Canvas(W, H)
    y0 = header(cv, s["title"], s.get("sub"), s.get("eyebrow"))
    hl = set(s.get("highlight", []))
    for i, (when, txt) in enumerate(rows):
        y = y0 + i * (rh + gap)
        on = i in hl
        cv.rect(56, y, W - 112, rh, C["blue_l"] if on else C["card"], r=24)
        cx = 56 + 52
        cv.ax.add_patch(Circle((cx, y + rh / 2), 18, fc=C["blue"] if on else C["bg"], ec=C["blue"] if on else C["line"],
                               lw=3, zorder=3))
        if on:
            cv.text(cx, y + rh / 2 + 1, "✓", 22, "b", "#FFFFFF", ha="center", va="center", zorder=4)
        cv.text(cx + 44, y + rh / 2, when, 24, "b", C["blue"] if on else C["sub"], va="center", zorder=3)
        cv.text(cx + 44 + 190, y + rh / 2, txt, 26, "sb" if on else "m", C["text"], va="center", zorder=3)
    cv.footer(s.get("source"))
    return cv.save(out)


def flow(s, out):
    """{title, sub?, question, yes:{tag, title, big, lines:[..]}, no:{...}, footer_note?, source?}"""
    W = BODY_W
    H = int(header_h(s) + 130 + 110 + 340 + (116 if s.get("footer_note") else 0) + 110)
    cv = Canvas(W, H)
    y0 = header(cv, s["title"], s.get("sub"), s.get("eyebrow"))
    qh = 130
    cv.rect(140, y0, W - 280, qh, C["navy"], r=28)
    cv.text(W / 2, y0 + qh / 2, s["question"], 32, "b", "#FFFFFF", ha="center", va="center", zorder=3)
    by = y0 + qh + 110
    bw, bh = (W - 112 - 24) / 2, 340
    for k, key in enumerate(("yes", "no")):
        b = s[key]
        x = 56 + k * (bw + 24)
        good = b.get("tone", "good" if key == "yes" else "bad") == "good"
        fc, col = (C["blue_l"], C["blue"]) if good else (C["card"], C["sub"])
        sx = W / 2 + (-1 if k == 0 else 1) * 120
        cv.ax.annotate("", xy=(x + bw / 2, by - 64), xytext=(sx, y0 + qh + 6),
                       arrowprops=dict(arrowstyle="-|>", color="#C5CBD3", lw=4, mutation_scale=28))
        cv.pill(x + bw / 2, by - 58, b["tag"], 22, fc=col, color="#FFFFFF", w="b", ha="center")
        cv.rect(x, by, bw, bh, fc, r=32)
        cv.text(x + 40, by + 40, b["title"], 28, "b", col, zorder=3)
        cv.text(x + 40, by + 90, b["big"], 52, "xb", C["text"] if good else C["sub"], zorder=3)
        for j, ln in enumerate(b.get("lines", [])):
            cv.text(x + 40, by + 190 + j * 42, ln, 22, "m", C["sub"], zorder=3)
    if s.get("footer_note"):
        fy = by + bh + 32
        cv.rect(56, fy, W - 112, 84, C["yellow_l"], r=22)
        cv.text(W / 2, fy + 42, s["footer_note"], 24, "sb", C["text"], ha="center", va="center", zorder=3)
    cv.footer(s.get("source"))
    return cv.save(out)


def table(s, out):
    """{title, sub?, header:[..], rows:[[..]], highlight_col?:int, highlight_row?:int, source?}"""
    W = BODY_W
    rows = s["rows"]
    rh = 92
    H = int(header_h(s) + (len(rows) + 1) * rh + 110)
    cv = Canvas(W, H)
    y0 = header(cv, s["title"], s.get("sub"), s.get("eyebrow"))
    n = len(s["header"])
    first = 0.34 if n > 2 else 0.5
    cws = [(W - 112) * first] + [(W - 112) * (1 - first) / (n - 1)] * (n - 1)
    xs = [56]
    for w in cws[:-1]:
        xs.append(xs[-1] + w)
    hc, hr = s.get("highlight_col"), s.get("highlight_row")
    if hc is not None:
        cv.rect(xs[hc] + 6, y0 - 6, cws[hc] - 12, (len(rows) + 1) * rh + 12, C["blue_l"], r=24, z=1)
    for j, h in enumerate(s["header"]):
        cv.text(xs[j] + (24 if j == 0 else cws[j] / 2), y0 + rh / 2, h, 22, "b",
                C["blue"] if j == hc else C["muted"], ha="left" if j == 0 else "center", va="center", zorder=3)
    for i, r in enumerate(rows):
        y = y0 + (i + 1) * rh
        cv.ax.plot([56, W - 56], [y, y], color=C["line"], lw=1.5, zorder=2)
        if i == hr:
            cv.rect(56, y + 6, W - 112, rh - 12, C["yellow_l"], r=18, z=1)
        for j, cell in enumerate(r):
            cv.text(xs[j] + (24 if j == 0 else cws[j] / 2), y + rh / 2, str(cell), 26 if j == 0 else 27,
                    "sb" if j == 0 else ("b" if j == hc else "m"), C["blue"] if j == hc else C["text"],
                    ha="left" if j == 0 else "center", va="center", zorder=3)
    cv.footer(s.get("source"))
    return cv.save(out)


def donut(s, out):
    """{title, sub?, items:[{label, value}], center:{value, label}, unit?, source?} 구성비(합이 전체)."""
    W = BODY_W
    H = int(header_h(s) + 560)
    cv = Canvas(W, H)
    y0 = header(cv, s["title"], s.get("sub"), s.get("eyebrow"))
    items = s["items"]
    tot = sum(i["value"] for i in items)
    cols = PALETTE if len(items) > 2 else [C["blue"], "#D1D6DB"]  # 둘이면 강조 1색 + 회색
    cx, cy, r = int(W * 0.27), y0 + 230, 196
    ang = 90
    for k, it in enumerate(items):
        sweep = 360 * it["value"] / tot
        cv.ax.add_patch(Wedge((cx, cy), r, ang - sweep, ang, width=70, fc=cols[k % len(cols)], ec="white", lw=6, zorder=2))
        ang -= sweep
    if s.get("center"):
        cv.text(cx, cy - 26, s["center"]["value"], 46, "xb", ha="center", va="center", zorder=3)
        cv.text(cx, cy + 30, s["center"]["label"], 22, "m", C["muted"], ha="center", va="center", zorder=3)
    lx = int(W * 0.54)
    unit = s.get("unit", "")
    for k, it in enumerate(items):
        y = y0 + 70 + k * 86
        cv.ax.add_patch(Circle((lx + 12, y), 12, color=cols[k % len(cols)], zorder=3))
        cv.text(lx + 40, y, it["label"], 26, "sb", va="center")
        cv.text(W - 56, y, f"{it['value'] / tot * 100:.0f}%" if not unit else fmt(it["value"], unit), 28, "b",
                C["sub"], ha="right", va="center")
    cv.footer(s.get("source"))
    return cv.save(out)


COMPONENTS = {"thumbnail": thumbnail, "kpi": kpi, "bars": bars, "trend": trend, "checklist": checklist,
              "flow": flow, "table": table, "donut": donut}


def slug(s):
    return re.sub(r"[^\w가-힣]+", "-", s).strip("-")[:60]


def render(spec, out_dir, name=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fn = COMPONENTS[spec["type"]]
    name = name or spec.get("file") or slug(spec.get("title", spec["type"]).replace("\n", " "))
    return fn(spec, out_dir / f"{name}.webp")


def render_spec(path, out_dir):
    """{"post": "글 슬러그", "source": "공통 출처", "graphics": [ {type,...}, ... ]}"""
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    outs = []
    for i, g in enumerate(doc["graphics"], 1):
        g.setdefault("source", doc.get("source"))
        name = g.get("file") or f"{doc.get('post', 'post')}-{i:02d}-{g['type']}"
        outs.append((render(g, out_dir, name), g.get("alt", "")))
    return outs
