"use strict";

const screen = document.querySelector("#screen");
const title = document.querySelector("#screen-title");
const dialog = document.querySelector("#detail-dialog");
const dialogBody = document.querySelector("#dialog-body");
const status = document.querySelector("#status");
const prepAudio = document.querySelector("#prep-bgm");
const bgmToggle = document.querySelector("#bgm-toggle");
const asset = (n) => `/assets/images/notion-${n}.png`;
const prepAsset = (name) => `/assets/images/harvest/${name}`;
const esc = (value) => String(value).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const PLAYER_PROFILE_KEY = "nottoday-player-profile-v1";
const PREP_FLOW_KEY = "nottoday-prep-flow-v1";
const RANDOM_PLAYER_NAMES = ["야근하는 제우스", "배고픈 나폴레옹", "길치 콜럼버스", "심심한 셰익스피어", "졸린 아인슈타인", "지각한 을지문덕", "감기 걸린 허준", "텅장 신사임당", "집콕하는 장보고", "생각많은 데카르트", "시간없는 하이데거", "슬픈 쇼펜하우어"];
const arrow = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h14m-6-6 6 6-6 6"/></svg>';
const book = '<svg viewBox="0 0 32 32" aria-hidden="true"><path d="M7 4h18v24H7zM11 4v24M15 11h6M15 16h6"/></svg>';
let state, panel = "talk", busy = false, draft = "", toastTimer;
let prepPhase = sessionStorage.getItem(PREP_FLOW_KEY) === "complete" ? "ready" : "teaser";
let returnToRosterAfterSetup = false, bgmAvailable = false;

function readPlayerProfile() {
  try {
    const saved = JSON.parse(sessionStorage.getItem(PLAYER_PROFILE_KEY) || "{}");
    return {gender:saved.gender === "female" ? "female" : "male",
      name:typeof saved.name === "string" && saved.name.trim() ? saved.name.trim().slice(0,16) : "수습자"};
  } catch { return {gender:"male",name:"수습자"}; }
}

let playerProfile = readPlayerProfile();
const playerName = () => playerProfile.name.trim() || "수습자";
const playerImage = () => prepAsset(playerProfile.gender === "female" ? "profile_f.jpg" : "profile_m.jpg");
function savePlayerProfile() { sessionStorage.setItem(PLAYER_PROFILE_KEY, JSON.stringify(playerProfile)); }
function resetPlayerName() {
  playerProfile = {gender:playerProfile.gender,name:"수습자"};
  savePlayerProfile();
}
function randomPlayerName(currentName = "") {
  const options = RANDOM_PLAYER_NAMES.filter(name => name !== currentName.trim());
  const names = options.length ? options : RANDOM_PLAYER_NAMES;
  return names[Math.floor(Math.random() * names.length)];
}

async function api(path, body) {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 20000);
  try {
    const response = await fetch(path, {method: body ? "POST" : "GET", credentials: "same-origin",
      headers: body ? {"Content-Type":"application/json"} : {},
      body: body ? JSON.stringify(body) : undefined, signal: controller.signal, cache: "no-store"});
    const data = await response.json();
    if (!response.ok) {
      const error = new Error(typeof data.detail === "string" ? data.detail : "요청 내용을 확인해주세요.");
      error.status = response.status;
      throw error;
    }
    return data;
  } catch (error) {
    if (error.name === "AbortError") throw new Error("응답 시간이 길어지고 있습니다. 진행 상태를 확인한 뒤 다시 시도해주세요.");
    if (error instanceof TypeError) throw new Error("서버에 연결하지 못했습니다. 연결을 확인한 뒤 다시 시도해주세요.");
    throw error;
  } finally { clearTimeout(timer); }
}

function notify(text) {
  status.textContent = text;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {status.textContent = "";}, 7000);
}

function messageHTML(m) {
  if (m.speaker === "narrator") return `<p class="narration">${esc(m.text)}</p>`;
  const user = m.speaker === "user";
  const mentor = m.speaker === "mentor";
  return `<div class="message ${user ? "user" : mentor ? "mentor" : ""}">
    <img class="avatar ${user ? "user-avatar" : ""}" src="${user ? playerImage() : asset(mentor ? 0 : 1)}" alt="${user ? `${esc(playerName())} 프로필` : ""}">
    <div class="message-content"><p class="speaker-line">${user ? esc(playerName()) : mentor ? "스승" : "이윤제"}</p>
    <div class="bubble">${esc(m.text)}</div></div></div>`;
}

function updateBgmControl() {
  if (!bgmToggle) return;
  const playing = Boolean(prepAudio && !prepAudio.paused);
  bgmToggle.hidden = !bgmAvailable;
  bgmToggle.setAttribute("aria-pressed", String(playing));
  bgmToggle.setAttribute("aria-label", playing ? "준비 단계 배경음 끄기" : "준비 단계 배경음 켜기");
  bgmToggle.title = playing ? "배경음 끄기" : "배경음 켜기";
}

async function startBgm() {
  if (!prepAudio) return;
  bgmAvailable = true;
  prepAudio.volume = 0.42;
  try { await prepAudio.play(); }
  catch { notify("배경음 재생이 차단되었습니다. 음표 버튼을 눌러 다시 시작해주세요."); }
  updateBgmControl();
}

function renderTeaser() {
  title.textContent = "낫 TODAY · 티저";
  screen.innerHTML = `<section class="teaser-screen" aria-label="낫 TODAY 티저 영상">
    <div class="teaser-frame">
      <video id="teaser-video" controls playsinline webkit-playsinline preload="auto" aria-label="낫 TODAY 티저 영상">
        <source src="/assets/media/teaser.mp4" type="video/mp4">
        티저 영상을 재생할 수 없습니다.
      </video>
      <div class="teaser-copy" id="teaser-copy"><p class="teaser-kicker">낫 TODAY</p><h2>The Scyther</h2><p class="teaser-description">인간은 자신이 내린 선택으로 만들어진다.</p>
        <button class="primary" data-video-play>시작하기</button>
      </div>
      <button class="text-button teaser-skip" data-video-skip>설명 건너뛰기</button>
    </div>
  </section>`;
  const video = screen.querySelector("#teaser-video");
  const teaser = screen.querySelector(".teaser-screen");
  const description = screen.querySelector(".teaser-description");
  let startTimer, frameTimer, gotVideoFrame = false;
  video.addEventListener("play", () => {delete video.dataset.displayFailure;});
  video.addEventListener("playing", () => {
    teaser.classList.add("is-starting");
    description.textContent = "어두운 장면이 지나면 화면이 이어집니다.";
    const canObserveVideoFrames = typeof video.requestVideoFrameCallback === "function";
    gotVideoFrame = !canObserveVideoFrames;
    clearTimeout(startTimer);
    startTimer = setTimeout(() => {
      if (!video.paused && gotVideoFrame) {
        teaser.classList.remove("is-starting");
        teaser.classList.add("is-playing");
      }
    }, 2800);
    if (canObserveVideoFrames) {
      gotVideoFrame = false;
      clearTimeout(frameTimer);
      video.requestVideoFrameCallback(() => {
        gotVideoFrame = true;
        clearTimeout(frameTimer);
      });
      frameTimer = setTimeout(() => {
        if (!gotVideoFrame && !video.paused) {
          video.dataset.displayFailure = "true";
          video.pause();
          teaser.classList.remove("is-starting", "is-playing");
          description.textContent = "브라우저가 영상 화면을 표시하지 못했습니다.<br>Chrome 또는 Edge에서 다시 열어주세요.";
          notify("티저의 화면을 불러오지 못했습니다. <br>Chrome 또는 Edge에서 다시 시도해주세요.");
        }
      }, 5000);
    }
  });
  video.addEventListener("pause", () => {
    clearTimeout(startTimer);
    clearTimeout(frameTimer);
    teaser.classList.remove("is-starting", "is-playing");
    if (!video.ended && video.dataset.displayFailure !== "true") description.textContent = "이어 보려면 시작하기를 눌러주세요.";
  });
  video.addEventListener("error", () => {
    video.dataset.displayFailure = "true";
    clearTimeout(startTimer);
    clearTimeout(frameTimer);
    teaser.classList.remove("is-starting", "is-playing");
    description.textContent = "티저 파일을 재생할 수 없습니다.<br>새로고침 후 다시 시도해주세요.";
    notify("티저 영상 파일을 불러오지 못했습니다.");
  });
  video.addEventListener("ended", () => {prepPhase = "customize";render();});
}

function renderCustomizeIntro() {
  PreparationPages.renderCustomizeIntro({screen,title,prepAsset});
}

function renderPlayerAppearance() {
  PreparationPages.renderPlayerAppearance({screen,title,prepAsset,escapeHTML:esc,playerName,playerImage,playerProfile});
}

function renderPlayerName() {
  PreparationPages.renderPlayerName({screen,title,prepAsset,escapeHTML:esc,playerName,playerImage});
}

function renderPrepGuide() {
  PreparationPages.renderPrepGuide({screen,title});
}

function composer(mentor = false) {
  const prompts = mentor ? ["왜 이 사람이 선정됐나요?", "두 딸은 어떻게 되나요?"] : state.intel
    ? ["그 의혹에 대해 말해주세요.", "따님들은 알고 있나요?", "왜 그렇게 생각하나요?"]
    : ["따님들 이야기를 듣고 싶어요.", "공장에서는 어떤 일을 하세요?", "조금 더 이야기해주세요."];
  return `<div class="screen-footer ${mentor ? "briefing-footer" : ""}">
    <div class="suggestions">${prompts.map(p => `<button class="chip" data-prompt="${esc(p)}" ${busy?"disabled":""}>${esc(p)}</button>`).join("")}</div>
    <form id="chat-form" class="composer"><label class="sr-only" for="message-input">${mentor?"스승":"이윤제"}에게 말하기</label>
    <textarea id="message-input" rows="1" maxlength="2000" placeholder="${mentor?"스승":"이윤제"}에게 말하기" ${busy?"disabled":""}>${esc(draft)}</textarea>
    <button class="send" type="submit" aria-label="메시지 보내기" ${busy?"disabled":""}>${arrow}</button></form>
    <div class="composer-note"><span>${busy ? "응답을 기다리는 중…" : "Enter 전송 · Shift+Enter 줄바꿈"}</span><span>예시 대화 모드</span></div>
    ${mentor ? '<button class="primary mentor-confirm" data-action="enter">스승과 대상 확인하기</button>' : `<div class="advance-row">${!state.intel ? '<button class="secondary" data-action="intel">스승의 추가 기록 확인</button>' : '<button class="secondary" data-dialog="intel">추가 기록 다시 보기</button><button class="primary" data-action="decide">판단 내리기 →</button>'}</div>`}
  </div>`;
}

function render() {
  if (!state) return;
  const setupPhases = ["customize", "appearance", "name", "guide"];
  document.body.classList.toggle("teaser-mode", prepPhase === "teaser");
  document.body.classList.toggle("prep-theme", prepPhase !== "teaser" && (setupPhases.includes(prepPhase) || state.stage === "selection" || state.stage === "briefing"));
  document.body.classList.toggle("prep-customization-pages", setupPhases.includes(prepPhase));
  document.body.classList.toggle("dossier-font", prepPhase === "ready" && state.stage === "briefing");
  updateBgmControl();
  if (prepPhase === "teaser") {renderTeaser();return;}
  if (prepPhase === "customize") {renderCustomizeIntro();return;}
  if (prepPhase === "appearance") {renderPlayerAppearance();return;}
  if (prepPhase === "name") {renderPlayerName();return;}
  if (prepPhase === "guide") {renderPrepGuide();return;}
  const oldScroll = document.querySelector(".scroll-area")?.scrollTop || 0;
  const prepStage = state.stage === "selection" || state.stage === "briefing";
  document.body.classList.toggle("prep-theme", prepStage);
  const headings = {selection:"오늘의 명단",briefing:"수확령 · 대상자 기록",conversation:panel === "explore" ? "거실" : panel === "notes" ? "단서 노트" : "이윤제와 대화 중",decision:"최종 선택",ending:"당신은 어떤 수확자인가"};
  title.textContent = headings[state.stage];
  if (state.stage === "selection") {
    screen.innerHTML = `<section class="prep-frame prep-roster" aria-label="대상자 명단">
      <div class="prep-notice"><span class="prep-notice-icon" aria-hidden="true">▤</span><span>수확 대상자 열람</span><i aria-hidden="true"></i></div>
      <div class="scroll-area prep-scroll"><button class="player-profile-chip" data-edit-profile><img src="${playerImage()}" alt=""><span><small>수습자</small><strong>${esc(playerName())}</strong></span><span class="profile-edit-label">프로필 수정</span></button><p class="selection-date"><span>날짜</span>2042년 10월 8일</p><p class="lead">이번 분기 마지막 할당량.<br>세 명 중 한 명을 선택하라.</p>
        <div class="candidate"><img src="${prepAsset("profile_yoonje.jpg")}" alt="이윤제의 초상"><div><div class="eyebrow">대상자 A · 0261024.2</div><h2>이윤제</h2><p>44세 · 남성 · 중공업 공장 노동자</p></div><span class="candidate-mark" aria-label="열람 가능">●</span></div>
        <div class="candidate empty" aria-label="대상자 B, 정보 미공개, 열람 잠금"><div class="empty-portrait"></div><div><h2>대상자 B</h2><p>정보 미공개 · 열람 잠금</p></div></div>
        <div class="candidate empty" aria-label="대상자 C, 정보 미공개, 열람 잠금"><div class="empty-portrait"></div><div><h2>대상자 C</h2><p>정보 미공개 · 열람 잠금</p></div></div>
        <p class="selection-note">대상자 A를 선택해야 상세 기록을 열람할 수 있습니다.</p>
      </div><div class="screen-footer prep-footer"><button class="primary" data-action="select" data-value="yoonje">대상자 A 정보 열람 →</button></div></section>`;
  } else if (state.stage === "briefing") {
    screen.innerHTML = `<section class="prep-frame prep-dossier" aria-label="이윤제 대상자 기록">
      <div class="prep-notice"><span class="prep-notice-icon" aria-hidden="true">▤</span><span>수확 대상자 열람 기록</span><i aria-hidden="true"></i></div>
      <div class="scroll-area prep-scroll"><article class="dossier">
        <div class="dossier-brand"><img src="${prepAsset("logo.png")}" alt=""><div><h2>수확령</h2><p>수확 대상자 열람 기록</p><small>문서번호 013577</small></div></div>
        <div class="dossier-profile"><div class="dossier-photo"><img src="${prepAsset("profile_yoonje.jpg")}" alt="이윤제의 측면 초상"></div><div class="dossier-identity"><span class="dossier-label">대상자</span><h2>이윤제</h2><p class="dossier-role">나이 44세</p><span class="dossier-label">신분 번호</span><p class="dossier-number">0261024.2</p></div></div>
        <dl class="dossier-grid">
        <dt>직업</dt><dd>중공업 공장 노동자</dd>
        <dt>가족</dt><dd>아내 한민주 (2년 전 수확으로 사망)<br>딸 2인(13세, 11세)<br>한부모 가정</dd>
        <dt>범죄 기록</dt><dd>무</dd>
        </dl>
        <div class="dossier-seal"><p>위와 같이 기록한다.</p><small>수확령 의장</small></div>
      </article></div>
      <div class="screen-footer prep-footer mentor-action-footer"><button class="primary mentor-confirm" data-action="enter">스승과 대상 확인하기</button></div></section>`;
  } else if (state.stage === "conversation") {
    const tabs = `<nav class="tabs" aria-label="상호작용 영역">${[["talk","대화"],["explore","집 탐색"],["notes","단서 노트"]].map(([id,label])=>`<button class="tab ${panel===id?"active":""}" data-panel="${id}" aria-pressed="${panel===id}">${label}${id==="notes"?`<span class="tab-count">${state.clues.length}/6</span>`:""}</button>`).join("")}</nav>`;
    let content;
    if (panel === "talk") {
      content = `<div class="scene-card"><img src="${asset(9)}" alt="거실에서 차를 내오는 이윤제"><span class="scene-caption">이윤제의 집 · 늦은 밤</span></div>
        ${state.intel?'<button class="intel-banner" data-dialog="intel">스승에게서 도착한 추가 기록<small>확인되지 않은 의혹 · 기록과 사실을 구분하세요.</small></button>':""}
        <div class="chat-log" role="log" aria-live="polite" aria-relevant="additions">${state.messages.filter(m=>m.id>1).map(messageHTML).join("")}</div>`;
    } else if (panel === "explore") {
      content = `<div class="room"><img src="${asset(6)}" alt="달력, 가족사진, 서랍과 컴퓨터가 놓인 거실">${state.objects.map(o=>`<button class="hotspot ${state.clues.some(c=>c.id===o.id)?"found":""}" style="left:${o.x}%;top:${o.y}%" data-inspect="${o.id}">${esc(o.title.replace(" · 진단서","").replace(" · 편지",""))}</button>`).join("")}</div>
        <p class="room-note"><span>물건을 눌러 살펴보세요.</span><span class="gold">단서 ${state.clues.length} / 6</span></p><p class="muted" style="font-size:12px">그의 말과 방 안에 남은 기록.<br>무엇을 더 알고 싶은가요?</p><button class="secondary" data-panel="talk">이윤제와 대화하기 →</button>`;
    } else {
      content = state.clues.length ? `<p class="muted" style="font-size:12px;margin-bottom:22px">직접 확인한 사실만 이곳에 기록됩니다.</p>${state.clues.map(c=>`<button class="clue-card" data-clue="${c.id}"><strong>${esc(c.title)}</strong><p>${esc(c.text)}</p></button>`).join("")}` : `<div class="empty-note">${book}<h2>아직 펼치지 않은 이야기</h2><p>집 안의 물건을 살펴보면<br>확인한 단서가 이곳에 남습니다.</p><button class="secondary" data-panel="explore">거실 살펴보기</button></div>`;
    }
    screen.innerHTML = `${tabs}<div class="scroll-area chat-area">${content}</div>${composer()}`;
  } else if (state.stage === "decision") {
    screen.innerHTML = `<div class="scroll-area"><img class="decision-scene" src="${asset(11)}" alt="아버지 앞을 막아선 두 딸"><div class="decision-intro"><h2>무엇을 하겠습니까?</h2><p>지금까지 알게 된 것과<br>당신의 기준으로 결정하세요.</p></div>
      ${state.choices.map((c,i)=>`<button class="choice" data-choice="${c.id}"><span class="choice-num">${i+1}</span><span class="choice-text">${esc(c.title)}</span><span class="choice-tag">${esc(c.tag)}</span></button>`).join("")}</div>
      <div class="screen-footer"><button class="secondary" data-action="back">← 돌아가서 더 대화하기</button></div>`;
  } else if (state.stage === "ending") {
    const r = state.result;
    screen.innerHTML = `<div class="scroll-area result ${esc(r.color)}"><img class="result-image" src="${esc(r.image)}" alt="선택 이후의 장면"><p class="latin">${esc(r.latin)}</p><h2>${esc(r.name)}</h2><p class="result-title">${esc(r.title)}</p><p class="result-body">${esc(r.body)}</p><div class="result-evidence"><small>당신의 판단 기록</small>${esc(r.evidence)}</div><p class="mentor-quote">“${esc(r.mentor)}”</p><p class="muted" style="font-size:10px">유형과 결과 설명은 현재 기획 기준이며 추후 변경될 수 있습니다.</p></div><div class="screen-footer"><button class="primary" data-reset>새로운 판단으로 다시 시작</button></div>`;
  }
  if (busy) screen.querySelectorAll("button,textarea").forEach(el=>el.disabled=true);
  const scroller = document.querySelector(".scroll-area");
  if (scroller && panel !== "talk") scroller.scrollTop = oldScroll;
}

function scrollLatest() {
  const scroller = document.querySelector(".scroll-area");
  if (scroller) scroller.scrollTop = scroller.scrollHeight;
}

async function act(action, value = "") {
  if (busy) return false;
  busy = true;
  render();
  const oldStage = state.stage;
  let success = false;
  try {
    state = action === "chat" ? await api("/api/chat", {message:value,revision:state.revision}) : await api("/api/action", {action,value,revision:state.revision});
    if (action === "chat") draft = "";
    success = true;
    if (state.stage !== oldStage) panel = "talk";
  } catch (error) {
    notify(error.message);
    if (error.status === 401) { showExpired(error.message); return false; }
    // 응답이 유실돼도 서버 상태를 다시 읽어 중복 진행을 피한다.
    try {state = await api("/api/game");} catch { /* 기존 오류 안내 유지 */ }
  } finally {busy = false;}
  render();
  if (action === "chat" || action === "intel") scrollLatest();
  if (oldStage !== state.stage) document.querySelector(".scroll-area")?.scrollTo(0,0);
  return success;
}

function modal(heading, content) {
  dialog.classList.remove("intel-dialog");
  dialogBody.innerHTML = `<div class="dialog-inner"><div class="dialog-top"><h2 id="dialog-title">${esc(heading)}</h2><button class="icon-button" data-close aria-label="대화상자 닫기">×</button></div>${content}</div>`;
  if (!dialog.open) dialog.showModal();
}

function clueModal(clue) {
  modal(clue.title, `${clue.image?`<img class="dialog-image" src="/assets/images/${esc(clue.image)}" alt="${esc(clue.title)}">`:""}<p class="dialog-copy">${esc(clue.text)}</p><button class="primary" data-ask-clue="${clue.id}">이 단서에 대해 물어보기</button><button class="secondary" data-close>닫기</button>`);
}

function intelModal() {
  modal("스승의 추가 정보 수신", `<div class="intel-sheet"><p class="section-label">윤리조사실 · ethics_info.01961</p>
    <dl class="intel-meta"><dt>대상자</dt><dd>이윤제</dd><dt>발신</dt><dd>스승</dd><dt>구분</dt><dd>확인되지 않은 의혹</dd></dl>
    <p class="intel-disclaimer">아래 내용은 사실 여부가 확인되지 않은 정보입니다.</p>
    <article class="intel-card"><div><h3>직장 내 괴롭힘 의혹</h3><span>미확인</span></div><p>5년 전 · 증거 불충분으로 징계 무효. 신고한 후배는 퇴사 후 연락 두절.</p></article>
    <article class="intel-card"><div><h3>성희롱 의혹</h3><span>미확인</span></div><p>2년 전 · 징계 없음. 합의 종결로 기록.</p></article>
    <p class="intel-note">※ 두 항목 모두 확인되지 않은 의혹입니다. 기록과 사실을 구분하세요.</p>
    <button class="primary" data-prompt="그 의혹에 대해 말해주세요." data-close-first>이윤제에게 직접 묻기</button><button class="secondary" data-close>기록 닫기</button></div>`);
  dialog.classList.add("intel-dialog");
}

async function receiveRoster() {
  if (busy) return;
  busy = true;
  try {
    state = await api("/api/game", {});
    draft = "";
    panel = "talk";
    returnToRosterAfterSetup = false;
    sessionStorage.setItem(PREP_FLOW_KEY, "complete");
    prepPhase = "ready";
  } catch (error) {
    notify(error.message);
    if (error.status === 401) showExpired(error.message);
  } finally {
    busy = false;
    render();
  }
}

async function reset() {
  if (busy) return;
  busy = true;
  dialog.close();
  prepPhase = "teaser";
  returnToRosterAfterSetup = false;
  sessionStorage.removeItem(PREP_FLOW_KEY);
  resetPlayerName();
  bgmAvailable = false;
  prepAudio?.pause();
  if (prepAudio) prepAudio.currentTime = 0;
  try {state = await api("/api/game", {});draft="";panel="talk";render();}
  catch(error) {showExpired(error.message);}
  finally {busy=false;render();}
}

function showExpired(text) {
  state = null;
  title.textContent = "임무 기록";
  screen.innerHTML = `<div class="boot"><p>${esc(text)}</p><div class="fatal-actions"><button class="primary" data-reset>새 임무 시작하기</button><button class="secondary" data-retry>연결 다시 확인</button></div></div>`;
}

async function load() {
  try {state = await api("/api/game");render();}
  catch(error) {
    if(error.status===401) await reset();
    else showExpired(error.message);
  }
}

document.addEventListener("click", async event => {
  const b = event.target.closest("button");
  if (!b || b.disabled) return;
  if (b.hasAttribute("data-close")) return dialog.close();
  if (b.hasAttribute("data-reset")) return reset();
  if (b.hasAttribute("data-retry")) return load();
  if (b.hasAttribute("data-video-play")) {
    const video = screen.querySelector("#teaser-video");
    video?.play().catch(() => {
      video.dataset.displayFailure = "true";
      screen.querySelector(".teaser-screen")?.classList.remove("is-starting", "is-playing");
      screen.querySelector(".teaser-description").textContent = "재생을 시작하지 못했습니다. 재생 버튼을 다시 눌러주세요.";
      notify("영상을 재생할 수 없습니다. 재생 버튼을 다시 누르거나 영상 건너뛰기를 눌러주세요.");
    });
    return;
  }
  if (b.hasAttribute("data-video-skip")) {screen.querySelector("#teaser-video")?.pause();prepPhase="customize";return render();}
  if (b.hasAttribute("data-begin-customization")) {
    void startBgm();
    prepPhase = "appearance";
    return render();
  }
  if (b.hasAttribute("data-appearance-next")) {prepPhase="name";return render();}
  if (b.hasAttribute("data-name-confirm")) {
    const nameInput = screen.querySelector("#player-name");
    const name = nameInput?.value.trim() || "";
    if (!name) {notify("수확자의 이름을 입력해주세요.");nameInput?.focus();return;}
    playerProfile.name = name.slice(0,16);
    savePlayerProfile();
    if (returnToRosterAfterSetup) {
      returnToRosterAfterSetup = false;
      prepPhase = "ready";
    } else prepPhase = "guide";
    return render();
  }
  if (b.hasAttribute("data-name-random") || b.hasAttribute("data-name-clear")) {
    const nameInput = screen.querySelector("#player-name");
    if (!nameInput) return;
    if (b.hasAttribute("data-name-random")) nameInput.value = randomPlayerName(nameInput.value);
    else nameInput.value = "";
    nameInput.dispatchEvent(new Event("input", {bubbles:true}));
    savePlayerProfile();
    if (b.hasAttribute("data-name-clear")) nameInput.focus();
    return;
  }
  if (b.hasAttribute("data-finish-prep")) {
    return receiveRoster();
  }
  if (b.hasAttribute("data-bgm-toggle")) {
    if (prepAudio?.paused) void startBgm();
    else {prepAudio?.pause();updateBgmControl();}
    return;
  }
  if (b.id === "menu-button") return modal("임무 메뉴", '<p class="demo-label">회의용 시연본 · 준비된 예시 대화로 동작합니다.<br>기록은 이 서버 실행 중에만 유지됩니다.</p><button class="secondary" data-reset>처음부터 다시 시작</button><button class="primary" data-close>이야기로 돌아가기</button>');
  if (b.dataset.playerGender) {
    playerProfile.gender = b.dataset.playerGender === "female" ? "female" : "male";
    savePlayerProfile();
    screen.querySelectorAll("[data-player-gender]").forEach(option => option.setAttribute("aria-pressed", String(option.dataset.playerGender === playerProfile.gender)));
    const image = playerImage();
    const preview = screen.querySelector("#player-preview-image");
    const chatAvatar = screen.querySelector(".prep-customizer .user-avatar");
    if (preview) preview.src = image;
    if (chatAvatar) chatAvatar.src = image;
    return;
  }
  if (b.hasAttribute("data-edit-profile")) {
    returnToRosterAfterSetup = true;
    prepPhase = "appearance";
    return render();
  }
  if (!state || busy) return;
  if (b.dataset.panel) {panel=b.dataset.panel;render();document.querySelector(".scroll-area")?.scrollTo(0,0);return;}
  if (b.dataset.inspect) {
    if(await act("inspect",b.dataset.inspect)) clueModal(state.clues.find(c=>c.id===b.dataset.inspect));
    return;
  }
  if (b.dataset.clue) return clueModal(state.clues.find(c=>c.id===b.dataset.clue));
  if (b.dataset.dialog === "intel") return intelModal();
  if (b.dataset.askClue) {
    const c=state.clues.find(c=>c.id===b.dataset.askClue);
    dialog.close();panel="talk";render();
    return act("chat", c.title+"에 대해 말씀해주시겠어요?");
  }
  if (b.dataset.prompt) {
    if (b.hasAttribute("data-close-first")) dialog.close();
    panel="talk";
    return act("chat",b.dataset.prompt);
  }
  if (b.dataset.choice) {
    const c=state.choices.find(c=>c.id===b.dataset.choice);
    return modal("이 선택을 확정할까요?",`<p class="dialog-copy">${esc(c.title)}</p><p class="muted" style="font-size:12px">확정하면 이번 임무의 결과가 기록됩니다.</p><button class="primary" data-confirm="${c.id}">선택 확정</button><button class="secondary" data-close>다시 생각하기</button>`);
  }
  if (b.dataset.confirm) {dialog.close();return act("choose",b.dataset.confirm);}
  if (b.dataset.action) {
    const done = await act(b.dataset.action,b.dataset.value||"");
    if(done && b.dataset.action==="intel") intelModal();
  }
});

document.addEventListener("input",event=>{
  if(event.target.id==="message-input"){draft=event.target.value;return;}
  if(event.target.id==="player-name"){
    playerProfile.name=event.target.value.slice(0,16);
    savePlayerProfile();
    const namePreview=screen.querySelector("#player-name-preview");
    const setupPreview=screen.querySelector("#player-preview-name");
    const imagePreview=screen.querySelector("#player-preview-image");
    if(namePreview)namePreview.textContent=playerName();
    if(setupPreview)setupPreview.textContent=playerName();
    if(imagePreview)imagePreview.alt=`${playerName()} 프로필`;
  }
});
prepAudio?.addEventListener("play", updateBgmControl);
prepAudio?.addEventListener("pause", updateBgmControl);
document.addEventListener("submit",async event=>{
  if(event.target.id!=="chat-form")return;
  event.preventDefault();
  if(!draft.trim()||busy)return;
  await act("chat",draft.trim());
  document.querySelector("#message-input")?.focus();
});
document.addEventListener("keydown",event=>{
  if(event.target.id==="message-input" && event.key==="Enter" && !event.shiftKey && !event.isComposing){event.preventDefault();event.target.form.requestSubmit();}
});
dialog.addEventListener("click",event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});
load();
