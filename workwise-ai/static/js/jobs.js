/* WorkWise AI — jobs.js
   Job listing: search, filters, internships tab, AI Fit display,
   quick-view modal and save/unsave. */

(function () {
  "use strict";

  var state = { type: "all", sort: "" };
  var grid = document.getElementById("job-grid");
  var statusEl = document.getElementById("jobs-status");
  var form = document.getElementById("job-filters");

  if (!grid) return; // not on the jobs page

  /* ---------- Read filter values ---------- */
  function readFilters() {
    var fd = new FormData(form);
    var params = new URLSearchParams();
    if (state.type === "internship") params.set("type", "internship");
    if (state.sort) params.set("sort", state.sort);
    ["q", "location", "experience", "job_type", "work_mode",
      "category", "min_salary", "max_salary"].forEach(function (k) {
      var v = (fd.get(k) || "").toString().trim();
      if (v) params.set(k, v);
    });
    return params.toString();
  }

  /* ---------- Render a job card ---------- */
  function jobCard(j) {
    var fit = j.ai_fit == null
      ? ""
      : '<span class="fit-badge" title="AI match (cosine similarity)">AI Fit ' + j.ai_fit + "%</span>";
    var gap = (j.skill_gap && j.skill_gap.length)
      ? '<div class="skill-tags" style="margin-top:8px">' +
        j.skill_gap.slice(0, 3).map(function (s) {
          return '<span class="skill-tag skill-gap">+' + window.WW_ESCAPE(s) + "</span>";
        }).join("") + "</div>"
      : "";
    var skills = j.skills.slice(0, 4).map(function (s) {
      return '<span class="skill-tag">' + window.WW_ESCAPE(s) + "</span>";
    }).join("");
    var salary = j.is_internship
      ? "Stipend: " + window.WW_ESCAPE(j.salary_text)
      : window.WW_ESCAPE(j.salary_text);

    return '<article class="job-card">' +
      '<div class="job-card-top">' +
      '<img src="/static/images/' + window.WW_ESCAPE(j.company_image) + '" class="company-logo-img" alt="' + window.WW_ESCAPE(j.company) + ' logo" width="44" height="44">' +
      "<div>" +
      "<h3><a href='/job/" + j.id + "'>" + window.WW_ESCAPE(j.title) + "</a></h3>" +
      '<p class="company">' + window.WW_ESCAPE(j.company) +
      (j.is_sample ? ' <span class="pill pill-sample">SAMPLE</span>' : "") +
      "</p></div>" + fit + "</div>" +
      '<p class="job-meta"><span>📍 ' + window.WW_ESCAPE(j.location) + "</span>" +
      "<span>💼 " + window.WW_ESCAPE(j.job_type) + "</span>" +
      "<span>🕒 " + window.WW_ESCAPE(j.experience_text) + "</span>" +
      "<span>🏠 " + window.WW_ESCAPE(j.work_mode) + "</span></p>" +
      '<p class="job-salary">' + salary + "</p>" +
      '<div class="skill-tags">' + skills + "</div>" + gap +
      "</article>";
  }

  /* ---------- Fetch and render ---------- */
  function loadJobs() {
    statusEl.textContent = "Loading jobs…";
    grid.innerHTML = "";
    fetch("/api/jobs?" + readFilters())
      .then(function (r) { return r.json(); })
      .then(function (data) {
        statusEl.textContent = data.count + " " +
          (state.type === "internship" ? "internships" : "jobs") +
          " found (sample listings)";
        if (!data.jobs.length) {
          grid.innerHTML = '<p class="muted">No jobs match your filters. Try clearing them.</p>';
          return;
        }
        grid.innerHTML = data.jobs.map(jobCard).join("");
      })
      .catch(function () {
        statusEl.textContent = "Could not load jobs. Is the server running?";
      });
  }

  /* ---------- Events ---------- */
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    loadJobs();
  });
  document.getElementById("clear-filters").addEventListener("click", function () {
    form.reset();
    loadJobs();
  });
  document.getElementById("sort").addEventListener("change", function () {
    state.sort = this.value;
    loadJobs();
  });
  document.getElementById("tab-jobs").addEventListener("click", function () {
    state.type = "all";
    this.classList.add("active");
    this.setAttribute("aria-selected", "true");
    var t = document.getElementById("tab-internships");
    t.classList.remove("active");
    t.setAttribute("aria-selected", "false");
    document.getElementById("jobs-title").textContent = "Jobs & Internships";
    loadJobs();
  });
  document.getElementById("tab-internships").addEventListener("click", function () {
    state.type = "internship";
    this.classList.add("active");
    this.setAttribute("aria-selected", "true");
    var t = document.getElementById("tab-jobs");
    t.classList.remove("active");
    t.setAttribute("aria-selected", "false");
    document.getElementById("jobs-title").textContent = "Internships";
    loadJobs();
  });

  /* ---------- Quick view modal ---------- */
  var modal = document.getElementById("job-modal");
  var modalBody = document.getElementById("modal-body");
  document.getElementById("modal-close").addEventListener("click", function () {
    modal.hidden = true;
  });
  modal.addEventListener("click", function (e) {
    if (e.target === modal) modal.hidden = true;
  });

  grid.addEventListener("click", function (e) {
    var card = e.target.closest(".job-card");
    if (!card) return;
    var titleEl = card.querySelector("h3 a");
    var id = titleEl.getAttribute("href").split("/")[2];
    fetch("/api/jobs/" + id)
      .then(function (r) { return r.json(); })
      .then(function (j) {
        document.getElementById("modal-title").textContent = j.title;
        modalBody.innerHTML =
          "<p><strong>" + window.WW_ESCAPE(j.company) + "</strong> · " +
          window.WW_ESCAPE(j.location) + " · " + window.WW_ESCAPE(j.experience_text) +
          "</p><p>" + window.WW_ESCAPE(j.description) + "</p>" +
          "<h4>Required skills</h4><div class='skill-tags'>" +
          j.skills.map(function (s) { return '<span class="skill-tag">' + window.WW_ESCAPE(s) + "</span>"; }).join("") +
          "</div>" +
          (j.skill_gap && j.skill_gap.length
            ? "<h4>Your skill gap</h4><div class='skill-tags'>" +
              j.skill_gap.map(function (s) { return '<span class="skill-tag skill-gap">' + window.WW_ESCAPE(s) + "</span>"; }).join("") + "</div>"
            : "") +
          '<p style="margin-top:14px"><a class="btn btn-primary" href="/job/' + j.id + '">View details</a> ' +
          '<a class="btn btn-outline" href="/job/' + j.id + '/apply">Apply</a></p>';
        modal.hidden = false;
      });
  });

  /* ---------- Sync state from URL parameters ----------
     Handles: navbar "Internships" link (/jobs?type=internship)
     and the home-page hero search (/jobs?q=...&experience=...&location=...) */
  function syncFromURL() {
    var params = new URLSearchParams(window.location.search);

    // Listing type (all | internship)
    var type = (params.get("type") || "").toLowerCase();
    if (type === "internship") {
      state.type = "internship";
      document.getElementById("tab-internships").classList.add("active");
      document.getElementById("tab-internships").setAttribute("aria-selected", "true");
      document.getElementById("tab-jobs").classList.remove("active");
      document.getElementById("tab-jobs").setAttribute("aria-selected", "false");
      document.getElementById("jobs-title").textContent = "Internships";
    }

    // Populate filter form from URL (hero search + direct links)
    ["q", "location", "experience", "job_type", "work_mode",
      "category", "min_salary", "max_salary"].forEach(function (k) {
      var v = params.get(k);
      if (v) {
        var field = document.getElementById("f-" + k);
        if (field) field.value = v;
      }
    });

    // Sort
    var sort = params.get("sort");
    if (sort) {
      state.sort = sort;
      var sortField = document.getElementById("sort");
      if (sortField) sortField.value = sort;
    }
  }

  syncFromURL();
  loadJobs();
})();
