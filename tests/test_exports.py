"""Pengujian ekspor: hasil di repositori harus sama dengan yang dihasilkan ulang.

Berkas di data/csv/, anki/, worksheets/, dan webdata.js adalah TURUNAN dari
data/*.json. Pengujian ini membuat ulang semuanya ke folder sementara lalu
membandingkannya dengan yang tersimpan. Bila berbeda, berarti data sudah
berubah tetapi ekspornya belum dibuat ulang.
"""

from __future__ import annotations

import csv
import json
import os
import re

import pytest

from conftest import ROOT, load_tool

CSV_DIR = os.path.join(ROOT, "data", "csv")
ANKI_DIR = os.path.join(ROOT, "anki")
WS_DIR = os.path.join(ROOT, "worksheets")
KEY_DIR = os.path.join(WS_DIR, "answers")
WEBDATA = os.path.join(ROOT, "webdata.js")


def _regenerate_exports(tmp_path):
    mod = load_tool("build_exports")
    mod.CSV_DIR = str(tmp_path / "csv")
    mod.ANKI_DIR = str(tmp_path / "anki")
    mod.main()
    return str(tmp_path / "csv"), str(tmp_path / "anki")


def _regenerate_worksheets(tmp_path):
    mod = load_tool("build_worksheets")
    mod.WS_DIR = str(tmp_path / "ws")
    mod.KEY_DIR = str(tmp_path / "ws" / "answers")
    mod.main()
    return str(tmp_path / "ws"), str(tmp_path / "ws" / "answers")


def _regenerate_web(tmp_path):
    mod = load_tool("build_web")
    mod.OUT = str(tmp_path / "webdata.js")
    mod.main()
    return str(tmp_path / "webdata.js")


def _compare_dirs(baru: str, lama: str, label: str, suffix: str | None = None) -> None:
    """Bandingkan isi dua folder.

    `suffix` membatasi perbandingan pada jenis berkas tertentu; anki/ memuat
    README.md yang ditulis tangan dan bukan hasil ekspor.
    """
    def daftar(d: str) -> list[str]:
        return sorted(
            f for f in os.listdir(d)
            if os.path.isfile(os.path.join(d, f)) and (suffix is None or f.endswith(suffix))
        )

    nama_baru = daftar(baru)
    nama_lama = daftar(lama)
    assert nama_baru == nama_lama, (
        f"{label}: daftar berkas berbeda.\nbaru: {nama_baru}\ntersimpan: {nama_lama}"
    )
    beda = []
    for nama in nama_baru:
        a = open(os.path.join(baru, nama), encoding="utf-8").read()
        b = open(os.path.join(lama, nama), encoding="utf-8").read()
        if a != b:
            beda.append(nama)
    assert not beda, (
        f"{label}: berkas berikut tidak mutakhir, jalankan ulang skripnya: {beda}"
    )


def test_ekspor_csv_mutakhir(tmp_path):
    csv_baru, anki_baru = _regenerate_exports(tmp_path)
    _compare_dirs(csv_baru, CSV_DIR, "data/csv")


def test_ekspor_anki_mutakhir(tmp_path):
    csv_baru, anki_baru = _regenerate_exports(tmp_path)
    _compare_dirs(anki_baru, ANKI_DIR, "anki", suffix=".csv")


def test_lembar_kerja_mutakhir(tmp_path):
    ws_baru, key_baru = _regenerate_worksheets(tmp_path)
    _compare_dirs(ws_baru, WS_DIR, "worksheets")
    _compare_dirs(key_baru, KEY_DIR, "worksheets/answers")


def test_webdata_mutakhir(tmp_path):
    baru = _regenerate_web(tmp_path)
    a = open(baru, encoding="utf-8").read()
    b = open(WEBDATA, encoding="utf-8").read()
    assert a == b, "webdata.js tidak mutakhir, jalankan: python tools/build_web.py"


# ------------------------------------------------------------ isi ekspor ---

def _webdata() -> dict:
    teks = open(WEBDATA, encoding="utf-8").read()
    awal = teks.index("{")
    akhir = teks.rindex("}") + 1
    return json.loads(teks[awal:akhir])


def test_webdata_ditulis_sebagai_ascii_murni():
    """Teks Korea ditulis sebagai escape \\uXXXX supaya tidak bergantung pada
    charset yang dikirim peladen."""
    isi = open(WEBDATA, encoding="utf-8").read()
    bukan_ascii = {ch for ch in isi if ord(ch) > 127}
    assert not bukan_ascii, f"webdata.js memuat karakter non-ASCII: {bukan_ascii}"


def test_aplikasi_web_tidak_memakai_fetch():
    """Aplikasi harus tetap jalan saat index.html dibuka langsung (file://)."""
    app = open(os.path.join(ROOT, "app.js"), encoding="utf-8").read()
    # Komentar dibuang lebih dahulu; kata "fetch()" boleh muncul di penjelasan,
    # yang dilarang adalah pemanggilannya.
    kode = re.sub(r"/\*.*?\*/", "", app, flags=re.S)
    kode = re.sub(r"^\s*//.*$", "", kode, flags=re.M)
    assert "fetch(" not in kode, "app.js memakai fetch(), yang gagal di file://"
    html = open(os.path.join(ROOT, "index.html"), encoding="utf-8").read()
    assert "webdata.js" in html


def test_kunci_soal_di_webdata_sama_dengan_data():
    from koreadrill import dataio

    d = _webdata()
    web = {x["id"]: x for x in d["tatabahasa"]}
    for item in dataio.grammar_items():
        w = web[item["id"]]
        assert w["options"] == item["options"]
        assert w["answer"] == item["answer"]

    web_baca = {x["id"]: x for x in d["baca"] if x["kind"] == "soal"}
    for item in dataio.reading_items():
        w = web_baca[item["id"]]
        assert w["options"] == item["options"]
        assert w["answer"] == item["answer"]


def test_lafal_di_webdata_sama_dengan_mesin():
    from koreadrill.pronounce import pronounce

    d = _webdata()
    salah = []
    for x in d["kosakata"]:
        if pronounce(x["ko"]) != x["pron"]:
            salah.append(x["id"])
    for x in d["baca"]:
        if pronounce(x["ko"]) != x["pron"]:
            salah.append(x["id"])
    assert not salah, f"lafal di webdata.js tidak cocok dengan mesin: {salah}"


def test_jumlah_kartu_webdata_cocok_dengan_data():
    from koreadrill import dataio

    d = _webdata()
    assert len(d["kosakata"]) == len(dataio.vocab_entries())
    assert len(d["tatabahasa"]) == len(dataio.grammar_items())
    assert len(d["hangeul"]) == (
        len(dataio.hangeul_letters()) + len(dataio.hangeul_batchim())
        + len(dataio.hangeul_rules()) + len(dataio.hangeul_items())
    )
    assert len(d["angka"]) == (
        len(dataio.numerals()) + len(dataio.counters()) + len(dataio.number_items())
    )
    assert len(d["baca"]) == len(dataio.reading_passages()) + len(dataio.reading_items())
    assert len(d["kesantunan"]) == (
        len(dataio.speech_honorifics()) + len(dataio.speech_items())
    )


# ------------------------------------------------------------------ anki ---

@pytest.mark.parametrize(
    "nama", ["hangeul.csv", "kosakata.csv", "tatabahasa.csv", "angka.csv",
             "lafal.csv", "kesantunan.csv"]
)
def test_format_berkas_anki(nama):
    path = os.path.join(ANKI_DIR, nama)
    baris = open(path, encoding="utf-8").read().split("\n")
    assert baris[0] == "#separator:Comma"
    assert baris[1] == "#html:false"
    assert re.match(r"^#tags column:\d+$", baris[2]), baris[2]

    kolom_tag = int(baris[2].split(":")[1])
    with open(path, encoding="utf-8", newline="") as f:
        rows = [r for r in csv.reader(f) if r and not r[0].startswith("#")]
    assert rows, f"{nama} tidak punya kartu"
    lebar = {len(r) for r in rows}
    assert len(lebar) == 1, f"{nama} punya jumlah kolom tidak seragam: {lebar}"
    assert kolom_tag == next(iter(lebar)), (
        f"{nama}: kolom tag menunjuk kolom {kolom_tag} tetapi kartunya {next(iter(lebar))} kolom"
    )
    for r in rows:
        assert r[0].strip(), f"{nama} punya kartu dengan sisi depan kosong"
        assert r[kolom_tag - 1].startswith("korea "), f"{nama}: tag tidak diawali 'korea'"


def test_anki_readme_menyebut_semua_berkas():
    readme = open(os.path.join(ANKI_DIR, "README.md"), encoding="utf-8").read()
    for nama in os.listdir(ANKI_DIR):
        if nama.endswith(".csv"):
            assert nama in readme, f"{nama} tidak dijelaskan di anki/README.md"
