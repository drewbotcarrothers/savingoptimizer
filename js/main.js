(function () {
  "use strict";

  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  var megaToggle = document.querySelector(".nav-mega-toggle");
  var mega = document.getElementById("nav-categories");
  var header = document.querySelector(".site-header");

  function closeMega() {
    if (!megaToggle || !mega) return;
    megaToggle.setAttribute("aria-expanded", "false");
    mega.hidden = true;
    mega.classList.remove("is-open");
  }

  function openMega() {
    if (!megaToggle || !mega) return;
    megaToggle.setAttribute("aria-expanded", "true");
    mega.hidden = false;
    mega.classList.add("is-open");
  }

  function isMegaOpen() {
    return !!(megaToggle && megaToggle.getAttribute("aria-expanded") === "true");
  }

  function closeMobileNav() {
    if (!toggle || !nav) return;
    toggle.setAttribute("aria-expanded", "false");
    nav.classList.remove("is-open");
  }

  function isMobileNavOpen() {
    return !!(toggle && toggle.getAttribute("aria-expanded") === "true");
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function (event) {
      event.stopPropagation();
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", open ? "false" : "true");
      nav.classList.toggle("is-open", !open);
      if (open) closeMega();
    });
  }

  if (megaToggle && mega) {
    megaToggle.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      if (isMegaOpen()) {
        closeMega();
      } else {
        openMega();
      }
    });

    mega.addEventListener("click", function (event) {
      var link = event.target.closest("a");
      if (link) {
        closeMega();
        closeMobileNav();
      }
    });

    document.addEventListener(
      "pointerdown",
      function (event) {
        if (!isMegaOpen()) return;
        if (header && header.contains(event.target)) {
          /* Clicks on Categories toggle are handled separately; other header
             chrome (logo, Guides, etc.) should close the mega. */
          if (megaToggle.contains(event.target) || mega.contains(event.target)) {
            return;
          }
        }
        closeMega();
      },
      true
    );
  }

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;

    if (isMegaOpen()) {
      closeMega();
      if (megaToggle) megaToggle.focus();
      return;
    }

    if (isMobileNavOpen()) {
      closeMobileNav();
      if (toggle) toggle.focus();
    }
  });

  var path = window.location.pathname.replace(/\/+$/, "") || "/";
  document.querySelectorAll(".site-nav a[href], .nav-mega a[href]").forEach(function (link) {
    var href = link.getAttribute("href");
    if (!href || href === "#") return;
    try {
      var resolved = new URL(href, window.location.href).pathname.replace(/\/+$/, "");
      if (resolved === path) {
        link.setAttribute("aria-current", "page");
      }
    } catch (err) {
      /* ignore malformed hrefs */
    }
  });

  var form = document.getElementById("contact-form");
  if (form) {
    var loaded = Date.now();
    var tsField = document.getElementById("form_ts");
    var elField = document.getElementById("form_elapsed");
    if (tsField) tsField.value = String(loaded);
    form.addEventListener("submit", function () {
      if (elField) elField.value = String(Date.now() - loaded);
    });
    if (/[?&]error=1(&|$)/.test(window.location.search)) {
      var alertBox = document.getElementById("contact-error");
      if (alertBox) {
        alertBox.hidden = false;
        alertBox.setAttribute("tabindex", "-1");
        alertBox.focus();
      }
    }
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest && e.target.closest('.yt-facade-btn');
    if (!btn) return;
    var box = btn.parentElement, id = box.getAttribute('data-videoid');
    if (!/^[A-Za-z0-9_-]{11}$/.test(id)) return;
    var f = document.createElement('iframe');
    f.src = 'https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&rel=0';
    f.title = box.getAttribute('data-title') || 'YouTube video';
    f.allow = 'accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share';
    f.referrerPolicy = 'strict-origin-when-cross-origin';
    f.allowFullscreen = true;
    box.replaceChildren(f);
  });

})();
