"use strict";

// A display profile belongs to one game run, never to the LLM or ending rules.
(() => {
  const KEY = "nottoday-run-profile-v1";
  const phases = new Set(["intro", "appearance", "name", "confirm"]);
  const images = Object.freeze({
    male:"/assets/images/harvest/profile_m.jpg",
    female:"/assets/images/harvest/profile_f.jpg"
  });
  let profile = null;
  let storageFailed = false;
  const cleanName = value => Array.from(String(value ?? "").replace(/[\u0000-\u001f\u007f-\u009f]/g, "")).slice(0, 16).join("");

  function save() {
    try { sessionStorage.setItem(KEY, JSON.stringify(profile)); }
    catch { storageFailed = true; }
  }

  function sync(runId) {
    if (profile?.runId === runId) return;
    let saved;
    try { saved = JSON.parse(sessionStorage.getItem(KEY)); }
    catch { /* A blocked or invalid store must not prevent story progression. */ }
    profile = {
      runId, gender:"male", name:"수습 수확자", phase:null, complete:false
    };
    if (saved?.runId === runId) {
      profile.gender = saved.gender === "female" ? "female" : "male";
      profile.name = cleanName(saved.name ?? "수습 수확자");
      profile.phase = phases.has(saved.phase) ? saved.phase : null;
      profile.complete = saved.complete === true && Boolean(profile.name.trim());
    }
    save();
  }

  function update(values) {
    if (!profile) return;
    if (values.gender === "male" || values.gender === "female") profile.gender = values.gender;
    if (Object.hasOwn(values, "name")) profile.name = cleanName(values.name);
    if (values.phase === null || phases.has(values.phase)) profile.phase = values.phase;
    if (typeof values.complete === "boolean") profile.complete = values.complete && Boolean(profile.name.trim());
    save();
  }

  window.PlayerProfile = Object.freeze({
    sync, update,
    get:() => profile ? {...profile} : null,
    name:() => profile?.name.trim() || "수습 수확자",
    image:() => images[profile?.gender] || images.male,
    storageFailed:() => storageFailed
  });
})();
