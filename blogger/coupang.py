"""쿠팡 파트너스 공식 API로 글 주제에 맞는 상품을 찾아 '내 파트너스 링크' 카드로 만든다.

- 키는 GitHub Secrets 의 COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY 에서만 읽는다.
- tools/coupang.json 의 enabled 가 false 면 아무것도 넣지 않는다 (지금 기본값).
- API 오류가 나도 글 게시는 막지 않는다 (상품 카드만 빠짐).

테스트:  python blogger/coupang.py --test "주식 투자 책"
"""
import hashlib
import hmac
import html
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "tools" / "coupang.json"
HOST = "https://api-gateway.coupang.com"
SEARCH = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"


def conf():
    return json.loads(CONF.read_text(encoding="utf-8"))


def keys():
    a = os.environ.get("COUPANG_ACCESS_KEY", "").strip()
    s = os.environ.get("COUPANG_SECRET_KEY", "").strip()
    return (a, s) if a and s else (None, None)


def _auth(method, path, query, ak, sk):
    dt = time.strftime("%y%m%dT%H%M%SZ", time.gmtime())
    msg = dt + method + path + query
    sig = hmac.new(sk.encode(), msg.encode(), hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ak}, signed-date={dt}, signature={sig}"


def search(keyword, limit=10):
    ak, sk = keys()
    if not ak:
        raise RuntimeError("COUPANG_ACCESS_KEY / COUPANG_SECRET_KEY 없음")
    query = urllib.parse.urlencode({"keyword": keyword, "limit": limit, "imageSize": "230x230"})
    req = urllib.request.Request(f"{HOST}{SEARCH}?{query}",
                                 headers={"Authorization": _auth("GET", SEARCH, query, ak, sk),
                                          "Content-Type": "application/json;charset=UTF-8"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"쿠팡 API {e.code}: {e.read().decode(errors='replace')[:300]}")
    if str(data.get("rCode")) != "0":
        raise RuntimeError(f"쿠팡 API 응답 오류: {data.get('rMessage')}")
    return (data.get("data") or {}).get("productData") or []


def pick(products, c):
    bad = [w.lower() for w in c.get("exclude_words", [])]
    good = [p for p in products if not any(w in p.get("productName", "").lower() for w in bad)]
    return good[: c.get("max_items", 2)]


def card_html(items, keyword):
    rows = []
    for p in items:
        name = html.escape(p["productName"])
        price = f'{int(p["productPrice"]):,}원' if p.get("productPrice") else ""
        rows.append(
            f'<a class="mg-shop-item" href="{html.escape(p["productUrl"])}" target="_blank" rel="sponsored noopener" '
            f'style="display:flex;gap:14px;align-items:center;padding:12px;border-radius:14px;background:#fff;text-decoration:none;color:#191F28">'
            f'<img src="{html.escape(p["productImage"])}" alt="{name}" loading="lazy" '
            f'style="width:72px;height:72px;object-fit:cover;border-radius:10px;margin:0;flex:none">'
            f'<span style="display:block;font-size:15px;font-weight:600;line-height:1.5">{name}'
            f'<b style="display:block;color:#3182F6;margin-top:4px">{price}</b></span></a>')
    return ('<div class="mg-shop" style="background:#F2F4F6;border-radius:18px;padding:18px;margin:32px 0;display:grid;gap:10px">'
            f'<div style="font-size:14px;font-weight:700;color:#4E5968">📚 이 글과 함께 보면 좋은 책</div>'
            + "".join(rows) + "</div>")


def disclosure_html(c):
    return ('<p class="mg-disclosure" style="font-size:13px;color:#8B95A1;margin:0 0 16px">'
            + html.escape(c["disclosure"]) + "</p>")


def keyword_for(meta, c):
    if meta.get("coupang") is False:
        return None
    kw = (meta.get("coupang") or {}).get("keyword") if isinstance(meta.get("coupang"), dict) else None
    if kw:
        return kw
    first = (meta.get("labels") or [""])[0]
    pool = c.get("keywords", {}).get(first)
    return random.choice(pool) if pool else None


def apply(body, meta):
    """게시 직전 본문에 상품 카드·대가성 문구를 넣는다. 꺼져 있거나 실패하면 본문 그대로."""
    try:
        c = conf()
    except FileNotFoundError:
        return body
    if not c.get("enabled") or not keys()[0]:
        return body
    kw = keyword_for(meta, c)
    if not kw:
        return body
    try:
        items = pick(search(kw), c)
    except Exception as e:  # 쿠팡 쪽 문제로 글 게시를 막지 않음
        print(f"  ! 쿠팡 상품 건너뜀: {e}")
        return body
    if not items:
        return body
    block = card_html(items, kw)
    i = body.find('<h2 id="faq">')
    body = body[:i] + block + "\n" + body[i:] if i >= 0 else body + "\n" + block
    j = body.find("</figure>")  # 첫 그림(썸네일) 바로 아래에 대가성 문구
    body = body[: j + 9] + "\n" + disclosure_html(c) + body[j + 9:] if j >= 0 else disclosure_html(c) + body
    print(f"  + 쿠팡 상품 {len(items)}개 ('{kw}')")
    return body


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--test":
        kw = sys.argv[2]
        try:
            ps = search(kw, 5)
        except Exception as e:
            sys.exit(f"실패: {e}")
        print(f"키 정상 · '{kw}' 검색 결과 {len(ps)}개")
        for p in ps:
            link = p.get("productUrl", "")
            print(f"- {p.get('productName')[:40]} | {p.get('productPrice')}원 | 파트너스 링크: "
                  f"{'예' if 'link.coupang.com' in link else '확인 필요'}")
    else:
        print(__doc__)
