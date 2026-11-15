"""style.css 를 theme.template.xml 에 넣어 블로거에 올릴 theme.xml 을 만든다.
    python theme/build.py
"""
from pathlib import Path
import xml.dom.minidom

HERE = Path(__file__).resolve().parent
css = (HERE / "style.css").read_text(encoding="utf-8")
assert "]]>" not in css
xml_text = (HERE / "theme.template.xml").read_text(encoding="utf-8").replace("/*{{CSS}}*/", css)
xml.dom.minidom.parseString(xml_text.encode("utf-8"))  # XML 문법 검사 (블로거 업로드 전 1차 확인)
(HERE / "theme.xml").write_text(xml_text, encoding="utf-8")
print("theme.xml 생성 + XML 문법 통과:", HERE / "theme.xml")
