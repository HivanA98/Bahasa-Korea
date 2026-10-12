"""Pengujian alih huruf Revisi (RR).

Kasus di bawah dipatok dari contoh resmi dan dari pemakaian baku, bukan dari
keluaran mesin yang sedang diuji.
"""

from __future__ import annotations

import pytest

from koreadrill import dataio
from koreadrill.hangeul import T_INDEX, V_INDEX
from koreadrill.romaja import FINAL, INITIAL, VOWEL, romanize, romanize_jamo

KASUS = [
    ("한국", "hanguk"),
    ("서울", "seoul"),
    ("부산", "busan"),
    ("김치", "gimchi"),
    ("한국어", "hangugeo"),      # mengikuti bunyi, bukan tulisan
    ("좋아요", "joayo"),
    ("감사합니다", "gamsahamnida"),
    ("안녕하세요", "annyeonghaseyo"),
    ("학교", "hakgyo"),          # pengerasan TIDAK dituliskan
    ("식당", "sikdang"),
    ("설날", "seollal"),         # ㄹㄹ ditulis ll, bukan lr
    ("신라", "silla"),
    ("있어요", "isseoyo"),
    ("꽃이", "kkochi"),
    ("같이", "gachi"),
    ("중앙", "jung-ang"),        # tanda hubung untuk menghindari jun-gang
    ("영어", "yeong-eo"),
    ("한글", "hangeul"),
    ("의사", "uisa"),
    ("떡볶이", "tteokbokki"),
    ("비빔밥", "bibimbap"),
    ("읽어요", "ilgeoyo"),
    ("못해요", "motaeyo"),
]


@pytest.mark.parametrize("ko,latin", KASUS)
def test_alih_huruf_kasus_dipatok(ko, latin):
    assert romanize(ko) == latin


def test_tidak_ada_hangeul_yang_tertinggal():
    sisa = []
    for e in dataio.vocab_entries():
        for teks in (e["ko"], e["example"]["ko"]):
            hasil = romanize(teks)
            if any("가" <= ch <= "힣" for ch in hasil):
                sisa.append((teks, hasil))
    assert not sisa, f"masih ada suku kata Hangeul di hasil alih huruf: {sisa}"


def test_alih_huruf_tanpa_aturan_mengikuti_tulisan():
    """apply_rules=False memperlihatkan tulisannya apa adanya, untuk
    membandingkan tulisan dan bunyi."""
    assert romanize("한국어", apply_rules=False) == "hangukeo"
    assert romanize("밥을", apply_rules=False) == "bapeul"
    # Tabel batchim tetap yang dipakai, sehingga ㅎ di batchim muncul sebagai t
    # (좋아요 menjadi jotayo). Mode ini hanya alat bantu untuk memperlihatkan
    # selisih tulisan dan bunyi, bukan alih huruf yang benar.
    assert romanize("좋아요", apply_rules=False) == "jotayo"


def test_alih_huruf_huruf_tunggal():
    assert romanize_jamo("ㄱ") == "g / k"
    assert romanize_jamo("ㄴ") == "n"
    assert romanize_jamo("ㅇ") == "- / ng"
    assert romanize_jamo("ㅏ") == "a"
    assert romanize_jamo("ㅓ") == "eo"
    assert romanize_jamo("ㅡ") == "eu"
    assert romanize_jamo("ㅢ") == "ui"
    with pytest.raises(ValueError):
        romanize_jamo("A")


def test_setiap_vokal_punya_alih_huruf():
    hilang = sorted(set(V_INDEX) - set(VOWEL))
    assert not hilang, f"vokal tanpa alih huruf: {hilang}"


def test_setiap_huruf_punya_alih_huruf_awal_dan_akhir():
    for x in dataio.hangeul_letters():
        j = x["jamo"]
        if x["kind"] == "vokal":
            assert j in VOWEL
        else:
            assert j in INITIAL, f"{j} tidak ada di tabel huruf awal"
            # ㄸ, ㅃ, dan ㅉ tidak pernah menjadi batchim, sehingga wajar bila
            # tidak ada di tabel batchim.
            if j in T_INDEX:
                assert j in FINAL, f"{j} tidak ada di tabel batchim"


def test_spasi_dan_tanda_baca_dipertahankan():
    assert romanize("안녕하세요, 저는 이반이에요.") == "annyeonghaseyo, jeoneun ibanieyo."
