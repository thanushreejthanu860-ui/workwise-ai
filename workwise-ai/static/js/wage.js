/* WorkWise AI — wage.js
   Fair wage form -> POST /api/predict-wage, plus a reference wage table
   generated from the trained model. */

(function () {
  "use strict";

  if (!document.getElementById("wage-form")) return; // not on the wage page

  var form = document.getElementById("wage-form");
  var result = document.getElementById("wage-result");
  var errorBox = document.getElementById("wage-error");

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    errorBox.hidden = true;

    var payload = {
      trade: document.getElementById("w-trade").value,
      city_type: document.getElementById("w-city").value,
      experience: parseInt(document.getElementById("w-exp").value, 10) || 0,
    };

    if (!payload.trade || !payload.city_type) {
      errorBox.textContent = "Please select both a trade and a city type.";
      errorBox.hidden = false;
      return;
    }

    fetch("/api/predict-wage", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    })
      .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, data: d }; }); })
      .then(function (res) {
        if (!res.ok) {
          errorBox.textContent = res.data.error || "Prediction failed.";
          errorBox.hidden = false;
          return;
        }
        var d = res.data;
        document.getElementById("wage-num").textContent = "₹" + Number(d.predicted_daily_wage).toLocaleString("en-IN");
        document.getElementById("wage-low").textContent = Number(d.lower_range).toLocaleString("en-IN");
        document.getElementById("wage-high").textContent = Number(d.upper_range).toLocaleString("en-IN");

        var verdict = document.getElementById("wage-verdict");
        verdict.textContent = d.verdict;
        verdict.className = "pill " + (d.verdict === "Fair / typical" ? "fair" : d.verdict === "Under typical range" ? "under" : "above");

        document.getElementById("wage-explanation").textContent =
          "A " + payload.trade + " with " + payload.experience + " years of experience in a " +
          payload.city_type + " area typically earns between ₹" +
          Number(d.lower_range).toLocaleString("en-IN") + " and ₹" +
          Number(d.upper_range).toLocaleString("en-IN") +
          " per day. Your estimate of ₹" + Number(d.predicted_daily_wage).toLocaleString("en-IN") +
          " is " + d.verdict.toLowerCase() + ". " + d.disclaimer;

        result.hidden = false;
        result.scrollIntoView({ behavior: "smooth", block: "center" });
      })
      .catch(function () {
        errorBox.textContent = "Network error. Is the server running?";
        errorBox.hidden = false;
      });
  });

  /* ---------- Reference table: model-based estimates ---------- */
  function buildReferenceTable() {
    var trades = ["Mason", "Painter", "Electrician", "Domestic Worker", "Driver", "Delivery Partner"];
    var cities = ["Metro", "Tier-2", "Rural"];
    var tbody = document.querySelector("#wage-table tbody");
    var cells = "";

    // Query the model for each trade/city at 5 years experience
    var pending = trades.length * cities.length;
    var results = {};

    trades.forEach(function (trade) {
      cities.forEach(function (city) {
        fetch("/api/predict-wage", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ trade: trade, city_type: city, experience: 5 }),
        })
          .then(function (r) { return r.json(); })
          .then(function (d) {
            results[trade + "|" + city] = d.predicted_daily_wage;
            if (--pending === 0) renderTable();
          })
          .catch(function () {
            results[trade + "|" + city] = null;
            if (--pending === 0) renderTable();
          });
      });
    });

    function renderTable() {
      cells = trades.map(function (trade) {
        var tds = cities.map(function (city) {
          var v = results[trade + "|" + city];
          return "<td>" + (v ? "₹" + Number(v).toLocaleString("en-IN") : "—") + "</td>";
        }).join("");
        return "<tr><th>" + trade + "</th>" + tds + "</tr>";
      }).join("");
      tbody.innerHTML = cells;
    }
  }

  buildReferenceTable();
})();
