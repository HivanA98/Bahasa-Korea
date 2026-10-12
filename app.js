/* ============================================================
   Latihan Bahasa Korea — app.js

   Data dimuat dari webdata.js (global KOREA_DATA), bukan lewat fetch(),
   sehingga aplikasi jalan baik di GitHub Pages maupun saat index.html dibuka
   langsung dari berkas (file://).

   Lafal dan alih huruf TIDAK dihitung di sini: keduanya sudah dihitung oleh
   koreadrill/pronounce.py dan koreadrill/romaja.py saat webdata.js dibuat,
   sehingga aturan bahasa hanya ada di satu tempat.

   Penjadwalan memakai lima kotak Leitner, sama seperti quiz.py. Progres
   disimpan di localStorage peramban dan tidak dikirim ke mana pun.
   ============================================================ */

"use strict";

/* ---------------------------------------------------- penyimpanan ---- */

const LS = { prog: "korea.progress.v1", prefs: "korea.prefs.v1", theme: "korea.theme" };

function lsGet(key, fallback) {
  try {
    const raw = localStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch { return fallback; }
}
function lsSet(key, val) {
  try { localStorage.setItem(key, JSON.stringify(val)); } catch { /* mode privat */ }
}

/* Jeda ulangan per kotak, dalam hari. Sama dengan INTERVALS di
   koreadrill/leitner.py; ubah keduanya bila ingin jadwal lain. */
const BOX_DAYS = { 1: 0, 2: 1, 3: 3, 4: 7, 5: 16 };
const MAX_BOX = 5;

const progress = lsGet(LS.prog, { cards: {} });
if (!progress.cards) progress.cards = {};

const prefs = Object.assign(
  { romaja: false, pron: false, arah: false, due: false, hide: false },
  lsGet(LS.prefs, {})
);

function todayISO() {
  const d = new Date();
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}
function addDays(iso, n) {
  const d = new Date(iso + "T00:00:00");
  d.setDate(d.getDate() + n);
  return new Date(d.getTime() - d.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
}
function stateOf(id) { return progress.cards[id] || null; }
function boxOf(id) { const s = stateOf(id); return s ? s.box : 0; }
function isDue(id) {
  const s = stateOf(id);
  if (!s) return true;                 // kartu baru selalu dianggap jatuh tempo
  return s.due <= todayISO();
}
function grade(id, ok) {
  const s = stateOf(id) || { box: 1, due: todayISO(), seen: 0, right: 0 };
  s.seen += 1;
  if (ok) { s.right += 1; s.box = Math.min(s.box + 1, MAX_BOX); }
  else { s.box = 1; }
  s.due = addDays(todayISO(), BOX_DAYS[s.box]);
  progress.cards[id] = s;
  lsSet(LS.prog, progress);
}

/* ---------------------------------------------------------- utilitas ---- */

const $ = (sel) => document.querySelector(sel);
const esc = (s) => String(s)
  .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
  .replace(/"/g, "&quot;");

function ko(text, size) {
  return `<div class="ko ${size || "ko-lg"}" lang="ko">${esc(text)}</div>`;
}
function rom(text) {
  return prefs.romaja && text ? `<div class="rom">${esc(text)}</div>` : "";
}
/* Lafal hanya ditampilkan bila memang BERBEDA dari tulisannya; menampilkan
   [학교] untuk 학교 hanya menambah keramaian tanpa menambah keterangan. */
function pron(x, big) {
  if (!x.beda) return "";
  return `<div class="pron${big ? " big" : ""}" lang="ko">[${esc(x.pron)}]</div>`;
}
function contoh(x) {
  if (!x) return "";
  return `<div class="example">${ko(x.ko, "ko-md")}${pron(x)}${rom(x.rom)}
    <div class="gloss">${esc(x.gloss)}</div></div>`;
}
function catatan(text) {
  return text ? `<div class="note">${esc(text)}</div>` : "";
}

/* ----------------------------------------------------- pembuat kartu ---- */

const D = typeof KOREA_DATA !== "undefined" ? KOREA_DATA : null;

/* Kartu soal pilihan ganda dipakai oleh beberapa modul, bentuknya sama. */
function soalFront(x) {
  return `<div class="prompt">${esc(x.prompt)}</div>
    ${x.promptKo ? ko(x.promptKo, "ko-lg") : ""}`;
}
function soalBack(x) {
  const kunci = x.optionsLang === "ko"
    ? `<span class="ko ko-md" lang="ko">${esc(x.options[x.answer])}</span>`
    : esc(x.options[x.answer]);
  return `<div class="detail">${esc(x.catLabel)}</div>
    <div class="meaning">${kunci}</div>
    ${catatan(x.explain)}`;
}

const MODES = {
  hangeul: {
    label: "Hangeul",
    toggles: [],
    items: () => D.hangeul,
    search: (x) => [x.jamo, x.name, x.rom, x.sound, x.title, x.letters, x.prompt,
                    x.explanation, x.example && x.example.ko, x.example && x.example.gloss]
      .concat(x.options || [], (x.examples || []).map((e) => e.ko + " " + e.gloss))
      .filter(Boolean).join(" "),
    kind: (x) => (x.kind === "soal" ? "mcq" : "flip"),
    front(x) {
      if (x.kind === "soal") return soalFront(x);
      if (x.kind === "huruf") {
        return ko(x.jamo, "ko-xl") +
          `<div class="hint" style="position:static;margin-top:12px">Dibaca apa, dan apa namanya?</div>`;
      }
      if (x.kind === "batchim") {
        return ko(x.jamo, "ko-xl") +
          `<div class="hint" style="position:static;margin-top:12px">Huruf apa saja yang berbunyi begini di batchim?</div>`;
      }
      return `<div class="id-xl">${esc(x.title)}</div>` +
        ko(x.examples[0].ko, "ko-lg") +
        `<div class="hint" style="position:static;margin-top:10px">Bagaimana kata ini dibaca, dan mengapa?</div>`;
    },
    back(x) {
      if (x.kind === "soal") return soalBack(x);
      if (x.kind === "huruf") {
        return `<div class="meaning">${esc(x.rom)}</div>
          <div class="detail">nama huruf: ${esc(x.name)} · ${esc(x.jenis)}</div>
          ${catatan(x.sound)}
          <hr class="sep" />${contoh(x.example)}
          ${catatan(x.note)}`;
      }
      if (x.kind === "batchim") {
        return `<div class="meaning"><span class="ko ko-md" lang="ko">${esc(x.letters)}</span></div>
          <div class="detail">${esc(x.sound)}</div>
          ${x.examples.map(contoh).join('<hr class="sep" />')}
          ${catatan(x.note)}`;
      }
      return `<div class="detail">${esc(x.title)}</div>
        <p style="text-align:center">${esc(x.explanation)}</p>
        ${x.examples.map(contoh).join('<hr class="sep" />')}
        ${catatan(x.note)}`;
    },
  },

  kosakata: {
    label: "Kosakata",
    toggles: ["arah"],
    items: () => D.kosakata,
    search: (x) => [x.ko, x.pron, x.rom, x.gloss, x.detail, x.haeyo, x.hanja,
                    x.example.ko, x.example.gloss].concat(x.alt).join(" "),
    kind: () => "flip",
    front(x) {
      if (prefs.arah) {
        return `<div class="id-xl">${esc(x.gloss)}</div>
                <div class="rom">${esc(x.pos)}</div>`;
      }
      return ko(x.ko, "ko-xl") + (prefs.pron ? pron(x, true) : "") + rom(x.rom);
    },
    back(x) {
      return `<div class="meaning">${esc(x.gloss)}</div>
        <div class="detail">${esc(x.detail)}</div>
        ${prefs.arah ? ko(x.ko, "ko-lg") + pron(x) + rom(x.rom) : pron(x)}
        <hr class="sep" />
        ${contoh(x.example)}
        ${catatan(x.note)}`;
    },
  },

  tatabahasa: {
    label: "Tata bahasa",
    toggles: [],
    items: () => D.tatabahasa,
    search: (x) => [x.prompt, x.promptKo, x.catLabel, x.explain].concat(x.options).join(" "),
    kind: () => "mcq",
    front: soalFront,
    back: soalBack,
  },

  angka: {
    label: "Angka",
    toggles: [],
    items: () => D.angka,
    search: (x) => [x.value, x.sino, x.native, x.nativeAttr, x.counter, x.gloss,
                    x.prompt, x.promptKo, x.note].concat(x.options || []).filter(Boolean).join(" "),
    kind: (x) => (x.kind === "soal" ? "mcq" : "flip"),
    front(x) {
      if (x.kind === "soal") return soalFront(x);
      if (x.kind === "angka") {
        return `<div class="ko ko-xl">${esc(x.value)}</div>
          <div class="hint" style="position:static;margin-top:12px">Sebutkan dalam kedua sistem angka</div>`;
      }
      return ko(x.counter, "ko-xl") +
        `<div class="hint" style="position:static;margin-top:12px">Untuk apa, dan dengan sistem angka yang mana?</div>`;
    },
    back(x) {
      if (x.kind === "soal") return soalBack(x);
      if (x.kind === "angka") {
        return `<dl class="kv">
            <dt>Sino-Korea</dt><dd><span class="ko ko-sm" lang="ko">${esc(x.sino)}</span>${
              prefs.romaja ? ` <em>${esc(x.sinoRom)}</em>` : ""}</dd>
            ${x.native ? `<dt>Asli Korea</dt><dd><span class="ko ko-sm" lang="ko">${esc(x.native)}</span>${
              prefs.romaja ? ` <em>${esc(x.nativeRom)}</em>` : ""}</dd>` : ""}
            ${x.nativeAttr && x.nativeAttr !== x.native
              ? `<dt>+ penggolong</dt><dd><span class="ko ko-sm" lang="ko">${esc(x.nativeAttr)}</span></dd>` : ""}
            ${!x.native ? `<dt>Asli Korea</dt><dd>tidak ada</dd>` : ""}
          </dl>
          ${catatan(x.note)}`;
      }
      return `<div class="meaning">${esc(x.gloss)}</div>
        <div class="detail">dipakai dengan ${esc(x.systemLabel)}</div>
        ${contoh(x.example)}
        ${catatan(x.note)}`;
    },
  },

  baca: {
    label: "Baca & lafal",
    toggles: [],
    items: () => D.baca,
    search: (x) => [x.ko, x.pron, x.rom, x.gloss, x.catLabel, x.explain]
      .concat(x.options || [], x.rules || []).filter(Boolean).join(" "),
    kind: (x) => (x.kind === "soal" ? "mcq" : "flip"),
    front(x) {
      if (x.kind === "soal") {
        return ko(x.ko, "ko-lg") +
          (x.type === "pron_choice"
            ? `<div class="rom">Bagaimana ini dibunyikan?</div>`
            : `<div class="rom">Apa arti kalimat ini?</div>`);
      }
      return ko(x.ko, "ko-lg") + (prefs.pron ? pron(x, false) : "") +
        `<div class="hint" style="position:static;margin-top:10px">Baca dengan suara, lalu bandingkan dengan lafalnya</div>`;
    },
    back(x) {
      const aturan = (x.rules || []).length
        ? `<div class="rules">Aturan yang bekerja: ${x.rules.map(esc).join(" · ")}</div>`
        : `<div class="rules">Tidak ada aturan yang bekerja: dibaca persis seperti tulisannya.</div>`;
      if (x.kind === "soal" && x.type === "meaning_choice") {
        return `<div class="meaning">${esc(x.gloss)}</div>
          ${ko(x.ko, "ko-md")}<div class="pron" lang="ko">[${esc(x.pron)}]</div>
          ${rom(x.rom)}${aturan}${catatan(x.explain)}`;
      }
      // Pada Level 1 lafalnya sama dengan tulisannya; menampilkan kurung siku
      // di situ hanya membuat pembaca mencari-cari perbedaan yang tidak ada.
      return (x.beda
          ? `<div class="pron big" lang="ko">[${esc(x.pron)}]</div>`
          : ko(x.ko, "ko-lg")) +
        `${rom(x.rom)}
        <div class="detail">${esc(x.gloss)}</div>
        ${aturan}
        ${catatan(x.explain)}`;
    },
  },

  kesantunan: {
    label: "Kesantunan",
    toggles: [],
    items: () => D.kesantunan,
    search: (x) => [x.plain, x.honorific, x.gloss, x.arah, x.prompt, x.promptKo, x.note]
      .concat(x.options || []).filter(Boolean).join(" "),
    kind: (x) => (x.kind === "soal" ? "mcq" : "flip"),
    front(x) {
      if (x.kind === "soal") return soalFront(x);
      return ko(x.plain, "ko-xl") + rom(x.plainRom) +
        `<div class="hint" style="position:static;margin-top:12px">Apa bentuk sopannya? (${esc(x.arah)})</div>`;
    },
    back(x) {
      if (x.kind === "soal") return soalBack(x);
      return `<div class="meaning"><span class="ko" lang="ko">${esc(x.honorific)}</span></div>
        <div class="detail">${esc(x.gloss)} · ${esc(x.arah)}</div>
        ${rom(x.honorificRom)}
        <hr class="sep" />
        ${contoh(x.example)}
        ${catatan(x.note)}`;
    },
  },
};

/* ------------------------------------------------------------ keadaan ---- */

let mode = "hangeul";
let deck = [];
let index = 0;
let activeCat = "*";
let activeStage = 0;
let query = "";
let shuffled = false;
let answered = false;

const els = {
  tabs: $("#tabs"), chips: $("#chips"), stages: $("#stages"), search: $("#search"),
  card: $("#card"), badge: $("#badge"), box: $("#box"), front: $("#front"),
  back: $("#back"), choices: $("#choices"), hint: $("#hint"),
  counter: $("#counter"), fill: $("#fill"), grade: $("#grade"),
  stats: $("#stats"), panel: $("#panel"),
};

/* ------------------------------------------------------------ susunan ---- */

function allItems() { return MODES[mode].items(); }

function buildDeck() {
  const cfg = MODES[mode];
  const q = query.trim().toLowerCase();
  deck = allItems().filter((x) => {
    if (activeCat !== "*" && x.cat !== activeCat) return false;
    if (activeStage && x.stage > activeStage) return false;
    if (prefs.due && !isDue(x.id)) return false;
    if (prefs.hide && boxOf(x.id) >= MAX_BOX) return false;
    if (q && !cfg.search(x).toLowerCase().includes(q)) return false;
    return true;
  });
  if (shuffled) {
    for (let i = deck.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [deck[i], deck[j]] = [deck[j], deck[i]];
    }
  }
  if (index >= deck.length) index = 0;
}

function renderChips() {
  const seen = new Map();
  for (const x of allItems()) {
    if (activeStage && x.stage > activeStage) continue;
    const prev = seen.get(x.cat) || { label: x.catLabel, n: 0 };
    prev.n += 1;
    seen.set(x.cat, prev);
  }
  const total = allItems().filter((x) => !activeStage || x.stage <= activeStage).length;
  let html = `<button data-cat="*" aria-pressed="${activeCat === "*"}">Semua<span class="n">${total}</span></button>`;
  for (const [cat, info] of seen) {
    html += `<button data-cat="${esc(cat)}" aria-pressed="${activeCat === cat}">${esc(info.label)}<span class="n">${info.n}</span></button>`;
  }
  els.chips.innerHTML = html;
}

function renderToggles() {
  const aktif = MODES[mode].toggles;
  $("#wrap-arah").hidden = !aktif.includes("arah");
}

/* ------------------------------------------------------------ tampilan ---- */

function render() {
  const cfg = MODES[mode];
  els.card.classList.remove("is-flipped");
  answered = false;

  if (!deck.length) {
    els.front.innerHTML = `<p class="empty">Tidak ada kartu yang cocok dengan saringan ini.<br />
      Coba hapus pencarian, pilih "Semua tahap", atau matikan "Jatuh tempo saja".</p>`;
    els.back.innerHTML = "";
    els.choices.hidden = true;
    els.grade.hidden = true;
    els.badge.textContent = "";
    els.box.textContent = "";
    els.counter.textContent = "0 / 0";
    els.fill.style.width = "0%";
    els.hint.textContent = "";
    return;
  }

  const x = deck[index];
  const kind = cfg.kind(x);

  els.badge.textContent = `${x.catLabel || ""} · tahap ${x.stage}`;
  const b = boxOf(x.id);
  els.box.textContent = b ? `kotak ${b}${isDue(x.id) ? " · jatuh tempo" : ""}` : "belum dilatih";

  els.front.innerHTML = cfg.front(x);
  els.back.innerHTML = cfg.back(x);

  if (kind === "mcq") {
    els.choices.hidden = false;
    els.choices.innerHTML = x.options.map((o, i) => {
      const isi = x.optionsLang === "ko"
        ? `<span class="opt-ko" lang="ko">${esc(o)}</span>`
        : esc(o);
      return `<button type="button" data-i="${i}"><span class="num">${i + 1}.</span>${isi}</button>`;
    }).join("");
    els.grade.hidden = true;
    els.hint.textContent = "Pilih satu jawaban (tekan 1–4)";
  } else {
    els.choices.hidden = true;
    els.choices.innerHTML = "";
    els.grade.hidden = false;
    els.hint.textContent = "Klik atau tekan Spasi untuk melihat jawaban";
  }

  els.counter.textContent = `${index + 1} / ${deck.length}`;
  els.fill.style.width = `${((index + 1) / deck.length) * 100}%`;
  renderPanel(x);
  fitCard();
}

/* Kedua sisi kartu diposisikan absolut, sehingga tingginya harus dihitung.
   Tanpa ini, kartu pilihan ganda yang panjang akan terpotong. */
function fitCard() {
  els.card.style.height = "auto";
  let h = 0;
  for (const face of els.card.querySelectorAll(".face")) {
    h = Math.max(h, face.scrollHeight);
  }
  // Sisa 4px supaya bilah gulir tidak muncul karena pembulatan.
  els.card.style.height = Math.max(300, h + 4) + "px";
}

function flip() {
  if (!deck.length) return;
  if (MODES[mode].kind(deck[index]) === "mcq" && !answered) return;
  els.card.classList.toggle("is-flipped");
}

function answer(i) {
  if (answered || !deck.length) return;
  const x = deck[index];
  if (MODES[mode].kind(x) !== "mcq") return;
  answered = true;
  const benar = i === x.answer;
  grade(x.id, benar);
  for (const btn of els.choices.querySelectorAll("button")) {
    const bi = Number(btn.dataset.i);
    btn.disabled = true;
    if (bi === x.answer) btn.classList.add("is-right");
    else if (bi === i) btn.classList.add("is-wrong");
  }
  els.hint.textContent = benar ? "Benar. Spasi untuk penjelasan." : "Belum tepat. Spasi untuk penjelasan.";
  els.box.textContent = `kotak ${boxOf(x.id)}`;
  renderStats();
}

function gradeFlip(ok) {
  if (!deck.length) return;
  grade(deck[index].id, ok);
  renderStats();
  next();
}

function next() { if (deck.length) { index = (index + 1) % deck.length; render(); } }
function prev() { if (deck.length) { index = (index - 1 + deck.length) % deck.length; render(); } }

/* -------------------------------------------------------------- panel ---- */

function renderPanel(x) {
  let html = "";
  if (mode === "hangeul") {
    const s = D.struktur;
    html = `<details><summary>${esc(s.title)}</summary><div class="body">
      <p>${esc(s.explanation)}</p>
      <ul>${s.examples.map((e) => `<li><span class="ko ko-sm" lang="ko">${esc(e.ko)}</span>
        &nbsp;= ${esc(e.parts)} — ${esc(e.gloss)}</li>`).join("")}</ul>
      <p><strong>Catatan:</strong></p>
      ${s.caveats.map((c) => `<div class="caveat">${esc(c)}</div>`).join("")}
    </div></details>`;
  } else if (mode === "tatabahasa") {
    const t = D.topik.find((t) => t.id === x.cat);
    if (t) {
      html = `<details open><summary>${esc(t.title)}</summary><div class="body">
        <p>${esc(t.explanation)}</p>
        ${t.examples.map((e) => `<div class="ko ko-sm" lang="ko">${esc(e.ko)}</div>
          <p style="margin-top:-2px">${esc(e.gloss)}</p>`).join("")}
        <p><strong>Pengecualian dan catatan:</strong></p>
        ${t.caveats.map((c) => `<div class="caveat">${esc(c)}</div>`).join("")}
      </div></details>`;
    }
  } else if (mode === "angka") {
    html = `<details><summary>Dua sistem angka: mana dipakai untuk apa</summary><div class="body">
      ${D.sistem.map((s) => `<p><strong>${esc(s.name)}</strong><br />${esc(s.range)}</p>
        <ul>${s.usedFor.map((u) => `<li>${esc(u)}</li>`).join("")}</ul>
        <div class="caveat">${esc(s.note)}</div>`).join("")}
    </div></details>`;
  } else if (mode === "baca") {
    html = `<details><summary>Tiga level pelafalan</summary><div class="body">
      <ul>${D.level.map((l) => `<li><strong>Level ${l.level} — ${esc(l.name)}.</strong>
        ${esc(l.note)}</li>`).join("")}</ul>
    </div></details>`;
  } else if (mode === "kesantunan") {
    html = `<details><summary>Tiga tingkat tutur</summary><div class="body">
      ${D.tingkat.map((t) => `<p><strong>${esc(t.name)}</strong> — ${esc(t.when)}<br />
        <span class="ko ko-sm" lang="ko">${esc(t.example.ko)}</span> ${esc(t.example.gloss)}<br />
        <span style="opacity:.75">${esc(t.note)}</span></p>`).join("")}
    </div></details>
    <details><summary>Yang perlu diingat tentang kesantunan</summary><div class="body">
      ${D.catatan.penting.map((c) => `<p>${esc(c)}</p>`).join("")}
      ${D.catatan.pemakaian.map((u) => `<p><strong>${esc(u.title)}.</strong> ${esc(u.text)}</p>`).join("")}
    </div></details>`;
  }
  els.panel.innerHTML = html;
}

function renderStats() {
  const ids = allItems().map((x) => x.id);
  const kotak = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };
  let baru = 0, jatuhTempo = 0, dilihat = 0, benar = 0;
  for (const id of ids) {
    const s = stateOf(id);
    if (!s) { baru += 1; continue; }
    kotak[s.box] += 1;
    dilihat += s.seen || 0;
    benar += s.right || 0;
    if (isDue(id)) jatuhTempo += 1;
  }
  const maxN = Math.max(1, ...Object.values(kotak));
  const baris = [1, 2, 3, 4, 5].map((b) =>
    `<tr><td>Kotak ${b}</td><td><span class="bar" style="width:${(kotak[b] / maxN) * 160}px"></span>
      &nbsp;${kotak[b]}</td></tr>`).join("");
  const pct = dilihat ? Math.round((benar / dilihat) * 100) : 0;
  els.stats.innerHTML = `<h3>Kemajuan pada modul ${esc(MODES[mode].label)}</h3>
    <table>
      <tr><td>Total kartu</td><td>${ids.length}</td></tr>
      <tr><td>Belum dilatih</td><td>${baru}</td></tr>
      <tr><td>Jatuh tempo</td><td>${jatuhTempo}</td></tr>
      ${baris}
    </table>
    <p>${dilihat ? `Jawaban tercatat: ${dilihat}, benar ${benar} (${pct}%).` : "Belum ada jawaban tercatat."}
    Jeda ulangan per kotak: 0, 1, 3, 7, dan 16 hari.</p>`;
}

/* ------------------------------------------------------------- kendali ---- */

function setMode(m) {
  mode = m;
  activeCat = "*";
  index = 0;
  answered = false;
  for (const b of els.tabs.querySelectorAll("button")) {
    b.setAttribute("aria-pressed", String(b.dataset.mode === m));
  }
  renderToggles();
  renderChips();
  buildDeck();
  render();
  renderStats();
}

function refresh() {
  renderChips();
  buildDeck();
  render();
}

function setTheme(name) {
  document.body.className = "theme-" + name;
  for (const b of document.querySelectorAll(".theme-dot")) {
    b.setAttribute("aria-pressed", String(b.dataset.theme === name));
  }
  lsSet(LS.theme, name);
}

function bindToggle(id, key) {
  const el = $(id);
  el.checked = prefs[key];
  el.addEventListener("change", () => {
    prefs[key] = el.checked;
    lsSet(LS.prefs, prefs);
    index = 0;
    refresh();
  });
}

function init() {
  if (!D) {
    document.body.innerHTML = '<p class="empty">webdata.js gagal dimuat. ' +
      'Jalankan <code>python tools/build_web.py</code> lalu muat ulang halaman.</p>';
    return;
  }

  setTheme(lsGet(LS.theme, "hanji"));

  els.tabs.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (b) setMode(b.dataset.mode);
  });
  els.chips.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    activeCat = b.dataset.cat;
    index = 0;
    refresh();
  });
  els.stages.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (!b) return;
    activeStage = Number(b.dataset.stage);
    for (const s of els.stages.querySelectorAll("button")) {
      s.setAttribute("aria-pressed", String(Number(s.dataset.stage) === activeStage));
    }
    activeCat = "*";
    index = 0;
    refresh();
  });
  els.search.addEventListener("input", () => {
    query = els.search.value;
    index = 0;
    buildDeck();
    render();
  });
  els.choices.addEventListener("click", (e) => {
    const b = e.target.closest("button");
    if (b) answer(Number(b.dataset.i));
  });
  els.card.addEventListener("click", (e) => {
    if (!e.target.closest(".choices")) flip();
  });

  $("#btn-flip").addEventListener("click", (e) => { e.stopPropagation(); flip(); });
  $("#btn-next").addEventListener("click", next);
  $("#btn-prev").addEventListener("click", prev);
  $("#btn-right").addEventListener("click", () => gradeFlip(true));
  $("#btn-wrong").addEventListener("click", () => gradeFlip(false));
  $("#btn-shuffle").addEventListener("click", (e) => {
    shuffled = !shuffled;
    e.currentTarget.setAttribute("aria-pressed", String(shuffled));
    index = 0;
    buildDeck();
    render();
  });
  $("#btn-stats").addEventListener("click", (e) => {
    const buka = els.stats.hidden;
    els.stats.hidden = !buka;
    e.currentTarget.setAttribute("aria-expanded", String(buka));
    if (buka) renderStats();
  });
  $("#btn-reset").addEventListener("click", () => {
    if (!confirm("Hapus seluruh progres di peramban ini? Tindakan ini tidak bisa dibatalkan.")) return;
    progress.cards = {};
    lsSet(LS.prog, progress);
    refresh();
    renderStats();
  });

  for (const b of document.querySelectorAll(".theme-dot")) {
    b.addEventListener("click", () => setTheme(b.dataset.theme));
  }

  bindToggle("#tg-romaja", "romaja");
  bindToggle("#tg-pron", "pron");
  bindToggle("#tg-arah", "arah");
  bindToggle("#tg-due", "due");
  bindToggle("#tg-hide", "hide");

  document.addEventListener("keydown", (e) => {
    if (e.target === els.search) {
      if (e.key === "Escape") { els.search.value = ""; query = ""; index = 0; refresh(); els.search.blur(); }
      return;
    }
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    switch (e.key) {
      case " ": case "Enter": e.preventDefault(); flip(); break;
      case "ArrowRight": e.preventDefault(); next(); break;
      case "ArrowLeft": e.preventDefault(); prev(); break;
      case "h": case "H": gradeFlip(true); break;
      case "b": case "B": gradeFlip(false); break;
      case "s": case "S": $("#btn-shuffle").click(); break;
      case "r": case "R": $("#tg-romaja").click(); break;
      case "p": case "P": $("#tg-pron").click(); break;
      case "/": e.preventDefault(); els.search.focus(); break;
      default:
        if (/^[1-9]$/.test(e.key)) answer(Number(e.key) - 1);
    }
  });

  window.addEventListener("resize", fitCard);
  if (document.fonts && document.fonts.ready) document.fonts.ready.then(fitCard);

  setMode("hangeul");

  // Jumlah kartu pada tab diambil dari data, bukan ditulis tangan.
  for (const b of els.tabs.querySelectorAll("button")) {
    const n = MODES[b.dataset.mode].items().length;
    b.querySelector("span").textContent = String(n);
  }
}

document.addEventListener("DOMContentLoaded", init);
