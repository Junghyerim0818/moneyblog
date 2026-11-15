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
