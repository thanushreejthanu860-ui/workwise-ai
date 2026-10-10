/* WorkWise AI — chatbot.js
   Floating offline rule-based assistant with quick buttons. */

(function () {
  "use strict";

  var bubble = document.getElementById("chat-bubble");
  var window_ = document.getElementById("chat-window");
  var closeBtn = document.getElementById("chat-close");
  var messages = document.getElementById("chat-messages");
  var form = document.getElementById("chat-form");
  var input = document.getElementById("chat-input");
  var quickBar = document.getElementById("chat-quick");

  if (!bubble) return;

  var GREETING = "Hi! I'm WorkWise AI. I can help you explore jobs, improve your resume, check fair wages, build career roadmaps, and prepare for interviews.";

  /* ---------- Open / close ---------- */
  function openChat() {
    window_.hidden = false;
    bubble.setAttribute("aria-expanded", "true");
    if (!messages.children.length) {
      addBotMessage(GREETING);
      addBotMessage("Try a quick action below, or ask me things like: " +
        "\"What is the wage of an electrician in a metro city?\" or " +
        "\"Give me a Data Analyst roadmap\".");
    }
    input.focus();
  }
  function closeChat() {
    window_.hidden = true;
    bubble.setAttribute("aria-expanded", "false");
  }

  bubble.addEventListener("click", function () {
    if (window_.hidden) openChat(); else closeChat();
  });
  closeBtn.addEventListener("click", closeChat);
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && !window_.hidden) closeChat();
  });

  /* ---------- Message rendering ---------- */
  function addBotMessage(text) {
    var msg = document.createElement("div");
    msg.className = "chat-msg bot";
    msg.textContent = text;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
    return msg;
  }

  function addUserMessage(text) {
    var msg = document.createElement("div");
    msg.className = "chat-msg user";
    msg.textContent = text;
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
  }

  function showTyping() {
    var msg = document.createElement("div");
    msg.className = "chat-msg bot typing";
    msg.textContent = "WorkWise AI is typing";
    messages.appendChild(msg);
    messages.scrollTop = messages.scrollHeight;
    return msg;
  }

  /* ---------- Send message ---------- */
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    input.value = "";
    addUserMessage(text);
    var typing = showTyping();

    fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        typing.remove();
        var msg = addBotMessage(data.reply || "Sorry, I did not understand that.");
        // If the intent is a roadmap request, render the roadmap SVG inline
        if (data.intent === "roadmap" && window.WW_SHOW_ROADMAP_IN_CHAT) {
          var roleMatch = text.match(/(?:roadmap for|roadmap of|roadmap to become|become)\s+([a-z ]+)/i);
          var role = roleMatch ? roleMatch[1].trim() : "Data Analyst";
          window.WW_SHOW_ROADMAP_IN_CHAT(role, messages);
        }
      })
      .catch(function () {
        typing.remove();
        addBotMessage("Network error — please check that the server is running.");
      });
  });

  /* ---------- Quick buttons ---------- */
  quickBar.addEventListener("click", function (e) {
    var btn = e.target.closest("button[data-quick]");
    if (!btn) return;
    var action = btn.dataset.quick;

    switch (action) {
      case "Explore Jobs":
        closeChat();
        window.location.href = "/jobs";
        break;
      case "Build My Resume":
        closeChat();
        window.location.href = "/resume";
        break;
      case "Check Fair Wage":
        closeChat();
        window.location.href = "/fair-wage";
        break;
      case "Ask a Question":
        openChat();
        input.focus();
        break;
      case "Roadmap Image":
        if (window_.hidden) openChat();
        if (window.WW_SHOW_ROADMAP_IN_CHAT) {
          window.WW_SHOW_ROADMAP_IN_CHAT("Data Analyst", messages);
        }
        break;
    }
  });
})();
