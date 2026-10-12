#!/usr/bin/env python3
"""Buat webdata.js untuk aplikasi kartu di browser.

    python tools/build_web.py

Data tetap bersumber dari data/*.json. Berkas hasilnya dimuat lewat tag
<script>, bukan fetch(), supaya aplikasi jalan baik di GitHub Pages maupun
saat index.html dibuka langsung dari berkas (file://) tanpa masalah CORS.

Teks Korea ditulis sebagai escape \\uXXXX (ASCII murni) supaya tidak bergantung
pada charset yang dikirim peladen.

Semua lafal dan alih huruf dihitung DI SINI memakai koreadrill/pronounce.py dan
koreadrill/romaja.py, sehingga aturan pelafalan tidak perlu ditulis ulang dalam
JavaScript dan tetap satu sumber dengan yang dipakai quiz.py.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from koreadrill import dataio  # noqa: E402
from koreadrill.hangeul import jamo_name  # noqa: E402
from koreadrill.pronounce import pronounce, pronounce_trace, rule_labels  # noqa: E402
from koreadrill.romaja import romanize, romanize_jamo  # noqa: E402

ROOT = dataio.ROOT
OUT = os.path.join(ROOT, "webdata.js")

LETTER_CAT = {
    ("konsonan", "dasar"): ("kons-dasar", "Huruf mati dasar"),
    ("konsonan", "beraspirat"): ("kons-aspirat", "Huruf berhembus"),
    ("konsonan", "kembar"): ("kons-kembar", "Huruf kembar"),
    ("vokal", "dasar"): ("vokal-dasar", "Vokal dasar"),
    ("vokal", "gabungan"): ("vokal-gabungan", "Vokal gabungan"),
}


def _ko(text: str) -> dict:
    """Satu teks Korea beserta lafal dan alih hurufnya."""
    lafal = pronounce(text)
    return {"ko": text, "pron": lafal, "rom": romanize(text), "beda": lafal != text}


def _contoh(x: dict) -> dict:
    d = _ko(x["ko"])
    d["gloss"] = x["gloss"]
    return d


# --------------------------------------------------------------- hangeul ---

def build_hangeul() -> list[dict]:
    out: list[dict] = []
    for x in dataio.hangeul_letters():
        cat, label = LETTER_CAT[(x["kind"], x["group"])]
        out.append({
            "id": x["id"], "kind": "huruf", "stage": x["stage"],
            "cat": cat, "catLabel": label,
            "jamo": x["jamo"], "name": jamo_name(x["jamo"]),
            "rom": romanize_jamo(x["jamo"]),
            "jenis": x["kind"],
            "sound": x["sound"],
            "example": _contoh(x["example"]),
            "note": x["note"],
        })
    for b in dataio.hangeul_batchim():
        out.append({
            "id": b["id"], "kind": "batchim", "stage": b["stage"],
            "cat": "batchim", "catLabel": "Batchim",
            "jamo": b["jamo"], "letters": b["letters"], "sound": b["sound"],
            "examples": [_contoh(e) for e in b["examples"]],
            "note": b["note"],
        })
    for r in dataio.hangeul_rules():
        out.append({
            "id": r["id"], "kind": "aturan", "stage": r["stage"],
            "cat": "aturan", "catLabel": "Aturan pelafalan",
            "title": r["title"], "explanation": r["explanation"],
            "examples": [_contoh(e) for e in r["examples"]],
            "note": r["note"],
        })
    for i in dataio.hangeul_items():
        out.append({
            "id": i["id"], "kind": "soal", "stage": i["stage"],
            "cat": "soal", "catLabel": "Soal",
            "prompt": i["prompt"], "promptKo": i.get("prompt_ko") or "",
            "optionsLang": i["options_lang"], "options": i["options"],
            "answer": i["answer"], "explain": i.get("explain") or "",
        })
    return out


def build_struktur() -> dict:
    s = dataio.syllable_structure()
    return {
        "title": s["title"],
        "explanation": s["explanation"],
        "examples": [
            {"ko": e["ko"], "rom": romanize(e["ko"]), "parts": e["parts"], "gloss": e["gloss"]}
            for e in s["examples"]
        ],
        "caveats": s["caveats"],
    }


# -------------------------------------------------------------- kosakata ---

def _detail(e: dict) -> str:
    bits = [dataio.POS_LABELS.get(e["pos"], e["pos"])]
    if e.get("haeyo"):
        bits.append("bentuk 해요: " + e["haeyo"])
    if e.get("hanja"):
        bits.append("hanja: " + e["hanja"])
    return " · ".join(bits)


def build_kosakata() -> list[dict]:
    out = []
    for e in dataio.vocab_entries():
        kartu = _ko(e["ko"])
        kartu.update({
            "id": e["id"], "stage": e["stage"],
            "cat": e["cat"], "catLabel": dataio.CAT_LABELS.get(e["cat"], e["cat"]),
            "gloss": e["gloss"], "alt": e.get("alt") or [],
            "pos": dataio.POS_LABELS.get(e["pos"], e["pos"]),
            "detail": _detail(e),
            "haeyo": e.get("haeyo") or "",
            "haeyoPron": pronounce(e["haeyo"]) if e.get("haeyo") else "",
            "hanja": e.get("hanja") or "",
            "example": _contoh(e["example"]),
            "note": e["note"],
        })
        out.append(kartu)
    return out


# ------------------------------------------------------------ tatabahasa ---

def build_tatabahasa() -> list[dict]:
    out = []
    for t in dataio.grammar_topics():
        for item in t["items"]:
            out.append({
                "id": item["id"], "cat": t["id"], "catLabel": t["title"],
                "stage": t["stage"],
                "prompt": item["prompt"], "promptKo": item.get("prompt_ko") or "",
                "optionsLang": item["options_lang"], "options": item["options"],
                "answer": item["answer"], "explain": item.get("explain") or "",
            })
    return out


def build_topik() -> list[dict]:
    return [
        {
            "id": t["id"], "title": t["title"], "stage": t["stage"],
            "explanation": t["explanation"], "caveats": t["caveats"],
            "examples": [_contoh(e) for e in t["examples"]],
        }
        for t in dataio.grammar_topics()
    ]


# ----------------------------------------------------------------- angka ---

def build_angka() -> list[dict]:
    out = []
    for n in dataio.numerals():
        out.append({
            "id": n["id"], "kind": "angka", "stage": n["stage"],
            "cat": "angka", "catLabel": "Angka",
            "value": n["value"], "sino": n["sino"],
            "sinoRom": romanize(n["sino"]),
            "native": n["native"] or "", "nativeAttr": n["native_attr"] or "",
            "nativeRom": romanize(n["native"]) if n["native"] else "",
            "note": n["note"],
        })
    for c in dataio.counters():
        out.append({
            "id": c["id"], "kind": "penggolong", "stage": c["stage"],
            "cat": "penggolong", "catLabel": "Penggolong",
            "counter": c["counter"], "gloss": c["gloss"],
            "system": c["system"],
            "systemLabel": "angka asli Korea" if c["system"] == "native" else "angka Sino-Korea",
            "example": _contoh(c["example"]),
            "note": c["note"],
        })
    for i in dataio.number_items():
        out.append({
            "id": i["id"], "kind": "soal", "stage": i["stage"],
            "cat": i["cat"], "catLabel": {
                "sistem": "Sistem angka", "bentuk": "Bentuk angka",
                "waktu": "Waktu", "uang": "Uang", "penggolong": "Penggolong",
            }.get(i["cat"], i["cat"]),
            "prompt": i["prompt"], "promptKo": i.get("prompt_ko") or "",
            "optionsLang": i["options_lang"], "options": i["options"],
            "answer": i["answer"], "explain": i.get("explain") or "",
        })
    return out


def build_sistem() -> list[dict]:
    return [
        {
            "id": s["id"], "name": s["name"], "range": s["range"],
            "usedFor": s["used_for"], "note": s["note"],
        }
        for s in dataio.number_systems()
    ]


# ------------------------------------------------------------------ baca ---

def build_baca() -> list[dict]:
    out = []
    for p in dataio.reading_passages():
        lafal, aturan = pronounce_trace(p["ko"])
        out.append({
            "id": p["id"], "kind": "teks", "stage": p["stage"], "level": p["level"],
            "cat": f"level{p['level']}", "catLabel": f"Level {p['level']}",
            "ko": p["ko"], "pron": lafal, "rom": romanize(p["ko"]),
            "beda": lafal != p["ko"],
            "gloss": p["gloss"], "rules": rule_labels(aturan),
        })
    for i in dataio.reading_items():
        lafal, aturan = pronounce_trace(i["ko"])
        out.append({
            "id": i["id"], "kind": "soal", "type": i["type"],
            "stage": i["stage"], "level": i["level"],
            "cat": f"level{i['level']}", "catLabel": f"Level {i['level']}",
            "ko": i["ko"], "pron": lafal, "rom": romanize(i["ko"]),
            "beda": lafal != i["ko"],
            "gloss": i["gloss"], "rules": rule_labels(aturan),
            "optionsLang": i["options_lang"], "options": i["options"],
            "answer": i["answer"], "explain": i.get("explain") or "",
        })
    return out


def build_level() -> list[dict]:
    return [{"level": l["level"], "name": l["name"], "note": l["note"]}
            for l in dataio.reading_levels()]


# ------------------------------------------------------------ kesantunan ---

def build_kesantunan() -> list[dict]:
    out = []
    for h in dataio.speech_honorifics():
        out.append({
            "id": h["id"], "kind": "hormat", "stage": h["stage"],
            "cat": "hormat", "catLabel": "Bentuk hormat",
            "plain": h["plain"], "plainRom": romanize(h["plain"]),
            "honorific": h["honorific"], "honorificRom": romanize(h["honorific"]),
            "gloss": h["gloss"], "arah": h["kind"],
            "example": _contoh(h["example"]),
            "note": h["note"],
        })
    for i in dataio.speech_items():
        out.append({
            "id": i["id"], "kind": "soal", "stage": i["stage"],
            "cat": i["cat"], "catLabel": {
                "tingkat": "Tingkat tutur", "hormat": "Bentuk hormat",
                "arah": "Arah kesantunan", "sapaan": "Sapaan",
                "penggolong": "Penggolong",
            }.get(i["cat"], i["cat"]),
            "prompt": i["prompt"], "promptKo": i.get("prompt_ko") or "",
            "optionsLang": i["options_lang"], "options": i["options"],
            "answer": i["answer"], "explain": i.get("explain") or "",
        })
    return out


def build_tingkat() -> list[dict]:
    return [
        {
            "id": s["id"], "name": s["name"], "when": s["when"],
            "example": _contoh(s["example"]), "note": s["note"],
        }
        for s in dataio.speech_levels()
    ]


def build_catatan() -> dict:
    n = dataio.speech_notes()
    return {"penting": n["penting"], "pemakaian": n["pemakaian"]}


def main() -> int:
    data = {
        "hangeul": build_hangeul(),
        "struktur": build_struktur(),
        "kosakata": build_kosakata(),
        "tatabahasa": build_tatabahasa(),
        "topik": build_topik(),
        "angka": build_angka(),
        "sistem": build_sistem(),
        "baca": build_baca(),
        "level": build_level(),
        "kesantunan": build_kesantunan(),
        "tingkat": build_tingkat(),
        "catatan": build_catatan(),
    }
    data["meta"] = {k: len(v) for k, v in data.items() if isinstance(v, list)}

    body = json.dumps(data, ensure_ascii=True, separators=(",", ":"), sort_keys=False)
    teks = (
        "/* Dibuat otomatis oleh tools/build_web.py dari data/*.json.\n"
        "   JANGAN disunting langsung; sunting datanya lalu jalankan ulang skripnya. */\n"
        '"use strict";\n'
        "const KOREA_DATA = " + body + ";\n"
    )
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(teks)
    kb = len(teks.encode("utf-8")) / 1024
    print(f"  webdata.js  ({kb:.0f} KB)")
    for k, n in data["meta"].items():
        print(f"    {k:12s} {n:4d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
