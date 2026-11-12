"use strict";

(() => {
  window.StoryAudio?.setScene({scene_id:"title"});
  const form = document.getElementById("start-form");
  const start = document.getElementById("start");
  const curtain = document.getElementById("curtain");
  const back = document.getElementById("back");
  const message = curtain.querySelector("p");
  let transition = null;
  let pending = false;
  let request = null;
  let attempt = 0;

  function resetTransition() {
    clearTimeout(transition);
    transition = null;
    attempt++;
    request?.abort();
    request = null;
    pending = false;
    curtain.classList.remove("on");
    curtain.inert = true;
    curtain.setAttribute("aria-hidden", "true");
    start.disabled = false;
    back.disabled = false;
    message.textContent = "수확령에 접속하는 중입니다…";
  }

  async function beginPreparation() {
    const currentAttempt = attempt;
    const controller = new AbortController();
    request = controller;
    back.disabled = true;
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const response = await fetch("/api/game", {
        method:"POST", credentials:"same-origin", cache:"no-store",
        headers:{"Content-Type":"application/json"}, body:"{}", signal:controller.signal
      });
      if (!response.ok) throw new Error("Cannot start mission");
      const mission = await response.json();
      if (currentAttempt !== attempt) return;
      if (mission.scene_id !== "intro1") throw new Error("Unexpected opening scene");
      window.location.assign(form.action);
    } catch {
      if (currentAttempt !== attempt) return;
      message.textContent = "새 임무를 시작하지 못했습니다. 처음 화면으로 돌아가 다시 시도해 주세요.";
      back.disabled = false;
    } finally {
      clearTimeout(timeout);
      if (request === controller) request = null;
    }
  }

  form.addEventListener("submit", event => {
    event.preventDefault();
    if (pending) return;
    pending = true;
    start.disabled = true;
    curtain.inert = false;
    curtain.setAttribute("aria-hidden", "false");
    curtain.classList.add("on");
    back.focus();
    const delay = matchMedia("(prefers-reduced-motion: reduce)").matches ? 0 : 350;
    transition = setTimeout(beginPreparation, delay);
  });
  back.addEventListener("click", () => {
    resetTransition();
    start.focus();
  });
  window.addEventListener("pageshow", resetTransition);
})();
