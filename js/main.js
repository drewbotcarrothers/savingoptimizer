(function () {
  "use strict";

  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");

  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", open ? "false" : "true");
      nav.classList.toggle("is-open", !open);
    });

    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") {
        toggle.setAttribute("aria-expanded", "false");
        nav.classList.remove("is-open");
        toggle.focus();
      }
    });
  }

  var path = window.location.pathname.replace(/\/+$/, "") || "/";
  document.querySelectorAll(".site-nav a[href]").forEach(function (link) {
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
