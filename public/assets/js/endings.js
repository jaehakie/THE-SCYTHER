"use strict";

// Result data stays on this browser. It never changes the live story or prompts.
window.EndingCollection = (() => {
  let database;
  function open() {
    if (!database) database = new Promise((resolve, reject) => {
      let blocked = false;
      const request = indexedDB.open("nottoday-endings", 1);
      request.onupgradeneeded = () => request.result.createObjectStore("endings", {keyPath:"id"});
      request.onsuccess = () => {
        const db = request.result;
        if (blocked) { db.close(); return; }
        db.onversionchange = () => { db.close(); database = null; };
        resolve(db);
      };
      request.onerror = () => reject(request.error);
      request.onblocked = () => { blocked = true; reject(new Error("Ending database is blocked")); };
    }).catch(error => { database = null; throw error; });
    return database;
  }

  const badResult = Object.freeze({id:"bad", name:"선택을 포기한 수확자", latin:"", label:"배드엔딩", color:"",
    description:"선택하지 않은 자에게는 색이 주어지지 않는다."});
  const allowedTypes = new Set(["fulvus", "caeruleus", "ruber", "bad"]);
  const sceneTypes = {result_fulvus_lie:"fulvus", result_fulvus_truth:"fulvus", result_caeruleus:"caeruleus",
    result_ruber:"ruber", result_ruber_early:"ruber", result_bad:"bad"};
  function validBasis(basis) {
    return typeof basis?.content === "string" && basis.content.trim().length > 0 && basis.content.length <= 2000 &&
      typeof basis.subject === "string";
  }
  function valid(record) {
    return record?.version === 1 && /^[a-f0-9]{32}$/.test(record.id) &&
      typeof record.saved_at === "string" && Number.isFinite(Date.parse(record.saved_at)) &&
      sceneTypes[record.scene_id] === record.result?.id &&
      [null, "yes", "no"].includes(record.report_answer) &&
      allowedTypes.has(record.result?.id) && typeof record.image === "string" && record.image.startsWith("/assets/images/") &&
      (record.result.id === "bad" ? record.basis === null && record.journal === null :
        (record.result.id === "fulvus" && record.basis === null) || validBasis(record.basis)) &&
      Number.isInteger(record.clue_count) && record.clue_count >= 0 && record.clue_count <= 6 &&
      ["name", "latin", "label", "color", "description"].every(key => typeof record.result[key] === "string") &&
      ["label", "record"].every(key => typeof record.ending_grade?.[key] === "string");
  }

  function snapshot(view, basis) {
    if (view.reviewing) return null;
    const bad = view.stage === "bad_result" && view.scene_id === "result_bad";
    if (!bad && (view.stage !== "result" || !allowedTypes.has(view.result?.id) || view.result.id === "bad")) return null;
    const noJournal = bad || view.result.id === "fulvus";
    if (!noJournal && !validBasis(basis)) return null;
    const record = structuredClone({version:1, id:view.run_id, saved_at:new Date().toISOString(),
      scene_id:view.scene_id, image:view.image, result:bad ? badResult : view.result, ending_grade:view.ending_grade,
      clue_count:view.clue_count, choice_title:view.choice_title, report_answer:view.report_answer,
      stop_reason:view.stop_reason || null,
      ending_reason:view.ending_reason || null,
      journal:noJournal ? null : view.journal, basis:noJournal ? null : basis});
    return valid(record) ? record : null;
  }

  async function list() {
    const db = await open();
    return new Promise((resolve, reject) => {
      const transaction = db.transaction("endings", "readonly");
      const request = transaction.objectStore("endings").getAll();
      transaction.oncomplete = () => resolve(request.result.filter(valid).sort((a,b) => b.saved_at.localeCompare(a.saved_at)));
      transaction.onabort = () => reject(transaction.error || new Error("Ending read failed"));
    });
  }

  async function save(record) {
    if (!valid(record)) throw new Error("Invalid ending record");
    const db = await open();
    return new Promise((resolve, reject) => {
      // One immutable snapshot per playthrough. Retries and multiple tabs cannot duplicate it.
      const transaction = db.transaction("endings", "readwrite");
      const store = transaction.objectStore("endings");
      const request = store.get(record.id);
      request.onsuccess = () => { if (!request.result) store.add(record); };
      transaction.oncomplete = () => resolve(record.id);
      transaction.onabort = () => reject(transaction.error || new Error("Ending save failed"));
    });
  }
  return {snapshot, list, save, badResult};
})();
