// Client-side site search over the generated entity graph.
// Loads search-index.json (emitted by generate.py from the graph nodes) and
// does a small token/prefix match — no external library, no build step.
(function () {
  "use strict";

  var KIND_ORDER = ["pc", "npc", "location", "item", "quest", "session"];
  var KIND_LABEL = {
    pc: "Crew", npc: "NPCs", location: "Locations",
    item: "Items", quest: "Quests", session: "Sessions"
  };
  var MAX_RESULTS = 8;

  var input = document.getElementById("site-search");
  var box = document.getElementById("search-results");
  if (!input || !box) return;

  var INDEX = null;
  var results = [];   // flattened, in render order, for keyboard nav
  var active = -1;

  function load() {
    if (INDEX) return Promise.resolve(INDEX);
    return fetch("search-index.json")
      .then(function (r) { return r.json(); })
      .then(function (data) { INDEX = data; return INDEX; })
      .catch(function () { INDEX = []; return INDEX; });
  }

  // Score one entry against the query terms. Returns 0 if any term is unmatched.
  function score(entry, terms) {
    var name = entry.name.toLowerCase();
    var aliases = (entry.aliases || []).map(function (a) { return a.toLowerCase(); });
    var blurb = (entry.blurb || "").toLowerCase();
    var total = 0;
    for (var i = 0; i < terms.length; i++) {
      var t = terms[i], best = 0;
      if (name === t) best = 120;
      else if (name.indexOf(t) === 0) best = 90;
      else if (name.indexOf(t) !== -1) best = 55;
      for (var j = 0; j < aliases.length; j++) {
        var a = aliases[j];
        if (a === t) best = Math.max(best, 80);
        else if (a.indexOf(t) === 0) best = Math.max(best, 60);
        else if (a.indexOf(t) !== -1) best = Math.max(best, 35);
      }
      if (best === 0 && blurb.indexOf(t) !== -1) best = 10;
      if (best === 0) return 0;   // AND semantics: every term must hit
      total += best;
    }
    return total;
  }

  function query(q) {
    var terms = q.toLowerCase().split(/\s+/).filter(Boolean);
    if (!terms.length) return [];
    var scored = [];
    for (var i = 0; i < INDEX.length; i++) {
      var s = score(INDEX[i], terms);
      if (s > 0) scored.push({ e: INDEX[i], s: s });
    }
    scored.sort(function (a, b) {
      return b.s - a.s || a.e.name.localeCompare(b.e.name);
    });
    return scored.slice(0, MAX_RESULTS).map(function (x) { return x.e; });
  }

  function render(entries) {
    results = [];
    active = -1;
    if (!entries.length) {
      box.innerHTML = '<div class="search-empty">No matches.</div>';
      box.hidden = false;
      return;
    }
    var byKind = {};
    entries.forEach(function (e) {
      (byKind[e.kind] = byKind[e.kind] || []).push(e);
    });
    var html = "";
    KIND_ORDER.forEach(function (kind) {
      var group = byKind[kind];
      if (!group) return;
      html += '<div class="search-group-label">' + (KIND_LABEL[kind] || kind) + "</div>";
      group.forEach(function (e) {
        var idx = results.length;
        results.push(e);
        html +=
          '<a class="search-hit" data-idx="' + idx + '" href="' + e.url + '">' +
          '<span class="search-hit-name">' + escapeHtml(e.name) + "</span>" +
          (e.blurb ? '<span class="search-hit-blurb">' + escapeHtml(e.blurb) + "</span>" : "") +
          "</a>";
      });
    });
    box.innerHTML = html;
    box.hidden = false;
  }

  function escapeHtml(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function setActive(i) {
    var hits = box.querySelectorAll(".search-hit");
    if (!hits.length) return;
    active = (i + hits.length) % hits.length;
    hits.forEach(function (h, n) { h.classList.toggle("active", n === active); });
    hits[active].scrollIntoView({ block: "nearest" });
  }

  function hide() { box.hidden = true; active = -1; }

  input.addEventListener("input", function () {
    var q = input.value.trim();
    if (!q) { hide(); return; }
    load().then(function () { render(query(q)); });
  });

  input.addEventListener("keydown", function (ev) {
    if (box.hidden) return;
    if (ev.key === "ArrowDown") { ev.preventDefault(); setActive(active + 1); }
    else if (ev.key === "ArrowUp") { ev.preventDefault(); setActive(active - 1); }
    else if (ev.key === "Enter") {
      var target = active >= 0 ? results[active] : results[0];
      if (target) { ev.preventDefault(); window.location.href = target.url; }
    } else if (ev.key === "Escape") { hide(); input.blur(); }
  });

  input.addEventListener("focus", function () {
    if (input.value.trim()) load().then(function () { render(query(input.value.trim())); });
  });

  document.addEventListener("click", function (ev) {
    if (!box.contains(ev.target) && ev.target !== input) hide();
  });
})();
