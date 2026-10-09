/* WorkWise AI — interview.js
   Role-based interview prep (rounds, questions, why, sample answers)
   and the practice box with offline answer evaluation. */

(function () {
  "use strict";

  if (!document.getElementById("prep-content")) return; // not on interview page

  var ROLES = ["Data Analyst", "Data Scientist", "Software Developer",
    "Web Developer", "Digital Marketing", "HR", "Sales", "Business Analyst"];

  // Map display names to API role keys
  var ROLE_KEYS = {
    "Digital Marketing": "Digital Marketing Specialist",
    "HR": "HR Specialist",
    "Sales": "Sales Executive",
  };

  var prepContent = document.getElementById("prep-content");
  var practiceRole = document.getElementById("practice-role");

  // Populate practice role dropdown
  practiceRole.innerHTML = ROLES.map(function (r) {
    return "<option>" + r + "</option>";
  }).join("");

  /* ---------- Load prep data for a role ---------- */
  document.getElementById("role-chips").addEventListener("click", function (e) {
    var btn = e.target.closest(".chip-btn");
    if (!btn) return;
    document.querySelectorAll(".chip-btn").forEach(function (c) { c.classList.remove("active"); });
    btn.classList.add("active");
    loadPrep(btn.dataset.role);
  });

  function loadPrep(displayRole) {
    var key = ROLE_KEYS[displayRole] || displayRole;
    prepContent.innerHTML = "<p class='muted'>Loading questions…</p>";
    fetch("/api/interview/questions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role: key }),
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
      .then(function (res) {
        if (!res.ok) {
          prepContent.innerHTML = "<p class='muted'>" + window.WW_ESCAPE(res.data.error || "Not available.") + "</p>";
          return;
        }
        renderPrep(res.data);
      })
      .catch(function () { prepContent.innerHTML = "<p class='muted'>Network error.</p>"; });
  }

  function renderPrep(data) {
    var html = "<h3>Interview rounds</h3><div class='round-card'>" +
      data.rounds.map(function (r) { return "① " + window.WW_ESCAPE(r); }).join(" &nbsp;→&nbsp; ") +
      "</div><h3>Sample questions</h3>";

    data.questions.forEach(function (q, i) {
      html += "<div class='question-card'>" +
        "<h4>Q" + (i + 1) + ". " + window.WW_ESCAPE(q.question) + "</h4>" +
        "<p class='q-why'>" + window.WW_ESCAPE(q.why) + "</p>" +
        "<div class='q-answer'>" + window.WW_ESCAPE(q.sample_answer) + "</div>" +
        "<button class='btn btn-ghost btn-sm q-ask' data-q='" + i + "'>Practise this question</button>" +
        "</div>";
    });

    // YouTube search links for learning videos
    html += "<h3>Learn more (YouTube)</h3><p>";
    html += data.rounds.map(function (r) {
      var query = encodeURIComponent(data.role + " " + r + " interview");
      return "<a href='https://www.youtube.com/results?search_query=" + query +
        "' target='_blank' rel='noopener'>🎬 " + window.WW_ESCAPE(r) + "</a>";
    }).join(" · ");
    html += "</p>";

    prepContent.innerHTML = html;

    // Wire "practise this question" buttons
    prepContent.querySelectorAll(".q-ask").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var q = data.questions[parseInt(btn.dataset.q, 10)];
        document.getElementById("practice-question").value = q.question;
        document.getElementById("practice-role").value = displayRole;
        document.getElementById("practice-answer").focus();
        document.getElementById("practice-answer").scrollIntoView({ behavior: "smooth", block: "center" });
      });
    });
  }

  /* ---------- Practice box ---------- */
  document.getElementById("practice-submit").addEventListener("click", function () {
    var question = document.getElementById("practice-question").value.trim();
    var answer = document.getElementById("practice-answer").value.trim();
    var role = document.getElementById("practice-role").value;
    var errBox = document.getElementById("practice-error");
    var resultBox = document.getElementById("practice-result");

    errBox.hidden = true;
    resultBox.hidden = true;

    if (!question) { errBox.textContent = "Enter the question you practised."; errBox.hidden = false; return; }
    if (answer.length < 10) { errBox.textContent = "Write at least a short answer (10+ characters)."; errBox.hidden = false; return; }

    var key = ROLE_KEYS[role] || role;
    var payload = { role: key, question: question, answer: answer };

    // Save practice (authenticated); still evaluate for guests
    var call = function () {
      return fetch("/api/practice", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      }).then(function (r) {
        return r.json().then(function (d) {
          if (!r.ok) throw new Error(d.error || "Failed");
          return d.feedback;
        });
      });
    };

    call().catch(function () {
      // Guest fallback: evaluate locally with the same rule-based logic
      return localEvaluate(answer);
    }).then(function (feedback) {
      renderFeedback(feedback);
    }).catch(function (err) {
      errBox.textContent = err.message;
      errBox.hidden = false;
    });
  });

  function localEvaluate(answer) {
    var words = answer.split(/\s+/).length;
    var sentences = Math.max(1, (answer.match(/[.!?]/g) || []).length);
    var keywords = ["because", "for example", "project", "team", "learned", "result", "goal", "skill", "experience"];
    var lower = answer.toLowerCase();
    var hits = keywords.filter(function (k) { return lower.indexOf(k) >= 0; }).length;
    var missing = [];
    if (words < 30) missing.push("Add more detail - aim for 30+ words.");
    if (lower.indexOf("because") < 0) missing.push("Explain WHY with 'because'.");
    if (lower.indexOf("example") < 0) missing.push("Include a concrete example.");
    if (sentences < 2) missing.push("Break your answer into short paragraphs.");
    return {
      scores: {
        clarity: Math.min(100, 40 + words),
        structure: Math.min(100, 30 + sentences * 25),
        relevance: Math.min(100, 30 + hits * 15),
      },
      overall: Math.round((Math.min(100, 40 + words) + Math.min(100, 30 + sentences * 25) + Math.min(100, 30 + hits * 15)) / 3),
      missing_points: missing.length ? missing : ["No major gaps found - keep practising!"],
    };
  }

  function renderFeedback(fb) {
    var resultBox = document.getElementById("practice-result");
    document.getElementById("practice-score").textContent = fb.overall + "/100";
    document.getElementById("practice-bars").innerHTML =
      Object.keys(fb.scores).map(function (k) {
        return "<div class='score-bar-row'>" +
          "<span>" + k.charAt(0).toUpperCase() + k.slice(1) + "</span>" +
          "<div class='progress'><div class='progress-bar' style='width:" + fb.scores[k] + "%'></div></div>" +
          "<strong>" + fb.scores[k] + "</strong></div>";
      }).join("");
    document.getElementById("practice-missing").innerHTML =
      fb.missing_points.map(function (m) { return "<li>" + window.WW_ESCAPE(m) + "</li>"; }).join("");
    resultBox.hidden = false;
    resultBox.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  // Load the first role by default
  loadPrep("Data Analyst");
})();
