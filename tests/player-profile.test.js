"use strict";
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {readFileSync} = require('node:fs');
const {runInNewContext} = require('node:vm');
const source = readFileSync(require('node:path').join(__dirname, '../public/assets/js/player-profile.js'), 'utf8');

function load(store = new Map(), blocked = false) {
  const window = {};
  runInNewContext(source, {window, sessionStorage:{
    getItem:key => { if (blocked) throw Error('blocked'); return store.get(key) || null; },
    setItem:(key, value) => { if (blocked) throw Error('blocked'); store.set(key, value); }
  }});
  return window.PlayerProfile;
}

test('reload retains draft and completed profile only for the same run', () => {
  const store = new Map();
  let profile = load(store);
  profile.sync('first');
  profile.update({gender:'female', name:'아리아', phase:'name'});
  profile = load(store);
  profile.sync('first');
  assert.equal(profile.get().phase, 'name');
  assert.equal(profile.name(), '아리아');
  assert.match(profile.image(), /profile_f.jpg$/);
  profile.update({complete:true, phase:null});
  profile = load(store);
  profile.sync('first');
  assert.equal(profile.get().complete, true);
  profile.sync('second');
  assert.equal(profile.name(), '수습 수확자');
  assert.equal(profile.get().complete, false);
  assert.equal(profile.get().phase, null);
});

test('damaged or unrecognized saved values cannot supply arbitrary images or phases', () => {
  const store = new Map([['nottoday-run-profile-v1', '{broken']]);
  const profile = load(store);
  profile.sync('first');
  profile.update({gender:'../../invalid', phase:'unknown', name:'\n\t'});
  profile.update({complete:true});
  assert.match(profile.image(), /profile_m.jpg$/);
  assert.equal(profile.get().phase, null);
  assert.equal(profile.get().complete, false);
  profile.update({name:'가'.repeat(30)});
  assert.equal(Array.from(profile.name()).length, 16);
});

test('blocked browser storage permits customization in memory without breaking progression', () => {
  const profile = load(new Map(), true);
  profile.sync('first');
  profile.update({name:'새 이름', gender:'female', complete:true});
  assert.equal(profile.name(), '새 이름');
  assert.equal(profile.get().complete, true);
  assert.equal(profile.storageFailed(), true);
  profile.sync('second');
  assert.equal(profile.get().complete, false);
});
