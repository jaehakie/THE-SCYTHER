"use strict";

(() => {
  function renderCustomizeIntro({screen, title, emblem}) {
    title.textContent = "나의 수확자 만들기";
    screen.innerHTML = `<section class="prep-frame prep-step-frame" aria-label="나의 수확자 만들기">
      <div class="prep-notice"><span class="prep-notice-mark" aria-hidden="true"></span><span>나의 수확자 만들기</span></div>
      <div class="prep-step-content">
        <div class="prep-emblem"><img src="${emblem}" alt="수확령 문장"></div>
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
        <p class="player-setup-hint">이 모습은 대화 프로필에 표시됩니다. 로브는 견습 회색입니다.</p>
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
        <form id="player-name-form"><input class="player-name-field" id="player-name" name="player-name" type="text" maxlength="16" autocomplete="off" spellcheck="false" value="${name}" placeholder="이름을 입력하세요" required aria-describedby="player-name-hint"></form>
        <p class="player-setup-hint" id="player-name-hint">대화에 표시할 이름을 16자 이내로 입력하세요.</p>
        <div class="player-name-actions">
          <button class="text-button" type="button" data-name-clear>이름 지우기</button>
        </div>
      </div>
      <div class="screen-footer prep-footer"><button class="primary" type="submit" form="player-name-form" data-name-confirm>이 이름으로 선택하기 →</button></div>
    </section>`;
  }

  function renderPrepGuide({screen, title, escapeHTML, playerName, playerImage}) {
    title.textContent = "나의 수확자 확인";
    const name = escapeHTML(playerName());
    screen.innerHTML = `<section class="prep-frame prep-step-frame" aria-label="수확자 설정 확인">
      <div class="prep-notice"><span class="prep-notice-mark" aria-hidden="true"></span><span>설정 확인</span></div>
      <div class="scroll-area prep-scroll prep-guide-content">
        <div class="player-preview"><img src="${playerImage()}" alt="${name} 프로필"><div><span class="dossier-label">수습 수확자</span><h2>${name}</h2><p>견습 회색 로브</p></div></div>
        <article class="guide-card"><h2>이 모습으로 시작합니다.</h2><p>선택한 모습과 이름이 내 대화 프로필에 표시됩니다.<br>이제 수확자의 계율을 확인하세요.</p></article>
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
