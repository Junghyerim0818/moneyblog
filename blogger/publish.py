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
        sys.exit(f"블로거 API 오류 {e.code}: {msg}")


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

    return re.sub(r'(<img[^>]*?\ssrc=")([^"]+)(")', fix, html)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only", help="이 폴더 이름만 처리")
    a = ap.parse_args()

    folders = sorted(p.parent for p in (ROOT / "posts").glob("*/meta.json"))
    if a.only:
        folders = [f for f in folders if f.name == a.only]
    todo = [f for f in folders if not (f / "posted.json").exists()]
    if not todo:
        print("새 글 없음")
        return
    token = None if a.dry_run else access_token()
    blog_id = os.environ.get("BLOGGER_BLOG_ID", "DRY-RUN").strip()
    if not a.dry_run and blog_id == "DRY-RUN":
        sys.exit("GitHub Secrets 에 없음: BLOGGER_BLOG_ID")

    for f in todo:
        meta = json.loads((f / "meta.json").read_text(encoding="utf-8"))
        mode = meta.get("mode", "draft")
        post = {"kind": "blogger#post", "title": meta["title"], "content": build_body(f),
                "labels": meta.get("labels", [])[:20]}
        print(f"- {f.name}: {meta['title']} ({mode})")
        if a.dry_run:
            print(f"  본문 {len(post['content']):,}자, 이미지 {post['content'].count('<img')}개, 라벨 {post['labels']}")
            continue
        res = http("POST", f"{API}/blogs/{blog_id}/posts?isDraft=true", post, token)
        if mode == "schedule":
            when = datetime.strptime(meta["at"], "%Y-%m-%d %H:%M").replace(tzinfo=KST).isoformat()
            res = http("POST", f"{API}/blogs/{blog_id}/posts/{res['id']}/publish?publishDate={urllib.parse.quote(when)}", {}, token)
        elif mode == "publish":
            res = http("POST", f"{API}/blogs/{blog_id}/posts/{res['id']}/publish", {}, token)
        state = {"draft": "임시저장", "schedule": f"예약 {meta.get('at')}", "publish": "발행"}[mode]
        print(f"  → {state} 완료 (id {res['id']}) {res.get('url', '')}")
        (f / "posted.json").write_text(json.dumps({"id": res["id"], "url": res.get("url"), "mode": mode,
                                                   "at": datetime.now(KST).isoformat(timespec='minutes')},
                                                  ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
