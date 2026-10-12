"""Pengujian skema data: id unik, tidak ada field kosong, nilai sah."""

from __future__ import annotations

import re

import pytest

from koreadrill import dataio

ID_PATTERNS = {
    "hangeul_letter": re.compile(r"^h\d{2}$"),
    "hangeul_batchim": re.compile(r"^b\d{2}$"),
    "hangeul_rule": re.compile(r"^pr\d{2}$"),
    "hangeul_item": re.compile(r"^hg-q\d{2}$"),
    "vocab": re.compile(r"^v\d{3}$"),
    "grammar_topic": re.compile(r"^g\d{2}$"),
    "grammar_item": re.compile(r"^g\d{2}-\d{2}$"),
    "numeral": re.compile(r"^n\d+$"),
    "counter": re.compile(r"^c\d{2}$"),
    "number_item": re.compile(r"^num-q\d{2}$"),
    "reading_passage": re.compile(r"^rp\d{2}$"),
    "reading_item": re.compile(r"^rd-(q|m)\d{2}$"),
    "speech_honorific": re.compile(r"^sp\d{2}$"),
    "speech_item": re.compile(r"^sp-q\d{2}$"),
}

#: Field yang boleh bernilai null. Field lain tidak boleh null MAUPUN kosong.
NULLABLE = {
    "haeyo", "hanja", "alt", "prompt_ko", "native", "native_attr", "note",
    "explain", "caveats", "quran_examples",
}


def _check_no_empty(obj, where: str, problems: list[str]) -> None:
    """Rekursif: tolak string kosong dan nilai null pada field wajib."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if v is None and k not in NULLABLE:
                problems.append(f"{where}.{k} bernilai null")
            elif isinstance(v, str) and not v.strip() and k not in NULLABLE:
                problems.append(f"{where}.{k} berupa teks kosong")
            else:
                _check_no_empty(v, f"{where}.{k}", problems)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, str) and not v.strip():
                problems.append(f"{where}[{i}] berupa teks kosong")
            else:
                _check_no_empty(v, f"{where}[{i}]", problems)


def test_semua_id_unik_di_seluruh_modul():
    ids = dataio.all_card_ids()
    ids += [t["id"] for t in dataio.grammar_topics()]
    duplikat = sorted({i for i in ids if ids.count(i) > 1})
    assert not duplikat, f"id ganda: {duplikat}"


@pytest.mark.parametrize(
    "kind,items",
    [
        ("hangeul_letter", dataio.hangeul_letters()),
        ("hangeul_batchim", dataio.hangeul_batchim()),
        ("hangeul_rule", dataio.hangeul_rules()),
        ("hangeul_item", dataio.hangeul_items()),
        ("vocab", dataio.vocab_entries()),
        ("grammar_topic", dataio.grammar_topics()),
        ("grammar_item", dataio.grammar_items()),
        ("numeral", dataio.numerals()),
        ("counter", dataio.counters()),
        ("number_item", dataio.number_items()),
        ("reading_passage", dataio.reading_passages()),
        ("reading_item", dataio.reading_items()),
        ("speech_honorific", dataio.speech_honorifics()),
        ("speech_item", dataio.speech_items()),
    ],
)
def test_format_id(kind, items):
    pola = ID_PATTERNS[kind]
    salah = [i["id"] for i in items if not pola.match(i["id"])]
    assert not salah, f"{kind}: id tidak sesuai pola {pola.pattern}: {salah}"


def test_tidak_ada_field_kosong():
    problems: list[str] = []
    for nama in dataio.MODULE_FILES:
        _check_no_empty(dataio.load(nama), nama, problems)
    assert not problems, "\n".join(problems)


def test_kelas_kata_sah():
    salah = [
        (e["id"], e["pos"]) for e in dataio.vocab_entries()
        if e["pos"] not in dataio.POS_VALUES
    ]
    assert not salah, f"kelas kata tidak dikenal: {salah}"


def test_kategori_punya_label():
    tanpa = sorted({e["cat"] for e in dataio.vocab_entries()} - set(dataio.CAT_LABELS))
    assert not tanpa, f"kategori tanpa label di dataio.CAT_LABELS: {tanpa}"


def test_kata_kerja_dan_sifat_punya_bentuk_haeyo():
    kurang = [
        e["id"] for e in dataio.vocab_entries()
        if e["pos"] in ("동사", "형용사") and not e.get("haeyo")
    ]
    assert not kurang, f"kata kerja/sifat tanpa bentuk 해요: {kurang}"


def test_kelas_kata_lain_tidak_punya_haeyo():
    lebih = [
        e["id"] for e in dataio.vocab_entries()
        if e["pos"] not in ("동사", "형용사") and e.get("haeyo")
    ]
    assert not lebih, f"bukan kata kerja tetapi punya bentuk 해요: {lebih}"


def test_setiap_tahap_terisi():
    for stage in range(1, dataio.MAX_STAGE + 1):
        kata = [e for e in dataio.vocab_entries() if e["stage"] == stage]
        assert kata, f"tahap {stage} tidak punya kosakata"
    for stage in range(1, dataio.MAX_STAGE + 1):
        topik = [t for t in dataio.grammar_topics() if t["stage"] == stage]
        assert topik, f"tahap {stage} tidak punya topik tata bahasa"


def test_setiap_level_baca_terisi():
    for level in (1, 2, 3):
        butir = dataio.reading_passages(level=level) + dataio.reading_items(level=level)
        assert butir, f"level {level} tidak punya butir latihan"


def test_tahap_dalam_jangkauan():
    salah = []
    for nama, items in (
        ("huruf", dataio.hangeul_letters()),
        ("kosakata", dataio.vocab_entries()),
        ("tata bahasa", dataio.grammar_topics()),
        ("angka", dataio.numerals()),
        ("penggolong", dataio.counters()),
        ("baca", dataio.reading_items()),
        ("kesantunan", dataio.speech_honorifics()),
    ):
        for i in items:
            if not 1 <= i["stage"] <= dataio.MAX_STAGE:
                salah.append((nama, i["id"], i["stage"]))
    assert not salah, f"tahap di luar 1-{dataio.MAX_STAGE}: {salah}"


def test_setiap_topik_tata_bahasa_punya_lima_soal():
    kurang = [t["id"] for t in dataio.grammar_topics() if len(t["items"]) != 5]
    assert not kurang, f"topik dengan jumlah soal bukan 5: {kurang}"


def test_setiap_topik_punya_catatan_dan_contoh():
    kurang = [
        t["id"] for t in dataio.grammar_topics()
        if len(t["caveats"]) < 2 or len(t["examples"]) < 3
    ]
    assert not kurang, f"topik dengan catatan atau contoh terlalu sedikit: {kurang}"


def test_jumlah_huruf_hangeul_lengkap():
    letters = dataio.hangeul_letters()
    konsonan = [x for x in letters if x["kind"] == "konsonan"]
    vokal = [x for x in letters if x["kind"] == "vokal"]
    assert len(konsonan) == 19, f"harus ada 19 huruf mati, ada {len(konsonan)}"
    assert len(vokal) == 21, f"harus ada 21 vokal, ada {len(vokal)}"
    assert len({x["jamo"] for x in letters}) == 40


def test_sistem_penggolong_sah():
    salah = [c["id"] for c in dataio.counters() if c["system"] not in ("native", "sino")]
    assert not salah, f"sistem angka tidak dikenal: {salah}"


def test_nilai_contoh_penggolong_ada_di_daftar_angka():
    hilang = [
        (c["id"], c["example_value"]) for c in dataio.counters()
        if dataio.numeral_by_value(c["example_value"]) is None
    ]
    assert not hilang, f"nilai contoh penggolong tidak ada di numerals: {hilang}"
