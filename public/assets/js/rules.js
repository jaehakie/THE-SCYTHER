"use strict";

// The menu displays the supplied original artwork without animation.
(() => {
  const source = "/assets/images/" + encodeURIComponent("계율.png");
  const escape = value => String(value).replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  function html(rules) {
    const transcript = '<ol class="sr-only rules-transcript">' + rules.map((rule, i) => {
      // Match the image's first word without changing the game's rule data.
      const text = i === 0 ? rule.replace(/^죽여라\./, "죽어라.") : rule;
      return '<li>' + escape(text) + '</li>';
    }).join("") + '</ol>';
    return '<figure class="rules-card rules-complete"><div class="rules-image-scroll"><button class="rules-art" data-rules-zoom aria-label="계율 원본 확대" aria-pressed="false" title="눌러서 확대 또는 축소">' +
      '<img src="' + source + '" width="1440" height="1080" alt="수확자의 계율. 인류를 위해 봉사하리라."></button></div>' + transcript + '</figure>';
  }
  window.RuleArtwork = {html, source};
})();
