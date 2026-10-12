"""Pengujian kunci jawaban: setiap soal punya tepat satu jawaban benar, dan
kunci soal buatan otomatis selalu sama dengan hasil mesin bahasanya."""

from __future__ import annotations

import random

import pytest

from koreadrill import dataio
from koreadrill.hangeul import compose, is_hangeul_text, particle
from koreadrill.pronounce import pronounce
from koreadrill.questions import (
    MODES,
    build_pool,
    counter_mcq,
    particle_question,
    syllable_question,
)

SEMUA_SOAL_DATA = (
    [("hangeul", i) for i in dataio.hangeul_items()]
    + [("tatabahasa", i) for i in dataio.grammar_items()]
    + [("angka", i) for i in dataio.number_items()]
    + [("baca", i) for i in dataio.reading_items()]
    + [("kesantunan", i) for i in dataio.speech_items()]
)


@pytest.mark.parametrize("modul,item", SEMUA_SOAL_DATA, ids=[f"{m}:{i['id']}" for m, i in SEMUA_SOAL_DATA])
def test_setiap_soal_punya_tepat_satu_jawaban(modul, item):
    opsi = item["options"]
    assert len(opsi) >= 3, f"{item['id']} terlalu sedikit pilihan"
    assert len(set(opsi)) == len(opsi), f"{item['id']} punya pilihan kembar: {opsi}"
    assert 0 <= item["answer"] < len(opsi), f"{item['id']} indeks jawaban di luar jangkauan"
    assert item.get("explain", "").strip(), f"{item['id']} tanpa penjelasan"
    assert item["options_lang"] in ("ko", "id"), f"{item['id']} bahasa pilihan tidak dikenal"
    if item["options_lang"] == "ko":
        # Hanya modul Hangeul yang boleh menampilkan huruf tunggal sebagai
        # pilihan (ㄱ, ㅏ); modul lain wajib memakai suku kata utuh, supaya
        # pengecoh tidak bisa dikenali dari bentuknya yang ganjil.
        boleh_jamo = modul == "hangeul"
        for o in opsi:
            assert is_hangeul_text(o, allow_jamo=boleh_jamo),                 f"{item['id']} pilihan bukan teks Korea: {o!r}"


def test_kunci_soal_lafal_sama_dengan_mesin():
    """Inilah pengujian terpenting modul baca: kunci TIDAK boleh ditulis tangan
    berbeda dari hasil koreadrill/pronounce.py."""
    salah = []
    for i in dataio.reading_items():
        if i["type"] != "pron_choice":
            continue
        lafal = pronounce(i["ko"])
        kunci = i["options"][i["answer"]]
        if kunci != lafal:
            salah.append(f"{i['id']}: kunci {kunci}, mesin {lafal}")
    assert not salah, "\n".join(salah)


def test_pengecoh_soal_lafal_tidak_ikut_benar():
    salah = []
    for i in dataio.reading_items():
        if i["type"] != "pron_choice":
            continue
        lafal = pronounce(i["ko"])
        for j, o in enumerate(i["options"]):
            if j != i["answer"] and o == lafal:
                salah.append(f"{i['id']}: pengecoh {o} juga benar")
    assert not salah, "\n".join(salah)


def test_level_baca_cocok_dengan_aturan_yang_bekerja():
    """Level 1 tidak boleh melewati aturan apa pun, level 2 hanya penyambungan
    bunyi dan penghilangan ㅎ, level 3 selebihnya."""
    from koreadrill.pronounce import pronounce_trace

    ringan = {"yeoneum", "h_talak"}
    salah = []
    for butir in list(dataio.reading_passages()) + list(dataio.reading_items()):
        teks = butir["ko"]
        lafal, aturan = pronounce_trace(teks)
        sebenarnya = 1 if lafal == teks else (2 if set(aturan) <= ringan else 3)
        if sebenarnya != butir["level"]:
            salah.append(
                f"{butir['id']} ditandai level {butir['level']} "
                f"tetapi sebenarnya level {sebenarnya} ({aturan})"
            )
    assert not salah, "\n".join(salah)


def test_kunci_soal_partikel_dihitung_dari_batchim():
    salah = []
    for i, e in enumerate(dataio.vocab_nouns()):
        q = particle_question(e, i)
        kunci = q.options[q.answer]
        jenis = [("은", "는"), ("이", "가"), ("을", "를")][i % 3]
        benar = particle(e["ko"], *jenis)
        if kunci != benar:
            salah.append(f"{e['id']}: kunci {kunci}, seharusnya {benar}")
        assert len(set(q.options)) == len(q.options), f"{e['id']} pilihan kembar"
    assert not salah, "\n".join(salah)


def test_soal_partikel_tetap_sama_di_setiap_pemanggilan():
    """Kartu Leitner hanya bermakna bila soalnya tidak berubah-ubah."""
    nouns = dataio.vocab_nouns()
    for i, e in enumerate(nouns[:20]):
        a = particle_question(e, i)
        b = particle_question(e, i)
        assert a.options == b.options and a.answer == b.answer
        assert a.card_id == dataio.particle_card_id(e)


def test_kunci_soal_penggolong_memakai_sistem_angka_yang_benar():
    rng = random.Random(0)
    for c in dataio.counters():
        q = counter_mcq(c, rng)
        n = dataio.numeral_by_value(c["example_value"])
        benar = (
            f"{n['native_attr']} {c['counter']}" if c["system"] == "native"
            else f"{n['sino']} {c['counter']}"
        )
        assert q.options[q.answer] == benar, f"{c['id']}: kunci {q.options[q.answer]} != {benar}"
        assert len(set(q.options)) == len(q.options), f"{c['id']} pilihan kembar"


def test_kunci_soal_blok_suku_kata_dihitung_hangeul():
    rng = random.Random(1)
    for x in dataio.hangeul_letters():
        q = syllable_question(x, rng)
        # Pertanyaannya memuat huruf penyusunnya; kuncinya harus hasil compose.
        bagian = q.reveal.split(" = ")[0].split(" + ")
        l, v = bagian[0], bagian[1]
        t = bagian[2] if len(bagian) > 2 else ""
        assert q.options[q.answer] == compose(l, v, t)
        assert len(set(q.options)) == len(q.options)


@pytest.mark.parametrize("mode", MODES)
def test_semua_soal_yang_dibangun_sehat(mode):
    rng = random.Random(42)
    pool = build_pool(mode, None, rng)
    assert pool, f"mode {mode} tidak menghasilkan soal"
    for q in pool:
        assert q.card_id, "soal tanpa id kartu"
        assert q.question.strip()
        assert q.stage is None or 1 <= q.stage <= dataio.MAX_STAGE
        if q.kind == "mcq":
            assert q.options and q.answer is not None
            assert 0 <= q.answer < len(q.options)
            assert len(set(q.options)) == len(q.options), f"{q.card_id}: {q.options}"
        elif q.kind == "typed":
            assert q.accepted, f"{q.card_id} tanpa jawaban yang diterima"
        assert q.reveal.strip(), f"{q.card_id} tanpa kunci"


def test_jawaban_bertaip_menerima_arti_sebagian():
    rng = random.Random(0)
    pool = {q.card_id: q for q in build_pool("kosakata-ko", None, rng)}
    # 저녁 berarti "sore, malam; makan malam": ketiganya harus diterima.
    q = pool["v083"]
    for jawaban in ("sore", "malam", "makan malam", "Sore, Malam; makan malam"):
        assert q.is_correct_text(jawaban), jawaban
    assert not q.is_correct_text("pagi")


def test_pengecoh_kosakata_tidak_punya_arti_yang_sama():
    """Soal 'mana kata Korea untuk X' tidak boleh memuat dua kata yang
    sama-sama berarti X."""
    rng = random.Random(3)
    entries = {e["id"]: e for e in dataio.vocab_entries()}
    from koreadrill.questions import accepted_set, normalize

    salah = []
    for q in build_pool("kosakata-id", None, rng):
        target = entries[q.card_id]
        kunci = normalize(target["gloss"])
        for o in q.options:
            if o == target["ko"]:
                continue
            lain = next((e for e in entries.values() if e["ko"] == o), None)
            if lain and kunci in accepted_set(lain):
                salah.append(f"{q.card_id}: pengecoh {o} juga berarti {target['gloss']}")
    assert not salah, "\n".join(salah)
