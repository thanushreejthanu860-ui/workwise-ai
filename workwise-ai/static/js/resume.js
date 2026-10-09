/* WorkWise AI — resume.js
   Live A4 resume preview, save, PDF via window.print(), Word .doc download. */

(function () {
  "use strict";

  if (!document.getElementById("resume-preview")) return; // not on resume page

  function $(id) { return document.getElementById(id); }

  /* ---------- Field map: input id -> (preview id, transform) ---------- */
  var FIELDS = [
    ["r-name", "pv-name"],
    ["r-headline", "pv-headline"],
    ["r-email", "pv-email"],
    ["r-phone", "pv-phone"],
    ["r-location", "pv-location"],
  ];

  /* ---------- Gather all resume data from the form ---------- */
  function collect() {
    return {
      name: $("r-name").value.trim(),
      headline: $("r-headline").value.trim(),
      email: $("r-email").value.trim(),
      phone: $("r-phone").value.trim(),
      location: $("r-location").value.trim(),
      education: {
        tenth: { school: $("r-tenth-school").value.trim(), pct: $("r-tenth-pct").value.trim(), year: $("r-tenth-year").value.trim() },
        twelfth: { school: $("r-twelfth-school").value.trim(), pct: $("r-twelfth-pct").value.trim(), year: $("r-twelfth-year").value.trim() },
        degree: { name: $("r-degree-name").value.trim(), cgpa: $("r-degree-cgpa").value.trim(), year: $("r-degree-year").value.trim() },
      },
      skills: $("r-skills").value.split(",").map(function (s) { return s.trim(); }).filter(Boolean),
      projects: parseLines($("r-projects").value),
      internships: parseLines($("r-internships").value),
      certificates: parseLines($("r-certificates").value),
      languages: $("r-languages").value.trim(),
      hobbies: $("r-hobbies").value.trim(),
    };
  }

  function parseLines(text) {
    return text.split("\n").map(function (l) { return l.trim(); }).filter(Boolean);
  }

  /* ---------- Live preview ---------- */
  function updatePreview() {
    var d = collect();
    FIELDS.forEach(function (pair) {
      var el = $(pair[1]);
      if (el) el.textContent = d[pair[0]] || "";
    });

    // Education
    var eduBits = [];
    if (d.education.tenth.school) eduBits.push("<strong>10th:</strong> " + esc(d.education.tenth.school) + " — " + esc(d.education.tenth.pct) + " (" + esc(d.education.tenth.year) + ")");
    if (d.education.twelfth.school) eduBits.push("<strong>12th:</strong> " + esc(d.education.twelfth.school) + " — " + esc(d.education.twelfth.pct) + " (" + esc(d.education.twelfth.year) + ")");
    if (d.education.degree.name) eduBits.push("<strong>" + esc(d.education.degree.name) + ":</strong> CGPA " + esc(d.education.degree.cgpa) + " (" + esc(d.education.degree.year) + ")");
    toggleSection("resume-h-education", eduBits.length);
    $("pv-education").innerHTML = eduBits.map(function (b) { return "<p>" + b + "</p>"; }).join("");

    // Skills
    toggleSection("resume-h-skills", d.skills.length);
    $("pv-skills").innerHTML = d.skills.map(function (s) { return "<span>" + esc(s) + "</span>"; }).join("");

    // Projects
    toggleSection("resume-h-projects", d.projects.length);
    $("pv-projects").innerHTML = d.projects.map(function (p) {
      var parts = p.split("—").map(function (x) { return x.trim(); });
      return "<li><strong>" + esc(parts[0] || p) + "</strong>" + (parts[1] ? " — " + esc(parts[1]) : "") + (parts[2] ? " <em>(" + esc(parts[2]) + ")</em>" : "") + "</li>";
    }).join("");

    // Internships
    toggleSection("resume-h-internships", d.internships.length);
    $("pv-internships").innerHTML = d.internships.map(function (p) {
      var parts = p.split("—").map(function (x) { return x.trim(); });
      return "<li><strong>" + esc(parts[0] || p) + "</strong>" + (parts[1] ? " — " + esc(parts[1]) : "") + (parts[2] ? " <em>(" + esc(parts[2]) + ")</em>" : "") + (parts[3] ? ": " + esc(parts[3]) : "") + "</li>";
    }).join("");

    // Certificates
    toggleSection("resume-h-certificates", d.certificates.length);
    $("pv-certificates").innerHTML = d.certificates.map(function (c) {
      var parts = c.split("—").map(function (x) { return x.trim(); });
      return "<li><strong>" + esc(parts[0] || c) + "</strong>" + (parts[1] ? " — " + esc(parts[1]) : "") + (parts[2] ? " (" + esc(parts[2]) + ")" : "") + "</li>";
    }).join("");

    // Languages & hobbies
    var langBits = [];
    if (d.languages) langBits.push("<strong>Languages:</strong> " + esc(d.languages));
    if (d.hobbies) langBits.push("<strong>Hobbies:</strong> " + esc(d.hobbies));
    toggleSection("resume-h-lang", langBits.length);
    $("pv-lang").innerHTML = langBits.join(" · ");
  }

  function toggleSection(headerId, show) {
    var h = $(headerId);
    if (h) h.hidden = !show;
  }

  function esc(str) {
    return String(str || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  /* ---------- Wire live updates ---------- */
  var inputs = document.querySelectorAll(".resume-form input, .resume-form textarea");
  inputs.forEach(function (input) {
    input.addEventListener("input", updatePreview);
  });

  /* ---------- Pre-fill from saved resume / user profile ---------- */
  function prefill() {
    fetch("/api/resume")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data || !Object.keys(data).length) return prefillFromProfile();
        setVal("r-name", data.name); setVal("r-headline", data.headline);
        setVal("r-email", data.email); setVal("r-phone", data.phone);
        setVal("r-location", data.location);
        if (data.education) {
          setVal("r-tenth-school", data.education.tenth && data.education.tenth.school);
          setVal("r-tenth-pct", data.education.tenth && data.education.tenth.pct);
          setVal("r-tenth-year", data.education.tenth && data.education.tenth.year);
          setVal("r-twelfth-school", data.education.twelfth && data.education.twelfth.school);
          setVal("r-twelfth-pct", data.education.twelfth && data.education.twelfth.pct);
          setVal("r-twelfth-year", data.education.twelfth && data.education.twelfth.year);
          setVal("r-degree-name", data.education.degree && data.education.degree.name);
          setVal("r-degree-cgpa", data.education.degree && data.education.degree.cgpa);
          setVal("r-degree-year", data.education.degree && data.education.degree.year);
        }
        setVal("r-skills", (data.skills || []).join(", "));
        setVal("r-projects", (data.projects || []).join("\n"));
        setVal("r-internships", (data.internships || []).join("\n"));
        setVal("r-certificates", (data.certificates || []).join("\n"));
        setVal("r-languages", data.languages || "");
        setVal("r-hobbies", data.hobbies || "");
        updatePreview();
      })
      .catch(function () {});
  }

  function prefillFromProfile() {
    fetch("/api/profile")
      .then(function (r) { return r.json(); })
      .then(function (p) {
        setVal("r-name", p.name); setVal("r-headline", p.headline);
        setVal("r-email", p.email); setVal("r-phone", p.phone);
        setVal("r-location", p.location);
        if (p.education && p.education.length) {
          var e = p.education;
          function find(level) { return e.filter(function (x) { return x.level && x.level.toLowerCase().indexOf(level) >= 0; })[0]; }
          var t = find("10th"), tw = find("12th"), dg = find("bachelor");
          if (t) { setVal("r-tenth-school", t.institution); setVal("r-tenth-pct", t.percentage_or_cgpa); setVal("r-tenth-year", t.year); }
          if (tw) { setVal("r-twelfth-school", tw.institution); setVal("r-twelfth-pct", tw.percentage_or_cgpa); setVal("r-twelfth-year", tw.year); }
          if (dg) { setVal("r-degree-name", dg.field_of_study || dg.level); setVal("r-degree-cgpa", dg.percentage_or_cgpa); setVal("r-degree-year", dg.year); }
        }
        setVal("r-skills", (p.skills || []).map(function (s) { return s.name; }).join(", "));
        updatePreview();
      })
      .catch(function () {});
  }

  function setVal(id, val) {
    var el = $(id);
    if (el && val != null) el.value = val;
  }

  prefill();

  /* ---------- Save resume ---------- */
  $("save-resume").addEventListener("click", function () {
    var data = collect();
    fetch("/api/resume", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
      .then(function (r) { return r.json(); })
      .then(function () {
        var st = $("resume-status");
        st.textContent = "Resume saved ✓";
        setTimeout(function () { st.textContent = ""; }, 4000);
      })
      .catch(function () { alert("Could not save resume."); });
  });

  /* ---------- Download PDF (browser print) ---------- */
  $("download-pdf").addEventListener("click", function () {
    updatePreview();
    window.print();
  });

  /* ---------- Download Word (.doc) ---------- */
  // Generates a browser-compatible HTML document with .doc extension,
  // which Microsoft Word opens correctly.
  $("download-doc").addEventListener("click", function () {
    var d = collect();
    var html =
      "<html xmlns:o='urn:schemas-microsoft-com:office:office' " +
      "xmlns:w='urn:schemas-microsoft-com:office:word'>" +
      "<head><meta charset='utf-8'>" +
      "<!--[if gte mso 9]><xml><w:WordDocument><w:View>Print</w:View></w:WordDocument></xml><![endif]-->" +
      "<title>Resume - " + esc(d.name || "resume") + "</title></head>" +
      "<body>" +
      "<h1 style='color:#6d28d9;margin-bottom:2px'>" + esc(d.name || "Your Name") + "</h1>" +
      "<p style='color:#444;margin-top:0'><strong>" + esc(d.headline) + "</strong></p>" +
      "<p style='color:#666'>" + esc(d.email) + " · " + esc(d.phone) + " · " + esc(d.location) + "</p>" +
      "<h2 style='color:#6d28d9;border-bottom:2px solid #6d28d9'>Education</h2>" +
      educationText(d) +
      "<h2 style='color:#6d28d9;border-bottom:2px solid #6d28d9'>Skills</h2>" +
      "<p>" + d.skills.map(esc).join(" · ") + "</p>" +
      "<h2 style='color:#6d28d9;border-bottom:2px solid #6d28d9'>Projects</h2>" +
      listText(d.projects) +
      "<h2 style='color:#6d28d9;border-bottom:2px solid #6d28d9'>Internships &amp; Experience</h2>" +
      listText(d.internships) +
      "<h2 style='color:#6d28d9;border-bottom:2px solid #6d28d9'>Certificates &amp; Achievements</h2>" +
      listText(d.certificates) +
      "<p><strong>Languages:</strong> " + esc(d.languages) + " &nbsp; <strong>Hobbies:</strong> " + esc(d.hobbies) + "</p>" +
      "<hr><p style='color:#999;font-size:11px'>Created with WorkWise AI — sample resume for demonstration.</p>" +
      "</body></html>";

    var blob = new Blob(["\ufeff" + html], { type: "application/msword" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = (d.name || "resume").replace(/\s+/g, "_") + "_resume.doc";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  });

  function educationText(d) {
    var parts = [];
    if (d.education.tenth.school) parts.push("<p><strong>10th:</strong> " + esc(d.education.tenth.school) + " — " + esc(d.education.tenth.pct) + " (" + esc(d.education.tenth.year) + ")</p>");
    if (d.education.twelfth.school) parts.push("<p><strong>12th:</strong> " + esc(d.education.twelfth.school) + " — " + esc(d.education.twelfth.pct) + " (" + esc(d.education.twelfth.year) + ")</p>");
    if (d.education.degree.name) parts.push("<p><strong>" + esc(d.education.degree.name) + ":</strong> CGPA " + esc(d.education.degree.cgpa) + " (" + esc(d.education.degree.year) + ")</p>");
    return parts.join("") || "<p>—</p>";
  }

  function listText(items) {
    if (!items.length) return "<p>—</p>";
    return "<ul>" + items.map(function (i) { return "<li>" + esc(i) + "</li>"; }).join("") + "</ul>";
  }
})();
