(function () {
  "use strict";

  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("site-nav");
  var dropdownToggle = document.querySelector(".nav-dropdown-toggle");
  var dropdown = document.getElementById("nav-categories");
  var dropdownItem = dropdownToggle
    ? dropdownToggle.closest(".has-dropdown")
    : null;

  function closeDropdown() {
    if (!dropdownToggle || !dropdown) return;
    dropdownToggle.setAttribute("aria-expanded", "false");
    dropdown.hidden = true;
    dropdown.classList.remove("is-open");
  }

  function openDropdown() {
    if (!dropdownToggle || !dropdown) return;
    dropdownToggle.setAttribute("aria-expanded", "true");
    dropdown.hidden = false;
    dropdown.classList.add("is-open");
    positionDropdown();
  }

  function isDropdownOpen() {
    return !!(dropdownToggle && dropdownToggle.getAttribute("aria-expanded") === "true");
  }

  /* Keep the panel on-screen in Chrome (wide multi-col menus near the right edge). */
  function positionDropdown() {
    if (!dropdown || !dropdownItem) return;
    if (window.matchMedia("(max-width: 1023.98px)").matches) {
      dropdown.style.left = "";
      dropdown.style.right = "";
      return;
    }
    dropdown.style.left = "0";
    dropdown.style.right = "auto";
    var rect = dropdown.getBoundingClientRect();
    var pad = 16;
    if (rect.right > window.innerWidth - pad) {
      dropdown.style.left = "auto";
      dropdown.style.right = "0";
    }
  }

  if (toggle && nav) {
    toggle.addEventListener("click", function (event) {
      event.stopPropagation();
      var open = toggle.getAttribute("aria-expanded") === "true";
      toggle.setAttribute("aria-expanded", open ? "false" : "true");
      nav.classList.toggle("is-open", !open);
      if (open) closeDropdown();
    });
  }

  if (dropdownToggle && dropdown) {
    dropdownToggle.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      if (isDropdownOpen()) {
        closeDropdown();
      } else {
        openDropdown();
      }
    });

    /* Use pointerdown in capture so Chrome doesn't treat the same gesture oddly with deferred listeners. */
    document.addEventListener(
      "pointerdown",
      function (event) {
        if (!isDropdownOpen()) return;
        if (dropdownItem && dropdownItem.contains(event.target)) return;
        closeDropdown();
      },
      true
    );
  }

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;

    if (isDropdownOpen()) {
      closeDropdown();
      if (dropdownToggle) dropdownToggle.focus();
      return;
    }

    if (toggle && toggle.getAttribute("aria-expanded") === "true") {
      toggle.setAttribute("aria-expanded", "false");
      if (nav) nav.classList.remove("is-open");
      toggle.focus();
    }
  });

  window.addEventListener("resize", function () {
    if (isDropdownOpen()) positionDropdown();
  });

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
