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
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      var name = (form.querySelector("#name") || {}).value || "";
      var email = (form.querySelector("#email") || {}).value || "";
      var topic = (form.querySelector("#topic") || {}).value || "General";
      var message = (form.querySelector("#message") || {}).value || "";
      var subject = "Saving Optimizer: " + topic + " — " + name.trim();
      var body =
        "Name: " + name.trim() + "\n" +
        "Email: " + email.trim() + "\n" +
        "Topic: " + topic + "\n\n" +
        message.trim();
      var mailto =
        "mailto:hello@savingoptimizer.com" +
        "?subject=" + encodeURIComponent(subject) +
        "&body=" + encodeURIComponent(body);
      window.location.href = mailto;
    });
  }
})();
