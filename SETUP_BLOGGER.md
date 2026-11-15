# 블로거 자동 게시 설정 (처음 한 번)

흐름: **글 폴더를 GitHub에 올림 → GitHub Actions가 블로거 API로 임시저장/예약/발행 → 블로거 앱에서 확인**
컴퓨터가 꺼져 있어도 돌아갑니다. 계정 열쇠는 GitHub Secrets에만 저장됩니다.

## 1단계. 블로거 블로그 만들기
1. https://www.blogger.com → 새 블로그 (이름·주소 정하기)
2. 테마 → ▾ → 백업 후 → 복원 → `theme/theme.xml` 업로드
3. 관리 화면 주소창의 숫자를 적어 두기: `blogger.com/blog/posts/`**`1234567890123456789`** ← 이게 BLOG ID

## 2단계. 구글 클라우드에서 블로거 API 켜기
1. https://console.cloud.google.com → 위쪽 프로젝트 선택 → **새 프로젝트** (이름 예: `moneyblog`)
2. 왼쪽 메뉴 **API 및 서비스 → 라이브러리** → `Blogger API v3` 검색 → **사용**
3. 왼쪽 메뉴 **Google 인증 플랫폼(Google Auth Platform)** → **시작하기**
   - 앱 정보: 앱 이름 아무거나, 지원 이메일 = 본인 Gmail
   - 대상(Audience): **외부(External)**
   - 연락처: 본인 Gmail → 동의 → 만들기
4. **클라이언트(Clients) → 클라이언트 만들기** → 애플리케이션 유형 **데스크톱 앱** → 만들기 → **JSON 다운로드**
   (파일 이름을 `client_secret.json` 으로 바꿔 두면 편함. 절대 GitHub에 올리지 말 것)
5. **대상(Audience)** → 게시 상태에서 **앱 게시(Publish app)** → 프로덕션으로 변경
   - 이걸 안 하면 '테스트' 상태라 열쇠가 **7일마다 만료**됩니다.
   - 구글 검수는 받지 않아도 됩니다. 본인만 쓰는 앱이라 로그인할 때 '확인되지 않은 앱' 경고만 뜹니다.

## 3단계. 내 PC에서 열쇠 받기 (5분)
```bash
pip install google-auth-oauthlib
python blogger/get_token.py client_secret.json
```
- 브라우저가 열리면 **블로그를 만든 구글 계정**으로 로그인
- '확인되지 않은 앱' → **고급** → **(앱 이름)(으)로 이동** → 블로거 권한 **허용**
- 터미널에 `BLOGGER_CLIENT_ID`, `BLOGGER_CLIENT_SECRET`, `BLOGGER_REFRESH_TOKEN` 3줄이 나옵니다.
- 이 값은 카톡·메일·Claude 대화창 등 어디에도 붙여넣지 말고 4단계 GitHub에만 넣으세요.

## 4단계. GitHub 저장소 만들고 비밀값 저장
1. GitHub → **New repository** → 이름 `moneyblog` → **Public** (사진을 블로그에서 불러오려면 공개여야 함. 기존 `salary` 저장소는 공개하지 말 것)
2. 이 폴더 전체(`.github` 폴더 포함)를 올리기. `client_secret.json` 은 `.gitignore` 로 자동 제외됨.
3. 저장소 **Settings → Secrets and variables → Actions → New repository secret** 에서 4개 저장

| 이름 | 값 |
|---|---|
| `BLOGGER_CLIENT_ID` | 3단계 출력값 |
| `BLOGGER_CLIENT_SECRET` | 3단계 출력값 |
| `BLOGGER_REFRESH_TOKEN` | 3단계 출력값 |
| `BLOGGER_BLOG_ID` | 1단계에서 적어 둔 숫자 |

4. **Settings → Actions → General → Workflow permissions** → **Read and write permissions** → Save

## 5단계. 시험 게시
1. 저장소 **Actions** 탭 → 왼쪽 **블로거 게시** → **Run workflow**
2. 1분쯤 뒤 블로거 관리 화면 **게시물**에 연말정산 예시 글이 **임시저장**으로 들어와 있으면 성공
3. 실패하면 Actions 실행 기록의 빨간 단계를 눌러 마지막 몇 줄을 캡처해서 보내 주세요.

## 이후 매일
- 새 글 = `posts/날짜-영문슬러그/` 폴더에 `post.html`, `meta.json`, 그래픽 webp
- `meta.json` 의 `mode`: `draft`(임시저장, 기본) / `schedule`(+ `"at": "2026-11-17 08:00"` 예약) / `publish`(바로 발행)
- 올라간 글은 `posted.json` 이 생겨 다시 올라가지 않습니다.

## 문제 해결
| 증상 | 원인 → 해결 |
|---|---|
| `invalid_grant` | 열쇠 만료(테스트 상태였거나 6개월 미사용) → 2-5 확인 후 3단계 다시 → Secret 교체 |
| `403 ... has not been used` | Blogger API 사용 안 켬 → 2-2 |
| `404` | BLOG ID 틀림 → 1-3 숫자 다시 확인 |
| 글은 올라갔는데 사진이 깨짐 | 저장소가 비공개 → Public 으로 |
| `Permission ... denied to github-actions` | 4-4 Read and write 설정 |
