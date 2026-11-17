"""Exercise the integrated preparation flow against a local mock server."""
import json
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = os.getenv("NOTTODAY_TEST_URL", "http://127.0.0.1:8000")
OUT = Path(__file__).resolve().parents[1] / "reference/qa/preparation"
OUT.mkdir(parents=True, exist_ok=True)


def ready(page):
    page.wait_for_function("state && !busy && !presentationPending()")


def capture_sizes(page, name):
    for label, size in (("mobile", {"width":390, "height":844}), ("desktop", {"width":1280, "height":900})):
        page.set_viewport_size(size)
        page.wait_for_function("[...document.images].every(i => i.complete && i.naturalWidth)")
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        for button in page.locator('.prep-footer button').all():
            bounds = button.bounding_box()
            assert bounds and bounds['y'] >= 0 and bounds['y'] + bounds['height'] <= size['height']
        page.screenshot(path=OUT / f"{name}-{label}.png")
    page.set_viewport_size({"width":390, "height":844})


def seed_intro(api):
    view = api.post(BASE + '/api/game', data={}).json()
    while view['scene_id'] != 'intro5':
        response = api.post(BASE + '/api/action', data={'action':'advance', 'revision':view['revision']})
        assert response.ok, response.text()
        view = response.json()


with sync_playwright() as p:
    browser = p.chromium.launch(channel='msedge', headless=True, args=['--mute-audio'])
    context = browser.new_context(viewport={'width':390, 'height':844}, reduced_motion='reduce')
    assert context.request.get(BASE + '/health').json()['dialogue_mode'] == 'mock'
    page = context.new_page()
    errors, failed = [], []
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('response', lambda r: failed.append(r.url) if '/assets/' in r.url and r.status >= 400 else None)
    page.goto(BASE + '/')
    page.locator('#start').click()
    page.wait_for_url('**/play')
    ready(page)
    # START must still enter the original introduction, not the customization screen.
    assert page.evaluate('state.scene_id') == 'intro1'
    while page.evaluate('state.scene_id') != 'intro5':
        ready(page)
        page.locator('[data-action="advance"]').click()
        page.wait_for_function('!busy')
    ready(page)
    original = page.evaluate('[state.run_id, state.revision]')
    page.locator('[data-action="advance"]').click()
    ready(page)
    assert page.evaluate('preparingPlayer()')
    capture_sizes(page, '01-intro')
    page.locator('#back-button').click()
    assert not page.evaluate('preparingPlayer()')
    page.locator('[data-action="advance"]').click()
    page.locator('[data-begin-customization]').click()
    page.locator('[data-player-gender="female"]').click()
    ready(page)
    capture_sizes(page, '02-appearance')
    # Menus and sound controls remain available without changing preparation state.
    page.locator('#menu-button').click()
    page.locator('[data-rules]').click()
    page.locator('[data-dialog-back]').click()
    page.locator('[data-close]').last.click()
    assert page.evaluate('PlayerProfile.get().gender') == 'female'
    page.reload()
    ready(page)
    assert page.locator('[data-player-gender="female"]').get_attribute('aria-pressed') == 'true'
    page.locator('[data-appearance-next]').click()
    page.locator('#player-name').fill('   ')
    page.locator('[data-name-confirm]').click()
    assert page.evaluate('PlayerProfile.get().phase') == 'name'
    name = '<별빛 & 수습>'
    page.locator('#player-name').fill(name)
    page.reload()
    ready(page)
    assert page.locator('#player-name').input_value() == name
    capture_sizes(page, '03-name')
    page.locator('#player-name').press('Enter')
    assert page.evaluate('PlayerProfile.get().phase') == 'confirm'
    capture_sizes(page, '04-confirm')
    page.locator('#back-button').click()
    assert page.locator('#player-name').input_value() == name
    page.locator('[data-name-confirm]').click()
    assert page.evaluate('[state.run_id, state.revision]') == original
    # Failed transition remains retryable, with the selected profile retained.
    page.route('**/api/action', lambda route: route.abort(), times=1)
    page.locator('[data-finish-prep]').click()
    ready(page)
    assert page.evaluate('preparingPlayer() && !PlayerProfile.get().complete')
    page.locator('[data-finish-prep]').dblclick()
    ready(page)
    assert page.evaluate('state.scene_id') == 'rules'
    assert page.evaluate('state.revision') == original[1] + 1
    page.locator('#back-button').click()
    ready(page)
    assert page.evaluate('state.reviewing && !preparingPlayer()')
    page.locator('.screen-footer [data-action="forward"]').click()
    ready(page)
    page.reload()
    ready(page)
    assert page.evaluate('PlayerProfile.name()') == name
    assert page.evaluate('PlayerProfile.get().complete')
    page.locator('[data-action="advance"]').click()
    ready(page)
    assert page.evaluate('state.scene_id') == 'guide'
    page.locator('[data-action="advance"]').click()
    ready(page)
    assert page.evaluate('state.scene_id') == 'selection'
    page.locator('[data-choice="yoonje"]').click()
    ready(page)
    page.locator('[data-action="advance"]').click()
    ready(page)
    assert page.evaluate('state.scene_id') == 'mentor'
    page.locator('#message-input').fill('선정한 이유가 궁금합니다.')
    page.locator('.send').click()
    ready(page)
    assert page.locator('.message.user .speaker-line').last.inner_text() == name
    assert page.locator('.message.user .avatar').last.get_attribute('src').endswith('profile_f.jpg')
    capture_sizes(page, '05-dialogue')
    # Starting a new run resets both completion and the old chosen name.
    page.locator('#menu-button').click()
    page.locator('[data-restart-confirm]').click()
    page.locator('[data-reset]').click()
    ready(page)
    assert page.evaluate('state.scene_id') == 'intro1'
    assert page.evaluate('state.run_id') != original[0]
    assert page.evaluate('PlayerProfile.name()') != name
    assert not page.evaluate('PlayerProfile.get().complete')
    context.close()

    # Blocking sessionStorage must not make preparation or the existing story unusable.
    context = browser.new_context(viewport={'width':320, 'height':640}, reduced_motion='reduce')
    context.add_init_script("""for (const method of ['getItem', 'setItem']) {
      Storage.prototype[method] = function() { throw new DOMException('Blocked', 'SecurityError'); };
    }""")
    seed_intro(context.request)
    page = context.new_page()
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.goto(BASE + '/play')
    ready(page)
    page.locator('[data-action="advance"]').click()
    for selector in ('[data-begin-customization]', '[data-appearance-next]', '[data-name-confirm]', '[data-finish-prep]'):
        ready(page)
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
        page.locator(selector).click()
    ready(page)
    assert page.evaluate('state.scene_id') == 'rules'
    assert page.evaluate('PlayerProfile.storageFailed()')
    assert not errors, errors
    assert not failed, failed
    report = {'mode':'mock', 'errors':errors, 'failed_assets':failed,
              'checks':['START/introduction', 'four preparation screens', 'both viewports', '320px width',
                        'name validation/escaping', 'refresh/draft', 'retry/double click', 'read-only review',
                        'rules/guide/roster', 'generated chat profile', 'new run isolation', 'blocked storage']}
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    browser.close()
    print(json.dumps(report, ensure_ascii=False))
