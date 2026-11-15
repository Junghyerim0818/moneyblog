"""[처음 한 번, 내 PC에서] 블로거 게시용 열쇠(refresh token)를 받는다.

    pip install google-auth-oauthlib
    python blogger/get_token.py client_secret.json

브라우저가 열리면 블로그를 운영하는 구글 계정으로 로그인 → '확인되지 않은 앱' 화면이 나오면
'고급' → '(앱 이름)(으)로 이동' → 블로거 권한 허용.
끝나면 GitHub Secrets 에 넣을 값 3개가 화면에 나온다. 이 값은 대화창·메신저 등에 붙여넣지 말 것.
"""
import json
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    sys.exit("먼저 실행: pip install google-auth-oauthlib")

if len(sys.argv) < 2 or not Path(sys.argv[1]).exists():
    sys.exit("사용법: python blogger/get_token.py <다운로드한 client_secret.json 경로>")

secret_file = sys.argv[1]
flow = InstalledAppFlow.from_client_secrets_file(secret_file, ["https://www.googleapis.com/auth/blogger"])
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
if not creds.refresh_token:
    sys.exit("refresh token 을 받지 못했습니다. https://myaccount.google.com/permissions 에서 앱 권한을 지우고 다시 실행하세요.")

info = json.loads(Path(secret_file).read_text(encoding="utf-8"))
info = info.get("installed") or info.get("web")
print("\n아래 3개를 GitHub 저장소 → Settings → Secrets and variables → Actions → New repository secret 에 각각 저장하세요.\n")
print(f"  BLOGGER_CLIENT_ID      = {info['client_id']}")
print(f"  BLOGGER_CLIENT_SECRET  = {info['client_secret']}")
print(f"  BLOGGER_REFRESH_TOKEN  = {creds.refresh_token}")
print("\n(네 번째 BLOGGER_BLOG_ID 는 블로거 관리 화면 주소의 숫자입니다.)")
