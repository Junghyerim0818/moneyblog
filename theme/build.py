"""style.css 를 theme.template.xml 에 넣어 블로거에 올릴 theme.xml 을 만든다.
    python theme/build.py
"""
from pathlib import Path
import xml.dom.minidom

HERE = Path(__file__).resolve().parent
css = (HERE / "style.css").read_text(encoding="utf-8")
assert "]]>" not in css
import re

# 블로거는 저장할 때 한글·기호를 &#번호; 로 바꿔 버려서 CSS content·JS 문자열이 깨진다 → 미리 이스케이프
def css_escape(t):
    return "".join(c if ord(c) < 128 else f"\\{ord(c):x} " for c in t)


def js_escape(t):
    out = []
    for c in t:
        o = ord(c)
        if o < 128:
            out.append(c)
        elif o <= 0xFFFF:
            out.append(f"\\u{o:04x}")
        else:
            o -= 0x10000
            out.append(f"\\u{0xD800 + (o >> 10):04x}\\u{0xDC00 + (o & 0x3FF):04x}")
    return "".join(out)


css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)  # 주석 제거
tpl = (HERE / "theme.template.xml").read_text(encoding="utf-8")
tpl = re.sub(r"(<script>//<!\[CDATA\[)(.*?)(//\]\]></script>)", lambda m: m.group(1) + js_escape(m.group(2)) + m.group(3), tpl, flags=re.S)
xml_text = tpl.replace("/*{{CSS}}*/", css_escape(css))
xml.dom.minidom.parseString(xml_text.encode("utf-8"))  # XML 문법 검사 (블로거 업로드 전 1차 확인)
(HERE / "theme.xml").write_text(xml_text, encoding="utf-8")
print("theme.xml 생성 + XML 문법 통과:", HERE / "theme.xml")
