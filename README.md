# nuku-mag-posts · @nuku.mag 카드뉴스 발행

영상 현장인을 위한 매거진 **@nuku.mag**의 카드뉴스 저장소 + 자동 발행 시스템.

## 구조
```
01_… 04_…/           각 덱 폴더 (card01~10.png + content.json + caption.txt)
publish.py           인스타 Graph API 발행기 (캐러셀 + 캡션)
queue.json           예약 발행 큐
requirements.txt     의존성 (requests)
.github/workflows/   GitHub Actions (수동 1클릭 / 예약 크론)
../13_클로드코드_가이드/TEAM91 인스타 자동발행 셋업하기.md       ⭐ 처음 셋업은 이 문서부터
```

## 빠른 사용
- **셋업(최초 1회):** [`TEAM91 인스타 자동발행 셋업하기`](<../13_클로드코드_가이드/TEAM91 인스타 자동발행 셋업하기.md>) 따라 인스타 프로페셔널·Meta 토큰·GitHub Secrets 등록.
- **발행:** Actions 탭 → *NUKU 카드뉴스 발행* → Run workflow → 덱 폴더명 입력. (검수 후 1클릭)
- **테스트:** `python publish.py --deck 02_계약전_물어야할7가지 --dry-run`

## 새 카드뉴스 만들기
1. 로컬 엔진(`_작업스크립트/_gen_cardnews.py`)으로 `content.json` → PNG 생성
2. 새 덱 폴더를 이 레포에 push
3. 검수 → 발행

> 사람이 하는 일 = **무슨 말 할지 + 검수**. 디자인·발행은 자동.
