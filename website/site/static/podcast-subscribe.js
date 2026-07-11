// Podcast subscribe control.
//
// Turns a .js-copy-feed link into a "copy the RSS feed URL to the clipboard"
// action with a small popover telling the user to paste it into their podcast
// app. Progressive enhancement: with JS off, the link still points at feed.xml.
//
// The production site is served over HTTP, where navigator.clipboard is
// unavailable (secure-context only), so copying falls back to execCommand and,
// failing that, to showing the URL as selectable text for a manual copy.
(function () {
  "use strict";

  var links = document.querySelectorAll(".js-copy-feed");
  if (!links.length) return; // no-op on pages without the control

  var openPopover = null; // the currently-visible popover element, if any

  function feedUrl(link) {
    return link.getAttribute("data-feed-url") ||
      new URL(link.getAttribute("href") || "feed.xml", location.href).href;
  }

  // Try to copy `text`; resolve true on success, false otherwise.
  function copyText(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
      return navigator.clipboard.writeText(text).then(
        function () { return true; },
        function () { return execCopy(text); }
      );
    }
    return Promise.resolve(execCopy(text));
  }

  // Legacy fallback for non-secure contexts (HTTP).
  function execCopy(text) {
    try {
      var ta = document.createElement("textarea");
      ta.value = text;
      ta.setAttribute("readonly", "");
      ta.style.position = "fixed";
      ta.style.top = "-1000px";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      var ok = document.execCommand("copy");
      document.body.removeChild(ta);
      return ok;
    } catch (e) {
      return false;
    }
  }

  function closePopover() {
    if (!openPopover) return;
    var p = openPopover;
    openPopover = null;
    p.classList.remove("is-visible");
    document.removeEventListener("click", onOutside, true);
    document.removeEventListener("keydown", onKey, true);
    window.setTimeout(function () {
      if (p.parentNode) p.parentNode.removeChild(p);
    }, 200);
  }

  function onOutside(e) {
    if (openPopover && !openPopover.contains(e.target) &&
        !e.target.closest(".js-copy-feed")) {
      closePopover();
    }
  }

  function onKey(e) {
    if (e.key === "Escape") closePopover();
  }

  function showPopover(wrap, url, copied) {
    closePopover();
    var pop = document.createElement("span");
    pop.className = "copy-feed-popover";
    pop.setAttribute("role", "status");
    pop.setAttribute("aria-live", "polite");

    var head = document.createElement("strong");
    head.className = "copy-feed-head";
    head.textContent = copied ? "Feed link copied" : "Copy this link:";
    pop.appendChild(head);

    var urlEl = document.createElement("span");
    urlEl.className = "copy-feed-url";
    urlEl.textContent = url;
    pop.appendChild(urlEl);

    var hint = document.createElement("span");
    hint.className = "copy-feed-hint";
    hint.textContent = "Paste it into your podcast app to subscribe.";
    pop.appendChild(hint);

    wrap.appendChild(pop);
    // force reflow so the transition runs, then reveal
    void pop.offsetWidth;
    pop.classList.add("is-visible");
    openPopover = pop;

    document.addEventListener("click", onOutside, true);
    document.addEventListener("keydown", onKey, true);
    window.setTimeout(closePopover, 6000);
  }

  Array.prototype.forEach.call(links, function (link) {
    link.addEventListener("click", function (e) {
      e.preventDefault();
      var wrap = link.closest(".copy-feed-wrap") || link.parentNode;
      var url = feedUrl(link);
      Promise.resolve(copyText(url)).then(function (ok) {
        showPopover(wrap, url, ok);
      });
    });
  });
})();
