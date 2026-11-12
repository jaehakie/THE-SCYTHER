"use strict";

const screen = document.querySelector("#screen");
const title = document.querySelector("#screen-title");
const backButton = document.querySelector("#back-button");
const dialog = document.querySelector("#detail-dialog");
const dialogBody = document.querySelector("#dialog-body");
const status = document.querySelector("#status");
const clueNotice = document.querySelector("#clue-notice");
const shell = document.querySelector(".app-shell");
const esc = value => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const arrow = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6"/></svg>';
const speakerNames = {mentor:"스승", yoonje:"이윤제", user:"나", daughters:"두 딸", older_daughter:"큰딸", younger_daughter:"작은딸"};
let state = null, busy = false, draft = "", journalDraft = "", toastTimer, polling = false;
let clueNoticeTimer = null, clueNoticeAnimation = null;
let silentSceneTimer = null;
let generation = 0, clockAnchor = performance.now(), remainingAtAnchor = null;
let introMediaController = null;
let hologramObserver = null;
let progressionFrame = null;
const hologramPlayback = new Map();
const HOLOGRAM_DURATION_MS = 1250;
let pendingRequest = null;
let pendingTurn = null;
let modalVersion = 0;
let dialogParent = null;
const collectedEndings = new Set(), collectingEndings = new Set();
const collectionErrors = new Set();
const sceneDrafts = new Map();
const INTRO_PHOTO_HOLD_MS = 2500;
const motionPreference = matchMedia("(prefers-reduced-motion: reduce)");
const textPlayback = {entries:new Map(), queueEnd:0, frame:null, active:false, followTail:false, readKeys:new Set()};
const progressionControls = '[data-action="advance"], [data-action="forward"], [data-choice], [data-topic], [data-finish-chat], .composer .send, button[form="journal-form"], [data-reset]';
const progressionActions = new Set(['advance', 'forward', 'back', 'choose', 'topic', 'chat', 'finish_chat', 'journal']);
const graphemes = typeof Intl.Segmenter === "function" ? new Intl.Segmenter("ko", {granularity:"grapheme"}) : null;
const sentences = typeof Intl.Segmenter === "function" ? new Intl.Segmenter("ko", {granularity:"sentence"}) : null;

function sentenceLines(text) {
  // Only format the display: session messages and model context keep their source text.
  return String(text).split(/\r?\n/).map(line => {
    const split = sentences
      ? Array.from(sentences.segment(line), part => part.segment.trimEnd()).join("\n")
      : line.replace(/([.!?。！？][.!?。！？]*[”’"'」』）)\]]*)[ \t]+(?=\S)/gu, "$1\n");
    return split
      .replace(/([다요죠까네라군오지야]…+[”’"'」』）)\]]*)[ \t]+(?=\S)/gu, "$1\n")
      .replace(/\b(No\.)\n(?=\d)/g, "$1 ")
      .replace(/(^|\n)((?:계율[ \t]*)?\d+조\.)\n(?=\S)/g, "$1$2 ");
  }).join("\n");
}

function animatedText(text, key, kind = "fade", singleLine = false) {
  text = singleLine ? String(text).replace(/\r?\n/g, " ") : sentenceLines(text);
  let entry = textPlayback.entries.get(key);
  if (!entry || entry.text !== text) {
    const characters = graphemes ? Array.from(graphemes.segment(text), part => part.segment) : Array.from(text);
    const duration = kind === "type" ? Math.min(6500, Math.max(250, characters.length * 24)) : 900;
    const start = Math.max(performance.now(), textPlayback.queueEnd);
    entry = {text, characters, kind, start, duration, done:motionPreference.matches || textPlayback.readKeys.has(key)};
    textPlayback.entries.set(key, entry);
    if (!entry.done) textPlayback.queueEnd = start + duration + 110;
  }
  if (state?.reviewing) entry.done = true;
  const progress = entry.done ? 1 : Math.max(0, Math.min(1, (performance.now() - entry.start) / entry.duration));
  const visible = kind === "type" ? entry.characters.slice(0, Math.floor(progress * entry.characters.length)).join("") : text;
  return '<span class="progressive-text" data-text-key="' + esc(key) + '"' + (kind === "fade" ? ' style="opacity:' + progress + '"' : '') + '>' +
    '<span class="text-visible" aria-hidden="true">' + esc(visible) + '</span><span class="sr-only text-accessible">' + esc(text) + '</span></span>';
}

function playbackAttributes(key) {
  const entry = textPlayback.entries.get(key);
  return ' data-reveal-key="' + esc(key) + '"' +
    (entry && !entry.done && performance.now() < entry.start ? ' hidden' : '');
}

function playText() {
  cancelAnimationFrame(textPlayback.frame);
  const nodes = Array.from(screen.querySelectorAll("[data-text-key]"));
  const tick = () => {
    let active = false;
    const now = performance.now();
    for (const node of nodes) {
      const entry = textPlayback.entries.get(node.dataset.textKey);
      if (!entry) continue;
      if (motionPreference.matches || now >= entry.start + entry.duration) entry.done = true;
      const block = node.closest("[data-reveal-key]");
      if (block) block.hidden = !entry.done && now < entry.start;
      const progress = entry.done ? 1 : Math.max(0, (now - entry.start) / entry.duration);
      if (entry.kind === "type") {
        const visible = entry.characters.slice(0, Math.floor(progress * entry.characters.length)).join("");
        const target = node.querySelector(".text-visible");
        if (target.textContent !== visible) target.textContent = visible;
        node.classList.toggle("is-typing", !entry.done && progress > 0);
      } else {
        node.style.opacity = progress;
      }
      active ||= !entry.done;
    }
    textPlayback.active = active;
    revealHologramAfterDialogue();
    const scroller = screen.querySelector(".scroll-area");
    if (active && textPlayback.followTail && scroller) scroller.scrollTop = scroller.scrollHeight;
    if (active) textPlayback.frame = requestAnimationFrame(tick);
  };
  tick();
}

motionPreference.addEventListener("change", () => {
  if (motionPreference.matches) {
    clueNoticeAnimation?.cancel();
    clueNoticeAnimation = null;
    playText();
    prepareHologram();
  }
  updateProgressionControls();
});

function presentationPending() {
  if (!state || state.stage === 'silence') return false;
  if (Array.from(screen.querySelectorAll('[data-text-key]')).some(node =>
    !textPlayback.entries.get(node.dataset.textKey)?.done)) return true;
  if (Array.from(screen.querySelectorAll('video')).some(video =>
    !video.ended && video.dataset.finished !== 'true' && video.dataset.failed !== 'true')) return true;
  if (Array.from(screen.querySelectorAll('.scene-visual img, .intro-frame img, .record-art img')).some(image => !image.complete)) return true;
  if (!motionPreference.matches) {
    const panel = screen.querySelector('[data-hologram-key]');
    if (panel && panel.dataset.hologramFailed !== 'true') {
      const started = hologramPlayback.get(panel.dataset.hologramKey);
      if (panel.hidden || started === undefined || performance.now() - started < HOLOGRAM_DURATION_MS) return true;
      if (panel.getAnimations({subtree:true}).some(animation => animation.playState !== 'finished')) return true;
    }
    if (Array.from(screen.querySelectorAll('.robe-reveal')).some(node =>
      node.getAnimations().some(animation => animation.playState !== 'finished'))) return true;
  }
  return false;
}

function updateProgressionControls() {
  cancelAnimationFrame(progressionFrame);
  const waiting = presentationPending();
  for (const button of screen.querySelectorAll(progressionControls)) {
    const expired = state?.stage === 'decision' && button.hasAttribute('data-choice') &&
      remainingAtAnchor !== null && remainingAtAnchor - (performance.now() - clockAnchor) / 1000 <= 0;
    button.disabled = busy || waiting || expired || button.dataset.storyDisabled === 'true';
  }
  backButton.disabled = busy || waiting;
  const hint = screen.querySelector('.intro-hint');
  if (hint) hint.hidden = waiting;
  if (waiting) progressionFrame = requestAnimationFrame(updateProgressionControls);
}

function revealHologramAfterDialogue() {
  const panel = screen.querySelector("[data-hologram-after-dialogue]");
  if (!panel?.hidden) return;
  const dialogue = panel.previousElementSibling?.querySelectorAll('.message.mentor [data-text-key]');
  if (!dialogue?.length || !Array.from(dialogue).every(node => textPlayback.entries.get(node.dataset.textKey)?.done)) return;
  panel.hidden = false;
  prepareHologram();
}

function prepareHologram() {
  hologramObserver?.disconnect();
  const panel = screen.querySelector("[data-hologram-key]");
  if (!panel || panel.hidden) return;
  const image = panel.querySelector("img");
  const key = panel.dataset.hologramKey;
  const project = () => {
    if (!panel.isConnected || !image.complete || !image.naturalWidth) return;
    const now = performance.now();
    const firstProjection = !hologramPlayback.has(key);
    if (firstProjection) hologramPlayback.set(key, now);
    const elapsed = now - hologramPlayback.get(key);
    const complete = motionPreference.matches || elapsed >= HOLOGRAM_DURATION_MS;
    panel.style.setProperty("--hologram-delay", -elapsed + "ms");
    panel.classList.toggle("hologram-complete", complete);
    panel.classList.toggle("hologram-projecting", !complete);
    const soundCue = panel.dataset.hologramSound || panel.dataset.hologramAfterDialogue;
    if (firstProjection && soundCue) window.StoryAudio?.reveal(soundCue);
    hologramObserver?.unobserve(panel);
  };
  const watch = () => {
    if (!panel.isConnected) return;
    if (hologramPlayback.has(key) || motionPreference.matches || typeof IntersectionObserver !== "function") return project();
    hologramObserver = new IntersectionObserver(entries => {
      if (entries.some(entry => entry.isIntersecting)) project();
    }, {root:screen.querySelector(".scroll-area")?.contains(panel) ? screen.querySelector(".scroll-area") : null, threshold:0.05});
    hologramObserver.observe(panel);
  };
  if (image.complete && image.naturalWidth) watch();
  else {
    image.addEventListener("load", watch, {once:true});
    const failed = () => {
      panel.dataset.hologramFailed = 'true';
      panel.classList.add('hologram-complete');
    };
    image.addEventListener('error', failed, {once:true});
    if (image.complete) failed();
  }
}

async function api(path, body) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 60000);
  try {
    const response = await fetch(path, {
      method: body === undefined ? "GET" : "POST", credentials:"same-origin", cache:"no-store",
      headers: body === undefined ? {} : {"Content-Type":"application/json"},
      body: body === undefined ? undefined : JSON.stringify(body), signal:controller.signal
    });
    const data = await response.json();
    if (!response.ok) {
      const error = new Error(typeof data.detail === "string" ? data.detail : "요청 내용을 확인해주세요.");
      error.status = response.status;
      throw error;
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("연결이 지연되고 있습니다. 진행 기록을 확인한 뒤 다시 시도해주세요.");
    if (error instanceof TypeError) throw new Error("서버에 연결하지 못했습니다. 연결을 확인해주세요.");
    throw error;
  } finally {
    clearTimeout(timeout);
  }
}

function notify(text) {
  status.textContent = text;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { status.textContent = ""; }, 7000);
}

function hideClueNotice() {
  clearTimeout(clueNoticeTimer);
  clueNoticeAnimation?.cancel();
  clueNoticeAnimation = null;
  if (typeof clueNotice.hidePopover === "function" && clueNotice.matches(":popover-open")) clueNotice.hidePopover();
  clueNotice.hidden = true;
  clueNotice.textContent = "";
  clueNotice.classList.remove("warning-notice");
}

function placeClueNotice() {
  if (clueNotice.hidden) return;
  // The notice belongs inside an open modal so it stays visible and accessible.
  const host = dialog.open ? dialog : shell;
  if (clueNotice.parentElement !== host) host.append(clueNotice);
  if (typeof clueNotice.showPopover === "function" && !clueNotice.matches(":popover-open")) clueNotice.showPopover();
}

function announceClue(clue) {
  const last = clue.title.trim().slice(-1);
  const code = last.charCodeAt(0);
  const consonant = code >= 0xac00 && code <= 0xd7a3 ? (code - 0xac00) % 28 !== 0 : "013678".includes(last);
  announceSystemNotice('단서 노트에 ' + clue.title + (consonant ? '이' : '가') + ' 추가되었습니다.');
}

function announceSystemNotice(text, warning = false) {
  hideClueNotice();
  clueNotice.classList.toggle("warning-notice", warning);
  clueNotice.hidden = false;
  placeClueNotice();
  clueNotice.textContent = text;
  if (!motionPreference.matches) {
    clueNoticeAnimation = clueNotice.animate([
      {opacity:0, offset:0}, {opacity:1, offset:.12},
      {opacity:1, offset:.78}, {opacity:0, offset:1}
    ], {duration:3400, easing:"ease-in-out", fill:"both"});
  }
  clueNoticeTimer = setTimeout(hideClueNotice, 3400);
}

dialog.addEventListener("close", placeClueNotice);

function setState(next, force = false) {
  if (!force && state && next.revision < state.revision) return false;
  const changed = !state || next.revision !== state.revision;
  const moved = !state || next.scene_id !== state.scene_id || next.reviewing !== state.reviewing;
  const warningAdded = state && next.warn_count > state.warn_count;
  if (state && next.run_id !== state.run_id) sceneDrafts.clear();
  else if (state && moved) sceneDrafts.set(state.run_id + ':' + state.scene_id, {
    draft, journalDraft, scroll:screen.querySelector('.scroll-area')?.scrollTop || 0
  });
  const savedDraft = sceneDrafts.get(next.run_id + ':' + next.scene_id);
  if (!state && next.messages.length > 4) {
    for (const message of next.messages.slice(0, -2)) textPlayback.readKeys.add('message:' + message.scene_id + ':' + message.id);
  }
  state = next;
  window.StoryAudio?.setScene(next);
  remainingAtAnchor = state.time_left;
  clockAnchor = performance.now();
  clearTimeout(silentSceneTimer);
  if (state.stage === "silence") {
    const currentGeneration = generation;
    silentSceneTimer = setTimeout(() => {
      if (generation === currentGeneration && state?.stage === "silence") poll();
    }, Math.max(0, state.silent_remaining * 1000) + 30);
  }
  if (moved) {
    hideClueNotice();
    draft = savedDraft?.draft || "";
    journalDraft = savedDraft?.journalDraft || "";
    closeDialog();
    textPlayback.queueEnd = performance.now();
  }
  if (changed || force) {
    render(moved);
    if (moved && savedDraft && state.stage !== "decision") {
      const scroller = screen.querySelector('.scroll-area');
      if (scroller) scroller.scrollTop = savedDraft.scroll;
    }
    if (state.stage === "decision") {
      const scroller = document.querySelector(".scroll-area");
      if (scroller) scroller.scrollTop = scroller.scrollHeight;
    }
  }
  if (warningAdded) announceSystemNotice('⚠️경고 ' + state.warn_count + '/3 — 주의를 받았습니다', true);
  collectEnding(next);
  return changed;
}

function picture(src, alt, className = "story-image") {
  return src ? '<img class="' + className + '" src="' + esc(src) + '" alt="' + esc(alt) + '">' : "";
}

function messageHTML(message) {
  const isDocument = state.objects.some(object => object.extra_image === message.image);
  const imageClass = isDocument ? "inline-image document-image" : "inline-image";
  const illustration = message.image ? '<button class="message-picture" data-image="' + esc(message.image) + '" aria-label="관련 이미지 크게 보기">' + picture(message.image, "관련 기록", imageClass) + '</button>' : "";
  const key = 'message:' + message.scene_id + ':' + message.id;
  const text = animatedText(message.text, key, message.speaker === "narrator" ? "fade" : "type");
  const playback = playbackAttributes(key);
  if (message.speaker === "narrator") return '<div class="narration"' + playback + '>' + text + illustration + '</div>';
  const portrait = state.portraits[message.speaker];
  return '<div class="message ' + esc(message.speaker) + '"' + playback + '>' +
    (portrait ? picture(portrait, "", "avatar") : "") +
    '<div class="message-content"><p class="speaker-line">' + esc(message.speaker === "yoonje" ? state.character_name : speakerNames[message.speaker] || message.speaker) +
    '</p><div class="bubble">' + text + '</div>' + illustration + '</div></div>';
}

function messagesHTML() {
  const pending = pendingTurn?.message.scene_id === state.scene_id ? pendingTurn : null;
  const messages = pending ? [...state.messages, pending.message] : state.messages;
  return '<div class="chat-log" role="log" aria-live="polite">' + messages.map(messageHTML).join("") +
    (pending?.generating && busy ? typingIndicatorHTML() : '') + '</div>';
}

function typingIndicatorHTML() {
  const speaker = state.scene_id === "mentor" ? "mentor" : "yoonje";
  const name = speaker === "yoonje" ? state.character_name : speakerNames[speaker];
  return '<div class="message ' + speaker + ' typing-indicator">' + picture(state.portraits[speaker], '', 'avatar') +
    '<div class="message-content"><p class="speaker-line">' + esc(name) + '</p>' +
    '<div class="bubble typing-bubble" role="status" aria-label="' + esc(name) + ' 답변을 기다리는 중">' +
    '<span class="typing-dots" aria-hidden="true"><span></span><span></span><span></span></span></div></div></div>';
}

function settlePendingTurn(next) {
  if (!pendingTurn) return;
  const message = pendingTurn.message;
  const key = 'message:' + message.scene_id + ':' + message.id;
  const confirmed = next?.scene_id === message.scene_id && next.messages.find(item =>
    item.speaker === 'user' && !pendingTurn.previousIds.has(item.id) && item.text === message.text);
  const playback = textPlayback.entries.get(key);
  if (confirmed && playback) {
    // Keep the in-flight typewriter position when the server confirms the send.
    textPlayback.entries.set('message:' + confirmed.scene_id + ':' + confirmed.id, playback);
  }
  textPlayback.entries.delete(key);
  pendingTurn = null;
}

function choicesHTML(compact = false) {
  return '<div class="' + (compact ? 'suggestions choice-suggestions' : 'story-choices') + '"' + (compact ? ' role="group" aria-label="예시 대화 보기" tabindex="0"' : '') + '>' + state.choices.map((choice, index) =>
    '<button class="choice" data-choice="' + esc(choice.id) + '" ' + (choice.disabled ? "disabled" : "") + '>' +
    (!compact && state.numbered_choices ? '<span class="choice-num">' + (index + 1) + '</span>' : '') + '<span class="choice-text">' + esc(compact || state.stage === "decision" ? choice.title : sentenceLines(choice.title)) +
    '</span>' + (choice.disabled ? '<span class="choice-tag">경고 받음</span>' : "") + '</button>').join("") + '</div>';
}

function composerHTML() {
  return '<form id="chat-form" class="composer"><label class="sr-only" for="message-input">하고 싶은 말</label>' +
    '<textarea id="message-input" rows="1" maxlength="2000" placeholder="하고 싶은 말을 입력하세요">' + esc(draft) +
    '</textarea><button class="send" type="submit" aria-label="메시지 보내기">' + arrow + '</button></form>';
}

function rulesHTML(rules = state.rules, start = 1, animate = false, singleLine = false) {
  const list = '<ol class="rule-list' + (singleLine ? ' rule-list-single-line' : '') + '" start="' + start + '">' + rules.map((rule, index) => {
    const twoLines = singleLine && start + index === 5;
    const keepOneLine = singleLine && !twoLines;
    return '<li' + (twoLines ? ' class="rule-two-lines"' : '') + '>' +
      (animate ? animatedText(rule, state.scene_id + ':rule:' + (start + index), "fade", keepOneLine) : esc(keepOneLine ? rule.replace(/\r?\n/g, " ") : sentenceLines(rule))) + '</li>';
  }).join("") + '</ol>';
  return singleLine ? '<div class="rule-list-scroll" tabindex="0" aria-label="계율 목록 · 좌우로 스크롤">' + list + '</div>' : list;
}

function rulesArtworkHTML() {
  return window.RuleArtwork.html(state.rules);
}

function rulesModal(parent = null) {
  modal("수확자의 계율", rulesArtworkHTML() + '<button class="primary" data-close>확인</button>', parent);
  dialog.classList.add("rules-dialog");
}

function recordHTML() {
  return '<figure class="record-art hologram-record" data-hologram-key="' + esc(state.scene_id + ':' + state.image) + '" data-hologram-sound="record"><button class="message-picture" data-image="' + esc(state.image) + '" aria-label="수확 대상자 기록 크게 보기">' +
    picture(state.image, "수확령 · 이윤제 대상자 열람 기록", "inline-image document-image") + '</button>' +
    '<figcaption class="sr-only">이윤제, 44세, 신분 번호 0261024.2. 중공업 공장 노동자. 아내는 2년 전 수확으로 사망. 딸 2명, 11세와 13세. 한부모 가정. 범죄 기록 없음.</figcaption></figure>';
}

function explorationVisualHTML() {
  const pointTops = new Map(state.objects.map(object => [object.id, object.y + '%']));
  const drawers = state.objects.filter(object => ['drawer1', 'drawer2'].includes(object.id)).sort((a, b) => a.y - b.y);
  if (drawers.length === 2) {
    // Keep this close cluster's 44px targets separate on narrow artwork.
    const middle = (drawers[0].y + drawers[1].y) / 2;
    const upperTop = 'min(' + drawers[0].y + '%,calc(' + middle + '% - 24px))';
    pointTops.set(drawers[0].id, upperTop);
    pointTops.set(drawers[1].id, 'max(' + drawers[1].y + '%,calc(' + middle + '% + 24px))');
    const family = state.objects.find(object => object.id === 'family');
    if (family && Math.abs(family.x - drawers[0].x) < 10) {
      pointTops.set(family.id, 'min(' + family.y + '%,calc(' + upperTop + ' - 48px))');
    }
  }
  return '<div class="room ' + (state.lantern_on ? "" : "lamp-off") + '">' +
    picture(state.image, "달력, 가족사진, 서랍과 컴퓨터가 있는 거실", "") +
    state.objects.map((object, index) => {
      const found = state.clues.some(clue => clue.id === object.id);
      const label = object.title + ' 살펴보기' + (found ? ' · 확인함' : '');
      return '<button class="hotspot ' + (found ? "found" : "") +
        '" style="left:' + object.x + '%;top:' + pointTops.get(object.id) + ';--pulse-delay:' + (-index * .35) + 's" data-inspect="' + object.id +
        '" aria-label="' + esc(label) + '" title="' + esc(label) + '"></button>';
    }).join("") +
    '<button class="hotspot lamp-switch" style="left:9%;top:42%" data-action="lantern" aria-pressed="' + state.lantern_on +
    '" aria-label="랜턴 ' + (state.lantern_on ? "끄기" : "켜기") + '" title="랜턴 ' + (state.lantern_on ? "끄기" : "켜기") + '"></button></div>';
}

function intelHTML() {
  return '<figure class="record-art intel-record hologram-record" data-hologram-key="' + esc(state.scene_id + ':' + state.image) + '" data-hologram-after-dialogue="intel" hidden aria-label="스승의 추가 정보 기록"><button class="message-picture" data-image="' + esc(state.image) + '" aria-label="스승의 추가 정보 크게 보기">' +
    picture(state.image, "수확령 · 스승의 추가 정보 수신", "inline-image document-image") + '</button>' +
    '<figcaption class="sr-only">대상자 이윤제, 발신 스승. 아래 내용은 사실 여부가 확인되지 않은 정보입니다. 직장 내 괴롭힘과 성희롱: 신고 접수 기록 있음, 미확인. 합의금: 지급 내역 있음, 미확인. 스승 메모: 보내지 못한 정보다. 판단은 네 몫이다. 초안 문구, 내용 미확정.</figcaption></figure>';
}

function journalHTML() {
  return '<p class="journal-instruction">' + animatedText('무엇을 근거로 판단했는지 수확일지에 남기세요.', state.scene_id + ':instruction') + '</p>' +
    '<form id="journal-form" class="journal-sheet">' + picture(state.image, "수확일지 양식", "journal-background") +
    '<label class="sr-only" for="journal-subject">수확 대상</label><input id="journal-subject" class="journal-subject" readonly value="' + esc(state.journal_subject) + '">' +
    '<label class="sr-only" for="journal-content">선택의 근거와 이유</label><textarea id="journal-content" class="journal-content" required maxlength="2000" placeholder="선택의 근거와 이유를 기록하세요…">' + esc(journalDraft) + '</textarea></form>' +
    '<p class="journal-note">' + esc(state.ending_grade.record) + ' · 대화 단서 ' + state.clue_count + '/6</p>';
}

function resultHTML(view = state, animate = true) {
  const result = view.result;
  return '<article class="ending-result ' + esc(result.id) + '"><p class="section-label">당신의 선택이 만든 색</p>' +
    '<div class="result-copy"><p class="result-latin">' + esc(result.latin) + '</p><h2>' + esc(result.name) +
    '</h2><p class="result-type">' + esc(result.label) + ' · ' + esc(result.color) + '</p></div>' +
    '<p class="result-description">' + (animate ? animatedText(result.description, view.scene_id + ':description') : esc(result.description)) + '</p><p class="clue-grade">' + esc(view.ending_grade.label) + ' · 대화 단서 ' + view.clue_count + '/6</p></article>';
}

function endingBasis(view) {
  if (view.result?.id === "fulvus") return null;
  const content = view.journal?.content;
  return content ? {subject:view.journal.subject, content} : null;
}

function basisHTML(basis) {
  return '<section class="collection-basis"><h3>수확 일지</h3>' +
    (basis.subject ? '<p class="section-label">' + esc(basis.subject) + '</p>' : '') +
    '<p class="journal-record">' + esc(basis.content) + '</p></section>';
}

function endingSaveStatus() {
  if (!state || state.stage !== "result") return;
  const node = screen.querySelector("#ending-save-status");
  if (!node) return;
  const saved = collectedEndings.has(state.run_id);
  node.hidden = saved;
  node.innerHTML = saved ? '' : collectionErrors.has(state.run_id)
    ? '이 브라우저에 엔딩을 보관하지 못했습니다. <button class="text-button" data-ending-save>다시 보관하기</button>'
    : '엔딩 모음에 보관하는 중…';
}

async function collectEnding(view, retry = false) {
  if (view.reviewing) return;
  const record = window.EndingCollection.snapshot(view, endingBasis(view));
  if (!record || collectedEndings.has(record.id) || collectingEndings.has(record.id) || (!retry && collectionErrors.has(record.id))) return;
  collectingEndings.add(record.id);
  collectionErrors.delete(record.id);
  endingSaveStatus();
  try {
    await window.EndingCollection.save(record);
    collectedEndings.add(record.id);
  } catch {
    collectionErrors.add(record.id);
  } finally {
    collectingEndings.delete(record.id);
    endingSaveStatus();
  }
}

function resultBasisHTML() {
  const basis = endingBasis(state);
  return (basis ? basisHTML(basis) : '') + (state.reviewing ? '' : '<p class="collection-info" id="ending-save-status" role="status"></p>');
}

function endingVisualHTML() {
  if (state.video) return '<div class="scene-video-frame"><video class="ending-video" src="' + esc(state.video) + '" poster="' + esc(state.image) +
    '" muted playsinline disablepictureinpicture controlslist="nodownload nofullscreen noremoteplayback" preload="auto" aria-label="' + esc(state.title) +
    '"></video><button class="scene-video-play secondary" hidden>영상 재생</button></div>';
  if (["ending_truth_mail", "ending_target_mail"].includes(state.scene_id)) {
    return '<figure class="record-art hologram-record ending-mail" data-hologram-key="' + esc(state.scene_id + ':' + state.image) +
      '" data-hologram-sound="' + esc(state.scene_id) + '"><button class="message-picture ending-picture" data-image="' + esc(state.image) +
      '" aria-label="미성년보호청 메일 크게 보기">' + picture(state.image, state.title, 'story-image ending-image') + '</button></figure>';
  }
  return '<button class="ending-picture" data-image="' + esc(state.image) + '" aria-label="장면 이미지 크게 보기">' + picture(state.image, state.title, 'story-image ending-image' + (state.reveal ? ' robe-reveal' : '')) + '</button>';
}

function sceneVideoHTML() {
  return '<div class="scene-video-frame"><video class="scene-video" src="' + esc(state.video) + '" poster="' + esc(state.image) +
    '" data-video-sound="' + Boolean(state.video_sound) + '" playsinline disablepictureinpicture controlslist="nodownload nofullscreen noremoteplayback" preload="auto" aria-label="' +
    esc(state.title) + '"></video><button class="scene-video-play secondary" hidden>영상을 재생하려면 눌러주세요</button></div>';
}

function prepareSceneVideo(video) {
  const retry = video.parentElement.querySelector(".scene-video-play");
  const logo = video.classList.contains("ending-video");
  const size = () => {
    if (!logo && video.videoWidth && video.videoHeight) video.closest(".scene-visual").style.aspectRatio = video.videoWidth + ' / ' + video.videoHeight;
    if (video.videoWidth && video.videoHeight && video.closest('#screen')?.classList.contains('decision-screen')) {
      screen.style.setProperty('--decision-video-ratio', video.videoHeight / video.videoWidth);
    }
  };
  const play = () => {
    if (video.ended || video.dataset.finished === "true" || video.dataset.failed === "true" || video.dataset.playPending === "true") return;
    video.dataset.playPending = "true";
    video.muted = video.dataset.videoSound !== "true" || window.StoryAudio?.getState().enabled === false;
    video.play().then(() => { retry.hidden = true; }).catch(error => {
      if (!video.isConnected || error.name === "AbortError") return;
      if (error.name === "NotAllowedError") retry.hidden = false;
      else {
        video.dataset.failed = "true";
        retry.hidden = true;
        notify("영상을 불러오지 못했습니다. 나머지 대사가 끝나면 이야기를 계속 진행할 수 있습니다.");
      }
    }).finally(() => { video.dataset.playPending = "false"; });
  };
  if (!video.dataset.bound) {
    video.dataset.bound = "true";
    video.addEventListener("loadedmetadata", size);
    video.addEventListener("ended", () => { video.dataset.finished = "true"; retry.hidden = true; });
    video.addEventListener("error", () => {
      video.dataset.failed = "true";
      retry.hidden = true;
      if (video.isConnected) notify("영상을 불러오지 못했습니다. 나머지 대사가 끝나면 이야기를 계속 진행할 수 있습니다.");
    });
    retry.addEventListener("click", play);
    if (logo && motionPreference.matches) retry.hidden = false;
  }
  size();
  // Reuse the same element and playback position across timed dialogue updates.
  if (retry.hidden) play();
}

function startIntroVideo(media) {
  const video = media.querySelector("video");
  const photo = media.querySelector(".intro-still");
  const retry = screen.querySelector('.intro-video-play');
  const controller = new AbortController();
  introMediaController = controller;
  let holdTimer;
  video.muted = true;
  controller.signal.addEventListener("abort", () => {
    clearTimeout(holdTimer);
    video.pause();
  }, {once:true});

  const play = async () => {
    if (controller.signal.aborted || video.dataset.failed === 'true') return;
    try {
      await video.play();
      if (!controller.signal.aborted) {
        media.classList.add("is-playing");
        retry.hidden = true;
      }
    } catch (error) {
      if (controller.signal.aborted || error.name === 'AbortError') return;
      if (error.name === 'NotAllowedError') retry.hidden = false;
      else failed();
    }
  };
  const failed = () => {
    video.dataset.failed = 'true';
    retry.hidden = true;
    notify('영상을 불러오지 못했습니다. 나머지 대사가 끝나면 이야기를 계속 진행할 수 있습니다.');
  };
  video.addEventListener('ended', () => { video.dataset.finished = 'true'; retry.hidden = true; }, {signal:controller.signal});
  video.addEventListener('error', failed, {signal:controller.signal});
  retry.addEventListener('click', play, {signal:controller.signal});
  const holdPhoto = () => {
    if (!controller.signal.aborted) holdTimer = setTimeout(play, INTRO_PHOTO_HOLD_MS);
  };
  // 사진을 실제로 표시한 시점부터 여유를 두고, 영상 준비가 끝나면 전환한다.
  if (photo.complete) holdPhoto();
  else {
    photo.addEventListener("load", holdPhoto, {once:true, signal:controller.signal});
    photo.addEventListener("error", holdPhoto, {once:true, signal:controller.signal});
  }
}

function render(moved = false) {
  if (!state) return;
  backButton.hidden = !state.can_back;
  backButton.disabled = busy;
  backButton.title = state.back_title ? '이전 장면: ' + state.back_title : '이전 장면 보기';
  const currentIntro = screen.querySelector(".intro-frame");
  if (state.stage === "intro" && state.video && currentIntro?.dataset.sceneId === state.scene_id) {
    updateProgressionControls();
    return;
  }
  introMediaController?.abort();
  introMediaController = null;
  hologramObserver?.disconnect();
  cancelAnimationFrame(textPlayback.frame);
  cancelAnimationFrame(progressionFrame);
  textPlayback.active = false;
  const previousScroller = screen.querySelector(".scroll-area");
  const previousScroll = previousScroller?.scrollTop || 0;
  const previousSuggestions = screen.querySelector(".suggestions")?.scrollLeft || 0;
  const previousVisual = screen.querySelector(".scene-visual");
  const previousVisualScroll = previousVisual?.scrollTop || 0;
  if (moved) textPlayback.followTail = state.stage === "decision";
  title.textContent = state.title || "문이 열린 순간";
  shell.classList.toggle("silent-scene", state.stage === "silence");
  shell.classList.toggle("intro-scene", state.stage === "intro");
  screen.classList.toggle("exploration-screen", state.stage === "exploration");
  screen.classList.toggle("decision-screen", state.stage === "decision");
  screen.classList.toggle("decision-ready", state.stage === "decision" && state.decision_ready);
  const logoVideo = ["ending_bad_motto", "ending_bad_fade"].includes(state.scene_id);
  screen.classList.toggle("logo-video-screen", logoVideo);
  screen.classList.toggle("logo-video-empty", logoVideo && state.messages.length === 0);
  screen.classList.toggle("immersive-screen", ["decision", "ending", "report", "result", "bad_result"].includes(state.stage) && (!state.video || state.stage === "decision"));
  let body = "", footer = "", toolbar = "", visual = "";
  if (state.stage === "silence") {
    screen.innerHTML = '<div class="silent-frame">' + picture(state.image, "문을 연 이윤제의 굳은 표정", "") + '</div>';
    return;
  }
  if (state.stage === "intro") {
    const visual = state.video
      ? '<span class="intro-media"><video class="intro-video" src="' + esc(state.video) + '" muted playsinline preload="auto" aria-label="수확령 로고 애니메이션"></video>' + picture(state.image, "", "intro-still") + '</span>'
      : picture(state.image, "", "");
    body = '<button class="intro-frame" data-scene-id="' + esc(state.scene_id) + '" data-action="' + (state.reviewing ? 'forward' : 'advance') + '" aria-label="다음 장면">' +
      visual + '<div class="intro-copy">' + state.messages.map(message => '<p>' + animatedText(message.text, 'message:' + message.scene_id + ':' + message.id, message.speaker === "narrator" ? "fade" : "type") + '</p>').join("") +
      '<span class="intro-hint">화면을 눌러 계속</span></div></button>' +
      (state.video ? '<button class="scene-video-play intro-video-play secondary" hidden>영상을 재생하려면 눌러주세요</button>' : '');
  } else if (state.stage === "selection") {
    const questionIcon = picture('/assets/images/' + encodeURIComponent('회청색 둥근 물음표 아이콘.png'), '', 'candidate-question');
    const lockIcon = picture('/assets/images/' + encodeURIComponent('미니멀 골드 자물쇠 아이콘.png'), '', 'candidate-lock');
    body = messagesHTML() + '<div class="candidate-list" role="group" aria-label="수확 대상자 명단">' +
      '<button class="candidate candidate-available" type="button" data-choice="yoonje" aria-label="이윤제 정보 열람">' + picture(state.portraits.yoonje, "", "") +
      '<span class="candidate-name">이윤제</span><span class="candidate-mark" aria-hidden="true">✓</span></button>' +
      ['B', 'C'].map(id => '<button class="candidate empty" type="button" data-candidate-locked="' + id + '" aria-label="대상자 ' + id + ', 잠김 안내">' +
        '<span class="empty-portrait" aria-hidden="true">' + questionIcon + '</span><span class="candidate-name">대상자 ' + id +
        '</span>' + lockIcon + '</button>').join("") + '</div>';
  } else if (state.stage === "record") {
    body = messagesHTML() + recordHTML();
  } else if (state.stage === "exploration") {
    visual = explorationVisualHTML();
  } else if (state.stage === "conversation") {
    visual = state.video ? sceneVideoHTML() : '<button class="scene-card" data-image="' + esc(state.image) + '" aria-label="장면 이미지 크게 보기">' + picture(state.image, "현재 이야기와 관련된 장면", "") + '</button>';
    body = messagesHTML();
    footer = '<div class="suggestions" role="group" aria-label="예시 대화 보기" tabindex="0">' + state.topics.map(topic => '<button class="chip" data-topic="' + topic.id + '">' + esc(topic.question) + '</button>').join("") +
      '</div>' + composerHTML() + '<button class="secondary finish-chat" data-finish-chat data-requires-question="' + (state.question_count === 0) + '">대화 마무리 →</button>';
  } else if (state.stage === "intel") {
    body = messagesHTML() + intelHTML();
  } else if (state.stage === "decision") {
    toolbar = '<div class="decision-clock"><span>남은 시간</span><strong id="countdown" role="timer">01:00</strong><span>마지막 판단</span></div>';
    visual = state.video ? sceneVideoHTML() : '<button class="scene-card" data-image="' + esc(state.image) + '" aria-label="장면 이미지 크게 보기">' + picture(state.image, "이윤제와 두 딸", "decision-scene") + '</button>';
    body = messagesHTML() +
      (state.decision_ready ? rulesHTML(state.rules.slice(3), 4, true) : '<p class="center muted">당신의 판단을 기다리는 목소리들.</p>');
    if (state.decision_ready) footer = '<div class="final-decision-choices" role="group" aria-label="최종 선택 5가지">' + choicesHTML() + '</div>';
  } else if (state.stage === "journal") {
    body = journalHTML();
    footer = '<button class="primary" type="submit" form="journal-form">수확일지 기록 →</button>';
  } else if (state.stage === "result") {
    visual = '<button class="scene-card" data-image="' + esc(state.image) + '" aria-label="결과 이미지 크게 보기">' + picture(state.image, state.result.color + " 로브를 입은 수확자", "result-art") + '</button>';
    body = resultHTML() + resultBasisHTML();
  } else if (state.stage === "bad_result") {
    visual = '<button class="scene-card" data-image="' + esc(state.image) + '" aria-label="결과 이미지 크게 보기">' + picture(state.image, "선택을 포기한 수확자", "result-art") + '</button>';
    body = '<article class="bad-result"><h2>선택을 포기한 수확자</h2><p class="ending-quote">' + animatedText('선택하지 않은 자에게는 색이 주어지지 않는다.', state.scene_id + ':quote') + '</p></article>';
    footer = '<button class="primary" data-reset>처음부터 다시 시작</button>';
  } else if (state.stage === "reflection") {
    body = '<article class="ending-reflection">' + picture(state.image, "수확령", "record-seal") + state.messages.map(message => '<p>' + animatedText(message.text, 'message:' + message.scene_id + ':' + message.id) + '</p>').join("") + '</article>';
    footer = '<button class="primary" data-reset>처음부터 다시 시작</button>';
  } else if (["ending", "report"].includes(state.stage)) {
    visual = endingVisualHTML();
    body = messagesHTML() + choicesHTML();
  } else {
    if (state.video) visual = sceneVideoHTML();
    else if (state.image) visual = '<button class="scene-card" data-image="' + esc(state.image) + '" aria-label="장면 이미지 크게 보기">' + picture(state.image, state.title) + '</button>';
    body = messagesHTML();
    if (state.stage === "rules") body += rulesHTML(state.rules, 1, true, true);
    if (state.input) footer = choicesHTML(true) + composerHTML();
    else body += choicesHTML();
  }
  if (state.can_advance && state.stage !== "intro") {
    const locked = state.stage === "exploration" && state.clues.length < 5;
    const label = state.advance_label || (state.stage === "exploration" ? "탐색 마치고 대화하기" : state.scene_id === "guide" ? "명단 받기" : state.scene_id === "record" ? "스승과 대상 확인하기" : state.scene_id === "daughters" ? "마지막 판단 시작 · 60초" : "계속");
    footer += '<button class="primary advance-button" data-action="advance" ' + (locked ? "disabled" : "") + '>' + label + ' →</button>';
  }
  if (["exploration", "conversation", "intel", "allegation"].includes(state.stage)) {
    toolbar = '<nav class="progress-strip" aria-label="진행 기록"><button class="text-button" data-notes>단서 노트 ' +
      state.clues.length + '/5 · 대화 ' + state.clue_count + '/6</button><span>' +
      (state.stage === "conversation" ? '질문 ' + state.question_count + ' · ' : "") + '경고 ' + state.warn_count + '/3</span></nav>';
  }
  if (state.reviewing) footer = '<button class="primary" data-action="forward">' + (state.forward_is_current ? '현재 장면으로 돌아가기' : '다음 장면 보기') + ' →</button>';
  const visualKey = state.scene_id + ':' + (state.video || state.image) + ':' + state.lantern_on + (state.stage === "exploration" ? ':' + state.clues.map(clue => clue.id).join(',') : '');
  const documentVisual = ["record", "intel"].includes(state.stage) || state.scene_id === "ending_bad_document" || state.scene_id.endsWith("_mail");
  const scrollingVisual = state.stage === "conversation";
  const visualHTML = visual ? '<section class="scene-visual' + (documentVisual ? ' document-visual' : '') + (state.scene_id === "guide" ? ' guide-visual' : '') + '" data-visual-key="' + esc(visualKey) + '" aria-label="장면 이미지">' + visual + '</section>' : '';
  screen.innerHTML = toolbar + (scrollingVisual ? '' : visualHTML) +
    '<div class="reading-pane">' +
    '<div class="scroll-area ' + (state.stage === "intro" ? "intro-area" : "") + '" tabindex="0" aria-label="대화와 이야기">' + (scrollingVisual ? visualHTML : '') + body + '</div></div>' +
    (footer ? '<div class="screen-footer">' + footer + '</div>' : "");
  const newVisual = screen.querySelector(".scene-visual");
  const reusedVisual = previousVisual && previousVisual.dataset.visualKey === visualKey && newVisual;
  if (reusedVisual) {
    newVisual.replaceWith(previousVisual);
    previousVisual.querySelectorAll("button").forEach(button => { button.disabled = busy; });
  } else previousVisual?.querySelectorAll("video").forEach(video => video.pause());
  if (state.stage === "exploration" && !moved) screen.querySelector(".scene-visual").scrollTop = previousVisualScroll;
  screen.querySelectorAll(progressionControls).forEach(button => { button.dataset.storyDisabled = String(button.disabled); });
  if (busy) screen.querySelectorAll("button,input,textarea").forEach(element => { element.disabled = true; });
  const scroller = document.querySelector(".scroll-area");
  if (scroller) {
    scroller.scrollTop = moved ? 0 : previousScroll;
    scroller.addEventListener("scroll", () => { textPlayback.followTail = scroller.scrollHeight - scroller.clientHeight - scroller.scrollTop < 48; });
  }
  const suggestions = screen.querySelector(".suggestions");
  if (suggestions && !moved) suggestions.scrollLeft = previousSuggestions;
  suggestions?.addEventListener("wheel", event => {
    if (Math.abs(event.deltaY) > Math.abs(event.deltaX) && suggestions.scrollWidth > suggestions.clientWidth) {
      const before = suggestions.scrollLeft;
      suggestions.scrollLeft += event.deltaY;
      if (suggestions.scrollLeft !== before) event.preventDefault();
    }
  }, {passive:false});
  const introMedia = screen.querySelector(".intro-media");
  if (introMedia) startIntroVideo(introMedia);
  const endingVideo = screen.querySelector(".ending-video");
  if (endingVideo) prepareSceneVideo(endingVideo);
  const sceneVideo = screen.querySelector(".scene-video");
  if (sceneVideo) prepareSceneVideo(sceneVideo);
  playText();
  if (state.stage !== "intel") prepareHologram();
  endingSaveStatus();
  updateClock();
  updateProgressionControls();
}

async function act(action, value = "") {
  if (busy || !state) return false;
  if (progressionActions.has(action) && presentationPending()) return false;
  if (state.reviewing && !["back", "forward"].includes(action)) return false;
  const sourceScene = state.scene_id;
  const lanternWasOn = state.lantern_on;
  const sentDraft = draft;
  busy = true;
  const tracked = ["back", "forward", "journal", "choose"].includes(action) || (state.dialogue_enabled && (action === "chat" || (state.stage === "conversation" && action === "topic")));
  if (tracked && (!pendingRequest || pendingRequest.action !== action || pendingRequest.value !== value)) {
    pendingRequest = {id:crypto.randomUUID(), action, value};
  }
  const requestId = tracked ? pendingRequest.id : undefined;
  if (["chat", "topic"].includes(action)) {
    textPlayback.followTail = true;
    pendingTurn = {
      message:{id:'pending-' + (requestId || crypto.randomUUID()), scene_id:sourceScene, speaker:'user',
        text:action === 'topic' ? state.topics.find(topic => topic.id === value)?.question || value : value.trim()},
      previousIds:new Set(state.messages.map(message => message.id)),
      generating:state.dialogue_enabled
    };
    if (action === "chat") draft = "";
  }
  render();
  let success = false;
  try {
    const next = action === "chat"
      ? await api("/api/chat", {message:value, revision:state.revision, request_id:requestId})
      : await api("/api/action", {action, value, revision:state.revision, request_id:requestId});
    if (action === "chat") draft = "";
    if (action === "journal") journalDraft = "";
    if (tracked) pendingRequest = null;
    settlePendingTurn(next);
    setState(next);
    success = true;
  } catch (error) {
    notify(error.message);
    if (error.status === 401) showExpired(error.message);
    else {
      try {
        const latest = await api("/api/game");
        if (requestId && latest.last_request_id === requestId) {
          if (action === "chat") draft = "";
          if (action === "journal") journalDraft = "";
          pendingRequest = null;
          success = true;
          notify("진행 기록을 확인했습니다.");
        }
        settlePendingTurn(latest);
        setState(latest);
      } catch { /* 입력과 요청 번호를 보존하여 같은 전송 버튼으로 재시도한다. */ }
    }
  } finally {
    settlePendingTurn();
    if (!success && action === "chat" && state?.scene_id === sourceScene) draft = sentDraft || value;
    busy = false;
    render();
  }
  if (success && state.confirmation) confirmChoice(state.confirmation);
  if (success && ["back", "forward"].includes(action)) {
    const target = state.reviewing
      ? (state.can_back ? backButton : screen.querySelector('.screen-footer [data-action="forward"]'))
      : screen.querySelector('#message-input, .advance-button, .intro-frame') || backButton;
    target?.focus({preventScroll:true});
  }
  if (success && action === "lantern" && !lanternWasOn && state.lantern_on) window.StoryAudio?.effect("lantern");
  if (success && ["chat", "topic"].includes(action)) {
    const scroller = document.querySelector(".scroll-area");
    if (scroller) scroller.scrollTop = scroller.scrollHeight;
  }
  return success;
}

function closeDialog() {
  modalVersion++;
  dialogParent = null;
  dialog.close();
}

function previousDialog() {
  if (dialogParent) {
    const parent = dialogParent;
    parent();
  } else closeDialog();
}

function modal(heading, content, parent = null) {
  modalVersion++;
  dialogParent = parent;
  if (dialog.open) window.StoryAudio?.cancelInspect();
  dialog.classList.remove("rules-dialog", "mission-menu", "ending-collection-dialog");
  dialogBody.innerHTML = '<div class="dialog-inner"><div class="dialog-top"><div class="dialog-heading">' +
    (parent ? '<button class="icon-button dialog-back" type="button" data-dialog-back aria-label="이전 메뉴로 돌아가기" title="이전 메뉴로 돌아가기">' + arrow + '</button>' : '') +
    '<h2 id="dialog-title">' + esc(heading) + '</h2></div><button class="icon-button" data-close aria-label="대화상자 닫기">×</button></div>' + content + '</div>';
  if (!dialog.open) dialog.showModal();
  dialog.scrollTop = 0;
  window.StoryAudio?.refreshControls();
  placeClueNotice();
}

function confirmChoice(choice) {
  return modal("이 선택을 확정할까요?", '<p class="dialog-copy">' + esc(sentenceLines(choice.title)) + '</p>' +
    (state.stage === "decision" ? '<p class="muted">선택을 확인하는 동안에도 시간이 흐릅니다.</p>' : "") +
    '<button class="primary" data-confirm="' + esc(choice.id) + '">선택 확정</button><button class="secondary" data-close>다시 생각하기</button>');
}

function clueModal(clue, parent = null) {
  if (!clue) return;
  modal(clue.title, picture(clue.image, clue.title, "dialog-image") +
    (clue.extra_image ? picture(clue.extra_image, "진단서", "dialog-image document-image") : "") +
    '<p class="dialog-copy">' + esc(sentenceLines(clue.text)) + '</p><button class="primary" data-close>확인</button>', parent);
}

function notesModal(parent = null) {
  modal("단서 노트", '<p class="section-label">탐색한 물건 · ' + state.clues.length + ' / 5</p>' +
    (state.clues.length ? state.clues.map(clue => '<button class="clue-card" data-clue="' + clue.id + '"><strong>' + esc(clue.title) + '</strong><p>' + esc(sentenceLines(clue.text)) + '</p></button>').join("") : '<p class="muted">아직 조사한 물건이 없습니다.</p>') +
    '<p class="section-label">대화와 장면에서 확인한 단서 · ' + state.clue_count + ' / 6</p>' +
    (state.dialogue_clues.length ? '<ul class="clue-summary">' + state.dialogue_clues.map(clue => '<li>' + esc(clue.title) + '</li>').join("") + '</ul>' : '<p class="muted">아직 확인한 대화 단서가 없습니다.</p>') +
    '<button class="secondary" data-close>' + (parent ? '임무 메뉴로' : '이야기로 돌아가기') + '</button>', parent);
}

function menuModal() {
  const modeLabel = state?.mode === "mock" ? "모의 응답 모드입니다. 실제 LLM을 사용하지 않습니다." : state?.mode === "openai" ? "입력칸에서는 현재 장면의 인물과 AI 대화를 나눕니다. 명확한 선택 의도는 기존 이야기 흐름으로 이어집니다." : "예시 대화로 진행하는 시연입니다.";
  const cards = [
    ["단서 노트", "픽셀 아트 단서 노트 아이콘.png", "data-notes"],
    ["계율 다시 보기", "계율 다시보기 픽셀 봉인 카드.png", "data-rules"],
    ["엔딩 모음", "빈티지 폴라로이드 사신 카드.png", "data-endings"],
    ["처음부터 다시 시작", "레트로 픽셀 새로고침 카드.png", "data-restart-confirm"]
  ];
  modal("임무 메뉴", '<p class="demo-label">' + modeLabel + ' 진행 기록은 현재 서버 실행 중 유지됩니다.</p>' +
    '<div class="menu-card-grid">' + cards.map(([label, file, action]) =>
      '<button class="menu-card" type="button" ' + action + ' aria-label="' + label + '"><img src="/assets/images/' + encodeURIComponent(file) + '" alt="" width="1280" height="1280"></button>'
    ).join("") + '</div>' +
    (state?.journal ? '<button class="secondary" data-journal>작성한 수확일지</button>' : '') +
    '<button class="primary" data-close>이야기로 돌아가기</button>');
  dialog.classList.add("mission-menu");
}

function endingRecordHTML(record) {
  return '<article class="collected-ending">' + picture(record.image, record.result.name + ' 엔딩', 'collected-ending-image') +
    resultHTML(record, false) +
    (record.choice_title ? '<p class="collection-choice">나의 선택 · ' + esc(record.choice_title) + '</p>' : '') +
    (record.report_answer ? '<p class="collection-choice">스승에게 한 보고 · ' + (record.report_answer === 'yes' ? '수확했습니다' : '수확하지 않았습니다') + '</p>' : '') +
    (record.result.id !== "fulvus" && record.basis ? basisHTML(record.basis) : '') +
    '<p class="collection-date">' + esc(new Date(record.saved_at).toLocaleString('ko-KR')) + '</p></article>';
}

async function endingsModal(parent = null) {
  modal("엔딩 모음", '<p class="muted" role="status">엔딩 기록을 불러오는 중…</p>', parent);
  dialog.classList.add("ending-collection-dialog");
  const version = modalVersion;
  try {
    const records = await window.EndingCollection.list();
    if (!dialog.open || modalVersion !== version) return;
    modal("엔딩 모음", '<p class="collection-info">이 브라우저에 보관한 엔딩 ' + records.length + '개 · 배드엔딩 제외</p>' +
      (records.length ? records.map(endingRecordHTML).join('') : '<div class="empty-note"><h3>아직 보관한 엔딩이 없습니다</h3><p>이야기의 결과가 이곳에 남습니다.</p></div>') +
      '<button class="secondary" data-menu>임무 메뉴로</button><button class="primary" data-close data-story-close>이야기로 돌아가기</button>', parent);
    dialog.classList.add("ending-collection-dialog");
  } catch {
    if (!dialog.open || modalVersion !== version) return;
    modal("엔딩 모음", '<p class="dialog-copy">브라우저의 엔딩 저장소를 열지 못했습니다. 저장소 사용을 허용한 뒤 다시 시도해주세요. 이야기 진행에는 영향을 주지 않습니다.</p>' +
      '<button class="secondary" data-endings>다시 불러오기</button><button class="primary" data-close data-story-close>이야기로 돌아가기</button>', parent);
  }
}

function updateClock() {
  const clock = document.querySelector("#countdown");
  if (!clock || remainingAtAnchor === null) return;
  const remaining = Math.max(0, Math.ceil(remainingAtAnchor - (performance.now() - clockAnchor) / 1000));
  clock.textContent = String(Math.floor(remaining / 60)).padStart(2, "0") + ":" + String(remaining % 60).padStart(2, "0");
  clock.classList.toggle("urgent", remaining <= 10);
  if (remaining === 0) {
    screen.querySelectorAll("[data-choice]").forEach(button => { button.disabled = true; });
    dialogBody.querySelectorAll("[data-confirm]").forEach(button => { button.disabled = true; });
  }
}

async function poll() {
  if (!state || !["decision", "silence"].includes(state.stage) || busy || polling) return;
  polling = true;
  const requestGeneration = generation;
  try {
    const next = await api("/api/game");
    if (generation === requestGeneration) setState(next);
  } catch (error) {
    if (error.status === 401) showExpired(error.message);
    else notify(error.message);
  } finally {
    polling = false;
  }
}

async function reset() {
  if (busy) return;
  window.StoryAudio?.reset();
  generation++;
  clearTimeout(silentSceneTimer);
  hideClueNotice();
  busy = true;
  closeDialog();
  try {
    const next = await api("/api/game", {});
    draft = "";
    journalDraft = "";
    pendingRequest = null;
    textPlayback.entries.clear();
    textPlayback.readKeys.clear();
    hologramPlayback.clear();
    sceneDrafts.clear();
    textPlayback.queueEnd = performance.now();
    setState(next, true);
  } catch (error) {
    showExpired(error.message);
  } finally {
    busy = false;
    render();
  }
}

function showExpired(text) {
  closeDialog();
  clearTimeout(silentSceneTimer);
  hideClueNotice();
  cancelAnimationFrame(textPlayback.frame);
  cancelAnimationFrame(progressionFrame);
  textPlayback.active = false;
  state = null;
  backButton.hidden = true;
  shell.classList.remove("silent-scene", "intro-scene");
  title.textContent = "임무 기록";
  screen.innerHTML = '<div class="boot"><p>' + esc(text) + '</p><div class="fatal-actions">' +
    '<button class="primary" data-reset>새 임무 시작하기</button><button class="secondary" data-retry>연결 다시 확인</button></div></div>';
}

async function load() {
  try { setState(await api("/api/game"), true); }
  catch (error) {
    if (error.status === 401) await reset();
    else showExpired(error.message);
  }
}

document.addEventListener("click", async event => {
  const button = event.target.closest("button");
  if (!button || button.disabled) return;
  if (button.hasAttribute("data-story-close")) return closeDialog();
  if (button.hasAttribute("data-close") || button.hasAttribute("data-dialog-back")) return previousDialog();
  if (button.hasAttribute("data-reset")) {
    if (screen.contains(button) && presentationPending()) return;
    return reset();
  }
  if (button.hasAttribute("data-retry")) return load();
  if (button.id === "menu-button" || button.hasAttribute("data-menu")) {
    return menuModal();
  }
  if (!state || busy) return;
  if (button.id === "back-button") return act("back");
  const menuParent = dialog.classList.contains("mission-menu") && dialog.open ? menuModal : null;
  if (button.hasAttribute("data-endings")) return endingsModal(menuParent || dialogParent);
  if (button.hasAttribute("data-ending-save")) return collectEnding(state, true);
  if (button.hasAttribute("data-candidate-locked") && state.stage === "selection") {
    if (!motionPreference.matches) {
      button.getAnimations().forEach(animation => animation.cancel());
      button.animate([{borderColor:"#c6a257", boxShadow:"0 0 18px #c6a25733"},
        {borderColor:"#343b46", boxShadow:"0 0 0 #c6a25700"}], {duration:700, easing:"ease-out"});
    }
    return notify('대상자 ' + button.dataset.candidateLocked + '는 아직 잠겨 있습니다.');
  }
  if (button.hasAttribute("data-notes")) return notesModal(menuParent);
  if (button.hasAttribute("data-journal")) return modal("작성한 수확일지", '<p class="section-label">' + esc(state.journal.subject) + '</p><p class="journal-record">' + esc(state.journal.content) + '</p><p class="muted">' + esc(state.journal.clue_record) + '</p><button class="primary" data-close>확인</button>', menuParent);
  if (button.hasAttribute("data-rules")) return rulesModal(menuParent);
  if (button.hasAttribute("data-rules-zoom")) {
    const expanded = button.classList.toggle("rules-expanded");
    button.setAttribute("aria-pressed", String(expanded));
    button.setAttribute("aria-label", expanded ? "계율 전체 보기" : "계율 원본 확대");
    return;
  }
  if (button.hasAttribute("data-restart-confirm")) return modal("처음부터 시작할까요?", '<p>현재 진행 기록이 새 임무로 바뀝니다.</p><button class="primary" data-reset>새 임무 시작</button><button class="secondary" data-close>' + (menuParent ? '임무 메뉴로' : '계속하기') + '</button>', menuParent);
  if (button.dataset.inspect) {
    const known = state.clues.some(clue => clue.id === button.dataset.inspect);
    if (await act("inspect", button.dataset.inspect)) {
      const clue = state.clues.find(clue => clue.id === button.dataset.inspect);
      clueModal(clue);
      if (clue) window.StoryAudio?.inspect(clue.id);
      if (!known && clue) announceClue(clue);
    }
    return;
  }
  if (button.dataset.clue) {
    const notesParent = dialogParent;
    return clueModal(state.clues.find(clue => clue.id === button.dataset.clue), () => notesModal(notesParent));
  }
  if (button.dataset.image) return modal("관련 기록", picture(button.dataset.image, "관련 기록", "dialog-image") + '<button class="primary" data-close>확인</button>');
  if (button.dataset.topic) return act("topic", button.dataset.topic);
  if (button.hasAttribute("data-finish-chat")) {
    if (!state.question_count) return modal("이야기를 들어보세요", '<p class="dialog-copy">한 가지 질문을 나눈 뒤 대화를 마무리할 수 있습니다.</p><button class="primary" data-close>질문하러 돌아가기</button>');
    return act("finish_chat");
  }
  if (button.dataset.choice) {
    if (presentationPending()) return;
    if (state.stage === "selection") { clearTimeout(toastTimer); status.textContent = ""; }
    const choice = state.choices.find(item => item.id === button.dataset.choice);
    if (state.stage === "decision" || button.dataset.choice === "harvest") {
      return confirmChoice(choice);
    }
    return act("choose", button.dataset.choice);
  }
  if (button.dataset.confirm) {
    if (presentationPending()) return;
    closeDialog();
    return act("choose", button.dataset.confirm);
  }
  if (button.dataset.action) return act(button.dataset.action);
});

document.addEventListener("input", event => {
  if (event.target.id === "message-input") draft = event.target.value;
  if (event.target.id === "journal-content") journalDraft = event.target.value;
});
document.addEventListener("submit", async event => {
  if (event.target.id === "journal-form") {
    event.preventDefault();
    if (!journalDraft.trim() || busy) return;
    await act("journal", journalDraft.trim());
    return;
  }
  if (event.target.id !== "chat-form") return;
  event.preventDefault();
  if (!draft.trim() || busy) return;
  await act("chat", draft.trim());
  document.querySelector("#message-input")?.focus();
});
document.addEventListener("keydown", event => {
  if (event.target.id === "message-input" && event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    event.target.form.requestSubmit();
  }
});
dialog.addEventListener("click", event => {
  if (event.target !== dialog) return;
  const bounds = dialog.getBoundingClientRect();
  if (event.clientX < bounds.left || event.clientX > bounds.right || event.clientY < bounds.top || event.clientY > bounds.bottom) previousDialog();
});

dialog.addEventListener("cancel", event => {
  event.preventDefault();
  previousDialog();
});
dialog.addEventListener("close", () => window.StoryAudio?.cancelInspect());
document.addEventListener("visibilitychange", () => {
  if (!document.hidden) poll();
});
document.addEventListener("load", event => {
  const image = event.target;
  if (image instanceof HTMLImageElement && image.closest(".scene-visual, .intro-frame, .silent-frame")) {
    image.classList.toggle("portrait-image", image.naturalHeight > image.naturalWidth);
  }
}, true);
setInterval(updateClock, 200);
setInterval(poll, 800);
load();
