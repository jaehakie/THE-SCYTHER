"use strict";

(() => {
  const preferenceKey = "nottoday.sound.enabled";
  let enabled = true, unlocked = false;
  try {
    enabled = sessionStorage.getItem(preferenceKey) !== "false";
    unlocked = sessionStorage.getItem("nottoday.sound.unlocked") === "true";
  } catch { /* Optional preference storage. */ }
  let blocked = false, pageSuspended = false, config = null, currentScene = null;
  let musicId = null, targetMusic = null, suspended = false, fadeFrame = null, needsSeek = false;
  let sceneEpoch = 0, inspectEpoch = 0, context = null, warmed = false;
  let mayReveal = false, revealed = false;
  const buffers = new Map(), activeEffects = new Set(), delays = new Set(), errors = [];
  const music = document.createElement("audio");
  music.id = "story-bgm";
  music.preload = "metadata";
  music.hidden = true;
  document.body.append(music);
  const icons = {
    on:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4V5Zm4 3a6 6 0 0 1 0 8m3-11a10 10 0 0 1 0 14"/></svg>',
    off:'<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M11 5 6 9H3v6h3l5 4V5Zm5 4 5 6m0-6-5 6"/></svg>'
  };
  const url = file => "/assets/sounds/" + file.split("/").map(encodeURIComponent).join("/");
  const volume = value => Math.max(0, Math.min(1, Number(value) || 0));
  const audible = () => enabled && unlocked && !blocked;
  const emit = (type, id) => window.dispatchEvent(new CustomEvent("storyaudio", {detail:{type, id, scene:currentScene?.scene_id, at:performance.now()}}));

  function refreshControls() {
    for (const button of document.querySelectorAll("[data-sound-toggle]")) {
      const label = audible() ? "소리 끄기" : "소리 켜기";
      button.setAttribute("aria-label", label);
      button.setAttribute("aria-pressed", String(audible()));
      button.title = label;
      if (button.hasAttribute("data-sound-icon")) button.innerHTML = audible() ? icons.on : icons.off;
      else button.textContent = label;
    }
  }

  function reportError(id, error) {
    if (errors.length < 20) errors.push(id + ": " + error.name);
    emit("error", id);
  }

  function fadeTo(target, milliseconds, complete) {
    cancelAnimationFrame(fadeFrame);
    const from = music.volume, started = performance.now();
    const tick = () => {
      const progress = Math.min(1, (performance.now() - started) / milliseconds);
      music.volume = volume(from + (target - from) * progress);
      if (progress < 1) fadeFrame = requestAnimationFrame(tick);
      else { fadeFrame = null; complete?.(); }
    };
    tick();
  }

  function mayPlayMusic() {
    return config && enabled && unlocked && !pageSuspended && !document.hidden && !suspended && musicId && musicId === targetMusic;
  }

  function playMusic() {
    if (!mayPlayMusic() || (needsSeek && config.music[musicId].startAt > 0) || (!music.paused && !music.ended)) return;
    if (music.ended) music.currentTime = config.music[musicId].startAt || 0;
    const expected = musicId;
    music.play().then(() => {
      if (expected !== musicId) return;
      if (!mayPlayMusic()) { music.pause(); return; }
      blocked = false;
      fadeTo(volume(config.music[musicId].volume), 350);
      refreshControls();
      emit("music", musicId);
    }).catch(error => {
      if (expected !== musicId || error.name === "AbortError") return;
      if (error.name === "NotAllowedError") blocked = true;
      else reportError(expected, error);
      refreshControls();
    });
  }

  function loadMusic(id) {
    cancelAnimationFrame(fadeFrame);
    music.pause();
    music.volume = 0;
    musicId = id;
    if (!id) { music.removeAttribute("src"); music.load(); return; }
    const track = config.music[id];
    needsSeek = true;
    music.loop = Boolean(track.loop && !track.startAt);
    music.src = url(track.file);
    music.load();
    playMusic();
  }

  function selectMusic(id) {
    if (id === targetMusic && musicId !== id) return; // A section transition is already fading out.
    targetMusic = id;
    if (musicId === id) {
      if (suspended) { cancelAnimationFrame(fadeFrame); music.pause(); }
      else playMusic();
      return;
    }
    if (!music.paused && enabled && !document.hidden && !pageSuspended) fadeTo(0, 180, () => loadMusic(targetMusic));
    else loadMusic(id);
  }

  music.addEventListener("loadedmetadata", () => {
    if (!musicId || !config) return;
    const start = Math.min(config.music[musicId].startAt || 0, Math.max(0, music.duration - .1));
    if (needsSeek) { music.currentTime = start; needsSeek = false; }
    playMusic();
  });
  music.addEventListener("ended", () => {
    if (!mayPlayMusic() || !config.music[musicId].loop) return;
    music.currentTime = config.music[musicId].startAt || 0;
    playMusic();
    emit("loop", musicId);
  });

  function cancelInspect() {
    inspectEpoch++;
    for (const timer of delays) clearTimeout(timer);
    delays.clear();
  }

  function stopEffects() {
    cancelInspect();
    for (const effect of activeEffects) { try { effect.stop(); } catch { /* Already ended. */ } }
    activeEffects.clear();
  }

  function getBuffer(id) {
    if (!buffers.has(id)) {
      const pending = fetch(url(config.effects[id].file)).then(response => {
        if (!response.ok) throw new Error("Audio file unavailable");
        return response.arrayBuffer();
      }).then(bytes => context.decodeAudioData(bytes)).catch(error => { buffers.delete(id); throw error; });
      buffers.set(id, pending);
    }
    return buffers.get(id);
  }

  async function effect(id, valid = () => true) {
    const epoch = sceneEpoch;
    if (!config?.effects[id] || !enabled || !unlocked || document.hidden || pageSuspended) return;
    try {
      if (!context) return;
      const buffer = await getBuffer(id);
      if (!enabled || epoch !== sceneEpoch || !valid() || document.hidden || pageSuspended) return;
      if (context.state === "suspended") await context.resume();
      if (context.state !== "running" || !enabled || epoch !== sceneEpoch || !valid()) return;
      const source = context.createBufferSource(), gain = context.createGain();
      source.buffer = buffer;
      source.connect(gain).connect(context.destination);
      const duration = Math.min(buffer.duration, config.effects[id].maxDuration || buffer.duration);
      gain.gain.setValueAtTime(volume(config.effects[id].volume), context.currentTime);
      gain.gain.setValueAtTime(volume(config.effects[id].volume), context.currentTime + Math.max(0, duration - .08));
      gain.gain.linearRampToValueAtTime(0, context.currentTime + duration);
      activeEffects.add(source);
      source.onended = () => { activeEffects.delete(source); source.disconnect(); gain.disconnect(); };
      source.start(0, 0, duration);
      emit("effect", id);
    } catch (error) { reportError(id, error); }
  }

  function inspect(id) {
    cancelInspect();
    const epoch = inspectEpoch;
    const valid = () => epoch === inspectEpoch;
    if (config?.interaction.drawerIds.includes(id)) effect("drawer", valid);
    else if (config?.interaction.genericIds.includes(id)) effect("inspect", valid);
    if (config?.interaction.delayedClueIds.includes(id)) {
      const timer = setTimeout(() => { delays.delete(timer); effect("clue_discovery", valid); }, config.interaction.clueDelayMs);
      delays.add(timer);
    }
  }

  function pauseAll() {
    cancelAnimationFrame(fadeFrame);
    music.pause();
    music.volume = 0;
    stopEffects();
    if (config && musicId !== targetMusic) loadMusic(targetMusic);
  }

  function unlock() {
    if (!enabled) return;
    document.querySelectorAll('video[data-video-sound="true"]').forEach(video => { video.muted = false; });
    unlocked = true;
    try { sessionStorage.setItem("nottoday.sound.unlocked", "true"); } catch { /* Optional storage. */ }
    blocked = false;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!context && AudioContextClass) context = new AudioContextClass();
      context?.resume().catch(() => { blocked = true; refreshControls(); });
    } catch { /* Music can still play on browsers without Web Audio. */ }
    ready.then(() => {
      if (config && context && !warmed) {
        warmed = true;
        for (const id of Object.keys(config.effects)) getBuffer(id).catch(error => reportError(id, error));
      }
    });
    playMusic();
    refreshControls();
  }

  function toggle() {
    if (!enabled || !unlocked || blocked) { enabled = true; unlock(); }
    else {
      enabled = false;
      pauseAll();
      document.querySelectorAll("video").forEach(video => { video.muted = true; });
    }
    try { sessionStorage.setItem(preferenceKey, String(enabled)); } catch { /* Optional storage. */ }
    refreshControls();
  }

  function setScene(next) {
    const first = !currentScene;
    const reviewing = next.reviewing || currentScene?.reviewing;
    const changed = currentScene?.scene_id !== next.scene_id;
    currentScene = next;
    if (!changed) return;
    mayReveal = !first && !reviewing;
    revealed = false;
    const epoch = ++sceneEpoch;
    stopEffects();
    ready.then(() => {
      if (!config || epoch !== sceneEpoch) return;
      suspended = config.suspendMusicScenes.includes(next.scene_id);
      let id = config.sceneMusic[next.scene_id] || null;
      if (id === "result") id = next.result?.id || null;
      selectMusic(id);
      if (!first && !reviewing && config.sceneEffects[next.scene_id]) effect(config.sceneEffects[next.scene_id]);
    });
  }

  function reveal(sceneId) {
    const epoch = sceneEpoch;
    ready.then(() => {
      if (!config || !mayReveal || revealed || epoch !== sceneEpoch || currentScene?.scene_id !== sceneId) return;
      revealed = true;
      for (const id of config.revealEffects?.[sceneId] || []) effect(id);
    });
  }

  function reset() {
    sceneEpoch++;
    currentScene = null;
    mayReveal = false;
    revealed = false;
    targetMusic = null;
    suspended = false;
    pauseAll();
    if (musicId) loadMusic(null);
  }

  const ready = fetch("/assets/audio/audio-config.json", {cache:"no-cache"}).then(response => {
    if (!response.ok) throw new Error("Audio configuration unavailable");
    return response.json();
  }).then(data => { config = data; return data; }).catch(error => { reportError("config", error); return null; });

  document.addEventListener("pointerdown", event => { if (!event.target.closest("[data-sound-toggle]")) unlock(); }, {capture:true});
  document.addEventListener("keydown", event => { if (["Enter", " ", "Tab"].includes(event.key) && !event.target.closest("[data-sound-toggle]")) unlock(); }, {capture:true});
  document.addEventListener("click", event => { if (event.target.closest("[data-sound-toggle]")) toggle(); });
  document.addEventListener("visibilitychange", () => { if (document.hidden) pauseAll(); else playMusic(); });
  window.addEventListener("pagehide", () => { pageSuspended = true; pauseAll(); });
  window.addEventListener("pageshow", () => { pageSuspended = false; playMusic(); refreshControls(); });
  window.StoryAudio = {
    ready, setScene, effect, inspect, reveal, cancelInspect, reset, refreshControls, toggle,
    getState:() => ({enabled, unlocked, blocked, musicId, targetMusic, suspended, time:music.currentTime, paused:music.paused,
      pendingEffects:delays.size, activeEffects:activeEffects.size, errors:[...errors]})
  };
  refreshControls();
})();
