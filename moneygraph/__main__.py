import argparse
import json
from pathlib import Path

from .core import render_spec

ap = argparse.ArgumentParser(prog="moneygraph", description="JSON 스펙 → 블로그 그래픽(webp)")
ap.add_argument("spec", help="그래픽 스펙 JSON")
ap.add_argument("--out", default="out", help="저장 폴더")
a = ap.parse_args()

outs = render_spec(a.spec, a.out)
snippets = []
for p, alt in outs:
    print(f"{p}  ({Path(p).stat().st_size // 1024}KB)")
    snippets.append(f'<!-- 사진: {Path(p).name} | alt: {alt} -->')
(Path(a.out) / "alt.txt").write_text("\n".join(snippets), encoding="utf-8")
print(f"\nalt 문구: {Path(a.out) / 'alt.txt'}")
