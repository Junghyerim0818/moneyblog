# 한눈머니 — 그래픽 위주 금융·경제 블로그 키트

토스·뱅크샐러드 톤의 **블로거 테마**와, 숫자만 넣으면 같은 스타일로 그래픽이 나오는 **그래픽 키트(moneygraph)** 입니다.

```
moneyblog/
├─ theme/theme.xml            ← 블로거에 올릴 테마 (style.css + theme.template.xml 로 build.py가 생성)
├─ moneygraph/                ← 그래픽 키트 (Pretendard 폰트 포함, OFL 라이선스)
├─ samples/year_end_tax.json  ← 그래픽 스펙 예시 (8가지 컴포넌트 전부)
├─ samples/post-2026-연말정산.html ← 테마 클래스를 쓴 원고 예시
├─ posts/2026-11-16-year-end-tax/ ← 자동 게시용 글 폴더 예시 (본문·meta·그래픽 9장)
├─ blogger/, .github/workflows/ ← 블로거 자동 게시 (SETUP_BLOGGER.md 참고)
└─ preview/home.html, post.html ← 블로거 없이 보는 테마 미리보기
```

## 1. 테마 적용

1. 블로거 관리 화면 → **테마** → '맞춤설정' 옆 ▾ → **백업**으로 지금 테마를 먼저 내려받아 둡니다.
2. 같은 메뉴에서 **복원** → `theme/theme.xml` 업로드.
3. **설정 → 게시물** 에서 메인 화면 게시물 수를 7개(대표 1 + 카드 6)로 맞추면 보기 좋습니다.
4. 상단 메뉴와 메인 칩은 라벨(카테고리) 링크입니다. 글에 아래 라벨을 똑같이 붙여야 연결됩니다.
   - 상단: `증권금융` `경제` `절세` / 메인 칩: `주식기초` `경제용어` `연말정산` `연금저축`
   - 바꾸려면 `theme/theme.template.xml` 에서 글자를 고치고 `python theme/build.py` 실행 → 다시 복원.
5. 하단의 소개·개인정보처리방침·문의 링크는 `/p/about.html` 등 **페이지**로 만들어야 열립니다 (애드센스 승인에도 필요).
6. 애드센스: 블로거 **수익** 메뉴에서 자동 광고를 켜면 이 테마에도 그대로 붙습니다. 직접 넣고 싶으면 **레이아웃**의 아래쪽 빈 영역에 가젯을 추가하세요.

테마에 들어 있는 것
- 메인: 히어로 문구, 카테고리 칩, 최신 글 1개를 크게 + 나머지 카드 그리드 (PC 3열 / 태블릿 2열 / 휴대폰 1열)
- 글 화면: 읽기 진행 바, 넓은 표 가로 스크롤, 라벨, 같은 라벨 다른 글 4개 자동 추천
- 카드 썸네일은 **글의 첫 번째 이미지**입니다. 썸네일(1200×630)을 맨 위에 넣으세요.
- 댓글 영역은 넣지 않았습니다 (정보형 블로그 기준). 필요하면 말씀해 주세요.

## 2. 원고에서 쓰는 꾸밈 클래스

블로거 'HTML 보기'에서 아래처럼 쓰면 테마가 토스 스타일로 꾸며 줍니다. 예시는 `samples/post-2026-연말정산.html`.

| 용도 | HTML |
|---|---|
| 3줄 요약 (파란 박스) | `<div class="mg-lead"><div class="t">3줄 요약</div><ul><li>…</li></ul></div>` |
| 목차 | `<div class="mg-toc"><div class="t">목차</div><ol><li><a href="#s1">…</a></li></ol></div>` + 소제목에 `id="s1"` |
| 숫자 카드 | `<div class="mg-kpis"><div class="mg-kpi"><div class="k-label">라벨</div><div class="k-value">148.5만 원</div><div class="k-delta up">상승</div></div>…</div>` |
| 팁 / 할 일 / 주의 | `<div class="mg-callout">` / `class="mg-callout todo"` / `class="mg-callout warn"` |
| 단계 | `<ol class="mg-steps"><li><b>제목</b>설명</li></ol>` |
| 표 강조 | 행 `<tr class="hl">`, 칸 `<td class="hl">` |
| FAQ (접히는) | `<div class="mg-faq"><details><summary>질문</summary><p>답</p></details></div>` |
| 출처 박스 | `<div class="mg-source"><div class="t">참고한 공식 자료</div><ul>…</ul></div>` |
| 작은 회색 글 | `<p class="mg-note">…</p>` |
| 상승/하락 색 | `<span class="up">+3.2%</span>` `<span class="down">-1.1%</span>` |

## 3. 그래픽 키트

```bash
pip install matplotlib pillow
python -m moneygraph samples/year_end_tax.json --out out/연말정산
```
- 결과: 스펙의 그래픽마다 webp 파일 + 붙여넣을 alt 문구 목록(`alt.txt`).
- 썸네일은 1200×630(검색·공유용)과 1080×1080(스레드·인스타용), 본문 그래픽은 폭 880px(휴대폰에서도 글자가 읽히는 크기).
- 블로그 이름·문구는 `moneygraph/brand.json` 에서 바꿉니다: `{"name": "한눈머니"}`

| type | 언제 | 주요 항목 |
|---|---|---|
| `thumbnail` | 대표 이미지 | `title`(줄바꿈 `\n`), `highlight`(파랑 강조 단어), `eyebrow`, `number{label,value}`, `badge`, `size:"square"` |
| `kpi` | 핵심 숫자 2~6개 | `items[{label, value, delta, dir:"up"/"down", note}]`, `cols` |
| `bars` | 항목 비교 | `items[{label, value, display}]`, `highlight:"max"/"min"/[번호]`, `signed:true`(등락률, 빨강/파랑) |
| `trend` | 시간에 따른 변화 | `x[...]`, `series[{name, values}]`, `unit`, `ymin` |
| `table` | 조건·한도 표 | `header`, `rows`, `highlight_col`, `highlight_row` |
| `flow` | "이럴 땐 이렇게" 판단 | `question`, `yes{tag,title,big,lines}`, `no{…}`, `footer_note` |
| `checklist` | 할 일·일정 | `rows[[언제, 할 일]]`, `highlight[번호]` |
| `donut` | 구성비 | `items[{label, value}]`, `center{value,label}` |

공통: `title`, `sub`, `eyebrow`, `source`(그래픽 하단 출처), `file`(파일 이름), `alt`.

색 규칙: 강조는 파랑 1색, 상승은 빨강·하락은 파랑(국내 증권 앱과 같은 방식), 나머지는 회색.
