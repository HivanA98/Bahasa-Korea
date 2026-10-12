"""Pemuat data dan pengakses per modul.

Satu-satunya sumber data adalah berkas JSON di folder data/. Berkas CSV di
data/csv/, berkas di anki/, lembar kerja di worksheets/, dan webdata.js adalah
hasil ekspor yang dibuat ulang oleh tools/, bukan sumber yang disunting
langsung.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DATA_DIR = os.path.join(ROOT, "data")

MODULE_FILES = {
    "hangeul": "hangeul.json",
    "vocab": "vocab.json",
    "grammar": "grammar.json",
    "numbers": "numbers.json",
    "reading": "reading.json",
    "speech": "speech.json",
}

#: Kelas kata yang dipakai di data/vocab.json, dalam istilah Korea beserta
#: padanan Indonesianya.
POS_LABELS = {
    "명사": "kata benda",
    "대명사": "kata ganti",
    "동사": "kata kerja",
    "형용사": "kata sifat",
    "부사": "kata keterangan",
    "감탄사": "kata seruan",
    "수사": "kata bilangan",
    "관형사": "kata penentu",
    "조사": "partikel",
}
POS_VALUES = set(POS_LABELS)

#: Kategori tematik di data/vocab.json beserta labelnya.
CAT_LABELS = {
    "인사": "Sapaan",
    "대명사": "Kata ganti & penunjuk",
    "질문": "Kata tanya",
    "사람": "Orang",
    "가족": "Keluarga",
    "물건": "Benda",
    "장소": "Tempat",
    "시간": "Waktu",
    "음식": "Makanan",
    "동사": "Kata kerja",
    "형용사": "Kata sifat",
    "부사": "Kata keterangan",
    "자연": "Alam & cuaca",
}

MAX_STAGE = 6


def _read_json(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=None)
def load(name: str) -> dict:
    """Muat satu modul data berdasarkan nama ('vocab', 'hangeul', ...)."""
    if name not in MODULE_FILES:
        raise KeyError(f"modul tidak dikenal: {name}")
    return _read_json(os.path.join(DATA_DIR, MODULE_FILES[name]))


def load_all() -> dict[str, dict]:
    return {name: load(name) for name in MODULE_FILES}


def _by_stage(items: list[dict], stage: int | None) -> list[dict]:
    if stage is None:
        return list(items)
    return [i for i in items if i["stage"] <= stage]


# --------------------------------------------------------- modul hangeul ---

def hangeul_letters(stage: int | None = None) -> list[dict]:
    return _by_stage(load("hangeul")["letters"], stage)


def hangeul_batchim(stage: int | None = None) -> list[dict]:
    return _by_stage(load("hangeul")["batchim"], stage)


def hangeul_rules(stage: int | None = None) -> list[dict]:
    return _by_stage(load("hangeul")["rules"], stage)


def hangeul_items(stage: int | None = None) -> list[dict]:
    return _by_stage(load("hangeul")["items"], stage)


def syllable_structure() -> dict:
    return load("hangeul")["syllable_structure"]


# -------------------------------------------------------- modul kosakata ---

def vocab_entries(stage: int | None = None) -> list[dict]:
    return _by_stage(load("vocab")["entries"], stage)


def vocab_nouns(stage: int | None = None) -> list[dict]:
    """Kata benda dan kata ganti, yaitu entri yang bisa diberi partikel."""
    return [e for e in vocab_entries(stage) if e["pos"] in ("명사", "대명사")]


# ------------------------------------------------------ modul tatabahasa ---

def grammar_topics(stage: int | None = None) -> list[dict]:
    return _by_stage(load("grammar")["topics"], stage)


def grammar_items(stage: int | None = None) -> list[dict]:
    out: list[dict] = []
    for topic in grammar_topics(stage):
        for item in topic["items"]:
            out.append({**item, "topic_id": topic["id"], "topic_title": topic["title"],
                        "stage": topic["stage"]})
    return out


# ----------------------------------------------------------- modul angka ---

def number_systems() -> list[dict]:
    return list(load("numbers")["systems"])


def numerals(stage: int | None = None) -> list[dict]:
    return _by_stage(load("numbers")["numerals"], stage)


def numeral_by_value(value: int) -> dict | None:
    for n in load("numbers")["numerals"]:
        if n["value"] == value:
            return n
    return None


def counters(stage: int | None = None) -> list[dict]:
    return _by_stage(load("numbers")["counters"], stage)


def number_items(stage: int | None = None) -> list[dict]:
    return _by_stage(load("numbers")["items"], stage)


# ------------------------------------------------------------ modul baca ---

def reading_passages(stage: int | None = None, level: int | None = None) -> list[dict]:
    out = _by_stage(load("reading")["passages"], stage)
    if level is not None:
        out = [p for p in out if p["level"] == level]
    return out


def reading_items(stage: int | None = None, level: int | None = None) -> list[dict]:
    out = _by_stage(load("reading")["items"], stage)
    if level is not None:
        out = [i for i in out if i["level"] == level]
    return out


def reading_levels() -> list[dict]:
    return list(load("reading")["levels"])


# ------------------------------------------------------ modul kesantunan ---

def speech_levels() -> list[dict]:
    return list(load("speech")["levels"])


def speech_honorifics(stage: int | None = None) -> list[dict]:
    return _by_stage(load("speech")["honorifics"], stage)


def speech_items(stage: int | None = None) -> list[dict]:
    return _by_stage(load("speech")["items"], stage)


def speech_notes() -> dict:
    d = load("speech")
    return {"penting": d["catatan_penting"], "pemakaian": d["usage_notes"]}


# ----------------------------------------------------------------- semua ---

def all_card_ids() -> list[str]:
    """Semua id yang dipakai sebagai kartu Leitner, dari seluruh modul.

    Kartu yang dibuat otomatis (soal partikel dan soal penggolong) memakai id
    turunan dan ikut didaftar di sini, supaya ringkasan kemajuan di quiz.py
    menghitung jumlah yang sama dengan yang benar-benar bisa muncul.
    """
    ids: list[str] = []
    for x in hangeul_letters():
        ids.append(x["id"])
        ids.append(syllable_card_id(x))
    for x in hangeul_batchim():
        ids.append(x["id"])
    for x in hangeul_rules():
        ids.append(x["id"])
    for x in hangeul_items():
        ids.append(x["id"])
    for e in vocab_entries():
        ids.append(e["id"])
    for e in vocab_nouns(PARTICLE_MAX_STAGE):
        ids.append(particle_card_id(e))
    for i in grammar_items():
        ids.append(i["id"])
    for i in speech_items():
        ids.append(i["id"])
    for x in speech_honorifics():
        ids.append(x["id"])
    for n in numerals():
        ids.append(n["id"])
    for c in counters():
        ids.append(c["id"])
        ids.append(counter_card_id(c))
    for i in number_items():
        ids.append(i["id"])
    for p in reading_passages():
        ids.append(p["id"])
    for i in reading_items():
        ids.append(i["id"])
    return ids


#: Batas tahap kata benda yang dibuatkan soal partikel otomatis. Dibatasi
#: supaya modul tata bahasa tidak kebanjiran latihan mekanis.
PARTICLE_MAX_STAGE = 4


def particle_card_id(entry: dict) -> str:
    return f"{entry['id']}-pt"


def counter_card_id(counter: dict) -> str:
    return f"{counter['id']}-n"


def syllable_card_id(letter: dict) -> str:
    """Id kartu soal penyusunan blok suku kata yang dibuat dari sebuah huruf."""
    return f"{letter['id']}-syl"


__all__ = [
    "CAT_LABELS",
    "DATA_DIR",
    "MAX_STAGE",
    "MODULE_FILES",
    "PARTICLE_MAX_STAGE",
    "POS_LABELS",
    "POS_VALUES",
    "ROOT",
    "all_card_ids",
    "counter_card_id",
    "counters",
    "grammar_items",
    "grammar_topics",
    "hangeul_batchim",
    "hangeul_items",
    "hangeul_letters",
    "hangeul_rules",
    "load",
    "load_all",
    "number_items",
    "number_systems",
    "numeral_by_value",
    "numerals",
    "particle_card_id",
    "reading_items",
    "reading_levels",
    "reading_passages",
    "speech_honorifics",
    "speech_items",
    "speech_levels",
    "speech_notes",
    "syllable_card_id",
    "syllable_structure",
    "vocab_entries",
    "vocab_nouns",
]
