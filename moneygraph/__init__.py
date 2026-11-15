"""moneygraph — 토스·뱅크샐러드 톤의 금융 블로그 그래픽 키트.

JSON 스펙 하나로 썸네일·KPI 카드·막대·추이선·체크리스트·흐름도·표·도넛을 같은 스타일로 만든다.
    python -m moneygraph samples/year_end_tax.json --out out/
"""
from .core import BRAND, render, render_spec  # noqa: F401
