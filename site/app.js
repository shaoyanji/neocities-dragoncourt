// app.js — two jobs: keep the clock honest, and glitch the title on request.
// No libraries, no network, no storage.

(function () {
  "use strict";

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // clock ---------------------------------------------------------------
  var clock = document.getElementById("clock");
  if (clock) {
    var tick = function () {
      var now = new Date();
      var hh = String(now.getHours()).padStart(2, "0");
      var mm = String(now.getMinutes()).padStart(2, "0");
      var ss = String(now.getSeconds()).padStart(2, "0");
      clock.textContent = hh + ":" + mm + ":" + ss;
      clock.setAttribute("datetime", now.toISOString());
    };
    tick();
    window.setInterval(tick, 1000);
  }

  // typewriter ----------------------------------------------------------
  var ops = document.getElementById("ops");
  if (ops) {
    var full = ops.textContent;
    if (reduce) {
      ops.textContent = full;
    } else {
      ops.textContent = "";
      var i = 0;
      var type = function () {
        if (i <= full.length) {
          ops.textContent = full.slice(0, i);
          i += 1;
          window.setTimeout(type, 38);
        }
      };
      window.setTimeout(type, 550);
    }
  }

  // glitch --------------------------------------------------------------
  var title = document.getElementById("title");
  if (title && !reduce) {
    var burst = function () {
      title.classList.remove("glitching");
      // force a reflow so the animation restarts on a second click
      void title.offsetWidth;
      title.classList.add("glitching");
      window.setTimeout(function () {
        title.classList.remove("glitching");
      }, 480);
    };

    title.addEventListener("click", burst);
    title.addEventListener("keydown", function (event) {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        burst();
      }
    });
    title.setAttribute("tabindex", "0");
    title.setAttribute("role", "button");
    title.setAttribute("aria-label", "dragon court — glitch the title");
  }
})();
