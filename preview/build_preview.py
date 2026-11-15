"""테마 모양 확인용 정적 미리보기 (블로거 없이 로컬에서). 실제 블로그와 같은 클래스·CSS 사용."""
import re, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from moneygraph.core import thumbnail
R = Path(__file__).resolve().parents[1]; P = R / "preview"; IMG = P / "img"; IMG.mkdir(exist_ok=True)
for f in (R / "out/sample").glob("*.webp"): shutil.copy(f, IMG / f.name)
demo = [("부업", "직장인 부업 소득\n신고 기준 총정리", "신고 기준"), ("재테크", "연금저축 vs IRP\n뭐부터 채울까", "뭐부터"),
        ("부업", "앱테크 한 달 해보니\n솔직 후기", "솔직 후기"), ("시황", "나스닥이 빠진 날\n3줄 정리", "3줄 정리"),
        ("재테크", "ISA 만기 됐다면\n이렇게 굴리세요", "이렇게")]
for i, (lab, t, hl) in enumerate(demo):
    thumbnail({"title": t, "highlight": hl, "eyebrow": lab}, IMG / f"demo{i}.webp")
css = (R / "theme/style.css").read_text(encoding="utf-8")
fonts = "".join(f"@font-face{{font-family:Pretendard;font-weight:{w};src:url('../moneygraph/fonts/Pretendard-{n}.otf')}}"
                for w, n in ((400, "Regular"), (500, "Medium"), (600, "SemiBold"), (700, "Bold"), (800, "ExtraBold")))
def page(body):
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>한눈머니 미리보기</title><style>{fonts}{css}</style></head><body>
<header class="top"><div class="wrap"><a class="logo" href="home.html"><i>₩</i>한눈머니</a><nav class="nav"><a class="on">재테크</a><a>부업</a><a>절세</a><a>시황</a></nav></div><div class="progress" style="width:35%"></div></header>
<main class="wrap">{body}</main><footer class="foot"><div class="wrap"><span>© 한눈머니 · 투자 판단의 책임은 본인에게 있습니다.</span><span><a>소개</a><a>개인정보처리방침</a><a>문의</a></span></div></footer></body></html>"""
cards = [("절세", "2026 연말정산 미리보기｜12월 31일 전에 해야 환급 늘어나는 5가지", "연말정산 환급액은 1월이 아니라 12월 31일에 거의 정해집니다. 연금저축·IRP, 카드, 고향사랑기부까지 남은 기간에 할 일을 정리했어요.", "2026-연말정산-12월31일-썸네일.webp", " is-featured")]
cards += [(lab, t.replace("\n", " "), "그래프와 표로 3분 안에 정리한 핵심만 담았습니다.", f"demo{i}.webp", "") for i, (lab, t, _) in enumerate(demo)]
grid = "".join(f'<a class="card{c}" href="post.html"><div class="thumb"><img src="img/{im}"></div><div class="txt"><div class="lab">{lab}</div><h3>{t}</h3><p>{d}</p><time>2026. 11. {15 - i}.</time></div></a>' for i, (lab, t, d, im, c) in enumerate(cards))
home = f"""<section class="hero"><h1>어려운 돈 이야기,<br><b>숫자 하나</b>로 정리합니다</h1><p>재테크·부업·절세를 그래프와 표로 3분 안에.</p>
<div class="chips"><a>🧾 연말정산</a><a>🏦 연금저축·IRP</a><a>💼 직장인 부업</a><a>📱 앱테크</a></div></section><div class="section-title"><h2>최신 글</h2></div><div class="grid">{grid}</div><div class="pager"><a>이전 글 →</a></div>"""
(P / "home.html").write_text(page(home), encoding="utf-8")
body = (R / "samples/post-2026-연말정산.html").read_text(encoding="utf-8")
body = re.sub(r"<!--.*?-->", "", body, flags=re.S)
body = re.sub(r'src="([^"]+\.webp)"', r'src="img/\1"', body)
body = body.replace("<details>", "<details open>", 2)
post = f"""<article class="post"><a class="crumb">절세</a><h1>2026 연말정산 미리보기｜12월 31일 전에 해야 환급 늘어나는 5가지</h1>
<div class="meta"><span>한눈머니</span><span class="dot"></span><time>2026. 11. 15.</time></div><div class="post-body">{body}</div>
<div class="post-labels"><a>#절세</a><a>#연말정산</a><a>#연금저축</a></div></article>
<section class="related"><h2>같은 주제 다른 글</h2><div class="grid">{"".join(f'<a class="card"><div class="thumb"><img src="img/demo{i}.webp"></div><h3>{demo[i][1].replace(chr(10)," ")}</h3></a>' for i in (1,4))}</div></section>"""
(P / "post.html").write_text(page(post), encoding="utf-8")
print("ok")
