# @nuku.mag 자동 발행 셋업 가이드

> 한 번만 셋업하면, 이후엔 **카드 만들기 → 폰으로 검수 → 버튼 1번 → 자동 게시**.
> 전부 **무료**(GitHub Actions). PC가 꺼져 있어도 클라우드에서 발행됩니다.

## 전체 그림
```
content.json 작성 → (엔진) 카드 PNG 생성 → GitHub에 push
        → [검수] 깃허브에서 카드 미리보기
        → [승인] Actions에서 Run workflow 1번 (또는 예약 큐에 approved)
        → 인스타 자동 게시 ✅
```

사람이 하는 일 = **무슨 말 할지 정하기 + 검수**. 나머지는 전부 자동.

---

## STEP 1. 인스타를 프로페셔널 + 페이스북 페이지 연결 (5분)
1. 인스타 앱 → 설정 → **계정 유형 및 도구** → **프로페셔널 계정으로 전환** (비즈니스 권장).
2. 같은 메뉴에서 **페이스북 페이지 연결**. (페이지 없으면 새로 무료 생성 → @nuku.mag 이름으로.)
   - ⚠️ Graph API 발행은 **비즈니스/크리에이터 계정 + 페이지 연결**이 필수입니다.

## STEP 2. Meta 개발자 앱 + 토큰 발급 (10분, 한 번만)
1. **developers.facebook.com** 접속 → 우상단 **내 앱** → **앱 만들기** → 유형 **비즈니스** → 이름(예: nuku-mag-publish).
2. 앱 대시보드 → **제품 추가** → **Instagram**(그래프 API) → 설정.
3. 상단 **도구 → Graph API 탐색기(Explorer)** 열기.
   - 앱 선택 → **User Token** → **권한 추가**:
     `instagram_basic`, `instagram_content_publish`, `pages_show_list`, `pages_read_engagement`, `business_management`
   - **액세스 토큰 생성** → 페이스북 로그인/권한 허용. (이 토큰은 짧은 수명 → 4번에서 연장)
4. **IG_USER_ID 알아내기** (탐색기에서 GET 요청):
   - `me/accounts` 실행 → 내 페이지의 `id` 확인
   - `{페이지id}?fields=instagram_business_account` 실행 → 나오는 `instagram_business_account.id` = **IG_USER_ID** (숫자)
5. **장기 토큰으로 교환** (브라우저 주소창에 입력, 값 채워서):
   ```
   https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id=<앱ID>&client_secret=<앱시크릿>&fb_exchange_token=<3번토큰>
   ```
   → 나오는 `access_token` = **IG_ACCESS_TOKEN** (약 60일 유효)
   - 앱ID·시크릿: 앱 대시보드 → 설정 → 기본설정.
   > 💡 **60일마다 갱신이 싫다면** → "토큰 무기한(시스템 유저)" 항목(맨 아래) 참고.
   > 본인 계정에 본인이 올리는 용도면 **앱 심사(App Review)는 불필요**합니다.

## STEP 3. GitHub 공개 레포 만들고 올리기 (5분)
1. github.com 가입/로그인 → **New repository** → 이름(예: `nuku-mag-posts`) → **Public** → Create.
   - ⚠️ Public이어야 카드 이미지가 공개 URL로 잡혀 API가 가져갑니다. (어차피 인스타에 공개될 이미지라 OK. **토큰은 레포에 안 들어가고 Secrets에 암호화 저장**됩니다.)
2. 이 `09_카드뉴스` 폴더를 그 레포로 올립니다. (Git 설치돼 있으면 폴더에서:)
   ```
   git init
   git add .
   git commit -m "init: nuku 카드뉴스 발행"
   git branch -M main
   git remote add origin https://github.com/<유저명>/nuku-mag-posts.git
   git push -u origin main
   ```
   - Git이 없으면: GitHub 웹에서 **Add file → Upload files**로 폴더 통째 드래그해도 됩니다.

## STEP 4. 레포에 Secrets 등록 (3분)
레포 → **Settings → Secrets and variables → Actions → New repository secret** 로 3개 등록:

| 이름 | 값 |
|---|---|
| `IG_USER_ID` | STEP 2-4의 숫자 ID |
| `IG_ACCESS_TOKEN` | STEP 2-5의 장기 토큰 |
| `IMG_BASE` | `https://raw.githubusercontent.com/<유저명>/nuku-mag-posts/main` |

## STEP 5. 발행하기

### 방식 A — 검수 후 수동 1클릭 (추천: 처음엔 이걸로)
1. 레포에서 덱 폴더 열어 `card01.png`~`card10.png` **눈으로 검수**.
2. 레포 → **Actions** 탭 → **NUKU 카드뉴스 발행** → **Run workflow** →
   덱 폴더명 입력(예: `02_계약전_물어야할7가지`) → **Run**.
3. 1~2분 뒤 인스타에 자동 게시 ✅. (실패하면 Actions 로그에 원인이 한국어로 찍힘.)
   - 📱 GitHub 모바일 앱으로 폰에서도 그대로 가능 = "검수만 하면 됨".

### 방식 B — 예약 자동 발행 (익숙해지면)
1. `queue.json`에 덱과 예약 시각을 적고, **검수 끝나면 `"status": "draft"` → `"approved"`** 로 바꿔 push.
2. 워크플로의 크론이 **평일 오전 9시(KST)**마다 큐를 확인 → 승인됐고 시각이 지난 덱을 자동 게시 → `posted`로 기록.
   - 발행 요일/시간 바꾸려면 `.github/workflows/publish.yml`의 `cron` 수정. (UTC 기준, +9시간=KST)
   - **주 5회**도 그냥 큐에 5개 넣고 5개 다 `approved`로 두면 됩니다.

---

## 토큰 무기한으로 (60일 갱신 없애기) — 선택
1. **business.facebook.com** → 비즈니스 설정 → **사용자 → 시스템 사용자** → 추가(역할: 관리자).
2. 자산 할당: 그 시스템 사용자에 **페이지**와 **앱**을 연결.
3. **토큰 생성** → 권한 `instagram_basic, instagram_content_publish, pages_show_list, pages_read_engagement` → **만료 안 함** 선택.
4. 이 토큰을 `IG_ACCESS_TOKEN` Secret에 넣으면 갱신 불필요.

## 자주 막히는 곳
- **이미지를 못 가져옴** → 레포가 Public인지, `IMG_BASE` 브랜치명이 `main`인지 확인. 먼저 `--dry-run`으로 URL이 브라우저에서 열리는지 테스트.
- **(#10) 권한 오류** → 토큰 권한에 `instagram_content_publish` 빠졌는지, 계정이 비즈니스+페이지 연결인지 확인.
- **첫 push 직후 발행 실패** → raw URL 반영에 몇십 초 걸릴 수 있음. 1분 뒤 재시도.

## 먼저 로컬에서 테스트(게시 X)
```
set IMG_BASE=https://raw.githubusercontent.com/<유저명>/nuku-mag-posts/main   (PowerShell: $env:IMG_BASE="...")
python publish.py --deck 02_계약전_물어야할7가지 --dry-run
```
→ 카드 10장의 공개 URL이 출력됩니다. 그 주소가 브라우저에서 열리면 준비 끝.
