"""[GitHub Actions 에서 자동 실행] posts/ 폴더의 새 글을 블로거에 올린다. 추가 설치 없이 표준 라이브러리만 사용.

글 폴더 구조 (예: posts/2026-11-16-year-end-tax/)
  post.html   본문 (블로거 'HTML 보기'에 들어갈 내용, 이미지는 같은 폴더 파일명으로)
  meta.json   {"title": "...", "labels": ["절세", ...], "mode": "draft" | "schedule" | "publish",
               "at": "2026-11-17 08:00"   ← mode 가 schedule 일 때 한국시간}
  *.webp      그래픽 (moneygraph 결과물)
올리고 나면 posted.json 이 생기고, 다음부터는 건너뛴다.

필요한 환경 변수 (GitHub Secrets): BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET, BLOGGER_REFRESH_TOKEN, BLOGGER_BLOG_ID
사진 주소: 공개 저장소의 raw.githubusercontent.com 주소로 바꿔 넣는다 (GITHUB_REPOSITORY, GITHUB_REF_NAME 자동 제공).

로컬 확인:  python blogger/publish.py --dry-run      (블로거에 보내지 않고 변환 결과만 출력)
"""
import argparse
import json
import time
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
ROOT = Path(__file__).resolve().parents[1]
API = "https://www.googleapis.com/blogger/v3"


def http(method, url, data=None, token=None, form=False):
    headers = {}
    body = None
    if form:
        body = urllib.parse.urlencode(data).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    elif data is not None:
        body = json.dumps(data).encode()
        headers["Content-Type"] = "application/json; charset=utf-8"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        msg = e.read().decode(errors="replace")[:500]
        if e.code in (429, 500, 503):
            raise RateLimited(f"{e.code}: {msg[:200]}")
        sys.exit(f"블로거 API 오류 {e.code}: {msg}")


class RateLimited(Exception):
    pass


def call(*args, tries=4):
    """요청 한도(429)에 걸리면 30초·60초·120초 쉬었다가 다시 시도."""
    for k in range(tries):
        try:
            return http(*args)
        except RateLimited as e:
            if k == tries - 1:
                raise
            wait = 30 * 2 ** k
            print(f"  … 요청 한도, {wait}초 쉬고 다시 시도 ({e})")
            time.sleep(wait)


def access_token():
    need = ["BLOGGER_CLIENT_ID", "BLOGGER_CLIENT_SECRET", "BLOGGER_REFRESH_TOKEN"]
    miss = [k for k in need if not os.environ.get(k, "").strip()]
    if miss:
        sys.exit(f"GitHub Secrets 에 없음: {', '.join(miss)}")
    r = http("POST", "https://oauth2.googleapis.com/token", {
        "client_id": os.environ["BLOGGER_CLIENT_ID"].strip().strip("\"'"),
        "client_secret": os.environ["BLOGGER_CLIENT_SECRET"].strip().strip("\"'"),
        "refresh_token": os.environ["BLOGGER_REFRESH_TOKEN"].strip().strip("\"'"),
        "grant_type": "refresh_token"}, form=True)
    return r["access_token"]


def image_base(folder):
    repo, ref = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_REF_NAME", "main")
    if not repo:
        return None
    rel = folder.relative_to(ROOT).as_posix()
    return f"https://raw.githubusercontent.com/{repo}/{ref}/{urllib.parse.quote(rel)}/"


def build_body(folder):
    html = (folder / "post.html").read_text(encoding="utf-8")
    html = re.sub(r"<!--.*?-->", "", html, flags=re.S).strip()
    base = image_base(folder)

    def fix(m):
        src = m.group(2)
        if src.startswith(("http://", "https://", "data:")):
            return m.group(0)
        if not (folder / src).exists():
            print(f"  ! 이미지 파일 없음: {src}")
        return f'{m.group(1)}{(base or "") + urllib.parse.quote(src)}{m.group(3)}'

    html = re.sub(r'(<img[^>]*?\ssrc=")([^"]+)(")', fix, html)
    # 편집기·RSS처럼 테마 CSS가 없는 곳에서도 폭에 맞게
    return re.sub(r'<img(?![^>]*\sstyle=)', '<img style="max-width:100%;height:auto;display:block;margin:8px auto"', html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="이 폴더 이름만 처리")
    a = ap.parse_args()

    folders = sorted(p.parent for p in (ROOT / "posts").glob("*/meta.json"))
    if a.only:
        folders = [f for f in folders if f.name == a.only]
    todo = [f for f in folders if not (f / "posted.json").exists()]
    # 임시저장으로 올렸던 글의 meta.json mode 를 publish/schedule 로 바꾸면 그 글을 공개 처리
    promote = []
    for f in folders:
        pj = f / "posted.json"
        if pj.exists():
            rec = json.loads(pj.read_text(encoding="utf-8"))
            mode = json.loads((f / "meta.json").read_text(encoding="utf-8")).get("mode", "draft")
            if rec.get("mode") == "draft" and mode in ("publish", "schedule"):
                promote.append((f, rec, mode))
    if not todo and not promote:
        print("새 글 없음")
        return
    token = None if a.dry_run else access_token()
    blog_id = os.environ.get("BLOGGER_BLOG_ID", "DRY-RUN").strip()
    if not a.dry_run and blog_id == "DRY-RUN":
        sys.exit("GitHub Secrets 에 없음: BLOGGER_BLOG_ID")

    for n, (f, rec, mode) in enumerate(promote):
        meta = json.loads((f / "meta.json").read_text(encoding="utf-8"))
        print(f"- {f.name}: 임시저장 → {mode}")
        if a.dry_run:
            continue
        if n:
            time.sleep(10)
        q = ""
        if mode == "schedule":
            when = datetime.strptime(meta["at"], "%Y-%m-%d %H:%M").replace(tzinfo=KST).isoformat()
            q = "?publishDate=" + urllib.parse.quote(when)
        try:
            res = call("POST", f"{API}/blogs/{blog_id}/posts/{rec['id']}/publish{q}", {}, token)
        except RateLimited:
            print("요청 한도가 풀리지 않아 멈춤. 나머지는 다음 실행 때 이어서 합니다.")
            return
        print(f"  → 완료 {res.get('url', '')}")
        rec.update({"mode": mode, "url": res.get("url", rec.get("url")),
                    "at": datetime.now(KST).isoformat(timespec="minutes")})
        (f / "posted.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1), encoding="utf-8")

    for n, f in enumerate(todo):
        if n and not a.dry_run:
            time.sleep(15)  # 블로거 API 요청 한도 여유
        meta = json.loads((f / "meta.json").read_text(encoding="utf-8"))
        mode = meta.get("mode", "draft")
        post = {"kind": "blogger#post", "title": meta["title"], "content": build_body(f),
                "labels": meta.get("labels", [])[:20]}
        print(f"- {f.name}: {meta['title']} ({mode})")
        if a.dry_run:
            print(f"  본문 {len(post['content']):,}자, 이미지 {post['content'].count('<img')}개, 라벨 {post['labels']}")
            continue
        try:
            res = call("POST", f"{API}/blogs/{blog_id}/posts?isDraft=true", post, token)
        except RateLimited:
            left = len(todo) - n
            print(f"요청 한도가 풀리지 않아 멈춤. 남은 {left}개는 다음 실행 때 이어서 올립니다.")
            return
        if mode == "schedule":
            when = datetime.strptime(meta["at"], "%Y-%m-%d %H:%M").replace(tzinfo=KST).isoformat()
            res = call("POST", f"{API}/blogs/{blog_id}/posts/{res['id']}/publish?publishDate={urllib.parse.quote(when)}", {}, token)
        elif mode == "publish":
            res = call("POST", f"{API}/blogs/{blog_id}/posts/{res['id']}/publish", {}, token)
        state = {"draft": "임시저장", "schedule": f"예약 {meta.get('at')}", "publish": "발행"}[mode]
        print(f"  → {state} 완료 (id {res['id']}) {res.get('url', '')}")
        (f / "posted.json").write_text(json.dumps({"id": res["id"], "url": res.get("url"), "mode": mode,
                                                   "at": datetime.now(KST).isoformat(timespec='minutes')},
                                                  ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
