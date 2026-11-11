"use strict";

(() => {
  function renderCustomizeIntro({screen, title, prepAsset}) {
    title.textContent = "나의 수확자 만들기";
    screen.innerHTML = `<section class="prep-frame prep-step-frame" aria-label="나의 수확자 만들기">
      <div class="prep-notice"><span class="prep-notice-mark" aria-hidden="true"></span><span>나의 수확자 만들기</span></div>
      <div class="prep-step-content">
        <div class="prep-emblem"><img src="${prepAsset("logo.png")}" alt="수확령 문장"></div>
        <h2>나의 수확자 만들기</h2>
        <p>임무를 시작하기 전에<br>수습 수확자의 성별과 이름을 정합니다.</p>
      </div>
      <div class="screen-footer prep-footer"><button class="primary" data-begin-customization>나의 수확자 만들기 →</button></div>
    </section>`;
  }

  function renderPlayerAppearance({screen, title, prepAsset, escapeHTML, playerName, playerImage, playerProfile}) {
    title.textContent = "나의 수확자 만들기";
    const name = escapeHTML(playerName());
    screen.innerHTML = `<section class="prep-frame prep-customizer" aria-label="나의 수확자 만들기">
      <div class="prep-notice"><span class="prep-notice-mark" aria-hidden="true"></span><span>나의 수확자 만들기</span></div>
      <div class="scroll-area prep-scroll">
        <div class="player-preview"><img id="player-preview-image" src="${playerImage()}" alt="${name} 프로필"><div><span class="dossier-label">수습 수확자</span><h2 id="player-preview-name">${name}</h2><p>대화 기록에 표시될 모습을 선택하세요.</p></div></div>
        <fieldset class="player-gender"><legend>성별 선택</legend>
          <button type="button" class="player-choice" data-player-gender="male" aria-pressed="${playerProfile.gender === "male"}"><img src="${prepAsset("profile_m.jpg")}" alt=""><span>남성</span></button>
          <button type="button" class="player-choice" data-player-gender="female" aria-pressed="${playerProfile.gender === "female"}"><img src="${prepAsset("profile_f.jpg")}" alt=""><span>여성</span></button>
        </fieldset>
        <p class="player-setup-hint">성별과 이름은 대화 프로필로 설정됩니다.</p>
      </div>
      <div class="screen-footer prep-footer"><button class="primary" data-appearance-next>이름 선택 →</button></div>
    </section>`;
  }

  function renderPlayerName({screen, title, prepAsset, escapeHTML, playerName, playerImage}) {
    title.textContent = "이름 입력";
    const name = escapeHTML(playerName());
    screen.innerHTML = `<section class="prep-frame prep-customizer" aria-label="수습 수확자 이름 입력">
      <div class="prep-notice"><span class="prep-notice-mark" aria-hidden="true"></span><span>이름 선택</span></div>
      <div class="scroll-area prep-scroll">
        <div class="player-preview"><img id="player-preview-image" src="${playerImage()}" alt="${name} 프로필"><div><span class="dossier-label">수확자</span><h2 id="player-name-preview">${name}</h2><p>선택한 이름은 이후 프로필에 표시됩니다.</p></div></div>
        <label class="player-name-label" for="player-name">수확자의 이름</label>
        <input class="player-name-field" id="player-name" name="player-name" type="text" maxlength="16" autocomplete="off" spellcheck="false" value="${name}" placeholder="이름을 입력하세요" required>
        <p class="player-setup-hint">원하는 이름을 입력합니다.</p>
        <div class="player-name-actions">
          <button class="secondary" type="button" data-name-random>랜덤 이름 뽑기</button>
          <button class="text-button" type="button" data-name-clear>이름 지우기</button>
        </div>
      </div>
      <div class="screen-footer prep-footer"><button class="primary" data-name-confirm>이 이름으로 선택하기 →</button></div>
    </section>`;
  }

  function renderPrepGuide({screen, title}) {
    title.textContent = "임무 전 안내";
    screen.innerHTML = `<section class="prep-frame prep-step-frame" aria-label="임무 진행 안내">
      <div class="prep-notice"><span class="prep-notice-mark" aria-hidden="true"></span><span>임무 진행 안내</span></div>
      <div class="scroll-area prep-scroll prep-guide-content">
        <article class="guide-card"><span class="dossier-label">스승의 안내</span><h2>기록을 읽고 확인하세요.</h2><p>대상자 기록을 살펴보고,<br>궁금한 내용은 스승에게 물어볼 수 있습니다.</p></article>
        <article class="guide-card"><span class="dossier-label">진행 방법</span><h2>선택하거나 직접 말하기</h2><p>화면의 선택지를 누르거나,<br>하고 싶은 말을 직접 입력해 진행할 수 있습니다.</p></article>
      </div>
      <div class="screen-footer prep-footer"><button class="primary" data-finish-prep>계율 보기 →</button></div>
    </section>`;
  }

  window.PreparationPages = Object.freeze({
    renderCustomizeIntro,
    renderPlayerAppearance,
    renderPlayerName,
    renderPrepGuide,
  });
})();
