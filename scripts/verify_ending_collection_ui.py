"""Normal story transitions plus browser-local ending persistence and failures."""
from pathlib import Path
import json
import os
import time

from playwright.sync_api import sync_playwright

BASE = os.getenv("NOTTODAY_TEST_URL", "http://127.0.0.1:8000")
OUT = Path(__file__).resolve().parents[1] / "reference/qa/ending-collection"
OUT.mkdir(parents=True, exist_ok=True)


def act(api, view, action, value=""):
    response = api.post(BASE + "/api/action", data={"action": action, "value": value, "revision": view["revision"]})
    assert response.ok, response.text()
    return response.json()


def seed(api, early=False):
    view = api.post(BASE + "/api/game", data={}).json()
    for _ in range(60):
        scene = view["scene_id"]
        if scene == "decision" or view["stop_reason"]:
            return view
        choices = {"selection":"yoonje", "mentor":"follow", "knock":"break" if early else "truth",
                   "entry_plea":"harvest", "allegation":"wife", "wife_tears":"ask"}
        if scene in choices:
            view = act(api, view, "choose", choices[scene])
        elif scene == "exploration":
            for key in ("calendar", "family", "drawer1", "drawer2", "computer"):
                view = act(api, view, "inspect", key)
            view = act(api, view, "advance")
        elif scene == "conversation":
            for key in ("calendar", "drawer1", "drawer2", "computer"):
                view = act(api, view, "topic", key)
            view = act(api, view, "finish_chat")
        else:
            view = act(api, view, "advance")
    raise AssertionError("Decision not reached")


def ready(page):
    page.wait_for_function("state && !busy")
    retry = page.locator('.scene-video-play')
    if retry.count() and retry.is_visible():
        retry.click()


def count(page):
    return page.evaluate("async()=> (await EndingCollection.list()).length")


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True, args=["--mute-audio"])
    context = browser.new_context(viewport={"width":390, "height":844}, reduced_motion="reduce")
    assert context.request.get(BASE + "/health").json()["dialogue_mode"] == "mock"
    context.request.post(BASE + "/api/game", data={})
    page = context.new_page()
    errors, failed = [], []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("response", lambda r: failed.append(r.url) if "/assets/" in r.url and r.status >= 400 else None)
    page.goto(BASE + "/play", wait_until="networkidle")
    ready(page)
    initial = page.evaluate("[state.run_id,state.revision,state.scene_id]")
    page.locator("#menu-button").click()
    page.locator("[data-endings]").click()
    page.locator(".empty-note").wait_for()
    page.locator("#detail-dialog [data-close]").last.click()
    assert page.evaluate("[state.run_id,state.revision,state.scene_id]") == initial

    cases = [("fulvus-truth", "warn", "report_no"), ("fulvus-lie", "lie", "report_yes"),
             ("caeruleus", "target", None), ("ruber", "all", None),
             ("ruber-early", None, None), ("bad", "give_up", None)]
    jobs = []
    for name, choice, report in cases:
        api = p.request.new_context()
        seed(api, early=name == "ruber-early")
        jobs.append((name, choice, report, api))
    time.sleep(15)
    for name, choice, report, api in jobs:
        if choice:
            view = api.get(BASE + "/api/game").json()
            act(api, view, "choose", choice)

    expected = 0
    for name, choice, report, api in jobs:
        # Only the session cookie changes; all ending records share the same browser profile.
        context.add_cookies(api.storage_state()["cookies"])
        page.goto(BASE + "/play", wait_until="networkidle")
        ready(page)
        note = '<script>window.collectionXss=1</script>\n' + name + " · 확인한 단서와 가족의 상황을 근거로 판단했다."
        for _ in range(25):
            stage = page.evaluate("state.stage")
            if stage in {"result", "bad_result"}:
                break
            if stage == "report":
                page.locator('[data-choice="' + report + '"]').click()
            elif stage == "journal":
                page.locator("#journal-content").fill(note)
                page.locator('[form="journal-form"]').click()
            else:
                page.locator('[data-action="advance"]').click()
            ready(page)
        else:
            raise AssertionError(name)
        if name.startswith("fulvus"):
            assert page.locator("#ending-note-form,#ending-note,.collection-basis").count() == 0
            assert page.evaluate("state.journal") is None
        expected += 1
        page.wait_for_function("collectedEndings.has(state.run_id)")
        assert count(page) == expected
        records = page.evaluate("EndingCollection.list()")
        record = next(r for r in records if r["id"] == page.evaluate("state.run_id"))
        assert page.evaluate("EndingCollection.snapshot({...structuredClone(state),scene_id:'unknown'},{subject:'x',content:'x'})") is None
        if name.startswith("fulvus") or name == "bad":
            assert record["basis"] is None and record["journal"] is None
        else:
            assert record["basis"]["content"] == note
            assert page.locator(".collection-basis .journal-record").inner_text() == note
        assert record["image"] == page.evaluate("state.image")
        if name == "bad":
            assert record["result"]["id"] == "bad" and record["ending_reason"] == "give_up"
            assert record["stop_reason"] == page.evaluate("state.stop_reason")
            assert page.evaluate("state.result") is None
            assert page.locator('.collection-basis').count() == 0
        else:
            assert record["result"] == page.evaluate("state.result")
        assert page.evaluate("window.collectionXss===undefined")
        page.evaluate("render();setState(structuredClone(state),true)")
        page.reload(wait_until="networkidle")
        ready(page)
        page.wait_for_function("collectedEndings.has(state.run_id)")
        assert count(page) == expected
        before = page.evaluate("[state.run_id,state.scene_id,state.revision,state.final_choice,state.time_left]")
        page.locator("#menu-button").click()
        page.locator("[data-endings]").click()
        page.locator(".collected-ending").first.wait_for()
        assert page.locator(".collected-ending").count() == expected
        assert page.locator(".collected-ending:has(.fulvus) .collection-basis").count() == 0
        if name == "bad":
            assert page.locator('.collected-ending .bad-result').count() == 1
            assert page.locator('.collected-ending:has(.bad-result) .collection-basis').count() == 0
            assert page.locator('#detail-dialog .collection-info').inner_text().find('배드엔딩 제외') == -1
        assert page.evaluate("window.collectionXss===undefined")
        if name == "caeruleus":
            for label, size in (("mobile", {"width":390,"height":844}), ("desktop", {"width":1280,"height":900}), ("small", {"width":320,"height":568})):
                page.set_viewport_size(size)
                page.wait_for_function("[...document.querySelectorAll('.collected-ending-image')].every(i=>i.complete&&i.naturalWidth)")
                assert page.locator("#detail-dialog").evaluate("e=>e.scrollWidth<=e.clientWidth")
                assert page.locator(".collected-ending-image").first.evaluate("i=>Math.abs(i.width/i.height-i.naturalWidth/i.naturalHeight)<.02")
                assert page.locator(".collected-ending-image").first.bounding_box()["height"] <= min(size["height"] * .4, 360) + 1
                page.screenshot(path=OUT/(label+".png"))
            page.set_viewport_size({"width":390,"height":844})
        page.locator("#detail-dialog [data-close]").last.click()
        assert page.evaluate("[state.run_id,state.scene_id,state.revision,state.final_choice,state.time_left]") == before
        if name != "bad":
            page.locator('[data-action="advance"]').click()
            ready(page)
            assert page.evaluate("state.stage") == "reflection"
        page.locator("[data-reset]").click()
        ready(page)
        assert page.evaluate("state.scene_id==='intro1' && state.result===null")
        assert count(page) == expected
        print("passed " + name, flush=True)

    # Failure recovery never mutates the live story or removes existing snapshots.
    source = page.evaluate("async()=> (await EndingCollection.list()).find(r=>['caeruleus','ruber'].includes(r.result.id))")
    source["id"] = "a" * 32
    page.evaluate("()=>{window.qaSave=EndingCollection.save;EndingCollection.save=async()=>{throw new DOMException('full','QuotaExceededError')}}")
    page.evaluate("record=>setState({...structuredClone(state),...record,run_id:record.id,stage:'result',journal:record.journal,revision:state.revision+1},true)", source)
    page.locator("[data-ending-save]").wait_for()
    assert count(page) == expected
    page.evaluate("()=>{EndingCollection.save=window.qaSave}")
    page.locator("[data-ending-save]").click()
    page.wait_for_function("collectedEndings.has(state.run_id)")
    assert count(page) == expected + 1
    # Reject bad HTML/content in the browser renderer, and ignore bad stored schemas.
    assert page.evaluate("window.collectionXss===undefined")
    page.reload(wait_until="networkidle")
    ready(page)
    assert count(page) == expected + 1
    second = context.new_page()
    second.goto(BASE + "/play", wait_until="networkidle")
    second.wait_for_function("state && !busy")
    assert second.evaluate("async()=> (await EndingCollection.list()).length") == expected + 1
    second.close()

    isolated = browser.new_context()
    other = isolated.new_page()
    other.add_init_script("Object.defineProperty(window,'indexedDB',{value:{open(){throw new DOMException('blocked','SecurityError')}}})")
    other.goto(BASE + "/play", wait_until="networkidle")
    ready(other)
    scene = other.evaluate("state.scene_id")
    other.locator("#menu-button").click()
    other.locator("[data-endings]").click()
    other.locator("#detail-dialog .dialog-copy").wait_for()
    assert other.evaluate("state.scene_id") == scene
    other.locator("#detail-dialog [data-close]").last.click()
    other.locator('[data-action="advance"]').click()
    ready(other)
    assert other.evaluate("state.scene_id") != scene
    isolated.close()
    assert not errors, errors
    assert not failed, failed
    report = {"status":"passed", "normal_routes":5, "bad_included":True,
              "checks":["empty", "full result and journal", "fulvus without journal", "reload", "new playthrough", "one snapshot per run", "XSS", "quota retry", "blocked storage", "3 sizes", "story flow"],
              "javascript_errors":errors, "failed_assets":failed}
    (OUT/"report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report), flush=True)
    browser.close()
