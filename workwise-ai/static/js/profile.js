/* WorkWise AI — profile.js
   Editable profile, skill management with proficiency, profile strength. */

(function () {
  "use strict";

  if (!document.getElementById("save-profile")) return; // not on profile page

  var PROFILE = null;

  /* ---------- Load profile ---------- */
  function load() {
    fetch("/api/profile")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        PROFILE = data;
        fillForm(data);
        renderSkills(data.skills);
        renderSections(data);
        renderStrength(data.profile_strength);
        loadSkillDatalist();
      })
      .catch(function () {});
  }

  function $(id) { return document.getElementById(id); }

  function fillForm(p) {
    $("p-headline").value = p.headline || "";
    $("p-about").value = p.about || "";
    $("p-phone").value = p.phone || "";
    $("p-location").value = p.location || "";
    $("p-role").value = p.preferred_role || "";
    $("p-jobtype").value = p.job_type || "";
    $("p-workmode").value = p.work_mode || "";
    $("p-prefloc").value = p.preferred_location || "";
    $("p-salary").value = p.expected_salary || "";
    $("p-linkedin").value = p.links && p.links.LinkedIn ? p.links.LinkedIn : "";
    $("p-github").value = p.links && p.links.GitHub ? p.links.GitHub : "";
    $("p-languages").value = (p.languages || []).join(", ");
    $("p-hobbies").value = (p.hobbies || []).join(", ");
  }

  /* ---------- Skills ---------- */
  function renderSkills(skills) {
    var el = $("my-skills");
    if (!skills.length) {
      el.innerHTML = "<li class='muted'>No skills added yet — add your first skill above.</li>";
      return;
    }
    el.innerHTML = skills.map(function (s) {
      return "<li>" +
        "<span class='skill-name'>" + window.WW_ESCAPE(s.name) + "</span>" +
        "<span class='prof-pill prof-" + s.proficiency + "'>" + s.proficiency + "</span>" +
        "<span class='skill-years'>" + (s.years || 0) + " yrs</span>" +
        "<button class='btn btn-ghost btn-sm skill-del' data-id='" + s.id + "' aria-label='Remove " + window.WW_ESCAPE(s.name) + "'>✕</button>" +
        "</li>";
    }).join("");
  }

  $("my-skills").addEventListener("click", function (e) {
    var btn = e.target.closest(".skill-del");
    if (!btn) return;
    fetch("/api/profile/skills/" + btn.dataset.id, { method: "DELETE" })
      .then(function (r) { return r.json(); })
      .then(function () { load(); })
      .catch(function () {});
  });

  $("add-skill").addEventListener("click", function () {
    var name = $("skill-name").value.trim();
    if (!name) { alert("Enter a skill name first."); return; }
    fetch("/api/profile/skills", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        name: name,
        proficiency: $("skill-prof").value,
        years: parseFloat($("skill-years").value) || 0,
      }),
    })
      .then(function (r) { return r.json(); })
      .then(function () {
        $("skill-name").value = "";
        $("skill-years").value = "";
        load();
      })
      .catch(function () {});
  });

  function loadSkillDatalist() {
    fetch("/api/skills")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        $("skill-datalist").innerHTML = data.skills.map(function (s) {
          return "<option value='" + window.WW_ESCAPE(s) + "'></option>";
        }).join("");
      })
      .catch(function () {});
  }

  /* ---------- Profile sections checklist + strength ---------- */
  var SECTION_LABELS = {
    headline: "Headline", about: "About", phone: "Phone",
    location: "Location", skills: "Skills", education: "Education",
    projects: "Projects", certificates: "Certificates",
    experience: "Experience", preferred_role: "Preferred role",
    job_preferences: "Job preferences", links: "Links",
  };

  function renderSections(p) {
    var el = $("profile-sections");
    el.innerHTML = Object.keys(SECTION_LABELS).map(function (key) {
      var done = p.profile_sections[key];
      return "<li class='" + (done ? "done" : "") + "'>" + SECTION_LABELS[key] + (done ? "" : " — add this") + "</li>";
    }).join("");
  }

  function renderStrength(pct) {
    $("profile-strength").textContent = pct;
    var ring = document.querySelector(".strength-ring");
    ring.style.background =
      "conic-gradient(var(--primary) " + pct + "%, var(--surface-2) " + pct + "%)";
  }

  /* ---------- Save handlers ---------- */
  function flash(id, msg) {
    var el = $(id);
    el.textContent = msg;
    setTimeout(function () { el.textContent = ""; }, 4000);
  }

  $("save-profile").addEventListener("click", function () {
    var payload = {
      headline: $("p-headline").value, about: $("p-about").value,
      phone: $("p-phone").value, location: $("p-location").value,
      preferred_role: $("p-role").value, job_type: $("p-jobtype").value,
      work_mode: $("p-workmode").value,
      preferred_location: $("p-prefloc").value,
      expected_salary: $("p-salary").value,
    };
    fetch("/api/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        flash("profile-status", "Profile saved! Strength: " + data.profile_strength + "%");
        load();
      })
      .catch(function () { alert("Could not save profile."); });
  });

  $("save-extra").addEventListener("click", function () {
    var links = {};
    if ($("p-linkedin").value.trim()) links.LinkedIn = $("p-linkedin").value.trim();
    if ($("p-github").value.trim()) links.GitHub = $("p-github").value.trim();
    var payload = {
      links: links,
      languages: $("p-languages").value.split(",").map(function (s) { return s.trim(); }).filter(Boolean),
      hobbies: $("p-hobbies").value.split(",").map(function (s) { return s.trim(); }).filter(Boolean),
    };
    fetch("/api/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        flash("profile-status", "Extras saved! Strength: " + data.profile_strength + "%");
        load();
      })
      .catch(function () { alert("Could not save."); });
  });

  /* ---------- Education / projects / certificates read-only list ---------- */
  function renderExtraLists() {
    // Filled by load(): shows counts from the profile payload
  }

  load();
})();
