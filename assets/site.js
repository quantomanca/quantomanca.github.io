/* Quanto Manca — conto alla rovescia, scene animate e piccole interazioni del sito. */
(function () {
  "use strict";
  document.documentElement.classList.remove("no-js");
  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var DAY = 86400000;
  var WEEKDAYS = ["domenica", "lunedì", "martedì", "mercoledì", "giovedì", "venerdì", "sabato"];
  var MONTHS = ["gennaio", "febbraio", "marzo", "aprile", "maggio", "giugno", "luglio", "agosto", "settembre", "ottobre", "novembre", "dicembre"];

  // ---------- Date delle feste (stesse regole dell'app) ----------

  function easter(y) {
    var a = y % 19, b = Math.floor(y / 100), c = y % 100, d = Math.floor(b / 4), e = b % 4;
    var f = Math.floor((b + 8) / 25), g = Math.floor((b - f + 1) / 3);
    var h = (19 * a + b - d - g + 15) % 30, i = Math.floor(c / 4), k = c % 4;
    var l = (32 + 2 * e + 2 * i - h - k) % 7, m = Math.floor((a + 11 * h + 22 * l) / 451);
    var month = Math.floor((h + l - 7 * m + 114) / 31), day = ((h + l - 7 * m + 114) % 31) + 1;
    return new Date(y, month - 1, day);
  }

  // "fixed:12:25", "easter:-47", "nth:5:6:2" (mese, giorno con 0 = lunedì, ordinale)
  function occurrence(rule, year) {
    var p = rule.split(":");
    if (p[0] === "fixed") return new Date(year, +p[1] - 1, +p[2]);
    if (p[0] === "easter") { var e = easter(year); return new Date(year, e.getMonth(), e.getDate() + +p[1]); }
    if (p[0] === "nth") {
      var first = new Date(year, +p[1] - 1, 1);
      var jsWeekday = (+p[2] + 1) % 7;
      var offset = (jsWeekday - first.getDay() + 7) % 7;
      return new Date(year, +p[1] - 1, 1 + offset + 7 * (+p[3] - 1));
    }
    return null;
  }

  function nextOccurrence(rule, now) {
    var y = now.getFullYear();
    for (var i = -1; i < 2; i++) {
      var d = occurrence(rule, y + i);
      var end = new Date(d.getFullYear(), d.getMonth(), d.getDate() + 1);
      if (now < end) return d;
    }
    return occurrence(rule, y + 2);
  }

  function startOfDay(d) { return new Date(d.getFullYear(), d.getMonth(), d.getDate()); }
  function calendarDays(target, now) { return Math.round((startOfDay(target) - startOfDay(now)) / DAY); }
  function longDate(d) { return WEEKDAYS[d.getDay()] + " " + d.getDate() + " " + MONTHS[d.getMonth()] + " " + d.getFullYear(); }
  function shortDate(d) { return WEEKDAYS[d.getDay()].slice(0, 3) + " " + d.getDate() + " " + MONTHS[d.getMonth()].slice(0, 3); }
  function pad(n) { return n < 10 ? "0" + n : "" + n; }

  function each(sel, fn, root) { Array.prototype.forEach.call((root || document).querySelectorAll(sel), fn); }
  function setText(el, value) { if (el && el.textContent !== value) el.textContent = value; }

  function updateCountdown(el, now) {
    var rule = el.getAttribute("data-countdown");
    var target = nextOccurrence(rule, now);
    var today = now >= target;
    el.classList.toggle("is-today", today);
    var ms = Math.max(0, target - now);
    var parts = { d: Math.floor(ms / DAY), h: Math.floor(ms / 3600000) % 24, m: Math.floor(ms / 60000) % 60, s: Math.floor(ms / 1000) % 60 };
    each("[data-u]", function (u) {
      var k = u.getAttribute("data-u");
      setText(u, k === "d" ? String(parts.d) : pad(parts[k]));
    }, el);
    each("[data-days-left]", function (u) { setText(u, today ? "0" : String(calendarDays(target, now))); }, el);
    each("[data-next-year]", function (u) { setText(u, String(target.getFullYear())); }, el);
    each("[data-next-long]", function (u) { setText(u, longDate(target)); }, el);
    var prev = occurrence(rule, target.getFullYear() - 1);
    var progress = today ? 1 : Math.min(1, Math.max(0, (now - prev) / (target - prev)));
    each("[data-progress]", function (u) { u.style.width = (progress * 100).toFixed(1) + "%"; }, el);
  }

  function updateDays(now) {
    each("[data-days-to]", function (el) {
      var target = nextOccurrence(el.getAttribute("data-days-to"), now);
      var n = calendarDays(target, now);
      var num = el.querySelector("[data-n]"), lbl = el.querySelector("[data-l]");
      setText(num, n === 0 ? "Oggi" : String(n));
      setText(lbl, n === 0 ? "" : n === 1 ? "giorno" : "giorni");
    });
    each("[data-date-of]", function (el) { setText(el, shortDate(nextOccurrence(el.getAttribute("data-date-of"), now))); });
  }

  // Le feste della home in ordine di arrivo, con la prima in evidenza.
  function sortHolidays(now) {
    each("[data-sort]", function (grid) {
      var cards = Array.prototype.slice.call(grid.querySelectorAll("[data-rule]"));
      cards.sort(function (a, b) {
        return nextOccurrence(a.getAttribute("data-rule"), now) - nextOccurrence(b.getAttribute("data-rule"), now);
      });
      cards.forEach(function (card, i) {
        card.classList.toggle("is-next", i === 0);
        var badge = card.querySelector(".hc-badge");
        if (badge) badge.hidden = i !== 0;
        grid.insertBefore(card, grid.querySelector(".custom"));
      });
    });
  }

  function tick() {
    var now = new Date();
    each("[data-countdown]", function (el) { updateCountdown(el, now); });
    updateDays(now);
  }

  // ---------- Frase del giorno e calendario dell'Avvento ----------

  function dayNumber(now) { return Math.floor(Date.UTC(now.getFullYear(), now.getMonth(), now.getDate()) / DAY); }

  function setupQuote(now) {
    var data = document.getElementById("qm-quotes");
    if (!data) return;
    var quotes = JSON.parse(data.textContent);
    var q = quotes[((dayNumber(now) * 7) % quotes.length + quotes.length) % quotes.length];
    each("[data-quote]", function (el) {
      setText(el.querySelector("[data-q-text]"), q.text.replace(/ \/ /g, "\n"));
      setText(el.querySelector("[data-q-author]"), q.author);
      setText(el.querySelector("[data-q-source]"), q.source);
    });
  }

  function setupAdvent(now) {
    each("[data-advent]", function (grid) {
      if (now.getMonth() !== 11 || now.getDate() > 24) return;
      var today = now.getDate();
      each(".door", function (door) {
        var n = +door.getAttribute("data-n");
        door.classList.toggle("open", n < today);
        door.classList.toggle("today", n === today);
        door.classList.remove("gold");
        door.textContent = n < today ? door.getAttribute("data-ornament") : String(n);
      }, grid);
    });
  }

  // ---------- Scene animate ----------

  function hash(i, salt) {
    var x = Math.sin(i * 127.1 + salt * 311.7) * 43758.5453;
    return x - Math.floor(x);
  }
  function wrap(v, m) { return ((v % m) + m) % m; }
  function rgba(hex, a) {
    var n = parseInt(hex.slice(1), 16);
    return "rgba(" + (n >> 16) + "," + ((n >> 8) & 255) + "," + (n & 255) + "," + a + ")";
  }

  function glow(ctx, x, y, r, color, a) {
    var g = ctx.createRadialGradient(x, y, 0, x, y, r);
    g.addColorStop(0, rgba(color, a));
    g.addColorStop(1, rgba(color, 0));
    ctx.fillStyle = g;
    ctx.fillRect(x - r, y - r, r * 2, r * 2);
  }

  function stars(ctx, w, h, t, count, top) {
    for (var i = 0; i < count; i++) {
      var x = hash(i, 1) * w, y = hash(i, 2) * h * (top || 0.6);
      var a = 0.35 + 0.65 * Math.abs(Math.sin(t * (0.6 + hash(i, 3) * 1.6) + i));
      ctx.fillStyle = "rgba(255,250,242," + (a * (0.4 + hash(i, 4) * 0.6)).toFixed(3) + ")";
      var r = 0.5 + hash(i, 5) * 1.3;
      ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
    }
  }

  function moon(ctx, x, y, r, color) {
    glow(ctx, x, y, r * 4, color || "#FFF6DC", 0.22);
    ctx.fillStyle = color || "#FFF6DC";
    ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
    ctx.fillStyle = "rgba(0,0,0,0.06)";
    ctx.beginPath(); ctx.arc(x - r * 0.3, y - r * 0.2, r * 0.22, 0, 6.283); ctx.arc(x + r * 0.25, y + r * 0.3, r * 0.15, 0, 6.283); ctx.fill();
  }

  function snowfall(ctx, w, h, t, count, speed) {
    for (var i = 0; i < count; i++) {
      var r = 0.8 + hash(i, 7) * 2.6;
      var v = (14 + r * 9) * (speed || 1);
      var y = wrap(hash(i, 8) * h * 1.2 + t * v, h * 1.2) - h * 0.1;
      var x = wrap(hash(i, 9) * w + Math.sin(t * 0.6 + i) * 14 + t * 6, w + 20) - 10;
      ctx.fillStyle = "rgba(255,250,242," + (0.35 + r / 5).toFixed(2) + ")";
      ctx.beginPath(); ctx.arc(x, y, r, 0, 6.283); ctx.fill();
    }
  }

  function hills(ctx, w, h, base, amp, color, seed) {
    ctx.fillStyle = color;
    ctx.beginPath(); ctx.moveTo(0, h);
    for (var x = 0; x <= w + 10; x += 10) {
      var y = base + Math.sin(x / w * 3.1 + seed) * amp + Math.sin(x / w * 7.3 + seed * 2) * amp * 0.35;
      ctx.lineTo(x, y);
    }
    ctx.lineTo(w, h); ctx.closePath(); ctx.fill();
  }

  function pine(ctx, x, y, s, color) {
    ctx.fillStyle = color;
    for (var k = 0; k < 3; k++) {
      var top = y - s * (1 - k * 0.28), wdt = s * (0.32 + k * 0.1);
      ctx.beginPath(); ctx.moveTo(x, top - s * 0.12); ctx.lineTo(x - wdt, top + s * 0.42); ctx.lineTo(x + wdt, top + s * 0.42); ctx.fill();
    }
    ctx.fillRect(x - s * 0.05, y, s * 0.1, s * 0.12);
  }

  function heart(ctx, x, y, s) {
    ctx.beginPath();
    ctx.moveTo(x, y + s * 0.35);
    ctx.bezierCurveTo(x - s * 0.9, y - s * 0.25, x - s * 0.45, y - s * 0.95, x, y - s * 0.45);
    ctx.bezierCurveTo(x + s * 0.45, y - s * 0.95, x + s * 0.9, y - s * 0.25, x, y + s * 0.35);
    ctx.fill();
  }

  var palette = ["#F2C261", "#FF5C7A", "#BFE0FF", "#FF9EDB", "#8CF2B4", "#FFFAF2"];

  var scenes = {
    snow: function (ctx, w, h, t) {
      stars(ctx, w, h, t, Math.round(w * h / 5000));
      moon(ctx, w * 0.76, h * 0.17, Math.min(w, h) * 0.07);
      hills(ctx, w, h, h * 0.74, h * 0.04, "#13265a", 1);
      for (var i = 0; i < 9; i++) pine(ctx, w * (i / 8) + hash(i, 3) * 20, h * 0.76 + hash(i, 4) * 10, h * (0.07 + hash(i, 5) * 0.05), "#0b1a3d");
      hills(ctx, w, h, h * 0.86, h * 0.03, "#d8e6ff", 4);
      ctx.fillStyle = "rgba(255,190,90,0.9)";
      var hx = w * 0.22, hy = h * 0.84;
      ctx.fillStyle = "#0b1a3d"; ctx.fillRect(hx - 22, hy - 26, 44, 28);
      ctx.beginPath(); ctx.moveTo(hx - 28, hy - 24); ctx.lineTo(hx, hy - 46); ctx.lineTo(hx + 28, hy - 24); ctx.fill();
      var flick = 0.8 + 0.2 * Math.sin(t * 9) * Math.sin(t * 3.7);
      ctx.fillStyle = "rgba(255,190,90," + flick.toFixed(2) + ")"; ctx.fillRect(hx - 12, hy - 18, 9, 9); ctx.fillRect(hx + 4, hy - 18, 9, 9);
      glow(ctx, hx, hy - 14, 40, "#FFB85A", 0.25 * flick);
      snowfall(ctx, w, h, t, Math.round(w * h / 2600));
    },

    fireworks: function (ctx, w, h, t) {
      stars(ctx, w, h, t, Math.round(w * h / 7000), 0.5);
      for (var b = 0; b < 4; b++) {
        var period = 3.4 + b * 0.7, phase = wrap(t + b * 1.3, period) / period, cycle = Math.floor((t + b * 1.3) / period);
        var bx = w * (0.18 + hash(b + cycle * 7, 11) * 0.64), by = h * (0.16 + hash(b + cycle * 7, 12) * 0.3);
        var color = palette[Math.floor(hash(b + cycle * 7, 13) * palette.length)];
        if (phase < 0.22) {
          var p = phase / 0.22, ry = h * 0.8 - (h * 0.8 - by) * (1 - Math.pow(1 - p, 2));
          ctx.fillStyle = rgba(color, 0.9); ctx.beginPath(); ctx.arc(bx, ry, 2, 0, 6.283); ctx.fill();
        } else {
          var q = (phase - 0.22) / 0.78, radius = Math.min(w, h) * 0.24 * (1 - Math.pow(1 - q, 3)), alpha = Math.pow(1 - q, 1.4);
          if (q < 0.15) glow(ctx, bx, by, radius * 1.6 + 20, color, 0.35 * (1 - q / 0.15));
          for (var k = 0; k < 36; k++) {
            var ang = k / 36 * 6.283 + hash(k, b) * 0.1;
            var px = bx + Math.cos(ang) * radius, py = by + Math.sin(ang) * radius + q * q * h * 0.06;
            ctx.fillStyle = rgba(k % 3 === 0 ? "#FFFAF2" : color, alpha.toFixed(3));
            ctx.beginPath(); ctx.arc(px, py, 1.8 * (1 - q * 0.5), 0, 6.283); ctx.fill();
          }
        }
      }
      ctx.fillStyle = "#07071a";
      var x = 0, i = 0;
      while (x < w) {
        var bw = 18 + hash(i, 21) * 30, bh = h * (0.08 + hash(i, 22) * 0.16);
        ctx.fillRect(x, h - bh, bw - 2, bh);
        for (var wy = h - bh + 6; wy < h - 6; wy += 9) for (var wx = x + 4; wx < x + bw - 6; wx += 7) {
          if (hash(wx * 3 + wy, i) > 0.62) { ctx.fillStyle = "rgba(255,214,140,0.55)"; ctx.fillRect(wx, wy, 3, 4); ctx.fillStyle = "#07071a"; }
        }
        x += bw; i++;
      }
    },

    befana: function (ctx, w, h, t) {
      stars(ctx, w, h, t, Math.round(w * h / 4500));
      var mx = w * 0.62, my = h * 0.28, mr = Math.min(w, h) * 0.16;
      moon(ctx, mx, my, mr, "#FFEFC2");
      var p = wrap(t, 15) / 15, bx = w * 1.2 - p * w * 1.5, by = my + Math.sin(p * 6.283) * mr * 0.4;
      ctx.save(); ctx.translate(bx, by); ctx.rotate(-0.12); ctx.fillStyle = "#140a1f"; ctx.strokeStyle = "#140a1f";
      ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-34, 6); ctx.lineTo(30, -2); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(30, -2); ctx.lineTo(48, -10); ctx.lineTo(50, 8); ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.moveTo(-8, 4); ctx.lineTo(12, 4); ctx.lineTo(4, -20); ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.arc(2, -22, 6, 0, 6.283); ctx.fill();
      ctx.beginPath(); ctx.moveTo(-8, -24); ctx.lineTo(12, -24); ctx.lineTo(4, -42); ctx.closePath(); ctx.fill();
      ctx.beginPath(); ctx.moveTo(-6, 0); ctx.quadraticCurveTo(-26, -4 + Math.sin(t * 6) * 4, -30, 8); ctx.lineTo(-10, 6); ctx.fill();
      ctx.restore();
      ctx.fillStyle = "#0d0816";
      var x = 0, i = 0;
      while (x < w) {
        var rw = 50 + hash(i, 31) * 50, rh = h * (0.12 + hash(i, 32) * 0.08);
        ctx.beginPath(); ctx.moveTo(x, h); ctx.lineTo(x, h - rh); ctx.lineTo(x + rw / 2, h - rh - 22); ctx.lineTo(x + rw, h - rh); ctx.lineTo(x + rw, h); ctx.fill();
        ctx.fillRect(x + rw * 0.7, h - rh - 24, 9, 22);
        if (hash(i, 33) > 0.4) { ctx.fillStyle = "rgba(255,170,80,0.7)"; ctx.fillRect(x + rw * 0.3, h - rh * 0.6, 8, 10); ctx.fillStyle = "#0d0816"; }
        x += rw; i++;
      }
      snowfall(ctx, w, h, t, Math.round(w * h / 9000), 0.6);
    },

    hearts: function (ctx, w, h, t) {
      for (var i = 0; i < 18; i++) {
        var bx = hash(i, 41) * w, by = hash(i, 42) * h, br = 20 + hash(i, 43) * 60;
        glow(ctx, bx + Math.sin(t * 0.3 + i) * 20, by, br, i % 2 ? "#FFFFFF" : "#FFB3CC", 0.12 + 0.08 * Math.sin(t + i));
      }
      var n = Math.round(w * h / 5500);
      for (var k = 0; k < n; k++) {
        var s = 6 + hash(k, 44) * 16, v = 12 + s * 1.5;
        var y = h * 1.15 - wrap(hash(k, 45) * h * 1.3 + t * v, h * 1.3);
        var x = hash(k, 46) * w + Math.sin(t * 0.8 + k) * 16;
        ctx.fillStyle = k % 3 === 0 ? "rgba(255,250,242,0.75)" : "rgba(255," + Math.round(60 + hash(k, 47) * 100) + ",120,0.8)";
        heart(ctx, x, y, s);
      }
    },

    confetti: function (ctx, w, h, t) {
      for (var i = 0; i < 3; i++) glow(ctx, w * (0.2 + i * 0.3), h * (0.2 + Math.sin(t * 0.5 + i) * 0.1), w * 0.45, ["#FF4FB8", "#FFE04C", "#7AD7FF"][i], 0.18);
      var n = Math.round(w * h / 1700);
      for (var k = 0; k < n; k++) {
        var v = 28 + hash(k, 51) * 50;
        var y = wrap(hash(k, 52) * h * 1.2 + t * v, h * 1.2) - h * 0.1;
        var x = wrap(hash(k, 53) * w + Math.sin(t * 1.2 + k) * 24, w);
        ctx.save(); ctx.translate(x, y); ctx.rotate(t * (1 + hash(k, 54) * 3) + k);
        ctx.scale(1, Math.abs(Math.cos(t * 3 + k)) + 0.15);
        ctx.fillStyle = ["#FFE04C", "#FF4FB8", "#7AD7FF", "#8CF2B4", "#FFFAF2", "#FF7A45"][k % 6];
        ctx.fillRect(-4, -2.5, 8, 5); ctx.restore();
      }
    },

    stars: function (ctx, w, h, t) {
      stars(ctx, w, h, t, Math.round(w * h / 1800), 0.85);
      var p = wrap(t, 7) / 7;
      if (p < 0.18) {
        var q = p / 0.18, sx = w * (0.15 + q * 0.55), sy = h * (0.12 + q * 0.2);
        var g = ctx.createLinearGradient(sx - 90, sy - 33, sx, sy);
        g.addColorStop(0, "rgba(255,250,242,0)"); g.addColorStop(1, "rgba(255,250,242," + (1 - q).toFixed(2) + ")");
        ctx.strokeStyle = g; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(sx - 90, sy - 33); ctx.lineTo(sx, sy); ctx.stroke();
      }
      glow(ctx, w * 0.5, h * 0.95, w * 0.8, "#9EDBFF", 0.22);
      hills(ctx, w, h, h * 0.82, h * 0.05, "#0c1b24", 2);
      hills(ctx, w, h, h * 0.9, h * 0.03, "#070f14", 5);
    },

    petals: function (ctx, w, h, t, accent) {
      glow(ctx, w * 0.75, h * 0.12, Math.min(w, h) * 0.5, "#FFF3B0", 0.55);
      for (var c = 0; c < 4; c++) {
        var cx = wrap(hash(c, 61) * w + t * (6 + c * 2), w + 200) - 100, cy = h * (0.12 + c * 0.08);
        ctx.fillStyle = "rgba(255,255,255,0.22)";
        ctx.beginPath(); ctx.ellipse(cx, cy, 60, 16, 0, 0, 6.283); ctx.ellipse(cx + 30, cy - 8, 36, 14, 0, 0, 6.283); ctx.fill();
      }
      hills(ctx, w, h, h * 0.8, h * 0.03, "rgba(20,90,60,0.55)", 3);
      hills(ctx, w, h, h * 0.88, h * 0.02, "rgba(10,60,40,0.75)", 6);
      for (var f = 0; f < Math.round(w / 14); f++) {
        var fx = hash(f, 62) * w, fy = h * (0.88 + hash(f, 63) * 0.1), sway = Math.sin(t * 1.4 + f) * 3;
        ctx.strokeStyle = "rgba(40,120,70,0.9)"; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.moveTo(fx, fy + 12); ctx.lineTo(fx + sway, fy); ctx.stroke();
        ctx.fillStyle = ["#FFFAF2", "#FFE666", accent || "#FFB3D9", "#FF8FB8"][f % 4];
        for (var pp = 0; pp < 5; pp++) { var a = pp / 5 * 6.283; ctx.beginPath(); ctx.arc(fx + sway + Math.cos(a) * 3, fy + Math.sin(a) * 3, 2.4, 0, 6.283); ctx.fill(); }
        ctx.fillStyle = "#FFC93C"; ctx.beginPath(); ctx.arc(fx + sway, fy, 1.6, 0, 6.283); ctx.fill();
      }
      var n = Math.round(w * h / 6000);
      for (var k = 0; k < n; k++) {
        var v = 16 + hash(k, 64) * 20;
        var y = wrap(hash(k, 65) * h * 1.2 + t * v, h * 1.2) - h * 0.1;
        var x = wrap(hash(k, 66) * w + Math.sin(t * 0.9 + k) * 30 + t * 10, w + 20) - 10;
        ctx.save(); ctx.translate(x, y); ctx.rotate(t * 1.5 + k);
        ctx.fillStyle = k % 2 ? "rgba(255,250,242,0.85)" : (accent ? rgba(accent, 0.85) : "rgba(255,180,210,0.85)");
        ctx.beginPath(); ctx.ellipse(0, 0, 5, 2.6, 0, 0, 6.283); ctx.fill(); ctx.restore();
      }
    },

    sea: function (ctx, w, h, t) {
      var horizon = h * 0.62, sr = Math.min(w, h) * 0.13, sunY = horizon - sr * 0.35 + Math.sin(t * 0.1) * 4;
      glow(ctx, w * 0.5, sunY, Math.min(w, h) * 0.6, "#FFD27A", 0.5);
      ctx.fillStyle = "#FFE3A3"; ctx.beginPath(); ctx.arc(w * 0.5, sunY, sr, 0, 6.283); ctx.fill();
      var g = ctx.createLinearGradient(0, horizon, 0, h);
      g.addColorStop(0, "#2a4f8a"); g.addColorStop(1, "#0d1f40");
      ctx.fillStyle = g; ctx.fillRect(0, horizon, w, h - horizon);
      for (var i = 0; i < 40; i++) {
        var y = horizon + Math.pow(i / 40, 1.6) * (h - horizon), len = 10 + (i / 40) * 60;
        var x = w * 0.5 + Math.sin(t * 1.3 + i * 1.7) * (8 + i * 1.5) - len / 2;
        ctx.fillStyle = "rgba(255,224,150," + (0.7 - i / 60).toFixed(2) + ")"; ctx.fillRect(x, y, len, 2);
      }
      for (var k = 0; k < 30; k++) {
        var wy = horizon + hash(k, 71) * (h - horizon), wx = wrap(hash(k, 72) * w + t * 12, w);
        ctx.fillStyle = "rgba(255,255,255,0.15)"; ctx.fillRect(wx, wy, 14 + hash(k, 73) * 20, 1.5);
      }
      var bp = wrap(t, 60) / 60, bx = -60 + bp * (w + 120), by = horizon + 8 + Math.sin(t * 1.5) * 1.5;
      ctx.fillStyle = "#14223d";
      ctx.beginPath(); ctx.moveTo(bx - 22, by); ctx.lineTo(bx + 22, by); ctx.lineTo(bx + 15, by + 7); ctx.lineTo(bx - 15, by + 7); ctx.fill();
      ctx.beginPath(); ctx.moveTo(bx, by - 2); ctx.lineTo(bx, by - 40); ctx.lineTo(bx + 18, by - 4); ctx.fill();
      ctx.beginPath(); ctx.moveTo(bx - 2, by - 2); ctx.lineTo(bx - 2, by - 32); ctx.lineTo(bx - 16, by - 4); ctx.fill();
      ctx.strokeStyle = "#2a1a2a"; ctx.lineWidth = 1.6;
      for (var b = 0; b < 3; b++) {
        var gp = wrap(t * 0.8 + b * 3, 14) / 14, gx = w * 1.1 - gp * w * 1.3 + b * 26, gy = h * (0.2 + b * 0.05) + Math.sin(t * 1.3 + b) * 6, f = Math.sin(t * 7 + b) * 4;
        ctx.beginPath(); ctx.moveTo(gx - 9, gy - f); ctx.quadraticCurveTo(gx - 4, gy - 4, gx, gy); ctx.quadraticCurveTo(gx + 4, gy - 4, gx + 9, gy - f); ctx.stroke();
      }
    },

    halloween: function (ctx, w, h, t) {
      stars(ctx, w, h, t, Math.round(w * h / 6000));
      moon(ctx, w * 0.5, h * 0.3, Math.min(w, h) * 0.2, "#FFB95A");
      for (var f = 0; f < 3; f++) {
        ctx.fillStyle = "rgba(180,140,220,0.08)";
        var fy = h * (0.62 + f * 0.08), fx = wrap(t * (8 + f * 4), w * 2) - w;
        ctx.beginPath(); ctx.ellipse(fx + w * 0.5, fy, w * 0.7, 18, 0, 0, 6.283); ctx.fill();
      }
      ctx.fillStyle = "#08040c";
      for (var b = 0; b < 5; b++) {
        var p = wrap(t * 0.7 + b * 2.3, 11) / 11, bx = -40 + p * (w + 80), by = h * (0.18 + hash(b, 81) * 0.35) + Math.sin(t * 2 + b) * 16;
        var flap = Math.sin(t * 12 + b) * 7, s = 0.7 + hash(b, 82) * 0.6;
        ctx.save(); ctx.translate(bx, by); ctx.scale(s, s);
        ctx.beginPath(); ctx.moveTo(0, 0); ctx.quadraticCurveTo(-8, -6 - flap, -18, -2 - flap); ctx.quadraticCurveTo(-12, 0, -10, 4); ctx.quadraticCurveTo(-5, 2, 0, 5);
        ctx.quadraticCurveTo(5, 2, 10, 4); ctx.quadraticCurveTo(12, 0, 18, -2 - flap); ctx.quadraticCurveTo(8, -6 - flap, 0, 0); ctx.fill();
        ctx.restore();
      }
      hills(ctx, w, h, h * 0.84, h * 0.03, "#0b0610", 2);
      for (var k = 0; k < 4; k++) {
        var px = w * (0.12 + k * 0.26), py = h * 0.86 + hash(k, 83) * 10, pr = 16 + hash(k, 84) * 12;
        var fl = 0.75 + 0.25 * Math.sin(t * 8 + k * 2) * Math.sin(t * 3.1 + k);
        glow(ctx, px, py, pr * 3, "#FF8C1A", 0.25 * fl);
        ctx.fillStyle = "#E86A10"; ctx.beginPath(); ctx.ellipse(px, py, pr * 1.2, pr, 0, 0, 6.283); ctx.fill();
        ctx.strokeStyle = "rgba(120,40,0,0.5)"; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.ellipse(px, py, pr * 0.45, pr, 0, 0, 6.283); ctx.stroke();
        ctx.fillStyle = "#3a6b1a"; ctx.fillRect(px - 2, py - pr - 6, 4, 8);
        ctx.fillStyle = "rgba(255,220,90," + fl.toFixed(2) + ")";
        ctx.beginPath(); ctx.moveTo(px - pr * 0.55, py - pr * 0.15); ctx.lineTo(px - pr * 0.25, py - pr * 0.45); ctx.lineTo(px - pr * 0.12, py - pr * 0.1); ctx.fill();
        ctx.beginPath(); ctx.moveTo(px + pr * 0.55, py - pr * 0.15); ctx.lineTo(px + pr * 0.25, py - pr * 0.45); ctx.lineTo(px + pr * 0.12, py - pr * 0.1); ctx.fill();
        ctx.beginPath(); ctx.moveTo(px - pr * 0.6, py + pr * 0.2); ctx.quadraticCurveTo(px, py + pr * 0.75, px + pr * 0.6, py + pr * 0.2); ctx.quadraticCurveTo(px, py + pr * 0.45, px - pr * 0.6, py + pr * 0.2); ctx.fill();
      }
    }
  };

  var running = [];

  function Scene(canvas) {
    this.canvas = canvas;
    this.ctx = canvas.getContext("2d");
    this.visible = true;
    this.offset = Math.random() * 20;
    var self = this;
    if (window.ResizeObserver) new ResizeObserver(function () { self.resize(); }).observe(canvas);
    if (window.IntersectionObserver) new IntersectionObserver(function (e) { self.visible = e[0].isIntersecting; }).observe(canvas);
    this.resize();
  }
  Scene.prototype.resize = function () {
    var dpr = Math.min(window.devicePixelRatio || 1, 2), r = this.canvas.getBoundingClientRect();
    this.w = r.width; this.h = r.height;
    this.canvas.width = Math.max(1, Math.round(r.width * dpr)); this.canvas.height = Math.max(1, Math.round(r.height * dpr));
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    if (reduceMotion) this.draw(12);
  };
  Scene.prototype.draw = function (t) {
    var draw = scenes[this.canvas.getAttribute("data-scene")];
    this.ctx.clearRect(0, 0, this.w, this.h);
    if (draw && this.w > 0) draw(this.ctx, this.w, this.h, t + this.offset, this.canvas.getAttribute("data-accent"));
  };

  function loop(ms) {
    if (!document.hidden) running.forEach(function (s) { if (s.visible) s.draw(ms / 1000); });
    requestAnimationFrame(loop);
  }

  // ---------- iPhone di esempio con le feste che cambiano ----------

  function setupDemo() {
    var data = document.getElementById("qm-holidays");
    var phone = document.querySelector("[data-phone]");
    if (!data || !phone) return;
    var holidays = JSON.parse(data.textContent), byId = {};
    holidays.forEach(function (h) { byId[h.id] = h; });
    var buttons = Array.prototype.slice.call(document.querySelectorAll("[data-demo]"));
    var canvas = phone.querySelector("canvas"), timer = null, index = 0;

    function show(id) {
      var h = byId[id];
      phone.style.setProperty("--c1", h.colors[0]); phone.style.setProperty("--c2", h.colors[1]);
      phone.style.setProperty("--c3", h.colors[2]); phone.style.setProperty("--accent", h.accent);
      phone.setAttribute("data-countdown", h.rule);
      canvas.setAttribute("data-scene", h.scene); canvas.setAttribute("data-accent", h.accent);
      setText(phone.querySelector("[data-demo-name]"), h.name);
      setText(phone.querySelector("[data-demo-emoji]"), h.emoji);
      buttons.forEach(function (b) { b.setAttribute("aria-pressed", String(b.getAttribute("data-demo") === id)); });
      index = buttons.findIndex(function (b) { return b.getAttribute("data-demo") === id; });
      updateCountdown(phone, new Date());
      running.forEach(function (s) { if (s.canvas === canvas && reduceMotion) s.draw(12); });
    }

    buttons.forEach(function (b) {
      b.addEventListener("click", function () { clearInterval(timer); show(b.getAttribute("data-demo")); });
    });
    if (!reduceMotion) timer = setInterval(function () { show(buttons[(index + 1) % buttons.length].getAttribute("data-demo")); }, 6000);
  }

  // ---------- Avvio ----------

  var now = new Date();
  sortHolidays(now);
  setupQuote(now);
  setupAdvent(now);
  setupDemo();
  tick();
  setInterval(tick, 1000);

  each("canvas[data-scene]", function (c) { running.push(new Scene(c)); });
  if (!reduceMotion && running.length) requestAnimationFrame(loop);

  if (window.IntersectionObserver && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add("in"); io.unobserve(e.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    each(".reveal", function (el) { io.observe(el); });
  } else {
    each(".reveal", function (el) { el.classList.add("in"); });
  }
})();
