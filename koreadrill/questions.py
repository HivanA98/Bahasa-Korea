"""Pembuat soal untuk setiap mode latihan.

Soal yang dibuat otomatis selalu mengambil kunci jawaban LANGSUNG dari data
atau dari mesin bahasa (hangeul.py, pronounce.py), bukan dari daftar jawaban
terpisah. Dengan begitu kunci tidak mungkin menyimpang dari sumbernya. Ada
empat keluarga soal buatan di berkas ini:

* pemilihan partikel (은/는, 이/가, 을/를) — kuncinya dihitung dari ada
  tidaknya batchim oleh hangeul.particle();
* penyusunan blok suku kata dari tiga huruf — kuncinya dihitung oleh
  hangeul.compose();
* angka + penggolong — kuncinya disusun dari data angka dan penggolong,
  termasuk bentuk tak beraturan 하나/한 dan 스물/스무;
* membaca lafal sebuah kalimat — kuncinya dihitung oleh pronounce().

Pengecoh dipilih dengan generator acak ber-seed agar hasilnya bisa diulang
dan diuji.
"""

from __future__ import annotations

import random
import re
import unicodedata
from dataclasses import dataclass, field

from . import dataio
from .hangeul import (
    BASIC_CONSONANTS,
    BASIC_VOWELS,
    L_LIST,
    V_LIST,
    compose,
    decompose,
    ends_with_batchim,
    jamo_name,
    particle,
)
from .pronounce import pronounce, pronounce_trace, rule_labels
from .romaja import romanize, romanize_jamo

MODES = ("hangeul", "kosakata-ko", "kosakata-id", "tatabahasa", "angka", "baca")

MODE_LABELS = {
    "hangeul": "Hangeul: huruf dan suku kata",
    "kosakata-ko": "Kosakata: Korea ke Indonesia",
    "kosakata-id": "Kosakata: Indonesia ke Korea",
    "tatabahasa": "Tata bahasa dan kesantunan",
    "angka": "Angka dan penggolong",
    "baca": "Membaca dan pelafalan",
}

#: Tiga pasang partikel yang dipilih berdasarkan batchim. Urutannya tetap,
#: karena jenis soal untuk sebuah kata ditentukan dari urutan entri (bukan
#: acak), supaya id kartunya tetap sama di setiap sesi.
PARTICLE_SETS = [
    ("topik", "은", "는"),
    ("subjek", "이", "가"),
    ("objek", "을", "를"),
]

PARTICLE_HINT = {
    "topik": "partikel topik",
    "subjek": "partikel subjek",
    "objek": "partikel objek",
}


@dataclass
class Question:
    card_id: str
    mode: str
    kind: str  # "mcq" | "typed" | "selfcheck"
    question: str
    stimulus_ko: str | None = None
    stimulus_label: str | None = None
    options: list[str] | None = None
    options_lang: str | None = None
    answer: int | None = None
    accepted: list[str] = field(default_factory=list)
    #: Petunjuk yang ditampilkan quiz.py pada soal bertaip. Jawaban modul
    #: hangeul berupa alih huruf Latin, bukan arti Bahasa Indonesia.
    input_hint: str = "Arti dalam Bahasa Indonesia"
    reveal: str = ""
    reveal_ko: str | None = None
    explain: str | None = None
    #: True bila soal ini adalah pengulangan materi baru di lintasan kedua
    #: sesi yang sama. quiz.py tidak menaikkan kotak Leitner dua kali.
    repeat: bool = False
    #: Tahap materi (1-6). Dipakai session.py untuk memperkenalkan kartu baru
    #: menurut urutan tahap, bukan secara acak dari seluruh materi.
    stage: int | None = None

    def is_correct_text(self, text: str) -> bool:
        return normalize(text) in {normalize(a) for a in self.accepted}


# ------------------------------------------------------- jawaban bertaip ---

_PUNCT_RE = re.compile(r"[^\w\s]", flags=re.UNICODE)
_SPACE_RE = re.compile(r"\s+")


def normalize(text: str) -> str:
    """Bakukan jawaban bertaip: huruf kecil, tanpa tanda baca, spasi tunggal."""
    text = unicodedata.normalize("NFKC", text).strip().lower()
    text = _PUNCT_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def expand_accepted(gloss: str, alt: list[str] | None = None) -> list[str]:
    """Kembangkan arti menjadi daftar jawaban yang diterima.

    "sore, malam; makan malam" menghasilkan kalimat utuhnya, "sore", "malam",
    dan "makan malam". Tujuannya supaya pengguna tidak dihukum karena menulis
    salah satu arti saja.
    """
    out: list[str] = []

    def add(s: str) -> None:
        s = s.strip()
        if s and s not in out:
            out.append(s)

    add(gloss)
    for piece in re.split(r"[,;/]", gloss):
        add(piece)
        add(re.sub(r"\([^)]*\)", "", piece))
    for a in alt or []:
        add(a)
        add(re.sub(r"\([^)]*\)", "", a))
    return [o for o in out if o]


_ACCEPTED_CACHE: dict[tuple, frozenset[str]] = {}


def accepted_set(entry: dict) -> frozenset[str]:
    """Himpunan jawaban yang diterima untuk satu entri, sudah dibakukan."""
    key = (entry["gloss"], tuple(entry.get("alt") or ()))
    cached = _ACCEPTED_CACHE.get(key)
    if cached is None:
        cached = frozenset(
            normalize(a) for a in expand_accepted(entry["gloss"], entry.get("alt"))
        )
        _ACCEPTED_CACHE[key] = cached
    return cached


# ------------------------------------------------------------- pengecoh ---

def _pick_distractors(
    rng: random.Random, pool: list[dict], target: dict, key: str, n: int = 3
) -> list[str]:
    """Pilih n pengecoh, mengutamakan kata dengan kelas kata yang sama."""
    want = target[key]
    same_pos = [e for e in pool if e[key] != want and e.get("pos") == target.get("pos")]
    same_cat = [e for e in pool if e[key] != want and e.get("cat") == target.get("cat")]
    others = [e for e in pool if e[key] != want]
    chosen: list[str] = []
    for bucket in (same_pos, same_cat, others):
        rng.shuffle(bucket)
        for e in bucket:
            if e[key] not in chosen and len(chosen) < n:
                chosen.append(e[key])
        if len(chosen) >= n:
            break
    return chosen[:n]


def _shuffle_options(
    rng: random.Random, correct: str, distractors: list[str]
) -> tuple[list[str], int]:
    opts = [correct]
    for d in distractors:
        if d != correct and d not in opts:
            opts.append(d)
    rng.shuffle(opts)
    return opts, opts.index(correct)


# ------------------------------------------------------------- kosakata ---

def _vocab_detail(e: dict) -> str:
    bits = [dataio.POS_LABELS.get(e["pos"], e["pos"])]
    if e.get("haeyo"):
        bits.append(f"bentuk 해요: {e['haeyo']}")
    if e.get("hanja"):
        bits.append(f"hanja: {e['hanja']}")
    return " · ".join(bits)


def vocab_ko_to_id(e: dict) -> Question:
    lafal = pronounce(e["ko"])
    return Question(
        card_id=e["id"],
        mode="kosakata-ko",
        kind="typed",
        stage=e["stage"],
        question="Apa arti kata ini?",
        stimulus_ko=e["ko"],
        stimulus_label=(f"dibaca [{lafal}]" if lafal != e["ko"] else None),
        accepted=expand_accepted(e["gloss"], e.get("alt")),
        reveal=f"{e['gloss']}  ({_vocab_detail(e)})",
        reveal_ko=e["example"]["ko"],
        explain=f"{e['example']['ko']} = {e['example']['gloss']}",
    )


def vocab_id_to_ko(e: dict, pool: list[dict], rng: random.Random) -> Question:
    # Pengecoh tidak boleh menerima teks pertanyaan sebagai jawabannya sendiri.
    # Tanpa saringan ini, pertanyaan "kata Korea untuk 'terima kasih'" bisa
    # memuat 감사합니다 dan 고맙습니다 sekaligus, sehingga ada dua jawaban benar.
    prompt_key = normalize(e["gloss"])
    safe = [o for o in pool if o["id"] != e["id"] and prompt_key not in accepted_set(o)]
    distractors = _pick_distractors(rng, safe, e, "ko", 3)
    options, answer = _shuffle_options(rng, e["ko"], distractors)
    return Question(
        card_id=e["id"],
        mode="kosakata-id",
        kind="mcq",
        stage=e["stage"],
        question=f"Mana kata Korea untuk ‘{e['gloss']}’?",
        options=options,
        options_lang="ko",
        answer=answer,
        reveal=f"{e['ko']} = {e['gloss']}  ({_vocab_detail(e)})",
        reveal_ko=e["example"]["ko"],
        explain=f"{e['example']['ko']} = {e['example']['gloss']}",
    )


# -------------------------------------------------------------- hangeul ---

def letter_question(letter: dict) -> Question:
    """Kartu huruf: bunyinya apa, dan namanya apa."""
    j = letter["jamo"]
    rom = romanize_jamo(j)
    nama = jamo_name(j)
    accepted = [rom, nama] + [p.strip() for p in rom.split("/")]
    return Question(
        card_id=letter["id"],
        mode="hangeul",
        kind="typed",
        stage=letter["stage"],
        question="Huruf ini dibaca apa? (tulis alih hurufnya, misalnya g atau a)",
        stimulus_ko=j,
        stimulus_label=("vokal" if letter["kind"] == "vokal" else "huruf mati"),
        accepted=accepted,
        input_hint="Alih huruf Latin, atau nama hurufnya",
        reveal=f"{j} = {rom}   (nama huruf: {nama})",
        reveal_ko=letter["example"]["ko"],
        explain=(
            f"{letter['sound']}\n   Contoh: {letter['example']['ko']} "
            f"({romanize(letter['example']['ko'])}) = {letter['example']['gloss']}"
        ),
    )


def which_letter(letter: dict, others: list[dict], rng: random.Random) -> Question:
    """Soal buatan: 'mana huruf yang berbunyi X'. Kunci diambil dari data huruf."""
    rom = romanize_jamo(letter["jamo"])
    sejenis = [o for o in others if o["kind"] == letter["kind"] and o["jamo"] != letter["jamo"]]
    rng.shuffle(sejenis)
    options, answer = _shuffle_options(
        rng, letter["jamo"], [o["jamo"] for o in sejenis[:3]]
    )
    return Question(
        card_id=letter["id"],
        mode="hangeul",
        kind="mcq",
        stage=letter["stage"],
        question=f"Mana huruf yang dialihhurufkan ‘{rom}’?",
        options=options,
        options_lang="ko",
        answer=answer,
        reveal=f"{letter['jamo']} ({jamo_name(letter['jamo'])})",
        explain=letter["sound"],
    )


def syllable_question(letter: dict, rng: random.Random) -> Question:
    """Soal buatan: menyusun blok suku kata dari tiga huruf.

    Kunci dan pengecoh sama-sama dihitung oleh hangeul.compose(), sehingga
    semuanya pasti blok Hangeul yang sah dan kuncinya tidak bisa salah.
    """
    # Huruf pendamping diambil dari huruf DASAR saja, supaya blok yang muncul
    # masih menyerupai suku kata Korea yang wajar (짠, 뮤, 골) dan bukan
    # gabungan ganjil seperti ㅉ + ㅠ + ㄹ.
    dasar_l = [j for j in BASIC_CONSONANTS if j in L_LIST]
    l = letter["jamo"] if letter["kind"] == "konsonan" and letter["jamo"] in L_LIST else rng.choice(dasar_l)
    v = letter["jamo"] if letter["kind"] == "vokal" else rng.choice(list(BASIC_VOWELS))
    t = rng.choice(["", "ㄴ", "ㅁ", "ㄹ", "ㄱ"])
    benar = compose(l, v, t)

    salah: list[str] = []
    for _ in range(12):
        if len(salah) >= 3:
            break
        pilih = rng.random()
        if pilih < 0.34:
            kandidat = compose(rng.choice(dasar_l), v, t)
        elif pilih < 0.67:
            kandidat = compose(l, rng.choice(list(BASIC_VOWELS)), t)
        else:
            kandidat = compose(l, v, rng.choice(["", "ㄴ", "ㅁ", "ㄹ", "ㄱ", "ㅂ"]))
        if kandidat != benar and kandidat not in salah:
            salah.append(kandidat)

    options, answer = _shuffle_options(rng, benar, salah)
    bagian = f"{l} + {v}" + (f" + {t}" if t else "")
    return Question(
        card_id=dataio.syllable_card_id(letter),
        mode="hangeul",
        kind="mcq",
        stage=letter["stage"],
        question=f"Mana blok suku kata yang tersusun dari {bagian} ?",
        options=options,
        options_lang="ko",
        answer=answer,
        reveal=f"{bagian} = {benar}",
        explain=(
            "Huruf awal di kiri atau atas, vokal di kanan atau bawah, batchim di dasar blok. "
            f"{benar} dialihhurufkan {romanize(benar)}."
        ),
    )


def batchim_question(b: dict) -> Question:
    contoh = ", ".join(
        f"{x['ko']} [{pronounce(x['ko'])}] = {x['gloss']}" for x in b["examples"]
    )
    return Question(
        card_id=b["id"],
        mode="hangeul",
        kind="selfcheck",
        stage=b["stage"],
        question="Huruf apa saja yang berbunyi seperti batchim ini, dan bagaimana bunyinya?",
        stimulus_ko=b["jamo"],
        stimulus_label="batchim",
        reveal=f"{b['letters']}  —  {b['sound']}",
        explain=f"{contoh}\n   {b['note']}",
    )


def rule_question(r: dict) -> Question:
    contoh = "; ".join(
        f"{x['ko']} dibaca [{pronounce(x['ko'])}]" for x in r["examples"]
    )
    return Question(
        card_id=r["id"],
        mode="hangeul",
        kind="selfcheck",
        stage=r["stage"],
        question=f"Apa isi aturan ‘{r['title']}’?",
        stimulus_ko=r["examples"][0]["ko"],
        stimulus_label="bagaimana kata ini dibaca?",
        reveal=r["explanation"],
        explain=f"{contoh}\n   {r['note']}",
    )


def hangeul_item_question(item: dict) -> Question:
    return Question(
        card_id=item["id"],
        mode="hangeul",
        kind="mcq",
        stage=item["stage"],
        question=item["prompt"],
        stimulus_ko=item.get("prompt_ko"),
        options=list(item["options"]),
        options_lang=item["options_lang"],
        answer=item["answer"],
        reveal=item["options"][item["answer"]],
        explain=item.get("explain"),
    )


# ----------------------------------------------------------- tatabahasa ---

def grammar_question(item: dict) -> Question:
    return Question(
        card_id=item["id"],
        mode="tatabahasa",
        kind="mcq",
        stage=item["stage"],
        question=item["prompt"],
        stimulus_ko=item.get("prompt_ko"),
        options=list(item["options"]),
        options_lang=item["options_lang"],
        answer=item["answer"],
        reveal=item["options"][item["answer"]],
        explain=item.get("explain"),
    )


def speech_question(item: dict) -> Question:
    return Question(
        card_id=item["id"],
        mode="tatabahasa",
        kind="mcq",
        stage=item["stage"],
        question=item["prompt"],
        stimulus_ko=item.get("prompt_ko"),
        options=list(item["options"]),
        options_lang=item["options_lang"],
        answer=item["answer"],
        reveal=item["options"][item["answer"]],
        explain=item.get("explain"),
    )


def honorific_question(h: dict) -> Question:
    arah = h["kind"]
    return Question(
        card_id=h["id"],
        mode="tatabahasa",
        kind="selfcheck",
        stage=h["stage"],
        question=f"Apa bentuk sopan dari kata ini? (arah: {arah})",
        stimulus_ko=h["plain"],
        stimulus_label=f"arti: {h['gloss']}",
        accepted=[h["honorific"], h["honorific"].replace("다", "세요")],
        reveal=f"{h['plain']} → {h['honorific']}  ({h['gloss']})",
        reveal_ko=h["example"]["ko"],
        explain=f"{h['example']['ko']} = {h['example']['gloss']}\n   {h['note']}",
    )


def particle_question(entry: dict, index: int) -> Question:
    """Soal buatan: partikel mana yang menempel pada kata ini.

    Kuncinya dihitung oleh hangeul.particle() dari ada tidaknya batchim, jadi
    tidak ada daftar jawaban yang bisa menyimpang. Jenis partikel ditentukan
    dari urutan entri (bukan diacak), supaya satu kata selalu melatih partikel
    yang sama dan kotak Leitner-nya tetap bermakna.
    """
    jenis, dengan, tanpa = PARTICLE_SETS[index % len(PARTICLE_SETS)]
    benar = particle(entry["ko"], dengan, tanpa)
    salah = tanpa if benar == dengan else dengan
    lain = [p for pair in PARTICLE_SETS for p in pair[1:] if p not in (benar, salah)]
    options = [benar, salah, lain[0], lain[1]]
    rng = random.Random(entry["id"])
    rng.shuffle(options)
    batchim = ends_with_batchim(entry["ko"])
    return Question(
        card_id=dataio.particle_card_id(entry),
        mode="tatabahasa",
        kind="mcq",
        stage=max(entry["stage"], 2),
        question=f"Mana {PARTICLE_HINT[jenis]} yang tepat untuk kata ini?",
        stimulus_ko=entry["ko"],
        stimulus_label=f"arti: {entry['gloss']}",
        options=options,
        options_lang="ko",
        answer=options.index(benar),
        reveal=f"{entry['ko']}{benar}",
        explain=(
            f"{entry['ko']} {'berakhir dengan batchim' if batchim else 'berakhir dengan vokal'}, "
            f"sehingga memakai {benar}. "
            f"Dibaca [{pronounce(entry['ko'] + benar)}]."
        ),
    )


# ---------------------------------------------------------------- angka ---

def numeral_question(n: dict) -> Question:
    """Kartu angka: satu nilai, dua sistem."""
    bagian = [f"Sino-Korea: {n['sino']}"]
    if n["native"]:
        bagian.append(f"asli Korea: {n['native']}")
        if n["native_attr"] != n["native"]:
            bagian.append(f"di depan penggolong: {n['native_attr']}")
    else:
        bagian.append("tidak ada bentuk asli Korea")
    return Question(
        card_id=n["id"],
        mode="angka",
        kind="selfcheck",
        stage=n["stage"],
        question=f"Bagaimana menyebut angka {n['value']} dalam kedua sistem?",
        stimulus_ko=str(n["value"]),
        accepted=[x for x in (n["sino"], n["native"], n["native_attr"]) if x],
        reveal=" · ".join(bagian),
        explain=n["note"],
    )


def counter_question(c: dict) -> Question:
    """Kartu penggolong: dipakai untuk apa, dan dengan sistem angka yang mana."""
    sistem = "angka asli Korea" if c["system"] == "native" else "angka Sino-Korea"
    return Question(
        card_id=c["id"],
        mode="angka",
        kind="selfcheck",
        stage=c["stage"],
        question="Penggolong ini dipakai untuk apa, dan dengan sistem angka yang mana?",
        stimulus_ko=c["counter"],
        reveal=f"{c['gloss']} · {sistem}",
        reveal_ko=c["example"]["ko"],
        explain=f"{c['example']['ko']} = {c['example']['gloss']}\n   {c['note']}",
    )


def counter_mcq(c: dict, rng: random.Random) -> Question:
    """Soal buatan: 'bagaimana mengatakan N + penggolong'.

    Kunci disusun dari data: bentuk di depan penggolong diambil dari
    numerals.native_attr (yang memuat bentuk tak beraturan 한, 두, 세, 네,
    스무), sedangkan pengecohnya memakai bentuk sistem yang salah.
    """
    nilai = c["example_value"]
    n = dataio.numeral_by_value(nilai)
    if n is None:
        raise ValueError(f"nilai {nilai} pada penggolong {c['id']} tidak ada di numerals")

    if c["system"] == "native":
        benar = f"{n['native_attr']} {c['counter']}"
        salah = [f"{n['sino']} {c['counter']}"]
        if n["native"] and n["native"] != n["native_attr"]:
            salah.append(f"{n['native']} {c['counter']}")
    else:
        benar = f"{n['sino']} {c['counter']}"
        salah = [f"{n['native_attr']} {c['counter']}" if n["native_attr"] else f"{n['sino']}{c['counter']}"]
        if n["native"] and n["native"] != n["native_attr"]:
            salah.append(f"{n['native']} {c['counter']}")

    # Pengecoh tambahan: penggolong lain dengan angka yang benar.
    lain = [x for x in dataio.counters() if x["counter"] != c["counter"]]
    rng.shuffle(lain)
    for x in lain:
        if len(salah) >= 3:
            break
        awal = n["native_attr"] if x["system"] == "native" and n["native_attr"] else n["sino"]
        salah.append(f"{awal} {x['counter']}")

    options, answer = _shuffle_options(rng, benar, salah)
    sistem = "asli Korea" if c["system"] == "native" else "Sino-Korea"
    return Question(
        card_id=dataio.counter_card_id(c),
        mode="angka",
        kind="mcq",
        stage=c["stage"],
        question=f"Bagaimana mengatakan ‘{nilai} {c['gloss']}’?",
        stimulus_ko=f"{nilai} + {c['counter']}",
        options=options,
        options_lang="ko",
        answer=answer,
        reveal=benar,
        explain=(
            f"Penggolong {c['counter']} memakai angka {sistem}. {c['note']}"
        ),
    )


def number_item_question(item: dict) -> Question:
    return Question(
        card_id=item["id"],
        mode="angka",
        kind="mcq",
        stage=item["stage"],
        question=item["prompt"],
        stimulus_ko=item.get("prompt_ko"),
        options=list(item["options"]),
        options_lang=item["options_lang"],
        answer=item["answer"],
        reveal=item["options"][item["answer"]],
        explain=item.get("explain"),
    )


# ----------------------------------------------------------------- baca ---

def reading_question(item: dict) -> Question:
    if item["type"] == "pron_choice":
        lafal, aturan = pronounce_trace(item["ko"])
        penjelasan = item.get("explain") or ""
        if aturan:
            penjelasan = f"{penjelasan}\n   Aturan yang bekerja: {', '.join(rule_labels(aturan))}"
        return Question(
            card_id=item["id"],
            mode="baca",
            kind="mcq",
            stage=item["stage"],
            question="Bagaimana kata ini dibunyikan?",
            stimulus_ko=item["ko"],
            stimulus_label=f"arti: {item['gloss']}",
            options=list(item["options"]),
            options_lang="ko",
            answer=item["answer"],
            reveal=f"[{lafal}]  ({romanize(item['ko'])})",
            explain=penjelasan,
        )
    if item["type"] == "meaning_choice":
        return Question(
            card_id=item["id"],
            mode="baca",
            kind="mcq",
            stage=item["stage"],
            question="Apa arti kalimat ini?",
            stimulus_ko=item["ko"],
            stimulus_label=f"dibaca [{pronounce(item['ko'])}]",
            options=list(item["options"]),
            options_lang=item["options_lang"],
            answer=item["answer"],
            reveal=item["gloss"],
            explain=item.get("explain"),
        )
    raise ValueError(f"jenis soal baca tidak dikenal: {item['type']}")


def passage_question(p: dict) -> Question:
    lafal, aturan = pronounce_trace(p["ko"])
    penjelasan = (
        f"Aturan yang bekerja: {', '.join(rule_labels(aturan))}"
        if aturan
        else "Tidak ada aturan yang bekerja: kalimat ini dibaca persis seperti tulisannya."
    )
    return Question(
        card_id=p["id"],
        mode="baca",
        kind="selfcheck",
        stage=p["stage"],
        question=(
            f"Bacalah dengan suara (Level {p['level']}), lalu bandingkan dengan lafalnya."
        ),
        stimulus_ko=p["ko"],
        reveal=f"[{lafal}]  =  {p['gloss']}",
        reveal_ko=p["ko"],
        explain=f"{penjelasan}\n   Alih huruf: {romanize(p['ko'])}",
    )


# -------------------------------------------------------------- kumpulan ---

def build_pool(mode: str, stage: int | None, rng: random.Random) -> list[Question]:
    """Bangun seluruh soal yang tersedia untuk satu mode."""
    if mode == "hangeul":
        letters = dataio.hangeul_letters(stage)
        qs = [letter_question(x) for x in letters]
        if len(letters) >= 4:
            qs += [which_letter(x, letters, rng) for x in letters]
            qs += [syllable_question(x, rng) for x in letters]
        qs += [batchim_question(b) for b in dataio.hangeul_batchim(stage)]
        qs += [rule_question(r) for r in dataio.hangeul_rules(stage)]
        qs += [hangeul_item_question(i) for i in dataio.hangeul_items(stage)]
        return qs
    if mode == "kosakata-ko":
        return [vocab_ko_to_id(e) for e in dataio.vocab_entries(stage)]
    if mode == "kosakata-id":
        pool = dataio.vocab_entries(stage)
        return [vocab_id_to_ko(e, pool, rng) for e in pool]
    if mode == "tatabahasa":
        qs = [grammar_question(i) for i in dataio.grammar_items(stage)]
        qs += [speech_question(i) for i in dataio.speech_items(stage)]
        qs += [honorific_question(h) for h in dataio.speech_honorifics(stage)]
        batas = dataio.PARTICLE_MAX_STAGE if stage is None else min(stage, dataio.PARTICLE_MAX_STAGE)
        # Urutan diambil dari SELURUH daftar kata benda, bukan dari daftar yang
        # sudah disaring tahap. Tanpa ini, satu kata bisa melatih partikel
        # topik pada satu sesi dan partikel objek pada sesi lain, sehingga
        # kotak Leitner-nya kehilangan makna.
        urutan = {e["id"]: i for i, e in enumerate(dataio.vocab_nouns())}
        qs += [
            particle_question(e, urutan[e["id"]])
            for e in dataio.vocab_nouns(batas)
        ]
        return qs
    if mode == "angka":
        qs = [numeral_question(n) for n in dataio.numerals(stage)]
        qs += [counter_question(c) for c in dataio.counters(stage)]
        qs += [counter_mcq(c, rng) for c in dataio.counters(stage)]
        qs += [number_item_question(i) for i in dataio.number_items(stage)]
        return qs
    if mode == "baca":
        qs = [reading_question(i) for i in dataio.reading_items(stage)]
        qs += [passage_question(p) for p in dataio.reading_passages(stage)]
        return qs
    raise ValueError(f"mode tidak dikenal: {mode}")


__all__ = [
    "MODES",
    "MODE_LABELS",
    "PARTICLE_SETS",
    "Question",
    "accepted_set",
    "batchim_question",
    "build_pool",
    "counter_mcq",
    "counter_question",
    "expand_accepted",
    "grammar_question",
    "hangeul_item_question",
    "honorific_question",
    "letter_question",
    "normalize",
    "number_item_question",
    "numeral_question",
    "particle_question",
    "passage_question",
    "reading_question",
    "rule_question",
    "speech_question",
    "syllable_question",
    "vocab_id_to_ko",
    "vocab_ko_to_id",
    "which_letter",
]
