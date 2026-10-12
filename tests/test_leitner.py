"""Pengujian sistem Leitner dan penyimpanan progres."""

from __future__ import annotations

import datetime as dt
import json

from koreadrill.leitner import (
    INTERVALS,
    MAX_BOX,
    MIN_BOX,
    PROGRESS_VERSION,
    CardState,
    Progress,
)

HARI = dt.date(2026, 1, 1)


def test_kartu_baru_mulai_di_kotak_satu_dan_langsung_jatuh_tempo():
    st = CardState()
    assert st.box == MIN_BOX
    assert st.is_due()


def test_jawaban_benar_menaikkan_kotak():
    st = CardState()
    st.answer(True, HARI)
    assert st.box == 2
    assert st.due == (HARI + dt.timedelta(days=INTERVALS[2])).isoformat()


def test_jawaban_salah_mengembalikan_ke_kotak_satu():
    st = CardState()
    for _ in range(4):
        st.answer(True, HARI)
    assert st.box == MAX_BOX
    st.answer(False, HARI)
    assert st.box == MIN_BOX
    assert st.due == HARI.isoformat()


def test_kotak_tidak_melebihi_maksimum():
    st = CardState()
    for _ in range(20):
        st.answer(True, HARI)
    assert st.box == MAX_BOX


def test_hitungan_benar_dan_salah_tercatat():
    st = CardState()
    st.answer(True, HARI)
    st.answer(False, HARI)
    st.answer(True, HARI)
    assert st.seen == 3
    assert st.correct == 2
    assert st.wrong == 1


def test_jeda_sesuai_tabel_interval():
    for target_box in range(2, MAX_BOX + 1):
        st = CardState()
        for _ in range(target_box - 1):
            st.answer(True, HARI)
        assert st.box == target_box
        diharapkan = HARI + dt.timedelta(days=INTERVALS[target_box])
        assert st.due == diharapkan.isoformat()


def test_belum_jatuh_tempo_sebelum_tanggalnya():
    st = CardState()
    st.answer(True, HARI)  # kotak 2, jeda 1 hari
    assert not st.is_due(HARI)
    assert st.is_due(HARI + dt.timedelta(days=1))
    assert st.is_due(HARI + dt.timedelta(days=5))


def test_simpan_dan_muat_ulang(tmp_path):
    path = tmp_path / "progress.json"
    p = Progress()
    p.record_answer("v001", True, HARI)
    p.record_answer("v002", False, HARI)
    p.settings["romaja"] = True
    p.log_session({"tanggal": HARI.isoformat(), "soal": 2, "benar": 1})
    p.save(str(path))

    q = Progress.load(str(path))
    assert q.version == PROGRESS_VERSION
    assert q.settings["romaja"] is True
    assert q.cards["v001"].box == 2
    assert q.cards["v002"].box == 1
    assert q.cards["v001"].correct == 1
    assert q.cards["v002"].wrong == 1
    assert len(q.sessions) == 1


def test_berkas_progres_adalah_json_utf8_yang_sah(tmp_path):
    path = tmp_path / "progress.json"
    p = Progress()
    p.record_answer("v001", True, HARI)
    p.save(str(path))
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert raw["version"] == PROGRESS_VERSION
    assert "v001" in raw["cards"]


def test_muat_berkas_yang_tidak_ada_mengembalikan_progres_kosong(tmp_path):
    p = Progress.load(str(tmp_path / "belum-ada.json"))
    assert p.cards == {}
    assert p.version == PROGRESS_VERSION


def test_berkas_versi_lain_tidak_merusak_pemuatan(tmp_path):
    path = tmp_path / "progress.json"
    path.write_text(
        json.dumps({"version": 1, "cards": {"v001": {"box": 3, "due": "2026-01-01"}}}),
        encoding="utf-8",
    )
    p = Progress.load(str(path))
    assert p.version == PROGRESS_VERSION
    assert p.cards["v001"].box == 3


def test_entri_kartu_rusak_diabaikan(tmp_path):
    path = tmp_path / "progress.json"
    path.write_text(
        json.dumps({"version": PROGRESS_VERSION, "cards": {"v001": "bukan objek"}}),
        encoding="utf-8",
    )
    p = Progress.load(str(path))
    assert "v001" not in p.cards


def test_is_new_dan_due_ids():
    p = Progress()
    assert p.is_new("v001")
    p.record_answer("v001", False, HARI)
    assert not p.is_new("v001")
    assert p.due_ids(["v001", "v002"], HARI) == ["v001"]
    assert p.new_ids(["v001", "v002"]) == ["v002"]


def test_box_counts():
    p = Progress()
    p.record_answer("a", True, HARI)
    p.record_answer("b", True, HARI)
    p.record_answer("c", False, HARI)
    counts = p.box_counts(["a", "b", "c"])
    assert counts[1] == 1
    assert counts[2] == 2


def test_penyimpanan_atomik_tidak_meninggalkan_berkas_sementara(tmp_path):
    path = tmp_path / "progress.json"
    p = Progress()
    p.record_answer("v001", True, HARI)
    p.save(str(path))
    p.save(str(path))
    sisa = [f.name for f in tmp_path.iterdir() if f.name.endswith(".tmp")]
    assert not sisa, f"berkas sementara tertinggal: {sisa}"
