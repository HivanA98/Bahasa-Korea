"""Hangeul: komposisi dan dekomposisi suku kata, nama huruf, validator.

Satu suku kata Hangeul adalah SATU karakter Unicode yang tersusun dari dua
atau tiga huruf (jamo):

    초성 (awal, wajib) + 중성 (vokal, wajib) + 종성 (akhir/batchim, boleh kosong)

Letaknya dihitung, bukan dicari di tabel:

    kode = 0xAC00 + (L * 21 + V) * 28 + T

dengan L indeks 19 huruf awal, V indeks 21 vokal, dan T indeks 28 batchim
(indeks 0 berarti tanpa batchim). Seluruh modul lain memakai fungsi di berkas
ini, sehingga aritmetika di atas hanya ditulis satu kali.

Huruf tunggal diwakili oleh "compatibility jamo" (ㄱ U+3131 dan seterusnya),
yaitu bentuk yang tampil wajar bila ditulis sendirian. Bentuk conjoining jamo
(U+1100 dst.) tidak dipakai di proyek ini supaya teks tidak pernah tampil
sebagai huruf yang berserakan.
"""

from __future__ import annotations

import unicodedata

BASE = 0xAC00
LAST = 0xD7A3
N_V = 21
N_T = 28

#: 19 huruf awal (초성), berurutan menurut indeks L.
L_LIST = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"

#: 21 vokal (중성), berurutan menurut indeks V.
V_LIST = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"

#: 28 batchim (종성). Indeks 0 adalah "tanpa batchim" dan diwakili string kosong.
T_LIST = ["", *"ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"]

L_INDEX = {j: i for i, j in enumerate(L_LIST)}
V_INDEX = {j: i for i, j in enumerate(V_LIST)}
T_INDEX = {j: i for i, j in enumerate(T_LIST)}

#: 14 huruf dasar dan 5 huruf kembar (쌍자음).
BASIC_CONSONANTS = "ㄱㄴㄷㄹㅁㅂㅅㅇㅈㅊㅋㅌㅍㅎ"
TENSE_CONSONANTS = "ㄲㄸㅃㅆㅉ"

#: 10 vokal dasar dan 11 vokal gabungan.
BASIC_VOWELS = "ㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ"
COMPOUND_VOWELS = "ㅐㅒㅔㅖㅘㅙㅚㅝㅞㅟㅢ"

#: Batchim ganda (겹받침) dan dua huruf penyusunnya. Huruf KEDUA-lah yang
#: berpindah ke suku kata berikutnya saat terjadi penyambungan bunyi (연음),
#: misalnya 읽어 dibaca 일거.
CLUSTERS = {
    "ㄳ": ("ㄱ", "ㅅ"),
    "ㄵ": ("ㄴ", "ㅈ"),
    "ㄶ": ("ㄴ", "ㅎ"),
    "ㄺ": ("ㄹ", "ㄱ"),
    "ㄻ": ("ㄹ", "ㅁ"),
    "ㄼ": ("ㄹ", "ㅂ"),
    "ㄽ": ("ㄹ", "ㅅ"),
    "ㄾ": ("ㄹ", "ㅌ"),
    "ㄿ": ("ㄹ", "ㅍ"),
    "ㅀ": ("ㄹ", "ㅎ"),
    "ㅄ": ("ㅂ", "ㅅ"),
}

#: Nama huruf mati. Nama ini yang dipakai orang Korea saat mengeja.
CONSONANT_NAMES = {
    "ㄱ": "기역", "ㄲ": "쌍기역", "ㄴ": "니은", "ㄷ": "디귿", "ㄸ": "쌍디귿",
    "ㄹ": "리을", "ㅁ": "미음", "ㅂ": "비읍", "ㅃ": "쌍비읍", "ㅅ": "시옷",
    "ㅆ": "쌍시옷", "ㅇ": "이응", "ㅈ": "지읒", "ㅉ": "쌍지읒", "ㅊ": "치읓",
    "ㅋ": "키읔", "ㅌ": "티읕", "ㅍ": "피읖", "ㅎ": "히읗",
}

#: Tanda baca yang diizinkan muncul di dalam field berbahasa Korea.
PUNCT = set(".,?!~…'\"()")


# --------------------------------------------------------------- dasar ---

def is_syllable(ch: str) -> bool:
    """True bila ch satu suku kata Hangeul lengkap (가 sampai 힣)."""
    return len(ch) == 1 and BASE <= ord(ch) <= LAST


def is_jamo(ch: str) -> bool:
    """True bila ch satu huruf Hangeul berdiri sendiri (ㄱ, ㅏ, ㄳ, ...)."""
    return len(ch) == 1 and 0x3131 <= ord(ch) <= 0x3163


def decompose(ch: str) -> tuple[str, str, str]:
    """Pecah satu suku kata menjadi (awal, vokal, batchim).

    Batchim kosong dikembalikan sebagai string kosong.
    """
    if not is_syllable(ch):
        raise ValueError(f"bukan suku kata Hangeul: {ch!r}")
    code = ord(ch) - BASE
    t = code % N_T
    v = (code // N_T) % N_V
    l = code // (N_T * N_V)
    return L_LIST[l], V_LIST[v], T_LIST[t]


def compose(l: str, v: str, t: str = "") -> str:
    """Susun satu suku kata dari huruf awal, vokal, dan batchim."""
    if l not in L_INDEX:
        raise ValueError(f"bukan huruf awal yang sah: {l!r}")
    if v not in V_INDEX:
        raise ValueError(f"bukan vokal yang sah: {v!r}")
    if t not in T_INDEX:
        raise ValueError(f"bukan batchim yang sah: {t!r}")
    return chr(BASE + (L_INDEX[l] * N_V + V_INDEX[v]) * N_T + T_INDEX[t])


def jamo_of(text: str) -> list[str]:
    """Deret huruf dari seluruh teks; karakter non-Hangeul dilewatkan apa adanya."""
    out: list[str] = []
    for ch in text:
        if is_syllable(ch):
            l, v, t = decompose(ch)
            out.append(l)
            out.append(v)
            if t:
                out.append(t)
        else:
            out.append(ch)
    return out


def batchim_of(ch: str) -> str:
    """Batchim satu suku kata, atau string kosong."""
    return decompose(ch)[2] if is_syllable(ch) else ""


def has_batchim(ch: str) -> bool:
    return bool(batchim_of(ch))


def ends_with_batchim(word: str) -> bool:
    """Apakah kata berakhir dengan batchim.

    Penentu pilihan partikel: 은/는, 이/가, 을/를, 과/와, 으로/로 semuanya
    bergantung pada ada-tidaknya batchim pada suku kata terakhir.
    """
    for ch in reversed(word):
        if is_syllable(ch):
            return has_batchim(ch)
    return False


def particle(word: str, with_batchim: str, without_batchim: str) -> str:
    """Pilih bentuk partikel yang sesuai untuk sebuah kata.

        particle("책", "은", "는")   -> "은"
        particle("학교", "은", "는") -> "는"
    """
    return with_batchim if ends_with_batchim(word) else without_batchim


def jamo_name(j: str) -> str:
    """Nama sebuah huruf. Vokal namanya bunyinya sendiri (ㅏ dibaca 아)."""
    if j in CONSONANT_NAMES:
        return CONSONANT_NAMES[j]
    if j in V_INDEX:
        return compose("ㅇ", j)
    if j in CLUSTERS:
        a, b = CLUSTERS[j]
        return f"{CONSONANT_NAMES[a]}{CONSONANT_NAMES[b]}"
    raise ValueError(f"huruf tidak dikenal: {j!r}")


# ----------------------------------------------------------- validator ---

def is_hangeul_text(text: str, *, allow_jamo: bool = False) -> bool:
    """True bila teks hanya memuat suku kata Hangeul, spasi, dan tanda baca.

    `allow_jamo` dipakai untuk field yang memang memuat huruf tunggal,
    misalnya daftar huruf di data/hangeul.json.
    """
    for ch in text:
        if is_syllable(ch) or ch.isspace() or ch in PUNCT:
            continue
        if allow_jamo and is_jamo(ch):
            continue
        if ch.isdigit():
            continue
        return False
    return True


def latin_letters(text: str) -> set[str]:
    """Huruf Latin yang tersisa di dalam teks. Kosong berarti bersih."""
    return {ch for ch in text if ("a" <= ch.lower() <= "z")}


def is_nfc(text: str) -> bool:
    """True bila teks sudah dalam bentuk NFC (suku kata tergabung).

    Teks hasil tempel dari macOS sering berbentuk NFD, yaitu suku kata yang
    tersimpan sebagai deretan jamo. Tampilannya mirip, tetapi perbandingan
    string dan pencarian akan gagal.
    """
    return unicodedata.normalize("NFC", text) == text


def normalize(text: str) -> str:
    """Bakukan ke NFC dan rapatkan spasi ganda."""
    return " ".join(unicodedata.normalize("NFC", text).split())


def syllable_count(text: str) -> int:
    return sum(1 for ch in text if is_syllable(ch))


__all__ = [
    "BASE",
    "BASIC_CONSONANTS",
    "BASIC_VOWELS",
    "CLUSTERS",
    "COMPOUND_VOWELS",
    "CONSONANT_NAMES",
    "L_LIST",
    "LAST",
    "PUNCT",
    "T_LIST",
    "TENSE_CONSONANTS",
    "V_LIST",
    "batchim_of",
    "compose",
    "decompose",
    "ends_with_batchim",
    "has_batchim",
    "is_hangeul_text",
    "is_jamo",
    "is_nfc",
    "is_syllable",
    "jamo_name",
    "jamo_of",
    "latin_letters",
    "normalize",
    "particle",
    "syllable_count",
]
