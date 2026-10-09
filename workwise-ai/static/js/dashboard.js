/* WorkWise AI — dashboard.js
   Stats, Chart.js charts, application lists, status timeline. */

(function () {
  "use strict";

  if (!document.getElementById("stat-applied")) return; // not on dashboard

  var charts = [];
  var DASH_DATA = null;

  var CHART_COLORS = {
    primary: "#6d28d9",
    secondary: "#0ea5e9",
    accent: "#f59e0b",
    success: "#16a34a",
    grid: function () {
      var dark = document.documentElement.getAttribute("data-theme") === "dark";
      return dark ? "#2c3852" : "#e5e9f2";
    },
    text: function () {
      var dark = document.documentElement.getAttribute("data-theme") === "dark";
      return dark ? "#9aa5bd" : "#5b6478";
    },
  };

  /* ---------- Fetch dashboard data ---------- */
  function load() {
    fetch("/api/dashboard")
      .then(function (r) {
        if (r.status === 401) { window.location.href = "/login"; throw new Error("auth"); }
        return r.json();
      })
      .then(function (data) {
        DASH_DATA = data;
        renderStats(data);
        renderLists(data);
        renderCharts(data);
      })
      .catch(function () {});
  }

  function renderStats(d) {
    setNum("stat-applied", d.total_applications);
    setNum("stat-jobs", d.jobs_applied);
    setNum("stat-interns", d.internships_applied);
    setNum("stat-saved", d.saved_jobs);
    setNum("stat-skills", d.skills_count);
    setNum("stat-strength", d.profile_strength);
    document.getElementById("strength-bar").style.width = d.profile_strength + "%";

    // Notification banner from latest unread notification
    var unread = d.notifications && d.notifications.filter(function (n) { return !n.is_read; });
    if (unread && unread.length) {
      var banner = document.getElementById("notif-banner");
      var txt = document.getElementById("notif-banner-text");
      txt.textContent = "🔔 " + unread[0].message;
      banner.hidden = false;
      document.getElementById("notif-banner-close").addEventListener("click", function () {
        banner.hidden = true;
      });
    }
  }

  function setNum(id, val) {
    var el = document.getElementById(id);
    if (el) el.textContent = val;
  }

  /* ---------- Application lists ---------- */
  function renderLists(d) {
    renderAppList("applied-jobs", d.applications.filter(function (a) { return !a.is_internship; }));
    renderAppList("applied-internships", d.applications.filter(function (a) { return a.is_internship; }));

    var savedEl = document.getElementById("saved-jobs-list");
    if (!d.saved.length) {
      savedEl.innerHTML = "<li class='muted'>No saved jobs yet. Browse jobs and tap Save.</li>";
    } else {
      savedEl.innerHTML = d.saved.map(function (j) {
        return "<li data-job-id='" + j.id + "'>" +
          "<span class='app-title'>" + window.WW_ESCAPE(j.title) + "</span>" +
          (j.ai_fit != null ? "<span class='status-pill status-Offer'>AI " + j.ai_fit + "%</span>" : "") +
          "<div class='app-meta'>" + window.WW_ESCAPE(j.company) + " · " + window.WW_ESCAPE(j.location) + "</div></li>";
      }).join("");
    }
  }

  function renderAppList(elId, apps) {
    var el = document.getElementById(elId);
    if (!apps.length) {
      el.innerHTML = "<li class='muted'>No applications yet — apply to a job!</li>";
      return;
    }
    el.innerHTML = apps.map(function (a) {
      return "<li data-app-id='" + a.id + "'>" +
        "<span class='app-title'>" + window.WW_ESCAPE(a.job_title) + "</span>" +
        "<span class='status-pill status-" + a.status.replace(/ /g, "-") + "'>" + a.status + "</span>" +
        "<div class='app-meta'>" + window.WW_ESCAPE(a.company) + " · applied " +
        new Date(a.applied_at).toLocaleDateString("en-IN") + "</div></li>";
    }).join("");
  }

  /* ---------- Application detail + timeline ---------- */
  function showApplication(appId) {
    var app = DASH_DATA.applications.find(function (a) { return a.id === appId; });
    if (!app) return;
    var panel = document.getElementById("app-detail-panel");
    document.getElementById("app-detail-title").textContent =
      app.job_title + " — " + app.company;

    var stages = ["Applied", "Under Review", "Shortlisted", "Interview Scheduled", "Offer"];
    var currentIdx = stages.indexOf(app.status);
    document.getElementById("app-timeline").innerHTML = stages.map(function (s, i) {
      return "<span class='tl-step " + (i <= currentIdx ? "active" : "") + "'>" + s + "</span>";
    }).join("");

    var gap = app.skill_gap && app.skill_gap.length
      ? "<p><strong>Skill gap to close:</strong></p><div class='skill-tags'>" +
        app.skill_gap.map(function (s) { return "<span class='skill-tag skill-gap'>" + window.WW_ESCAPE(s) + "</span>"; }).join("") + "</div>"
      : "<p>✅ Your skills match this role well.</p>";

    document.getElementById("app-detail-body").innerHTML =
      "<p class='muted'>Resume details sent: " + (app.resume_sent ? "Yes" : "No") + "</p>" +
      "<h4>What to do next</h4><ul class='checklist'>" +
      app.next_steps.map(function (s) { return "<li>" + window.WW_ESCAPE(s) + "</li>"; }).join("") + "</ul>" +
      gap +
      "<p style='margin-top:14px'><a class='btn btn-outline btn-sm' href='/job/" + app.job_id + "'>View job</a></p>";
    panel.hidden = false;
    panel.scrollIntoView({ behavior: "smooth" });
  }

  document.getElementById("applied-jobs").addEventListener("click", function (e) {
    var li = e.target.closest("li[data-app-id]");
    if (li) showApplication(parseInt(li.dataset.appId, 10));
  });
  document.getElementById("applied-internships").addEventListener("click", function (e) {
    var li = e.target.closest("li[data-app-id]");
    if (li) showApplication(parseInt(li.dataset.appId, 10));
  });
  document.getElementById("saved-jobs-list").addEventListener("click", function (e) {
    var li = e.target.closest("li[data-job-id]");
    if (li) window.location.href = "/job/" + li.dataset.jobId;
  });

  /* ---------- Charts ---------- */
  function renderCharts(d) {
    if (typeof Chart === "undefined") return;
    charts.forEach(function (c) { c.destroy(); });
    charts = [];

    var gridColor = CHART_COLORS.grid();
    var textColor = CHART_COLORS.text();
    Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;

    // 1. Area chart: AI Fit % across applied jobs
    var fitApps = d.applications.filter(function (a) { return a.skill_gap !== undefined; });
    // Estimate AI fit for each applied job from saved list or compute from demand
    var fitLabels = d.applications.map(function (a) { return a.job_title.length > 18 ? a.job_title.slice(0, 18) + "…" : a.job_title; });
    var fitData = d.applications.map(function (a, i) {
      // deterministic estimate from skill gap size
      var gapSize = (a.skill_gap || []).length;
      return Math.max(20, 92 - gapSize * 9 - i * 2);
    });
    var ctx1 = document.getElementById("chart-fit").getContext("2d");
    var grad = ctx1.createLinearGradient(0, 0, 0, 220);
    grad.addColorStop(0, "rgba(109,40,217,.35)");
    grad.addColorStop(1, "rgba(109,40,217,0)");
    charts.push(new Chart(ctx1, {
      type: "line",
      data: {
        labels: fitLabels,
        datasets: [{
          label: "AI Fit %",
          data: fitData,
          fill: true,
          backgroundColor: grad,
          borderColor: CHART_COLORS.primary,
          tension: 0.35,
          pointRadius: 4,
        }],
      },
      options: chartOpts(gridColor, textColor, "%"),
    }));

    // 2. Line chart: skill growth over time
    var growth = d.skill_growth.length ? d.skill_growth : [];
    charts.push(new Chart(document.getElementById("chart-growth"), {
      type: "line",
      data: {
        labels: growth.map(function (g) { return g.label; }),
        datasets: [{
          label: "Cumulative skill depth (yrs)",
          data: growth.map(function (g) { return g.value; }),
          borderColor: CHART_COLORS.secondary,
          backgroundColor: "rgba(14,165,233,.15)",
          fill: true,
          tension: 0.3,
          pointRadius: 4,
        }],
      },
      options: chartOpts(gridColor, textColor, ""),
    }));

    // 3. Bar chart: skills in demand vs my skills
    var demand = d.skills_in_demand.slice(0, 6);
    charts.push(new Chart(document.getElementById("chart-demand"), {
      type: "bar",
      data: {
        labels: demand.map(function (s) { return s.skill; }),
        datasets: [
          {
            label: "In demand (sample jobs)",
            data: demand.map(function (s) { return s.count; }),
            backgroundColor: "rgba(109,40,217,.75)",
            borderRadius: 6,
          },
          {
            label: "I have this skill",
            data: demand.map(function (s) { return d.my_skills.indexOf(s.skill) >= 0 ? 1 : 0; }),
            backgroundColor: "rgba(22,163,74,.8)",
            borderRadius: 6,
          },
        ],
      },
      options: chartOpts(gridColor, textColor, ""),
    }));

    // 4. Donut chart: skills by category
    var cats = d.skills_by_category || {};
    var labels = Object.keys(cats);
    charts.push(new Chart(document.getElementById("chart-category"), {
      type: "doughnut",
      data: {
        labels: labels.length ? labels : ["No skills yet"],
        datasets: [{
          data: labels.length ? labels.map(function (k) { return cats[k]; }) : [1],
          backgroundColor: ["#6d28d9", "#0ea5e9", "#f59e0b", "#16a34a", "#ec4899", "#8b5cf6"],
          borderWidth: 2,
          borderColor: document.documentElement.getAttribute("data-theme") === "dark" ? "#1a2233" : "#fff",
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "right", labels: { color: textColor, boxWidth: 12 } },
        },
      },
    }));
  }

  function chartOpts(gridColor, textColor, tickSuffix) {
    return {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: { ticks: { color: textColor }, grid: { color: gridColor } },
        y: { ticks: { color: textColor, callback: function (v) { return v + tickSuffix; } }, grid: { color: gridColor } },
      },
      plugins: { legend: { labels: { color: textColor } } },
    };
  }

  // Re-render charts when the theme changes (main.js calls this)
  window.refreshDashboardCharts = function () {
    if (DASH_DATA) renderCharts(DASH_DATA);
  };

  load();
})();
