"""Pengujian mesin Hangeul: komposisi suku kata, batchim, partikel, dan
kebersihan teks Korea di seluruh data."""

from __future__ import annotations

import pytest

from koreadrill import dataio
from koreadrill.hangeul import (
    BASE,
    L_LIST,
    LAST,
    T_LIST,
    V_LIST,
    compose,
    decompose,
    ends_with_batchim,
    is_hangeul_text,
    is_jamo,
    is_nfc,
    is_syllable,
    jamo_name,
    latin_letters,
    particle,
    syllable_count,
)

#: Field yang memuat teks Korea pada setiap modul, beserta cara mengambilnya.
KO_FIELDS = {
    "hangeul": lambda d: (
        [(x["id"], x["example"]["ko"]) for x in d["letters"]]
        + [(b["id"], e["ko"]) for b in d["batchim"] for e in b["examples"]]
        + [(r["id"], e["ko"]) for r in d["rules"] for e in r["examples"]]
    ),
    "vocab": lambda d: (
        [(e["id"], e["ko"]) for e in d["entries"]]
        + [(e["id"], e["haeyo"]) for e in d["entries"] if e.get("haeyo")]
        + [(e["id"], e["example"]["ko"]) for e in d["entries"]]
    ),
    "grammar": lambda d: [
        (t["id"], e["ko"]) for t in d["topics"] for e in t["examples"]
    ],
    "numbers": lambda d: (
        [(c["id"], c["example"]["ko"]) for c in d["counters"]]
        + [(n["id"], n["sino"]) for n in d["numerals"]]
        + [(n["id"], n["native"]) for n in d["numerals"] if n["native"]]
    ),
    "reading": lambda d: (
        [(p["id"], p["ko"]) for p in d["passages"]]
        + [(i["id"], i["ko"]) for i in d["items"]]
    ),
    "speech": lambda d: (
        [(h["id"], h["plain"]) for h in d["honorifics"]]
        + [(h["id"], h["honorific"]) for h in d["honorifics"]]
        + [(h["id"], h["example"]["ko"]) for h in d["honorifics"]]
        + [(s["id"], s["example"]["ko"]) for s in d["levels"]]
    ),
}


# ------------------------------------------------------- aritmetika blok ---

def test_komposisi_dan_dekomposisi_bolak_balik():
    """Setiap suku kata Hangeul yang mungkin harus bisa dipecah dan disusun ulang."""
    for code in range(BASE, LAST + 1):
        ch = chr(code)
        l, v, t = decompose(ch)
        assert compose(l, v, t) == ch


def test_jumlah_huruf_sesuai_tabel_unicode():
    assert len(L_LIST) == 19
    assert len(V_LIST) == 21
    assert len(T_LIST) == 28
    assert T_LIST[0] == ""
    # 19 x 21 x 28 adalah jumlah seluruh blok suku kata Hangeul di Unicode.
    assert len(L_LIST) * len(V_LIST) * len(T_LIST) == LAST - BASE + 1


@pytest.mark.parametrize(
    "ch,bagian",
    [
        ("가", ("ㄱ", "ㅏ", "")),
        ("한", ("ㅎ", "ㅏ", "ㄴ")),
        ("깊", ("ㄱ", "ㅣ", "ㅍ")),
        ("값", ("ㄱ", "ㅏ", "ㅄ")),
        ("왕", ("ㅇ", "ㅘ", "ㅇ")),
        ("힣", ("ㅎ", "ㅣ", "ㅎ")),
    ],
)
def test_dekomposisi_kasus_dipatok(ch, bagian):
    assert decompose(ch) == bagian


def test_bukan_suku_kata_ditolak():
    for ch in ("ㄱ", "A", "1", " ", "一"):
        assert not is_syllable(ch)
        with pytest.raises(ValueError):
            decompose(ch)


def test_compose_menolak_huruf_yang_salah_tempat():
    with pytest.raises(ValueError):
        compose("ㅏ", "ㅏ")          # vokal di tempat huruf awal
    with pytest.raises(ValueError):
        compose("ㄱ", "ㄱ")          # huruf mati di tempat vokal
    with pytest.raises(ValueError):
        compose("ㄱ", "ㅏ", "ㄸ")    # ㄸ tidak pernah menjadi batchim


def test_nama_huruf():
    assert jamo_name("ㄱ") == "기역"
    assert jamo_name("ㅎ") == "히읗"
    assert jamo_name("ㅏ") == "아"
    assert jamo_name("ㅘ") == "와"
    assert jamo_name("ㄺ") == "리을기역"


def test_is_jamo():
    assert is_jamo("ㄱ") and is_jamo("ㅏ") and is_jamo("ㄳ")
    assert not is_jamo("가") and not is_jamo("a")


def test_syllable_count():
    assert syllable_count("한국어") == 3
    assert syllable_count("한국 사람") == 4
    assert syllable_count("ㄱㄴㄷ") == 0


# --------------------------------------------------------------- partikel ---

@pytest.mark.parametrize(
    "kata,berbatchim",
    [("책", True), ("학교", False), ("물", True), ("저", False),
     ("선생님", True), ("친구", False), ("밥", True), ("커피", False)],
)
def test_deteksi_batchim(kata, berbatchim):
    assert ends_with_batchim(kata) is berbatchim


@pytest.mark.parametrize(
    "kata,topik,subjek,objek",
    [
        ("책", "은", "이", "을"),
        ("학교", "는", "가", "를"),
        ("물", "은", "이", "을"),
        ("친구", "는", "가", "를"),
    ],
)
def test_pemilihan_partikel(kata, topik, subjek, objek):
    assert particle(kata, "은", "는") == topik
    assert particle(kata, "이", "가") == subjek
    assert particle(kata, "을", "를") == objek


def test_partikel_mengabaikan_tanda_baca_di_akhir():
    assert particle("책.", "은", "는") == "은"
    assert particle("학교!", "은", "는") == "는"


# ----------------------------------------------- kebersihan teks di data ---

def test_semua_teks_korea_berbentuk_nfc():
    salah = []
    for nama, ambil in KO_FIELDS.items():
        for ident, teks in ambil(dataio.load(nama)):
            if not is_nfc(teks):
                salah.append(f"{nama}:{ident} = {teks!r}")
    assert not salah, f"teks bukan NFC (suku kata terpisah): {salah}"


def test_tidak_ada_huruf_latin_di_field_korea():
    salah = []
    for nama, ambil in KO_FIELDS.items():
        for ident, teks in ambil(dataio.load(nama)):
            if latin_letters(teks):
                salah.append(f"{nama}:{ident} = {teks!r}")
    assert not salah, f"huruf Latin di dalam field Korea: {salah}"


def test_field_korea_hanya_memuat_suku_kata_utuh():
    """Tidak boleh ada huruf tunggal (ㄱ, ㅏ) yang tercecer di dalam kata.

    Huruf tunggal sah hanya pada field yang memang membahas huruf, yaitu
    letters[].jamo dan batchim[].letters; keduanya tidak ikut diperiksa di sini.
    """
    salah = []
    for nama, ambil in KO_FIELDS.items():
        for ident, teks in ambil(dataio.load(nama)):
            if not is_hangeul_text(teks, allow_jamo=False):
                salah.append(f"{nama}:{ident} = {teks!r}")
    assert not salah, f"field Korea memuat karakter yang tidak diizinkan: {salah}"


def test_field_huruf_memuat_huruf_tunggal_yang_sah():
    for x in dataio.hangeul_letters():
        assert is_jamo(x["jamo"]), f"{x['id']}: {x['jamo']!r} bukan huruf tunggal"
    for b in dataio.hangeul_batchim():
        for j in b["letters"].split():
            assert is_jamo(j), f"{b['id']}: {j!r} bukan huruf tunggal"
