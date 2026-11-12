"""실행 중인 로컬 앱을 Edge로 검증한다. python scripts/verify_ui.py"""
from pathlib import Path
import json
import os

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reference" / "qa"
OUT.mkdir(parents=True, exist_ok=True)
BASE = os.environ.get("NOTTODAY_TEST_URL", "http://127.0.0.1:8000")


def ready(page):
    page.wait_for_function("state && !busy")
    retry = page.locator(".scene-video-play")
    if retry.count() and retry.is_visible():
        try:
            retry.click(timeout=2000)
        except PlaywrightTimeoutError:
            # A successful automatic retry can hide the button between the
            # visibility check and click; only that disappearance is harmless.
            if retry.count() and retry.is_visible():
                raise


def scene_id(page):
    ready(page)
    return page.evaluate("state.scene_id")


def advance_to(page, target):
    for _ in range(40):
        if scene_id(page) == target:
            return
        page.locator('[data-action="advance"]').click()
        ready(page)
    raise AssertionError("Scene not reached: " + target)


def choose(page, choice):
    ready(page)
    page.locator('[data-choice="' + choice + '"]').click()
    ready(page)


def check_layout(page):
    page.wait_for_function("Array.from(document.images).every(image => image.complete && image.naturalWidth > 0)")
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth"), "Horizontal overflow"
    assert page.evaluate("document.querySelector('#screen').getBoundingClientRect().height > 200"), "No room for scene"
    for element in page.locator("button:visible").all():
        bounds = element.bounding_box()
        assert bounds and bounds["width"] > 0 and bounds["height"] > 0


def capture(page, filename):
    check_layout(page)
    page.screenshot(path=OUT / filename)


def capture_sizes(page, name):
    original = page.viewport_size
    for label, size in (("mobile", {"width":390, "height":844}), ("desktop", {"width":1280, "height":900})):
        page.set_viewport_size(size)
        capture(page, name + "-" + label + ".png")
    page.set_viewport_size(original)


def api_path_to_decision(page):
    """두 번째 경로도 정상 API를 통해 진행하고 실제 시간 초과를 검증한다."""
    state = page.request.post(BASE + "/api/game", data={}).json()

    def act(action, value=""):
        nonlocal state
        response = page.request.post(BASE + "/api/action", data={
            "action": action, "value": value, "revision": state["revision"],
        })
        assert response.ok, response.text()
        state = response.json()

    for _ in range(60):
        current = state["scene_id"]
        if current == "decision":
            break
        selections = {"selection":"yoonje", "mentor":"follow", "knock":"truth", "allegation":"rush"}
        if current in selections:
            act("choose", selections[current])
        elif current == "exploration":
            for key in ("calendar", "family", "drawer1", "drawer2", "computer"):
                act("inspect", key)
            act("advance")
        elif current == "conversation":
            act("topic", "calendar")
            act("finish_chat")
        else:
            act("advance")
    assert state["scene_id"] == "decision"


with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="msedge", headless=True)
    context = browser.new_context(viewport={"width":390, "height":844}, device_scale_factor=1, reduced_motion="reduce")
    page = context.new_page()
    errors, failed = [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("response", lambda response: failed.append(response.url)
            if response.status >= 500 or ("/assets/" in response.url and response.status >= 400) else None)
    page.goto(BASE + "/play", wait_until="networkidle")
    ready(page)
    capture(page, "story-01-intro-mobile.png")
    advance_to(page, "intro3")
    page.wait_for_function("document.querySelector('.intro-still')?.complete")
    page.wait_for_timeout(1000)
    assert page.locator("video").evaluate("video => video.paused && video.currentTime === 0")
    assert page.locator(".intro-still").evaluate("image => getComputedStyle(image).opacity === '1'")
    page.wait_for_function("document.querySelector('video')?.currentTime > 1", timeout=20000)
    assert page.locator("video").evaluate("video => video.muted && video.videoWidth > 0 && !video.error")
    capture_sizes(page, "review-01-intro-video")
    advance_to(page, "guide")
    assert "hf_20261103_061016" in page.locator(".story-image").get_attribute("src")
    capture_sizes(page, "review-02-guide")
    advance_to(page, "selection")
    candidate_text = page.locator(".candidate:not(.empty)").inner_text()
    assert "이윤제" in candidate_text
    assert not any(text in candidate_text for text in ("0261024", "44세", "남성", "공장"))
    capture(page, "story-02-selection-mobile.png")
    choose(page, "yoonje")
    advance_to(page, "mentor")
    choose(page, "delay")
    advance_to(page, "mentor")
    assert page.locator('[data-choice="delay"]').is_disabled()
    choose(page, "follow")
    advance_to(page, "knock")
    choose(page, "wait")
    choose(page, "delivery")
    assert "%EA%B5%B3%EC%9D%80%EC%96%BC%EA%B5%B4" in page.locator(".story-image").get_attribute("src")
    page.locator('[data-action="advance"]').click()
    page.wait_for_function("state && state.stage === 'silence'")
    assert page.locator("button:visible").count() == 0
    page.wait_for_function("state && state.scene_id === 'entry_truth'", timeout=5000)
    assert "%EB%AC%B8%EC%97%B4%EB%A6%BC" in page.locator(".story-image").get_attribute("src")
    advance_to(page, "exploration")
    assert page.locator('[data-action="advance"]').is_disabled()
    assert page.locator(".room").get_attribute("class").strip() == "room lamp-off"
    capture(page, "story-03-exploration-mobile.png")
    page.locator('[data-action="lantern"]').click()
    ready(page)
    assert page.locator(".room").get_attribute("class").strip() == "room"
    page.locator('[data-action="lantern"]').click()
    ready(page)
    assert page.locator(".room").get_attribute("class").strip() == "room lamp-off"
    for key in ("calendar", "family", "drawer1", "drawer2", "computer"):
        page.locator('[data-inspect="' + key + '"]').first.click()
        page.get_by_role("dialog").wait_for()
        if key == "drawer1":
            assert "생존율" not in page.locator(".dialog-copy").inner_text()
            capture(page, "story-04-diagnosis-mobile.png")
        page.get_by_role("button", name="확인", exact=True).click()
    page.locator('[data-action="advance"]').click()
    ready(page)
    page.locator("[data-finish-chat]").click()
    page.get_by_role("heading", name="이야기를 들어보세요").wait_for()
    page.get_by_role("button", name="질문하러 돌아가기").click()
    for key in ("calendar", "drawer1", "drawer2", "computer"):
        page.locator('[data-topic="' + key + '"]').click()
        ready(page)
        if key == "drawer1":
            capture_sizes(page, "review-03-diagnosis-dialogue")
            assert page.locator(".inline-image").evaluate_all("images => images.every(image => Math.abs(image.clientWidth / image.clientHeight - image.naturalWidth / image.naturalHeight) < .02)")
    assert page.locator(".composer-note").count() == 0
    page.locator("#message-input").fill("달력의 생일은 내일인가요?")
    page.locator("#message-input").press("Enter")
    ready(page)
    assert page.evaluate("state.clue_count") == 4
    capture(page, "story-05-conversation-mobile.png")
    page.locator("[data-notes]").click()
    assert page.locator(".clue-card").count() == 5
    page.get_by_role("button", name="이야기로 돌아가기").click()
    page.locator("[data-finish-chat]").click()
    ready(page)
    assert scene_id(page) == "intel"
    capture(page, "story-06-intel-mobile.png")
    assert page.locator(".intel-record").count() == 1
    assert page.locator(".scene-visual").count() == 0
    assert page.locator(".intel-record").evaluate("e => !!(document.querySelector('.chat-log').compareDocumentPosition(e) & Node.DOCUMENT_POSITION_FOLLOWING)")
    assert page.locator(".intel-record img").get_attribute("src").endswith("/mentor-intel.png")
    assert "사실 여부가 확인되지 않은 정보" in page.locator(".intel-record figcaption").text_content()
    capture_sizes(page, "review-04-intel")
    advance_to(page, "allegation")
    choose(page, "wife")
    advance_to(page, "wife_tears")
    assert page.evaluate("state.clue_count") == 6
    assert "hf_20261102_163612" in page.locator(".story-image").get_attribute("src")
    assert page.locator(".story-choices .choice-num").count() == 0
    capture_sizes(page, "review-05-wife-tears")
    choose(page, "ask")
    assert scene_id(page) == "wife_question"
    assert "%ED%81%B4%EB%A1%9C%EC%A6%88%EC%97%85" in page.locator(".story-image").get_attribute("src")
    capture_sizes(page, "review-06-wife-question")
    page.locator('[data-action="advance"]').click()
    ready(page)
    assert scene_id(page) == "wife_averted"
    advance_to(page, "daughters")
    capture(page, "story-07-daughters-mobile.png")
    advance_to(page, "decision")
    page.wait_for_function("state && state.decision_ready", timeout=20000)
    before_reload = page.evaluate("state.time_left")
    page.reload(wait_until="networkidle")
    ready(page)
    assert page.evaluate("state.time_left") <= before_reload
    assert page.locator('[data-choice="target"]').is_visible()
    choice_box = page.locator('[data-choice="target"]').bounding_box()
    assert choice_box["y"] >= 0 and choice_box["y"] + choice_box["height"] <= 844
    capture(page, "story-08-timer-mobile.png")
    page.locator('[data-choice="target"]').click()
    page.get_by_role("button", name="다시 생각하기").click()
    page.locator('[data-choice="target"]').click()
    page.get_by_role("button", name="선택 확정").click()
    page.wait_for_function("state && state.scene_id === 'ending_target_children'")
    assert page.evaluate("state.final_choice") == "target"
    capture(page, "story-09-record-mobile.png")
    page.reload(wait_until="networkidle")
    ready(page)
    assert page.evaluate("state.final_choice") == "target"
    advance_to(page, "journal_target")
    page.locator("#journal-content").fill("아이들은 보호청에 맡기고 대상자만 수확했다. 확인한 단서와 계율 사이에서 판단했다.")
    page.get_by_role("button", name="수확일지 기록").click()
    ready(page)
    advance_to(page, "result_caeruleus")
    assert page.locator(".result-copy").inner_text().find("카이룰레우스") >= 0
    capture_sizes(page, "story-result-caeruleus")
    advance_to(page, "ending_reflection")
    page.get_by_role("button", name="처음부터 다시 시작", exact=True).click()
    ready(page)
    page.set_viewport_size({"width":1280, "height":900})
    advance_to(page, "selection")
    capture(page, "story-10-selection-desktop.png")
    choose(page, "yoonje")
    advance_to(page, "mentor")
    choose(page, "doubt")
    advance_to(page, "knock")
    choose(page, "break")
    advance_to(page, "entry_plea")
    choose(page, "harvest")
    page.get_by_role("button", name="선택 확정").click()
    page.wait_for_function("state && state.stop_reason === 'early_harvest'")
    capture(page, "story-11-early-desktop.png")
    advance_to(page, "journal_early")
    page.locator("#journal-content").fill("명령과 원칙을 따라 대상자를 수확했다.")
    page.get_by_role("button", name="수확일지 기록").click()
    ready(page)
    advance_to(page, "result_ruber_early")
    assert page.evaluate("state.result.id") == "ruber"
    api_path_to_decision(page)
    page.reload(wait_until="networkidle")
    ready(page)
    page.wait_for_function("state && state.decision_ready", timeout=20000)
    capture(page, "story-12-decision-desktop.png")
    page.locator('[data-choice="all"]').click()
    # 확인 창을 열어둔 상태에서도 서버 제한시간이 끝나야 한다.
    page.wait_for_function("state && state.stop_reason === 'timeout'", timeout=65000)
    assert not page.get_by_role("dialog").is_visible()
    assert page.evaluate("state.final_choice") is None
    capture(page, "story-13-timeout-desktop.png")
    advance_to(page, "result_bad")
    assert page.locator(".ending-result").count() == 0
    assert page.locator(".bad-result").is_visible()
    assert not errors, errors
    assert not failed, failed
    print(json.dumps({
        "status":"passed", "screenshots":str(OUT),
        "flow":"intro, rules, mentor, delivery silence, exploration, dialogue, allegations, timed choice, reload, early harvest, real timeout",
        "javascript_errors":errors, "failed_assets_or_server_errors":failed,
    }, ensure_ascii=False), flush=True)
    browser.close()
