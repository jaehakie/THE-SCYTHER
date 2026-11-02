"""선택적으로 설치한 Playwright와 로컬 Edge로 회의 시연 흐름을 확인한다."""
from pathlib import Path
import json

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reference" / "qa"
OUT.mkdir(parents=True, exist_ok=True)


def check_layout(page):
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "가로 넘침"
    for el in page.locator("button:visible").all():
        box = el.bounding_box()
        assert box is not None and box["width"] > 0 and box["height"] > 0


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=1)
    page = context.new_page()
    errors, failed = [], []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("response", lambda r: failed.append(r.url) if r.status >= 500 or ("/assets/" in r.url and r.status >= 400) else None)
    page.goto("http://127.0.0.1:8000", wait_until="networkidle")
    page.get_by_role("button", name="이윤제 정보 열람").wait_for()
    check_layout(page)
    page.screenshot(path=OUT / "01-selection-mobile.png")
    page.get_by_role("button", name="이윤제 정보 열람").click()
    page.get_by_role("button", name="이윤제의 집으로").wait_for()
    page.get_by_role("button", name="왜 이 사람이 선정됐나요?").click()
    page.get_by_text("과거 통계와 선정 절차에 따라 올라온 명단이다.", exact=False).wait_for()
    page.get_by_role("button", name="이윤제의 집으로").click()
    page.get_by_role("button", name="따님들 이야기를 듣고 싶어요.", exact=True).click()
    page.get_by_text("아내가 떠난 뒤로 두 딸과 지내고 있어요.", exact=False).wait_for()
    page.screenshot(path=OUT / "02-conversation-mobile.png")
    page.get_by_role("button", name="집 탐색", exact=True).click()
    page.get_by_role("button", name="서랍 1", exact=True).click()
    page.get_by_role("dialog").wait_for()
    page.get_by_role("button", name="이 단서에 대해 물어보기").click()
    page.get_by_text("서랍의 진단서를 보셨군요.", exact=False).wait_for()
    page.get_by_role("button", name="집 탐색", exact=True).click()
    page.get_by_role("button", name="달력", exact=True).click()
    page.get_by_role("button", name="닫기", exact=True).click()
    check_layout(page)
    page.screenshot(path=OUT / "03-explore-mobile.png")
    page.get_by_role("button", name="단서 노트", exact=False).click()
    assert page.locator(".clue-card").count() == 2
    page.get_by_role("button", name="대화", exact=True).click()
    page.locator("#message-input").fill("내일이 생일인가요?")
    page.locator("#message-input").press("Enter")
    page.get_by_text("내일이 큰아이 생일이에요.", exact=False).wait_for()
    page.get_by_role("button", name="스승의 추가 기록 확인").click()
    page.get_by_role("button", name="이윤제에게 직접 묻기").click()
    page.get_by_text("…그 기록을 보셨군요.", exact=False).wait_for()
    page.get_by_role("button", name="판단 내리기").click()
    page.get_by_role("button", name="이윤제만 수확한다.", exact=False).click()
    page.get_by_role("button", name="다시 생각하기").click()
    assert page.get_by_role("heading", name="최종 선택", exact=True).is_visible()
    page.get_by_role("button", name="이윤제만 수확한다.", exact=False).click()
    page.get_by_role("button", name="선택 확정", exact=True).click()
    page.get_by_role("heading", name="카이룰레우스", exact=True).wait_for()
    assert "달력" in page.locator(".result-evidence").inner_text()
    assert "진단서" in page.locator(".result-evidence").inner_text()
    page.screenshot(path=OUT / "04-ending-mobile.png")
    page.reload(wait_until="networkidle")
    page.get_by_role("heading", name="카이룰레우스", exact=True).wait_for()
    page.get_by_role("button", name="새로운 판단으로 다시 시작").click()
    page.get_by_role("button", name="이윤제 정보 열람").wait_for()
    page.set_viewport_size({"width": 1280, "height": 900})
    check_layout(page)
    page.screenshot(path=OUT / "05-selection-desktop.png")
    assert not errors, errors
    assert not failed, failed
    print(json.dumps({"status":"passed", "flow":"selection, mentor, conversation, clues, intel, confirmation, ending, reload, reset", "javascript_errors":errors,"failed_assets_or_server_errors":failed,"screenshots":str(OUT)}, ensure_ascii=False))
    browser.close()
