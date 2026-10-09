/* WorkWise AI — main.js
   Theme toggle, mobile nav, notification bell, shared helpers. */

(function () {
  "use strict";

  /* ---------- Theme toggle (persisted) ---------- */
  var themeToggle = document.getElementById("theme-toggle");
  var iconSun = document.getElementById("icon-sun");
  var iconMoon = document.getElementById("icon-moon");

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    if (iconSun && iconMoon) {
      iconSun.style.display = theme === "dark" ? "none" : "";
      iconMoon.style.display = theme === "dark" ? "" : "none";
    }
    try { localStorage.setItem("ww-theme", theme); } catch (e) { /* private mode */ }
    // Recreate charts so they pick up the new colours
    if (window.refreshDashboardCharts) window.refreshDashboardCharts();
  }

  var savedTheme = "light";
  try { savedTheme = localStorage.getItem("ww-theme") || "light"; } catch (e) {}
  applyTheme(savedTheme);

  if (themeToggle) {
    themeToggle.addEventListener("click", function () {
      var current = document.documentElement.getAttribute("data-theme");
      applyTheme(current === "dark" ? "light" : "dark");
    });
  }

  /* ---------- Mobile nav toggle ---------- */
  var navToggle = document.getElementById("nav-toggle");
  var navLinks = document.getElementById("nav-links");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", function () {
      var open = navLinks.classList.toggle("open");
      navToggle.setAttribute("aria-expanded", String(open));
    });
    navLinks.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        navLinks.classList.remove("open");
        navToggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---------- Notification bell ---------- */
  var bell = document.getElementById("notif-bell");
  var panel = document.getElementById("notif-panel");
  var list = document.getElementById("notif-list");
  var badge = document.getElementById("notif-badge");
  var readBtn = document.getElementById("notif-read");

  window.WW_NOTIFICATIONS = {
    refresh: function () {
      if (!bell) return;
      fetch("/api/notifications")
        .then(function (r) { return r.json(); })
        .then(function (data) {
          var unread = data.unread || 0;
          if (badge) {
            badge.hidden = unread === 0;
            badge.textContent = unread;
          }
          if (list) {
            list.innerHTML = data.notifications.length
              ? data.notifications.map(function (n) {
                  return '<li class="' + (n.is_read ? "" : "unread") + '">' +
                    escapeHtml(n.message) + "</li>";
                }).join("")
              : "<li>No notifications yet.</li>";
          }
        })
        .catch(function () {});
    },
    markRead: function () {
      fetch("/api/notifications/read", { method: "POST" })
        .then(function (r) { return r.json(); })
        .then(function () { window.WW_NOTIFICATIONS.refresh(); })
        .catch(function () {});
    },
  };

  if (bell && panel) {
    bell.addEventListener("click", function (e) {
      e.stopPropagation();
      panel.hidden = !panel.hidden;
      if (!panel.hidden) window.WW_NOTIFICATIONS.refresh();
    });
    document.addEventListener("click", function (e) {
      if (!panel.hidden && !panel.contains(e.target) && e.target !== bell) {
        panel.hidden = true;
      }
    });
  }
  if (readBtn) readBtn.addEventListener("click", function (e) {
    e.stopPropagation();
    window.WW_NOTIFICATIONS.markRead();
  });
  window.WW_NOTIFICATIONS.refresh();

  /* ---------- Shared helpers ---------- */
  function escapeHtml(str) {
    return String(str == null ? "" : str)
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  window.WW_ESCAPE = escapeHtml;

  function showError(containerId, message) {
    var el = document.getElementById(containerId);
    if (el) {
      el.innerHTML = '<div class="alert alert-error">' + escapeHtml(message) + "</div>";
      el.scrollIntoView({ behavior: "smooth" });
    }
  }
  window.WW_SHOW_ERROR = showError;

  function apiCall(url, options) {
    return fetch(url, options).then(function (res) {
      return res.json().then(function (data) {
        return { ok: res.ok, status: res.status, data: data };
      });
    });
  }
  window.WW_API = apiCall;

  /* ---------- Salary estimate widget (home page CTA) ---------- */
  // Small helper used by multiple pages to format INR.
  window.WW_INR = function (n) {
    return "₹" + Number(n).toLocaleString("en-IN");
  };
})();
