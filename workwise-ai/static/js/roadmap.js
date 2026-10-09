/* WorkWise AI — roadmap.js
   Generates a 5-stage career roadmap as SVG (numbered stages,
   skills with done/todo ticks, JOB-READY finish line).
   Exports window.buildRoadmapSVG so the chatbot can reuse it. */

(function () {
  "use strict";

  var USER_SKILLS = [];   // filled from /api/profile (if logged in)
  var LAST_ROADMAP = null; // last generated roadmap data
  var SVG_NS = "http://www.w3.org/2000/svg";

  /* ---------- Public SVG builder (also used by chatbot.js) ---------- */
  window.buildRoadmapSVG = function (roadmap, userSkills) {
    userSkills = (userSkills || []).map(function (s) { return s.toLowerCase().trim(); });
    var stages = roadmap.stages;
    var W = 860;
    var stageH = 108;
    var gap = 18;
    var topPad = 64;
    var H = topPad + stages.length * (stageH + gap) + 96;

    var svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 " + W + " " + H);
    svg.setAttribute("xmlns", SVG_NS);
    svg.setAttribute("role", "img");
    svg.setAttribute("aria-label", "Career roadmap for " + roadmap.role);

    var el = function (tag, attrs, parent) {
      var n = document.createElementNS(SVG_NS, tag);
      Object.keys(attrs || {}).forEach(function (k) { n.setAttribute(k, attrs[k]); });
      (parent || svg).appendChild(n);
      return n;
    };
    var text = function (x, y, str, attrs, parent) {
      var t = el("text", attrs, parent);
      t.setAttribute("x", x);
      t.setAttribute("y", y);
      t.textContent = str;
      return t;
    };

    /* --- defs: gradients --- */
    var defs = el("defs");
    var grad = el("linearGradient", { id: "rwg1", x1: "0", y1: "0", x2: "1", y2: "1" }, defs);
    el("stop", { offset: "0", "stop-color": "#6d28d9" }, grad);
    el("stop", { offset: "1", "stop-color": "#0ea5e9" }, grad);
    var grad2 = el("linearGradient", { id: "rwg2", x1: "0", y1: "0", x2: "1", y2: "0" }, defs);
    el("stop", { offset: "0", "stop-color": "#16a34a" }, grad2);
    el("stop", { offset: "1", "stop-color": "#4ade80" }, grad2);

    /* --- header --- */
    el("rect", { x: 0, y: 0, width: W, height: 52, fill: "url(#rwg1)", rx: 14 }, svg);
    text(W / 2, 34, "Career Roadmap: " + roadmap.role, {
      "font-size": "20", "font-weight": "bold", fill: "#fff",
      "text-anchor": "middle", "font-family": "Segoe UI, sans-serif",
    });
    text(16, 34, "≈ " + (roadmap.total_duration || "5 months"), {
      "font-size": "13", fill: "rgba(255,255,255,.85)", "font-family": "Segoe UI, sans-serif",
    });

    /* --- stages --- */
    stages.forEach(function (stage, i) {
      var y = topPad + i * (stageH + gap);
      var hasConnector = i < stages.length - 1;

      /* connector line */
      if (hasConnector) {
        el("line", {
          x1: 62, y1: y + stageH, x2: 62, y2: y + stageH + gap,
          stroke: "#0ea5e9", "stroke-width": 3, "stroke-dasharray": "5 4",
        });
        el("polygon", {
          points: "57," + (y + stageH + gap - 2) + " 67," + (y + stageH + gap - 2) + " 62," + (y + stageH + gap + 6),
          fill: "#0ea5e9",
        });
      }

      /* card */
      el("rect", {
        x: 24, y: y, width: W - 48, height: stageH, rx: 14,
        fill: "var(--surface, #fff)", stroke: "#dfe4ef", "stroke-width": 1.5,
        class: "rw-card",
      });

      /* stage number circle */
      el("circle", { cx: 62, cy: y + stageH / 2, r: 24, fill: "url(#rwg1)" });
      text(62, y + stageH / 2 + 8, String(stage.number || i + 1), {
        "font-size": "20", "font-weight": "bold", fill: "#fff", "text-anchor": "middle",
        "font-family": "Segoe UI, sans-serif",
      });

      /* title + duration */
      text(102, y + 34, stage.title, {
        "font-size": "17", "font-weight": "bold", fill: "#1e2433", "font-family": "Segoe UI, sans-serif",
        class: "rw-title",
      });
      text(102, y + 56, "⏱ " + stage.duration, {
        "font-size": "12.5", fill: "#5b6478", "font-family": "Segoe UI, sans-serif",
        class: "rw-sub",
      });

      /* skill chips with ticks */
      var chipX = 102;
      var chipY = y + 70;
      stage.skills.forEach(function (skill) {
        var has = userSkills.indexOf(skill.toLowerCase().trim()) >= 0;
        var label = skill;
        var width = Math.max(46, label.length * 7.6 + 34);
        if (chipX + width > W - 40) { chipX = 102; chipY += 28; }
        el("rect", {
          x: chipX, y: chipY, width: width, height: 22, rx: 11,
          fill: has ? "#dcfce7" : "#f1f5f9",
          stroke: has ? "#16a34a" : "#6d28d9", "stroke-width": 1.2,
          class: "rw-chip",
        });
        text(chipX + 14, chipY + 15.5, has ? "✓ " : "+ ", {
          "font-size": "11", "font-weight": "bold",
          fill: has ? "#16a34a" : "#6d28d9", "font-family": "Segoe UI, sans-serif",
          class: "rw-chip-mark",
        });
        text(chipX + 28, chipY + 15.5, label, {
          "font-size": "11.5", fill: has ? "#166534" : "#334155", "font-family": "Segoe UI, sans-serif",
          class: "rw-chip-text",
        });
        chipX += width + 8;
      });
    });

    /* --- JOB-READY finish line --- */
    var fy = topPad + stages.length * (stageH + gap) + 8;
    el("line", { x1: 62, y1: fy - 34, x2: 62, y2: fy, stroke: "#0ea5e9", "stroke-width": 3, "stroke-dasharray": "5 4" });
    el("rect", { x: W / 2 - 120, y: fy, width: 240, height: 52, rx: 26, fill: "url(#rwg2)" });
    text(W / 2, fy + 34, "🏁 JOB-READY", {
      "font-size": "22", "font-weight": "bold", fill: "#fff",
      "text-anchor": "middle", "font-family": "Segoe UI, sans-serif",
    });

    return svg;
  };

  /* ---------- Chatbot integration: generate + show roadmap in chat ----------
     Defined BEFORE the page-specific early return so it works on
     every page (the chatbot lives on all pages via base.html). */
  window.WW_SHOW_ROADMAP_IN_CHAT = function (role, chatContainer) {
    fetch("/api/roadmap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: role || "Data Analyst" }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        LAST_ROADMAP = data;
        var msg = document.createElement("div");
        msg.className = "chat-msg bot";
        var svg = window.buildRoadmapSVG(data, USER_SKILLS);
        svg.style.maxWidth = "100%";
        svg.style.height = "auto";
        msg.appendChild(document.createTextNode("Here is your " + data.role + " roadmap:"));
        msg.appendChild(svg);
        var link = document.createElement("span");
        link.className = "roadmap-link";
        link.innerHTML = "<a href='/roadmaps' target='_blank'>Open full roadmap →</a>";
        msg.appendChild(link);
        chatContainer.appendChild(msg);
        chatContainer.scrollTop = chatContainer.scrollHeight;
      })
      .catch(function () {});
  };

  /* ---------- Page logic ---------- */
  var form = document.getElementById("roadmap-form");
  if (!form) return; // not on the roadmaps page

  var stage = document.getElementById("roadmap-stage");
  var toolbar = document.getElementById("roadmap-toolbar");
  var legend = document.getElementById("roadmap-legend");
  var meta = document.getElementById("roadmap-meta");

  // Load user skills (if logged in) to tick chips
  fetch("/api/profile")
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (p) {
      if (p && p.skills) USER_SKILLS = p.skills.map(function (s) { return s.name; });
    })
    .catch(function () {});

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var role = document.getElementById("role-custom").value.trim() ||
      document.getElementById("role-select").value;

    fetch("/api/roadmap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: role }),
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
      .then(function (res) {
        if (!res.ok) { alert(res.data.error || "Could not generate roadmap."); return; }
        LAST_ROADMAP = res.data;
        stage.innerHTML = "";
        stage.appendChild(window.buildRoadmapSVG(res.data, USER_SKILLS));
        toolbar.hidden = false;
        legend.hidden = false;
        meta.textContent = "Role: " + res.data.role + " · " + res.data.stages.length +
          " stages · " + res.data.total_duration +
          (res.data.source === "generic" ? " · custom path" : "");
      })
      .catch(function () { alert("Network error."); });
  });

  /* ---------- Download SVG ---------- */
  document.getElementById("download-roadmap-svg").addEventListener("click", function () {
    if (!LAST_ROADMAP) return;
    var svg = window.buildRoadmapSVG(LAST_ROADMAP, USER_SKILLS);
    // Inline the theme colours for a standalone file
    var clone = svg.cloneNode(true);
    clone.querySelectorAll(".rw-card").forEach(function (c) { c.setAttribute("fill", "#ffffff"); });
    clone.querySelectorAll(".rw-title").forEach(function (t) { t.setAttribute("fill", "#1e2433"); });
    clone.querySelectorAll(".rw-sub").forEach(function (t) { t.setAttribute("fill", "#5b6478"); });
    clone.querySelectorAll(".rw-chip-text").forEach(function (t) { t.setAttribute("fill", "#334155"); });
    var serializer = new XMLSerializer();
    var source = serializer.serializeToString(clone);
    var blob = new Blob(["<?xml version='1.0' encoding='UTF-8'?>\n" + source], { type: "image/svg+xml" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = LAST_ROADMAP.role.replace(/\s+/g, "_") + "_roadmap.svg";
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(url); }, 1000);
  });

  /* ---------- Download PNG (rendered from the SVG) ---------- */
  document.getElementById("download-roadmap-png").addEventListener("click", function () {
    if (!LAST_ROADMAP) return;
    var svg = window.buildRoadmapSVG(LAST_ROADMAP, USER_SKILLS);
    var clone = svg.cloneNode(true);
    clone.querySelectorAll(".rw-card").forEach(function (c) { c.setAttribute("fill", "#ffffff"); });
    clone.querySelectorAll(".rw-title").forEach(function (t) { t.setAttribute("fill", "#1e2433"); });
    clone.querySelectorAll(".rw-sub").forEach(function (t) { t.setAttribute("fill", "#5b6478"); });
    clone.querySelectorAll(".rw-chip-text").forEach(function (t) { t.setAttribute("fill", "#334155"); });

    var serializer = new XMLSerializer();
    var source = serializer.serializeToString(clone);
    var svgBlob = new Blob([source], { type: "image/svg+xml;charset=utf-8" });
    var url = URL.createObjectURL(svgBlob);

    var img = new Image();
    img.onload = function () {
      var scale = 2; // retina-quality PNG
      var canvas = document.createElement("canvas");
      canvas.width = img.width * scale;
      canvas.height = img.height * scale;
      var ctx = canvas.getContext("2d");
      ctx.fillStyle = "#ffffff";
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);

      canvas.toBlob(function (pngBlob) {
        var pngUrl = URL.createObjectURL(pngBlob);
        var a = document.createElement("a");
        a.href = pngUrl;
        a.download = LAST_ROADMAP.role.replace(/\s+/g, "_") + "_roadmap.png";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(pngUrl); }, 1000);
      }, "image/png");
    };
    img.onerror = function () {
      URL.revokeObjectURL(url);
      alert("PNG export failed in this browser. Try downloading the SVG instead.");
    };
    img.src = url;
  });
})();
