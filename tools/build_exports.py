#!/usr/bin/env python3
"""Buat ulang ekspor CSV dari data/*.json.

Hasilnya:
  data/csv/*.csv   tabel mentah untuk dibaca di penyunting lembar kerja
  anki/*.csv       berkas impor untuk Anki (tanpa baris judul)

Berkas JSON di data/ adalah satu-satunya sumber data. Jangan menyunting hasil
ekspor; sunting JSON-nya lalu jalankan ulang skrip ini.

    python tools/build_exports.py
"""

from __future__ import annotations

import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from koreadrill import dataio  # noqa: E402
from koreadrill.hangeul import jamo_name  # noqa: E402
from koreadrill.pronounce import pronounce, pronounce_trace, rule_names  # noqa: E402
from koreadrill.romaja import romanize, romanize_jamo  # noqa: E402

ROOT = dataio.ROOT
CSV_DIR = os.path.join(ROOT, "data", "csv")
ANKI_DIR = os.path.join(ROOT, "anki")

#: Baris pengarah untuk Anki 2.1.55 ke atas. Versi Anki yang lebih tua tidak
#: mengenalinya; hapus baris-baris ini bila impor gagal (lihat anki/README.md).
ANKI_DIRECTIVES = ["#separator:Comma", "#html:false"]


def _write_csv(path: str, header: list[str], rows: list[list[str]]) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
        if header:
            w.writerow(header)
        w.writerows(rows)
    print(f"  {os.path.relpath(path, ROOT)}  ({len(rows)} baris)")


def _write_anki(path: str, rows: list[list[str]], tags_column: int) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        for line in ANKI_DIRECTIVES:
            f.write(line + "\n")
        f.write(f"#tags column:{tags_column}\n")
        w = csv.writer(f, lineterminator="\n", quoting=csv.QUOTE_ALL)
        w.writerows(rows)
    print(f"  {os.path.relpath(path, ROOT)}  ({len(rows)} kartu)")


def _s(value: object) -> str:
    """Ubah nilai menjadi teks; None dan daftar kosong menjadi string kosong."""
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(str(v) for v in value)
    return str(value)


def _lafal(text: str) -> str:
    """Lafal, atau string kosong bila sama dengan tulisannya."""
    p = pronounce(text)
    return p if p != text else ""


# ---------------------------------------------------------------- data/csv ---

def export_hangeul_csv() -> None:
    rows = [
        [
            x["id"], x["jamo"], jamo_name(x["jamo"]), romanize_jamo(x["jamo"]),
            x["kind"], x["group"], x["sound"], x["example"]["ko"],
            romanize(x["example"]["ko"]), x["example"]["gloss"],
            str(x["stage"]), x["note"],
        ]
        for x in dataio.hangeul_letters()
    ]
    _write_csv(
        os.path.join(CSV_DIR, "hangeul_letters.csv"),
        ["id", "jamo", "nama", "romaja", "jenis", "kelompok", "bunyi",
         "contoh", "contoh_romaja", "contoh_arti", "stage", "catatan"],
        rows,
    )

    rows = [
        [
            r["id"], r["rule"], r["title"], r["explanation"],
            "; ".join(f"{e['ko']} -> {pronounce(e['ko'])}" for e in r["examples"]),
            str(r["stage"]), r["note"],
        ]
        for r in dataio.hangeul_rules()
    ]
    _write_csv(
        os.path.join(CSV_DIR, "hangeul_rules.csv"),
        ["id", "aturan", "judul", "penjelasan", "contoh", "stage", "catatan"],
        rows,
    )


def export_vocab_csv() -> None:
    rows = [
        [
            e["id"], e["ko"], _lafal(e["ko"]), romanize(e["ko"]), e["gloss"],
            _s(e.get("alt")), e["pos"], _s(e.get("haeyo")), _s(e.get("hanja")),
            e["example"]["ko"], romanize(e["example"]["ko"]), e["example"]["gloss"],
            e["cat"], str(e["stage"]), e["note"],
        ]
        for e in dataio.vocab_entries()
    ]
    _write_csv(
        os.path.join(CSV_DIR, "vocab.csv"),
        ["id", "ko", "lafal", "romaja", "arti", "arti_lain", "kelas_kata",
         "haeyo", "hanja", "contoh", "contoh_romaja", "contoh_arti", "kategori",
         "stage", "catatan"],
        rows,
    )


def export_grammar_csv() -> None:
    rows = [
        [t["id"], t["title"], str(t["stage"]), t["explanation"], _s(t["caveats"]),
         "; ".join(f"{e['ko']} = {e['gloss']}" for e in t["examples"])]
        for t in dataio.grammar_topics()
    ]
    _write_csv(
        os.path.join(CSV_DIR, "grammar_topics.csv"),
        ["id", "judul", "stage", "penjelasan", "catatan", "contoh"],
        rows,
    )

    rows = [
        [i["id"], i["topic_id"], str(i["stage"]), i["type"], i["prompt"],
         _s(i.get("prompt_ko")), i["options_lang"], _s(i["options"]),
         i["options"][i["answer"]], _s(i.get("explain"))]
        for i in dataio.grammar_items()
    ]
    _write_csv(
        os.path.join(CSV_DIR, "grammar_items.csv"),
        ["id", "topik", "stage", "jenis", "soal", "soal_ko", "bahasa_pilihan",
         "pilihan", "jawaban", "penjelasan"],
        rows,
    )


def export_numbers_csv() -> None:
    rows = [
        [n["id"], str(n["value"]), n["sino"], _s(n["native"]), _s(n["native_attr"]),
         str(n["stage"]), n["note"]]
        for n in dataio.numerals()
    ]
    _write_csv(
        os.path.join(CSV_DIR, "numerals.csv"),
        ["id", "nilai", "sino", "asli", "asli_depan_penggolong", "stage", "catatan"],
        rows,
    )

    rows = [
        [c["id"], c["counter"], c["gloss"], c["system"], str(c["example_value"]),
         c["example"]["ko"], c["example"]["gloss"], str(c["stage"]), c["note"]]
        for c in dataio.counters()
    ]
    _write_csv(
        os.path.join(CSV_DIR, "counters.csv"),
        ["id", "penggolong", "arti", "sistem", "nilai_contoh", "contoh",
         "contoh_arti", "stage", "catatan"],
        rows,
    )


def export_reading_csv() -> None:
    rows = []
    for p in dataio.reading_passages():
        lafal, aturan = pronounce_trace(p["ko"])
        rows.append([p["id"], "teks", str(p["level"]), str(p["stage"]), p["ko"],
                     lafal, romanize(p["ko"]), p["gloss"], _s(rule_names(aturan)), ""])
    for i in dataio.reading_items():
        lafal, aturan = pronounce_trace(i["ko"])
        rows.append([i["id"], i["type"], str(i["level"]), str(i["stage"]), i["ko"],
                     lafal, romanize(i["ko"]), i["gloss"], _s(rule_names(aturan)),
                     i["options"][i["answer"]]])
    _write_csv(
        os.path.join(CSV_DIR, "reading.csv"),
        ["id", "jenis", "level", "stage", "tulisan", "lafal", "romaja", "arti",
         "aturan", "jawaban"],
        rows,
    )


def export_speech_csv() -> None:
    rows = [
        [h["id"], h["plain"], h["honorific"], h["gloss"], h["kind"],
         h["example"]["ko"], h["example"]["gloss"], str(h["stage"]), h["note"]]
        for h in dataio.speech_honorifics()
    ]
    _write_csv(
        os.path.join(CSV_DIR, "speech_honorifics.csv"),
        ["id", "biasa", "hormat", "arti", "arah", "contoh", "contoh_arti",
         "stage", "catatan"],
        rows,
    )


# -------------------------------------------------------------------- anki ---

def export_anki_hangeul() -> None:
    rows = [
        [
            x["jamo"],
            f"{romanize_jamo(x['jamo'])} ({jamo_name(x['jamo'])})",
            x["sound"],
            f"{x['example']['ko']} = {x['example']['gloss']}",
            f"korea hangeul {x['kind']} tahap{x['stage']}",
        ]
        for x in dataio.hangeul_letters()
    ]
    _write_anki(os.path.join(ANKI_DIR, "hangeul.csv"), rows, tags_column=5)


def export_anki_vocab() -> None:
    rows = []
    for e in dataio.vocab_entries():
        lafal = _lafal(e["ko"])
        depan = e["ko"] + (f" [{lafal}]" if lafal else "")
        belakang = e["gloss"]
        if e.get("haeyo"):
            belakang += f" ({e['haeyo']})"
        rows.append([
            depan,
            belakang,
            romanize(e["ko"]),
            f"{e['example']['ko']} = {e['example']['gloss']}",
            e["note"],
            f"korea kosakata {e['cat']} tahap{e['stage']}",
        ])
    _write_anki(os.path.join(ANKI_DIR, "kosakata.csv"), rows, tags_column=6)


def export_anki_grammar() -> None:
    rows = []
    for i in dataio.grammar_items():
        soal = i["prompt"]
        if i.get("prompt_ko"):
            soal += f"\n{i['prompt_ko']}"
        rows.append([
            soal,
            i["options"][i["answer"]],
            _s(i.get("explain")),
            i["topic_title"],
            f"korea tatabahasa {i['topic_id']} tahap{i['stage']}",
        ])
    _write_anki(os.path.join(ANKI_DIR, "tatabahasa.csv"), rows, tags_column=5)


def export_anki_numbers() -> None:
    rows = []
    for n in dataio.numerals():
        belakang = f"Sino-Korea: {n['sino']}"
        if n["native"]:
            belakang += f" · asli Korea: {n['native']}"
            if n["native_attr"] != n["native"]:
                belakang += f" (+ penggolong: {n['native_attr']})"
        rows.append([str(n["value"]), belakang, n["note"],
                     f"korea angka tahap{n['stage']}"])
    for c in dataio.counters():
        sistem = "angka asli Korea" if c["system"] == "native" else "angka Sino-Korea"
        rows.append([
            c["counter"],
            f"{c['gloss']} ({sistem})",
            f"{c['example']['ko']} = {c['example']['gloss']}\n{c['note']}",
            f"korea penggolong tahap{c['stage']}",
        ])
    _write_anki(os.path.join(ANKI_DIR, "angka.csv"), rows, tags_column=4)


def export_anki_reading() -> None:
    rows = []
    for i in dataio.reading_items():
        if i["type"] != "pron_choice":
            continue
        lafal, aturan = pronounce_trace(i["ko"])
        rows.append([
            i["ko"],
            lafal,
            f"{i['gloss']} · {romanize(i['ko'])}",
            f"{_s(rule_names(aturan))}\n{i.get('explain') or ''}",
            f"korea lafal level{i['level']} tahap{i['stage']}",
        ])
    for p in dataio.reading_passages():
        lafal, aturan = pronounce_trace(p["ko"])
        rows.append([
            p["ko"], lafal, f"{p['gloss']} · {romanize(p['ko'])}",
            _s(rule_names(aturan)),
            f"korea lafal level{p['level']} tahap{p['stage']}",
        ])
    _write_anki(os.path.join(ANKI_DIR, "lafal.csv"), rows, tags_column=5)


def export_anki_speech() -> None:
    rows = [
        [
            h["plain"],
            h["honorific"],
            f"{h['gloss']} · {h['kind']}",
            f"{h['example']['ko']} = {h['example']['gloss']}\n{h['note']}",
            f"korea kesantunan tahap{h['stage']}",
        ]
        for h in dataio.speech_honorifics()
    ]
    _write_anki(os.path.join(ANKI_DIR, "kesantunan.csv"), rows, tags_column=5)


def main() -> int:
    print("data/csv:")
    export_hangeul_csv()
    export_vocab_csv()
    export_grammar_csv()
    export_numbers_csv()
    export_reading_csv()
    export_speech_csv()
    print("anki:")
    export_anki_hangeul()
    export_anki_vocab()
    export_anki_grammar()
    export_anki_numbers()
    export_anki_reading()
    export_anki_speech()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
