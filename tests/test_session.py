"""Pengujian penyusunan sesi: batas kartu baru, prioritas ulangan, interleaving."""

from __future__ import annotations

import datetime as dt

from koreadrill import dataio
from koreadrill.leitner import Progress
from koreadrill.questions import MODES
from koreadrill.session import (
    DEFAULT_MINUTES,
    DEFAULT_NEW_PER_SESSION,
    NEW_SHARE,
    plan_session,
    upcoming_counts,
)

HARI = dt.date(2026, 1, 1)


def test_sesi_pengguna_baru_tidak_kosong():
    plan = plan_session(Progress(), seed=1, on=HARI)
    assert len(plan) > 0
    assert plan.n_due == 0
    assert plan.n_new > 0


def test_batas_jumlah_soal_dipatuhi():
    plan = plan_session(Progress(), limit=7, seed=1, on=HARI)
    assert len(plan) <= 7


def test_kartu_baru_dibatasi():
    plan = plan_session(Progress(), new_per_session=4, seed=1, on=HARI)
    # Pembagian per kelompok memakai pembulatan ke atas, jadi jumlahnya bisa
    # sedikit di atas angka yang diminta, tetapi tidak boleh berlipat.
    assert plan.n_new <= 4 + len(MODES)


def test_new_nol_berarti_tanpa_materi_baru():
    plan = plan_session(Progress(), new_per_session=0, seed=1, on=HARI)
    assert plan.n_new == 0
    assert len(plan) == 0  # pengguna baru belum punya kartu untuk diulang


def test_sesi_hanya_memuat_mode_yang_diminta():
    plan = plan_session(Progress(), modes=["baca"], seed=1, on=HARI)
    assert {q.mode for q in plan.questions} == {"baca"}


def test_pembatasan_tahap_dipatuhi():
    plan = plan_session(
        Progress(), modes=["kosakata-ko"], stage=1, new_per_session=40, seed=1, on=HARI
    )
    tahap1 = {e["id"] for e in dataio.vocab_entries() if e["stage"] == 1}
    assert {q.card_id for q in plan.questions} <= tahap1


def test_ulangan_tidak_tergeser_habis_oleh_materi_baru():
    """Dengan banyak kartu jatuh tempo, materi baru dibatasi NEW_SHARE."""
    p = Progress()
    for e in dataio.vocab_entries():
        p.record_answer(e["id"], False, HARI)  # semuanya kotak 1, jatuh tempo
    limit = 40
    plan = plan_session(p, limit=limit, seed=3, on=HARI)
    baru = sum(1 for q in plan.questions if p.is_new(q.card_id))
    assert baru <= int(limit * NEW_SHARE) + 1, f"materi baru {baru} dari {limit} soal"
    assert len(plan) == limit


def test_kartu_belum_jatuh_tempo_tidak_muncul():
    p = Progress()
    p.record_answer("v001", True, HARI)  # kotak 2, jatuh tempo besok
    plan = plan_session(p, modes=["kosakata-ko"], new_per_session=0, seed=1, on=HARI)
    assert "v001" not in {q.card_id for q in plan.questions}
    plan2 = plan_session(
        p, modes=["kosakata-ko"], new_per_session=0, seed=1,
        on=HARI + dt.timedelta(days=1),
    )
    assert "v001" in {q.card_id for q in plan2.questions}


def test_interleaving_mencampur_mode():
    """Sesi campuran tidak boleh berupa blok satu mode berturut-turut."""
    plan = plan_session(Progress(), seed=5, on=HARI)
    urutan = [q.mode for q in plan.questions]
    assert len(set(urutan)) > 1, "sesi campuran hanya memuat satu mode"
    terpanjang = 1
    berjalan = 1
    for a, b in zip(urutan, urutan[1:]):
        berjalan = berjalan + 1 if a == b else 1
        terpanjang = max(terpanjang, berjalan)
    assert terpanjang <= len(set(urutan)) + 2, (
        f"ada {terpanjang} soal mode sama berturut-turut dari urutan {urutan}"
    )


def test_satu_kata_baru_dilatih_dua_arah():
    """Kartu kosakata baru yang sama muncul pada kedua arah latihan."""
    plan = plan_session(
        Progress(), modes=["kosakata-ko", "kosakata-id"], new_per_session=6,
        seed=1, on=HARI,
    )
    arah_ar = {q.card_id for q in plan.questions if q.mode == "kosakata-ko"}
    arah_id = {q.card_id for q in plan.questions if q.mode == "kosakata-id"}
    assert arah_ar and arah_id
    assert arah_ar == arah_id, "kedua arah seharusnya melatih kata yang sama"


def test_ulangan_lintasan_kedua_ditandai():
    plan = plan_session(Progress(), seed=1, on=HARI)
    ulangan = [q for q in plan.questions if q.repeat]
    assert ulangan, "pengguna baru seharusnya mendapat lintasan kedua"
    pertama = {q.card_id for q in plan.questions if not q.repeat}
    assert {q.card_id for q in ulangan} <= pertama


def test_sesi_dapat_diulang_dengan_seed_sama():
    a = plan_session(Progress(), seed=99, on=HARI)
    b = plan_session(Progress(), seed=99, on=HARI)
    assert [(q.card_id, q.mode, q.repeat) for q in a.questions] == \
           [(q.card_id, q.mode, q.repeat) for q in b.questions]


def test_upcoming_counts_berjumlah_total():
    p = Progress()
    p.record_answer("v001", True, HARI)
    ids = dataio.all_card_ids()
    c = upcoming_counts(p, ids, HARI)
    assert c["baru"] + c["jatuh_tempo"] + c["belum_jatuh_tempo"] == len(ids)


def test_bawaan_sesi_masuk_akal():
    assert 10 <= DEFAULT_MINUTES <= 30
    assert 4 <= DEFAULT_NEW_PER_SESSION <= 20
    plan = plan_session(Progress(), seed=1, on=HARI)
    # Sesi 20 menit pada perkiraan 2,5 soal per menit.
    assert len(plan) <= int(DEFAULT_MINUTES * 2.5)


def test_semua_kartu_akhirnya_terjangkau():
    """Tidak ada kartu yang tidak pernah bisa muncul di mode mana pun."""
    terjangkau: set[str] = set()
    for m in MODES:
        from koreadrill.questions import build_pool
        import random
        terjangkau |= {q.card_id for q in build_pool(m, None, random.Random(0))}
    hilang = sorted(set(dataio.all_card_ids()) - terjangkau)
    assert not hilang, f"kartu tidak terjangkau mode apa pun: {hilang}"


def test_materi_baru_diperkenalkan_menurut_urutan_tahap():
    """Tanpa --stage pun, kartu baru harus masuk dari tahap 1 lebih dahulu.

    Yang diuji adalah PEMILIHAN per sesi, bukan urutan tampil di dalam satu
    sesi: urutan tampil memang diacak supaya materi tersilang (interleaving).
    Satu sesi boleh menjangkau dua tahap yang berdampingan, yaitu saat tahap
    sebelumnya hampir habis.
    """
    p = Progress()
    per_sesi: list[set[int]] = []
    hari = HARI
    for s in range(20):
        plan = plan_session(p, modes=["kosakata-ko"], seed=s, on=hari)
        baru = {q.stage for q in plan.questions if p.is_new(q.card_id)}
        if baru:
            per_sesi.append(baru)
        for q in plan.questions:
            p.record_answer(q.card_id, True, hari)
        hari += dt.timedelta(days=1)

    assert per_sesi, "tidak ada kartu baru yang diperkenalkan"
    assert min(per_sesi[0]) == 1, f"sesi pertama mulai dari tahap {min(per_sesi[0])}"
    for i, tahap in enumerate(per_sesi):
        assert max(tahap) - min(tahap) <= 1, (
            f"sesi {i + 1} menjangkau tahap tidak berdampingan: {sorted(tahap)}"
        )
    minimum = [min(t) for t in per_sesi]
    assert all(a <= b for a, b in zip(minimum, minimum[1:])), (
        f"tahap terendah per sesi tidak monoton naik: {minimum}"
    )
    maksimum = [max(t) for t in per_sesi]
    for a, b in zip(maksimum, minimum[1:]):
        assert b >= a - 1, "sesi berikutnya mundur lebih dari satu tahap"


def test_setiap_soal_punya_tahap():
    import random

    from koreadrill.questions import build_pool

    for m in MODES:
        kosong = [q.card_id for q in build_pool(m, None, random.Random(0))
                  if q.stage is None]
        assert not kosong, f"{m}: soal tanpa tahap: {kosong[:5]}"


def test_tahap_soal_sesuai_datanya():
    import random

    from koreadrill.questions import build_pool

    stage_kosakata = {e["id"]: e["stage"] for e in dataio.vocab_entries()}
    for q in build_pool("kosakata-ko", None, random.Random(0)):
        assert q.stage == stage_kosakata[q.card_id]
