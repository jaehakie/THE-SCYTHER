"""Check every scene's progression gate and real-input/media completion paths."""
import json
import os
from pathlib import Path
import sys

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from services.character import CharacterDialogue, ModelConfig
from services.endings import clue_grade
from services.game import GameService, Session
from services.story import SCENES, TIMED_LINES

BASE = os.getenv("NOTTODAY_TEST_URL", "http://127.0.0.1:8000")
OUT = ROOT / "reference/qa/scene-completion"
OUT.mkdir(parents=True, exist_ok=True)


def previews():
    game = GameService(clock=lambda: 100, dialogue=CharacterDialogue(ModelConfig(mode="mock")))
    views = {}
    for scene_id, scene in SCENES.items():
        session = Session(ending_type=scene.get("result_type", "fulvus"), ending_grade=clue_grade(4))
        game._enter(session, scene_id)
        if scene_id == "decision":
            session.decision_started = 85
            session.timed_beats = len(TIMED_LINES)
            for _, lines in TIMED_LINES:
                for speaker, text in lines:
                    game._say(session, speaker, text)
        views[scene_id] = game._view(session)
    return views


with sync_playwright() as p:
    browser = p.chromium.launch(channel="msedge", headless=True, args=["--mute-audio"])
    context = browser.new_context(viewport={"width":390,"height":844}, reduced_motion="no-preference")
    context.add_init_script("sessionStorage.setItem('nottoday.sound.enabled','false');")
    page = context.new_page()
    errors, unexpected, checked = [], [], []
    page.on("pageerror", lambda error: errors.append(str(error)))
    views = previews()
    active = views["intro1"]
    page.route("**/api/game", lambda route: route.fulfill(json=active))
    page.route("**/api/action", lambda route: (unexpected.append(route.request.post_data_json), route.fulfill(json=active)))
    page.route("**/api/chat", lambda route: (unexpected.append(route.request.post_data_json), route.fulfill(json=active)))
    page.clock.install()
    page.goto(BASE + "/play", wait_until="networkidle")

    # Serialized real scene data checks coverage; advancing the browser clock
    # only accelerates this QA run, and exposes no application skip control.
    for scene_id, view in views.items():
        active = view
        page.wait_for_function("!polling")
        page.evaluate("""snapshot => {
            generation++;
            screen.querySelectorAll('video').forEach(v=>v.pause());
            screen.innerHTML=''; state=null;
            textPlayback.entries.clear(); textPlayback.readKeys.clear();
            hologramPlayback.clear(); textPlayback.queueEnd=performance.now();
            setState(snapshot,true);
        }""", view)
        pending = page.evaluate("presentationPending()")
        assert page.locator(".reading-tools").count() == 0
        assert page.evaluate("typeof revealAllText") == "undefined"
        if pending:
            assert page.locator("#screen").evaluate("e=>!presentationPending() || [...e.querySelectorAll(progressionControls)].every(b=>b.disabled)"), scene_id
            revision = page.evaluate("state.revision")
            for action in ("advance", "choose", "chat", "topic", "finish_chat", "journal", "back", "forward"):
                assert page.evaluate("action=>presentationPending() ? act(action,'test') : null", action) in (False, None), (scene_id, action)
            assert page.evaluate("state.revision") == revision
        page.wait_for_function("[...document.images].every(i=>i.complete)")
        page.clock.fast_forward(20000)
        page.clock.fast_forward(2000)
        # Real clip decoding/end events are retained; seek only in this broad
        # coverage pass. Natural-duration playback is tested below.
        for video in page.locator("#screen video").all():
            page.wait_for_function("v=>v.readyState>=1 || v.error", arg=video.element_handle())
            video.evaluate("v=>{if(!v.error){v.currentTime=v.duration;v.play().catch(()=>{});}}")
        if page.locator("#screen video").count():
            page.wait_for_function("[...screen.querySelectorAll('video')].every(v=>v.ended||v.dataset.failed==='true')")
        page.clock.fast_forward(2000)
        page.wait_for_function("!presentationPending()")
        page.wait_for_function("[...screen.querySelectorAll(progressionControls)].every(b=>b.disabled===(b.dataset.storyDisabled==='true'))")
        for label, size in (("mobile", {"width":390,"height":844}), ("desktop", {"width":1280,"height":900})):
            page.set_viewport_size(size)
            assert page.evaluate("document.documentElement.scrollWidth<=innerWidth"), scene_id
            if scene_id in {"intro1", "rules", "record", "mentor", "intel", "decision", "ending_truth_mail", "ending_bad_ash"}:
                page.screenshot(path=OUT / f"{scene_id}-{label}.png")
        checked.append(scene_id)
        print("checked " + scene_id, flush=True)
    assert not unexpected, unexpected
    context.close()

    # Actual APIs + real-time sequential text, spam clicks and Enter submission.
    context = browser.new_context(viewport={"width":390,"height":844}, reduced_motion="no-preference")
    view = context.request.post(BASE + "/api/game", data={}).json()
    while view["scene_id"] != "mentor":
        action, value = ("choose", "yoonje") if view["scene_id"] == "selection" else ("advance", "")
        response = context.request.post(BASE + "/api/action", data={"action":action,"value":value,"revision":view["revision"]})
        assert response.ok, response.text()
        view = response.json()
    page = context.new_page()
    page.on("pageerror", lambda error: errors.append(str(error)))
    requests = []
    page.on("request", lambda r: requests.append(r.url) if "/api/chat" in r.url or "/api/action" in r.url else None)
    page.goto(BASE + "/play", wait_until="networkidle")
    page.wait_for_function("state?.scene_id==='mentor' && !busy")
    assert page.locator(".send").is_disabled()
    page.locator("#message-input").fill("Ask after the speech.")
    page.locator("#message-input").press("Enter")
    page.evaluate("()=>{for(let i=0;i<15;i++)screen.querySelector('[data-choice]').click();}")
    page.wait_for_timeout(150)
    assert not requests
    assert page.evaluate("state.scene_id") == "mentor"
    if page.locator('.scene-video-play').is_visible():
        page.locator('.scene-video-play').click()
    page.wait_for_function("!presentationPending()", timeout=20000)
    assert page.locator(".send").is_enabled()
    page.locator(".send").click()
    page.wait_for_function("!busy && state.messages.some(m=>m.speaker==='user')")
    assert len(requests) == 1
    assert page.locator(".send").is_disabled(), "Next send unlocked before the generated reply finished"
    page.wait_for_function("!presentationPending()", timeout=20000)
    assert page.locator(".send").is_enabled()
    context.close()

    # Blocked autoplay must offer Play, while next-scene stays locked. A failed
    # file can release the media gate, rather than trapping the player forever.
    for mode in ("blocked", "failed"):
        ctx = browser.new_context(reduced_motion="no-preference")
        preview = ctx.new_page()
        preview.on("pageerror", lambda error: errors.append(str(error)))
        preview.add_init_script("""(() => {
            const original=HTMLMediaElement.prototype.play;
            HTMLMediaElement.prototype.play=function(){
                if(!this.dataset.testBlocked){this.dataset.testBlocked='true';return Promise.reject(new DOMException('blocked','NotAllowedError'));}
                return original.call(this);
            };
        })();""")
        preview.route("**/api/game", lambda route: route.fulfill(json=views["intro3"]))
        if mode == "failed": preview.route("**/assets/videos/harvest-logo.mp4", lambda route: route.abort())
        preview.goto(BASE + "/play", wait_until="networkidle")
        if mode == "blocked":
            preview.locator(".intro-video-play").wait_for(state="visible")
            assert preview.locator(".intro-frame").is_disabled()
            assert preview.locator(".intro-video-play").is_enabled()
            preview.locator(".intro-video-play").click()
            preview.wait_for_function("document.querySelector('.intro-video').currentTime>0")
            assert preview.locator(".intro-frame").is_disabled()
            preview.wait_for_function("document.querySelector('.intro-video').ended", timeout=12000)
        preview.wait_for_function("!presentationPending()")
        assert preview.locator(".intro-frame").is_enabled()
        ctx.close()
    assert not errors, errors
    (OUT / "report.json").write_text(json.dumps({"status":"passed", "scenes":checked,
        "checks":["all scene gates", "mouse spam", "Enter guard", "normal API chat", "reply completion", "video end", "autoplay retry", "media failure", "mobile/desktop", "no skip function"],
        "javascript_errors":errors}, indent=2), encoding="utf-8")
    browser.close()
    print("PASS scene completion: " + str(len(checked)) + " scenes and real input/media paths", flush=True)
