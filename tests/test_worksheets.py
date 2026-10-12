"""Pengujian lembar kerja: kunci terpisah, bagian lengkap, isi berasal dari data."""

from __future__ import annotations

import os
import re

import pytest

from conftest import ROOT
from koreadrill import dataio
from koreadrill.hangeul import particle
from koreadrill.pronounce import pronounce

WS_DIR = os.path.join(ROOT, "worksheets")
KEY_DIR = os.path.join(WS_DIR, "answers")

NOMOR = [f"{n:02d}" for n in range(1, 13)]
BAGIAN = [
    "## A. Hangeul",
    "## B. Tulis arti kata",
    "## C. Tulis kata Korea",
    "## D. Tata bahasa",
    "## E. Partikel",
    "## F. Angka dan penggolong",
    "## G. Pelafalan",
]


def _ws(n: str) -> str:
    return open(os.path.join(WS_DIR, f"ws-{n}.md"), encoding="utf-8").read()


def _key(n: str) -> str:
    return open(os.path.join(KEY_DIR, f"ws-{n}-kunci.md"), encoding="utf-8").read()


@pytest.mark.parametrize("n", NOMOR)
def test_lembar_dan_kunci_ada(n):
    assert os.path.exists(os.path.join(WS_DIR, f"ws-{n}.md"))
    assert os.path.exists(os.path.join(KEY_DIR, f"ws-{n}-kunci.md"))


@pytest.mark.parametrize("n", NOMOR)
def test_semua_bagian_ada(n):
    teks = _ws(n)
    hilang = [b for b in BAGIAN if b not in teks]
    assert not hilang, f"ws-{n}: bagian hilang: {hilang}"


@pytest.mark.parametrize("n", NOMOR)
def test_lembar_kerja_tidak_memuat_kunci(n):
    """Jawaban tidak boleh bocor ke lembar soal."""
    teks = _ws(n)
    assert "**" not in teks, f"ws-{n}: ada penanda jawaban (**) di lembar soal"
    assert "Kunci jawaban:" in teks, f"ws-{n}: tidak menunjuk ke berkas kunci"
    assert "Jawaban: ____" in teks, f"ws-{n}: tidak ada tempat menulis jawaban"


@pytest.mark.parametrize("n", NOMOR)
def test_kunci_menunjuk_kembali_ke_soalnya(n):
    assert f"worksheets/ws-{n}.md" in _key(n)


@pytest.mark.parametrize("n", NOMOR)
def test_kunci_memuat_jawaban_pilihan_ganda(n):
    """Setiap soal pilihan ganda di lembar harus punya jawaban berhuruf di kunci."""
    jumlah_soal = len(re.findall(r"^   Jawaban: ____$", _ws(n), flags=re.M))
    jumlah_kunci = len(re.findall(r"^\d+\. \*\*[a-d]\*\* — ", _key(n), flags=re.M))
    assert jumlah_soal == jumlah_kunci, (
        f"ws-{n}: {jumlah_soal} soal pilihan ganda tetapi {jumlah_kunci} kunci"
    )


@pytest.mark.parametrize("n", NOMOR)
def test_butir_kosakata_berasal_dari_data(n):
    """Setiap kata pada bagian B harus benar-benar ada di data/vocab.json."""
    teks = _ws(n)
    bagian = teks.split("## B.")[1].split("## C.")[0]
    kata = re.findall(r"^\| \d+ \| (\S+) \|", bagian, flags=re.M)
    assert kata, f"ws-{n}: bagian B kosong"
    semua = {e["ko"] for e in dataio.vocab_entries()}
    asing = [k for k in kata if k not in semua]
    assert not asing, f"ws-{n}: kata tidak ada di data: {asing}"


@pytest.mark.parametrize("n", NOMOR)
def test_kunci_partikel_dihitung_dari_batchim(n):
    """Kunci bagian partikel harus cocok dengan hangeul.particle()."""
    bagian = _key(n).split("## E. Partikel")[1].split("## F.")[0]
    baris = re.findall(r"^\| \d+ \| (\S+) \| (\S+) \| (\S+) \|", bagian, flags=re.M)
    assert baris, f"ws-{n}: kunci partikel kosong"
    pasangan = {"topik": ("은", "는"), "subjek": ("이", "가"), "objek": ("을", "를")}
    for kata, jenis, jawaban in baris:
        dengan, tanpa = pasangan[jenis]
        assert jawaban == kata + particle(kata, dengan, tanpa), (
            f"ws-{n}: {kata} + {jenis} seharusnya {kata + particle(kata, dengan, tanpa)}, "
            f"tertulis {jawaban}"
        )


@pytest.mark.parametrize("n", NOMOR)
def test_kunci_pelafalan_sama_dengan_mesin(n):
    bagian = _key(n).split("## G. Pelafalan")[1]
    baris = re.findall(r"^\d+\. (\S+) dibunyikan \*\*\[(\S+)\]\*\*", bagian, flags=re.M)
    assert baris, f"ws-{n}: kunci pelafalan kosong"
    for kata, lafal in baris:
        assert pronounce(kata) == lafal, (
            f"ws-{n}: {kata} seharusnya [{pronounce(kata)}], tertulis [{lafal}]"
        )


def test_daftar_isi_menyebut_semua_lembar():
    index = open(os.path.join(WS_DIR, "README.md"), encoding="utf-8").read()
    for n in NOMOR:
        assert f"ws-{n}.md" in index
        assert f"ws-{n}-kunci.md" in index


def test_lembar_tersebar_merata_antar_tahap():
    tahap = []
    for n in NOMOR:
        m = re.search(r"tahap (\d)", _ws(n))
        assert m, f"ws-{n}: judul tidak menyebut tahap"
        tahap.append(int(m.group(1)))
    for s in range(1, dataio.MAX_STAGE + 1):
        assert tahap.count(s) == 2, f"tahap {s} punya {tahap.count(s)} lembar, seharusnya 2"
