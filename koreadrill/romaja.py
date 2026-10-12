"""Alih huruf Latin menurut Romanisasi Revisi (RR, 국어의 로마자 표기법).

RR adalah sistem resmi Korea Selatan sejak 2000; itulah tulisan yang Anda
lihat di papan nama jalan dan peta: Seoul, Busan, Gimpo, Hangang.

Dua hal penting tentang RR yang membuat berkas ini tidak sesederhana tabel:

1. RR mengikuti BUNYI, bukan huruf. 한국어 ditulis hangugeo, bukan hanguk-eo,
   karena bunyinya 한구거. Karena itu fungsi di sini memanggil
   pronounce.pronounce() lebih dahulu, sehingga aturan pelafalan hanya
   ditulis di satu tempat.
2. Pengerasan (경음화) TIDAK dituliskan. 학교 ditulis hakgyo walaupun
   dibunyikan 학꾜, dan 압구정 ditulis Apgujeong. Karena itu pemanggilannya
   memakai `tensify=False`.

Alih huruf di proyek ini MATI secara bawaan, sama seperti versi Bahasa Arab.
Alasannya sama: penyangga Latin membuat mata berhenti membaca Hangeul, dan
Hangeul justru bagian termudah dari Bahasa Korea. Pakailah sebagai pemeriksa
bacaan, bukan sebagai cara menghafal.
"""

from __future__ import annotations

from .hangeul import CONSONANT_NAMES, V_INDEX, decompose, is_syllable
from .pronounce import pronounce

#: Huruf awal suku kata. ㅇ tidak berbunyi, jadi kosong.
INITIAL = {
    "ㄱ": "g", "ㄲ": "kk", "ㄴ": "n", "ㄷ": "d", "ㄸ": "tt", "ㄹ": "r",
    "ㅁ": "m", "ㅂ": "b", "ㅃ": "pp", "ㅅ": "s", "ㅆ": "ss", "ㅇ": "",
    "ㅈ": "j", "ㅉ": "jj", "ㅊ": "ch", "ㅋ": "k", "ㅌ": "t", "ㅍ": "p",
    "ㅎ": "h",
}

#: Batchim. Setelah mesin pelafalan bekerja hanya tujuh yang tersisa, tetapi
#: tabelnya dilengkapi supaya fungsi alih huruf literal juga bisa dipakai.
FINAL = {
    "": "", "ㄱ": "k", "ㄲ": "k", "ㄳ": "k", "ㄴ": "n", "ㄵ": "n", "ㄶ": "n",
    "ㄷ": "t", "ㄹ": "l", "ㄺ": "k", "ㄻ": "m", "ㄼ": "l", "ㄽ": "l",
    "ㄾ": "l", "ㄿ": "p", "ㅀ": "l", "ㅁ": "m", "ㅂ": "p", "ㅄ": "p",
    "ㅅ": "t", "ㅆ": "t", "ㅇ": "ng", "ㅈ": "t", "ㅊ": "t", "ㅋ": "k",
    "ㅌ": "t", "ㅍ": "p", "ㅎ": "t",
}

VOWEL = {
    "ㅏ": "a", "ㅐ": "ae", "ㅑ": "ya", "ㅒ": "yae", "ㅓ": "eo", "ㅔ": "e",
    "ㅕ": "yeo", "ㅖ": "ye", "ㅗ": "o", "ㅘ": "wa", "ㅙ": "wae", "ㅚ": "oe",
    "ㅛ": "yo", "ㅜ": "u", "ㅝ": "wo", "ㅞ": "we", "ㅟ": "wi", "ㅠ": "yu",
    "ㅡ": "eu", "ㅢ": "ui", "ㅣ": "i",
}

_VOKAL_LATIN = set("aeiou")


def _syllable(l: str, v: str, t: str, *, prev_final: str) -> str:
    awal = INITIAL[l]
    # ㄹㄹ ditulis ll, bukan lr: 설날 -> seollal, 신라 -> silla.
    if l == "ㄹ" and prev_final == "ㄹ":
        awal = "l"
    return awal + VOWEL[v] + FINAL[t]


def romanize(text: str, *, apply_rules: bool = True) -> str:
    """Alih huruf satu kata atau kalimat.

    `apply_rules=False` mengalihhurufkan tulisannya apa adanya (한국어 menjadi
    hangukeo). Berguna untuk memperlihatkan perbedaan tulisan dan bunyi, tidak
    untuk dipakai sebagai alih huruf yang benar.
    """
    sumber = pronounce(text, tensify=False) if apply_rules else text
    keping: list[str] = []
    prev_final = ""
    for ch in sumber:
        if not is_syllable(ch):
            keping.append(ch)
            prev_final = ""
            continue
        l, v, t = decompose(ch)
        bagian = _syllable(l, v, t, prev_final=prev_final)
        # Tanda hubung hanya dipasang bila tanpa tanda itu bacaannya rancu,
        # misalnya 중앙 -> jung-ang (tanpa tanda bisa terbaca jun-gang).
        if keping and keping[-1].endswith("ng") and bagian[:1] in _VOKAL_LATIN:
            keping.append("-")
        keping.append(bagian)
        prev_final = t
    return "".join(keping)


def romanize_jamo(j: str) -> str:
    """Alih huruf satu huruf yang berdiri sendiri.

    Huruf mati punya dua nilai: sebagai huruf awal dan sebagai batchim
    (ㄱ berbunyi g di awal dan k di akhir), sehingga keduanya ditampilkan.
    """
    if j in V_INDEX:
        return VOWEL[j]
    awal = INITIAL.get(j)
    akhir = FINAL.get(j)
    if awal is None and akhir is None:
        raise ValueError(f"huruf tidak dikenal: {j!r}")
    if awal is None:
        return akhir or ""
    if akhir in (None, "") or awal == akhir:
        return awal
    # ㅇ tidak berbunyi di awal suku kata; tanda hubung menandainya supaya
    # kolomnya tidak tampak kosong.
    return f"{awal or '-'} / {akhir}"


def name_of(j: str) -> str:
    """Nama huruf dalam Hangeul (기역) untuk ditampilkan bersama alih hurufnya."""
    return CONSONANT_NAMES.get(j, j)


__all__ = ["FINAL", "INITIAL", "VOWEL", "name_of", "romanize", "romanize_jamo"]
