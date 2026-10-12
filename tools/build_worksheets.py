#!/usr/bin/env python3
"""Buat lembar kerja Markdown beserta kunci jawaban terpisah.

    python tools/build_worksheets.py

Hasilnya:
  worksheets/ws-NN.md                 lembar kerja (tanpa jawaban)
  worksheets/answers/ws-NN-kunci.md   kunci jawaban

Isi lembar kerja diambil langsung dari data/*.json dengan generator acak
ber-seed tetap, sehingga menjalankan ulang skrip ini menghasilkan lembar yang
sama persis. Kunci jawaban dibuat pada proses yang sama dengan soalnya,
sehingga tidak mungkin tidak sinkron.

Menulis Hangeul dengan tangan adalah bagian dari latihannya: bentuk blok suku
kata baru benar-benar masuk setelah tangan ikut menyusunnya.
"""

from __future__ import annotations

import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from koreadrill import dataio  # noqa: E402
from koreadrill.hangeul import compose, decompose, ends_with_batchim, jamo_name, particle  # noqa: E402
from koreadrill.pronounce import differs, pronounce, pronounce_trace, rule_names  # noqa: E402
from koreadrill.romaja import romanize, romanize_jamo  # noqa: E402

ROOT = dataio.ROOT
WS_DIR = os.path.join(ROOT, "worksheets")
KEY_DIR = os.path.join(WS_DIR, "answers")

#: (nomor lembar, tahap). Dua lembar per tahap, enam tahap.
PLAN = [(n, (n + 1) // 2) for n in range(1, 13)]

N_HANGEUL = 5
N_VOCAB_KO = 8
N_VOCAB_ID = 6
N_GRAMMAR = 4
N_PARTICLE = 5
N_NUMBER = 4
N_READING = 4
BLANK = " " * 20


class Picker:
    """Pengambil butir yang menghindari pengulangan antar lembar kerja."""

    def __init__(self, seed: int) -> None:
        self.rng = random.Random(seed)
        self.used: set[str] = set()

    def take(self, pool: list[dict], n: int, key: str = "id") -> list[dict]:
        fresh = [x for x in pool if x[key] not in self.used]
        self.rng.shuffle(fresh)
        chosen = fresh[:n]
        if len(chosen) < n:
            # Kolam sudah habis; ulangi butir lama agar lembar tetap penuh.
            rest = [x for x in pool if x[key] not in {c[key] for c in chosen}]
            self.rng.shuffle(rest)
            chosen += rest[: n - len(chosen)]
        for c in chosen:
            self.used.add(c[key])
        return chosen


def _mcq_block(lines: list[str], n: int, item: dict) -> None:
    lines.append(f"{n}. {item['prompt']}")
    if item.get("prompt_ko"):
        lines.append("")
        lines.append(f"   > {item['prompt_ko']}")
    lines.append("")
    for i, opt in enumerate(item["options"]):
        lines.append(f"   {chr(ord('a') + i)}. {opt}")
    lines.append("")
    lines.append("   Jawaban: ____")
    lines.append("")


def build_worksheet(number: int, stage: int, pickers: dict[str, Picker]) -> tuple[str, str]:
    letter_pool = dataio.hangeul_letters(stage)
    vocab_pool = dataio.vocab_entries(stage)
    noun_pool = dataio.vocab_nouns(min(stage, dataio.PARTICLE_MAX_STAGE))
    grammar_pool = dataio.grammar_items(stage)
    counter_pool = dataio.counters(stage)
    reading_pool = [
        {"id": i["id"], "ko": i["ko"], "gloss": i["gloss"], "explain": i.get("explain", "")}
        for i in dataio.reading_items(stage) if i["type"] == "pron_choice"
    ]
    # Pada tahap-tahap awal, modul baca belum punya cukup butir. Kolamnya
    # ditambah dengan kata dari kosakata yang lafalnya memang berbeda dari
    # tulisannya, sehingga bagian ini tidak pernah kosong.
    reading_pool += [
        {"id": e["id"] + "-lafal", "ko": e["ko"], "gloss": e["gloss"], "explain": ""}
        for e in vocab_pool if differs(e["ko"])
    ]

    letters = pickers["hangeul"].take(letter_pool, min(N_HANGEUL, len(letter_pool)), "id")
    v_ko = pickers["vocab_ko"].take(vocab_pool, N_VOCAB_KO)
    v_id = pickers["vocab_id"].take(vocab_pool, N_VOCAB_ID)
    gram = pickers["grammar"].take(grammar_pool, N_GRAMMAR)
    nouns = pickers["particle"].take(noun_pool, min(N_PARTICLE, len(noun_pool)))
    counts = pickers["number"].take(counter_pool, min(N_NUMBER, len(counter_pool)))
    read = pickers["reading"].take(reading_pool, min(N_READING, len(reading_pool)))

    rng = random.Random(1000 + number)

    ws: list[str] = []
    key: list[str] = []
    tag = f"ws-{number:02d}"

    ws.append(f"# Lembar kerja {number:02d} · tahap {stage}")
    ws.append("")
    ws.append(
        "Kerjakan dengan tulisan tangan tanpa membuka data. Menulis sendiri blok "
        "suku kata Hangeul adalah bagian dari latihannya. Perkiraan waktu 20-30 menit."
    )
    ws.append("")
    ws.append(f"Kunci jawaban: `worksheets/answers/{tag}-kunci.md`")
    ws.append("")

    key.append(f"# Kunci jawaban · lembar kerja {number:02d} · tahap {stage}")
    key.append("")
    key.append(f"Soal: `worksheets/{tag}.md`")
    key.append("")

    # --- A. Hangeul --------------------------------------------------------
    ws.append("## A. Hangeul: huruf dan blok suku kata")
    ws.append("")
    ws.append(
        "Tulis alih huruf Latin dan nama setiap huruf, lalu susun blok suku kata "
        "dari huruf-huruf yang diberikan."
    )
    ws.append("")
    ws.append("| No | Huruf | Alih huruf | Nama |")
    ws.append("|---:|:------|:-----------|:-----|")
    key.append("## A. Hangeul")
    key.append("")
    key.append("| No | Huruf | Alih huruf | Nama | Contoh |")
    key.append("|---:|:------|:-----------|:-----|:-------|")
    for i, x in enumerate(letters, 1):
        ws.append(f"| {i} | {x['jamo']} | {BLANK} | {BLANK} |")
        key.append(
            f"| {i} | {x['jamo']} | {romanize_jamo(x['jamo'])} | {jamo_name(x['jamo'])} | "
            f"{x['example']['ko']} = {x['example']['gloss']} |"
        )
    ws.append("")
    key.append("")

    # Penyusunan blok: huruf diambil dari sebuah kata yang sudah dipelajari,
    # lalu dipecah kembali oleh hangeul.decompose(), sehingga kuncinya pasti
    # sama dengan kata aslinya.
    kata_blok = rng.choice([e for e in vocab_pool if len(e["ko"]) >= 2])
    suku = [c for c in kata_blok["ko"] if c.strip()][:3]
    ws.append("Susun blok suku kata berikut, lalu gabungkan menjadi satu kata.")
    ws.append("")
    key.append("Blok suku kata:")
    key.append("")
    for i, s in enumerate(suku, 1):
        try:
            l, v, t = decompose(s)
        except ValueError:
            continue
        bagian = f"{l} + {v}" + (f" + {t}" if t else "")
        ws.append(f"{i}. {bagian} = ______")
        key.append(f"{i}. {bagian} = {compose(l, v, t)}")
    ws.append("")
    ws.append(f"Kata gabungannya: ______________  (artinya: {kata_blok['gloss']})")
    ws.append("")
    key.append("")
    key.append(f"Kata gabungannya: **{kata_blok['ko']}** = {kata_blok['gloss']}")
    key.append("")

    # --- B. Kosakata Korea ke Indonesia -----------------------------------
    ws.append("## B. Tulis arti kata berikut dalam Bahasa Indonesia")
    ws.append("")
    ws.append("| No | Kata | Arti |")
    ws.append("|---:|:-----|:-----|")
    key.append("## B. Arti kata")
    key.append("")
    key.append("| No | Kata | Arti | Keterangan |")
    key.append("|---:|:-----|:-----|:-----------|")
    for i, e in enumerate(v_ko, 1):
        ws.append(f"| {i} | {e['ko']} | {BLANK} |")
        extra = [dataio.POS_LABELS.get(e["pos"], e["pos"])]
        if e.get("haeyo"):
            extra.append("해요: " + e["haeyo"])
        lafal = pronounce(e["ko"])
        if lafal != e["ko"]:
            extra.append(f"dibaca [{lafal}]")
        key.append(f"| {i} | {e['ko']} | {e['gloss']} | {' · '.join(extra)} |")
    ws.append("")
    key.append("")

    # --- C. Kosakata Indonesia ke Korea -----------------------------------
    ws.append("## C. Tulis kata Korea dalam Hangeul untuk arti berikut")
    ws.append("")
    ws.append("| No | Arti | Kata Korea |")
    ws.append("|---:|:-----|:-----------|")
    key.append("## C. Kata Korea")
    key.append("")
    key.append("| No | Arti | Kata Korea | Contoh pemakaian |")
    key.append("|---:|:-----|:-----------|:-----------------|")
    for i, e in enumerate(v_id, 1):
        ws.append(f"| {i} | {e['gloss']} | {BLANK} |")
        key.append(
            f"| {i} | {e['gloss']} | {e['ko']} | "
            f"{e['example']['ko']} = {e['example']['gloss']} |"
        )
    ws.append("")
    key.append("")

    # --- D. Tata bahasa ----------------------------------------------------
    ws.append("## D. Tata bahasa: pilih satu jawaban")
    ws.append("")
    key.append("## D. Tata bahasa")
    key.append("")
    for i, item in enumerate(gram, 1):
        _mcq_block(ws, i, item)
        letter = chr(ord("a") + item["answer"])
        key.append(f"{i}. **{letter}** — {item['options'][item['answer']]}")
        if item.get("explain"):
            key.append(f"   {item['explain']}")
        key.append(f"   (topik {item['topic_id']}: {item['topic_title']})")
        key.append("")

    # --- E. Partikel -------------------------------------------------------
    # Kunci dihitung oleh hangeul.particle(), bukan ditulis tangan.
    jenis = [("topik", "은", "는"), ("subjek", "이", "가"), ("objek", "을", "를")]
    ws.append("## E. Partikel: lengkapi dengan bentuk yang tepat")
    ws.append("")
    ws.append("| No | Kata | Jenis partikel | Jawaban |")
    ws.append("|---:|:-----|:---------------|:--------|")
    key.append("## E. Partikel")
    key.append("")
    key.append("| No | Kata | Jenis | Jawaban | Alasan |")
    key.append("|---:|:-----|:------|:--------|:-------|")
    for i, e in enumerate(nouns, 1):
        nama, dengan, tanpa = jenis[(number + i) % 3]
        benar = particle(e["ko"], dengan, tanpa)
        ws.append(f"| {i} | {e['ko']} ({e['gloss']}) | {nama} ({dengan}/{tanpa}) | {BLANK} |")
        alasan = (
            "berakhir dengan batchim" if ends_with_batchim(e["ko"]) else "berakhir dengan vokal"
        )
        key.append(
            f"| {i} | {e['ko']} | {nama} | {e['ko']}{benar} | {alasan}, "
            f"dibaca [{pronounce(e['ko'] + benar)}] |"
        )
    ws.append("")
    key.append("")

    # --- F. Angka dan penggolong -------------------------------------------
    ws.append("## F. Angka dan penggolong")
    ws.append("")
    ws.append("Tulis dalam Hangeul, dengan sistem angka yang tepat.")
    ws.append("")
    ws.append("| No | Yang ditanyakan | Jawaban |")
    ws.append("|---:|:----------------|:--------|")
    key.append("## F. Angka dan penggolong")
    key.append("")
    key.append("| No | Yang ditanyakan | Jawaban | Sistem |")
    key.append("|---:|:----------------|:--------|:-------|")
    for i, c in enumerate(counts, 1):
        n = dataio.numeral_by_value(c["example_value"])
        if n is None:
            continue
        benar = (
            f"{n['native_attr']} {c['counter']}" if c["system"] == "native"
            else f"{n['sino']} {c['counter']}"
        )
        sistem = "asli Korea" if c["system"] == "native" else "Sino-Korea"
        ws.append(f"| {i} | {c['example_value']} {c['gloss']} | {BLANK} |")
        key.append(f"| {i} | {c['example_value']} {c['gloss']} | {benar} | {sistem} |")
    ws.append("")
    key.append("")

    # --- G. Pelafalan ------------------------------------------------------
    ws.append("## G. Pelafalan")
    ws.append("")
    ws.append(
        "Tulis bagaimana setiap kata DIBUNYIKAN (dalam Hangeul), lalu sebutkan "
        "aturan yang bekerja bila Anda mengenalinya."
    )
    ws.append("")
    key.append("## G. Pelafalan")
    key.append("")
    for i, item in enumerate(read, 1):
        ws.append(f"{i}. {item['ko']}   ({item['gloss']})")
        ws.append("")
        ws.append("   Dibunyikan: ______________________   Aturan: ______________________")
        ws.append("")
        lafal, aturan = pronounce_trace(item["ko"])
        key.append(f"{i}. {item['ko']} dibunyikan **[{lafal}]** ({romanize(item['ko'])})")
        key.append(f"   Aturan: {', '.join(rule_names(aturan)) or 'tidak ada'}")
        if item.get("explain"):
            key.append(f"   {item['explain']}")
        key.append("")

    ws.append("---")
    ws.append("")
    ws.append(
        "Setelah selesai, cocokkan dengan kunci jawaban. Butir yang salah "
        "sebaiknya dilatih lagi lewat `python quiz.py`, bukan hanya dibaca ulang."
    )
    ws.append("")

    return "\n".join(ws), "\n".join(key)


def main() -> int:
    os.makedirs(WS_DIR, exist_ok=True)
    os.makedirs(KEY_DIR, exist_ok=True)
    pickers = {
        name: Picker(seed)
        for name, seed in (
            ("hangeul", 10), ("vocab_ko", 11), ("vocab_id", 22), ("grammar", 33),
            ("particle", 44), ("number", 55), ("reading", 66),
        )
    }
    index: list[str] = [
        "# Lembar kerja",
        "",
        "Latihan tertulis yang dibuat dari `data/*.json` oleh "
        "`tools/build_worksheets.py`. Jangan menyunting berkas di folder ini; "
        "sunting datanya lalu jalankan ulang skripnya.",
        "",
        "| Lembar | Tahap | Kunci |",
        "|:-------|------:|:------|",
    ]
    for number, stage in PLAN:
        ws, key = build_worksheet(number, stage, pickers)
        tag = f"ws-{number:02d}"
        with open(os.path.join(WS_DIR, f"{tag}.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(ws)
        with open(os.path.join(KEY_DIR, f"{tag}-kunci.md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(key)
        index.append(
            f"| [{tag}.md]({tag}.md) | {stage} | [answers/{tag}-kunci.md](answers/{tag}-kunci.md) |"
        )
        print(f"  worksheets/{tag}.md  +  worksheets/answers/{tag}-kunci.md")
    index.append("")
    with open(os.path.join(WS_DIR, "README.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(index))
    print("  worksheets/README.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
