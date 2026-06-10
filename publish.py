# -*- coding: utf-8 -*-
"""
NUKU @nuku.mag 인스타그램 카드뉴스 자동 발행기 (Instagram Graph API)
- L9 자동화 파이프라인의 마지막 ④발행 단계.
- 캐러셀(이미지 2~10장) + 캡션을 인스타에 게시한다.
- 로컬 PC에서도, GitHub Actions(무료)에서도 동일하게 동작.

[필요 환경변수 / GitHub Secrets]
  IG_USER_ID       : 인스타 비즈니스 계정 ID (숫자)
  IG_ACCESS_TOKEN  : 장기/시스템유저 액세스 토큰
  IMG_BASE         : 이미지 공개 URL의 베이스 (예: https://raw.githubusercontent.com/<유저>/<레포>/main)
  GRAPH_VERSION    : (선택) 기본 v21.0

[사용법]
  # 한 덱을 지금 발행 (검수 후 수동 승인)
  python publish.py --deck 02_계약전_물어야할7가지
  # 흐름만 확인 (실제 게시 안 함)
  python publish.py --deck 02_계약전_물어야할7가지 --dry-run
  # 예약 큐 처리 (GitHub Actions 크론에서 호출)
  python publish.py --queue queue.json
"""
import os, sys, time, json, glob, argparse, urllib.parse
from datetime import datetime, timezone, timedelta

try:
    import requests
except ImportError:
    sys.exit("requests 모듈이 필요합니다:  pip install requests")

# Instagram API with Instagram Login → graph.instagram.com (graph.facebook.com 아님)
GRAPH = "https://graph.instagram.com/" + os.environ.get("GRAPH_VERSION", "v21.0")
KST = timezone(timedelta(hours=9))


def cfg():
    uid = os.environ.get("IG_USER_ID", "").strip()
    tok = os.environ.get("IG_ACCESS_TOKEN", "").strip()
    base = os.environ.get("IMG_BASE", "").strip().rstrip("/")
    return uid, tok, base


def img_url(base, deck, fname):
    """레포 내 경로를 공개 raw URL로. 한글/공백은 퍼센트 인코딩."""
    path = f"{deck}/{fname}".replace("\\", "/")
    return base + "/" + urllib.parse.quote(path)


def deck_assets(deck):
    """덱 폴더에서 card*.png(정렬)와 caption.txt를 읽는다."""
    imgs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(deck, "card*.png")))
    if not imgs:
        raise SystemExit(f"[!] {deck} 안에 card*.png가 없습니다.")
    if len(imgs) > 10:
        print(f"[!] 이미지가 {len(imgs)}장 → 인스타 캐러셀은 최대 10장. 앞 10장만 사용합니다.")
        imgs = imgs[:10]
    cap_path = os.path.join(deck, "caption.txt")
    caption = open(cap_path, encoding="utf-8").read().strip() if os.path.exists(cap_path) else ""
    return imgs, caption


def _post(url, data):
    r = requests.post(url, data=data, timeout=60)
    try:
        j = r.json()
    except Exception:
        r.raise_for_status(); raise
    if r.status_code >= 400 or "error" in j:
        raise SystemExit(f"[API 오류] {r.status_code}\n{json.dumps(j, ensure_ascii=False, indent=2)}")
    return j


def _wait_finished(container_id, tok, tries=20, gap=3):
    """컨테이너가 발행 가능 상태(FINISHED)가 될 때까지 폴링."""
    for _ in range(tries):
        r = requests.get(f"{GRAPH}/{container_id}",
                         params={"fields": "status_code", "access_token": tok}, timeout=30)
        sc = r.json().get("status_code")
        if sc == "FINISHED":
            return True
        if sc == "ERROR":
            raise SystemExit(f"[!] 컨테이너 {container_id} 처리 오류(ERROR)")
        time.sleep(gap)
    return True  # 이미지는 보통 즉시 완료. 타임아웃이어도 발행 시도.


def publish_deck(deck, dry_run=False):
    uid, tok, base = cfg()
    imgs, caption = deck_assets(deck)
    urls = [img_url(base, deck, f) for f in imgs]

    print(f"\n=== 발행: {deck} ===")
    print(f"이미지 {len(urls)}장 · 캡션 {len(caption)}자")
    for u in urls:
        print("  ·", u)

    if dry_run:
        print("\n[DRY-RUN] 실제 게시는 하지 않았습니다. URL이 브라우저에서 열리는지 확인하세요.")
        return None
    if not (uid and tok and base):
        raise SystemExit("[!] IG_USER_ID / IG_ACCESS_TOKEN / IMG_BASE 환경변수를 설정하세요.")

    # 1) 각 이미지를 캐러셀 자식 컨테이너로 생성
    children = []
    for i, u in enumerate(urls, 1):
        j = _post(f"{GRAPH}/{uid}/media",
                  {"image_url": u, "is_carousel_item": "true", "access_token": tok})
        children.append(j["id"])
        print(f"  [{i}/{len(urls)}] child {j['id']}")

    # 2) 캐러셀 부모 컨테이너 생성
    parent = _post(f"{GRAPH}/{uid}/media",
                   {"media_type": "CAROUSEL", "children": ",".join(children),
                    "caption": caption, "access_token": tok})["id"]
    print("  parent container:", parent)

    # 3) 발행 가능 상태 대기 후 게시
    _wait_finished(parent, tok)
    pub = _post(f"{GRAPH}/{uid}/media_publish",
                {"creation_id": parent, "access_token": tok})
    media_id = pub["id"]
    print(f"\n✅ 게시 완료! media_id = {media_id}")
    return media_id


def run_queue(qpath):
    """queue.json: [{deck, scheduled_at(ISO,+09:00), status:draft|approved|posted}]
       status==approved 이고 예약시각이 지난 항목만 발행 → posted로 기록."""
    data = json.load(open(qpath, encoding="utf-8"))
    now = datetime.now(KST)
    changed = False
    for item in data:
        if item.get("status") != "approved":
            continue
        when = datetime.fromisoformat(item["scheduled_at"])
        if when.tzinfo is None:
            when = when.replace(tzinfo=KST)
        if when > now:
            print(f"[대기] {item['deck']} — 예약 {item['scheduled_at']} 아직 안 됨")
            continue
        mid = publish_deck(item["deck"])
        item["status"] = "posted"
        item["media_id"] = mid
        item["posted_at"] = now.isoformat()
        changed = True
    if changed:
        json.dump(data, open(qpath, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\n[큐 갱신] {qpath} 저장됨")
    else:
        print("\n[큐] 지금 발행할 항목이 없습니다.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", help="발행할 덱 폴더 경로 (레포 루트 기준)")
    ap.add_argument("--queue", help="예약 큐 파일 경로 (queue.json)")
    ap.add_argument("--dry-run", action="store_true", help="실제 게시 없이 URL만 출력")
    a = ap.parse_args()
    if a.queue:
        run_queue(a.queue)
    elif a.deck:
        publish_deck(a.deck.rstrip("/\\"), dry_run=a.dry_run)
    else:
        ap.error("--deck 또는 --queue 중 하나가 필요합니다.")
