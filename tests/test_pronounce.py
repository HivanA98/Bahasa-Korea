"""Pengujian mesin pelafalan.

Kasus di bawah DIPATOK: nilainya ditulis tangan dari aturan 표준 발음법, bukan
dihasilkan oleh mesin yang sedang diuji. Bila mesinnya berubah dan salah satu
kasus ini bergeser, pengujian gagal.
"""

from __future__ import annotations

import pytest

from koreadrill import dataio
from koreadrill.hangeul import is_hangeul_text
from koreadrill.pronounce import (
    EXCEPTIONS,
    RULES,
    differs,
    pronounce,
    pronounce_trace,
    rule_labels,
)

#: (tulisan, lafal, id aturan yang WAJIB ikut bekerja)
KASUS = [
    # penyambungan bunyi
    ("한국어", "한구거", "yeoneum"),
    ("밥을", "바블", "yeoneum"),
    ("꽃이", "꼬치", "yeoneum"),
    ("옷을", "오슬", "yeoneum"),
    ("읽어요", "일거요", "yeoneum"),
    ("맛있어요", "마시써요", "yeoneum"),
    ("앞에", "아페", "yeoneum"),
    ("은행에", "은행에", None),          # batchim ㅇ tidak berpindah
    ("영어", "영어", None),
    # penghilangan ㅎ
    ("좋아요", "조아요", "h_talak"),
    ("많이", "마니", "h_talak"),
    ("싫어요", "시러요", "h_talak"),
    ("괜찮아요", "괜차나요", "h_talak"),
    # penetralan batchim
    ("옷", "옫", "kkeutsori"),
    ("꽃", "꼳", "kkeutsori"),
    ("부엌", "부억", "kkeutsori"),
    ("앞", "압", "kkeutsori"),
    ("밖", "박", "kkeutsori"),
    # penyederhanaan batchim ganda
    ("값", "갑", "jaeumgun"),
    ("읽다", "익따", "jaeumgun"),
    ("앉다", "안따", "jaeumgun"),
    ("넓다", "널따", "jaeumgun"),
    ("삶다", "삼따", "jaeumgun"),
    # penyengauan
    ("한국말", "한궁말", "bieumhwa"),
    ("입니다", "임니다", "bieumhwa"),
    ("감사합니다", "감사함니다", "bieumhwa"),
    ("국립", "궁닙", "bieumhwa"),
    ("심리", "심니", "bieumhwa"),
    ("작년", "장년", "bieumhwa"),
    ("일학년", "일항년", "bieumhwa"),
    # peleburan ke ㄹ
    ("신라", "실라", "yueumhwa"),
    ("설날", "설랄", "yueumhwa"),
    # pengerasan
    ("학교", "학꾜", "gyeongeum"),
    ("식당", "식땅", "gyeongeum"),
    ("있다", "읻따", "gyeongeum"),
    ("없어요", "업써요", "gyeongeum"),
    ("낮잠", "낟짬", "gyeongeum"),
    ("학생", "학쌩", "gyeongeum"),
    # pengaspiratan
    ("좋다", "조타", "gyeokeum"),
    ("축하", "추카", "gyeokeum"),
    ("못해요", "모태요", "gyeokeum"),
    ("백화점", "배콰점", "gyeokeum"),
    # palatalisasi
    ("같이", "가치", "gugae"),
    ("굳이", "구지", "gugae"),
    ("닫히다", "다치다", "gugae"),
    # sisipan ㄴ yang didaftar satu per satu
    ("십육", "심뉵", "n_chamga"),
    # kalimat
    ("책을 읽어요.", "채글 일거요.", "yeoneum"),
    ("밥을 먹었어요.", "바블 머거써요.", "yeoneum"),
    ("학교에서 한국어를 공부합니다.", "학꾜에서 한구거를 공부함니다.", "bieumhwa"),
]


@pytest.mark.parametrize("tulisan,lafal,aturan", KASUS)
def test_lafal_kasus_dipatok(tulisan, lafal, aturan):
    hasil, terpakai = pronounce_trace(tulisan)
    assert hasil == lafal, f"{tulisan} dibaca {hasil}, seharusnya {lafal}"
    if aturan is None:
        assert not terpakai, f"{tulisan} seharusnya tidak melewati aturan apa pun"
    else:
        assert aturan in terpakai, f"{tulisan}: aturan {aturan} tidak ikut bekerja ({terpakai})"


def test_aturan_tidak_melintasi_spasi_untuk_pengerasan_dan_peleburan():
    """Pengerasan dan peleburan ke ㄹ hanya berlaku di dalam satu kata.

    Tanpa pembatasan ini, 한국 사람 akan terbaca 한국 싸람 dan 오늘 날씨 akan
    terbaca 오늘 랄씨; keduanya salah.
    """
    assert pronounce("한국 사람") == "한국 사람"
    assert pronounce("오늘 날씨") == "오늘 날씨"
    assert pronounce("옷 가게") == "옫 가게"
    # Penyengauan justru TETAP berlaku antar kata.
    assert pronounce("밥 먹어요") == "밤 머거요"
    assert pronounce("몇 명") == "면 명"


def test_penyambungan_tidak_melintasi_spasi():
    assert pronounce("옷 안") == "옫 안"


def test_lafal_bersifat_tetap_bila_diulang():
    """Menjalankan mesin pada hasilnya sendiri tidak boleh mengubah apa pun lagi."""
    berubah = []
    for tulisan, lafal, _ in KASUS:
        if pronounce(lafal) != lafal:
            berubah.append((tulisan, lafal, pronounce(lafal)))
    assert not berubah, f"lafal berubah saat diproses ulang: {berubah}"


def test_hasil_lafal_selalu_teks_hangeul_yang_sah():
    for tulisan, _, _ in KASUS:
        hasil = pronounce(tulisan)
        assert is_hangeul_text(hasil), f"{tulisan} menghasilkan teks tidak sah: {hasil}"


def test_pengerasan_tidak_ditulis_pada_mode_alih_huruf():
    """romaja.py memanggil mesin dengan tensify=False, karena RR resmi tidak
    menuliskan pengerasan (학교 ditulis hakgyo)."""
    assert pronounce("학교", tensify=False) == "학교"
    assert pronounce("식당", tensify=False) == "식당"
    # Aturan lain tetap berjalan.
    assert pronounce("한국어", tensify=False) == "한구거"


def test_setiap_contoh_aturan_di_data_benar_benar_memicu_aturannya():
    """Kunci modul Hangeul tidak boleh menyimpang dari mesinnya."""
    salah = []
    for r in dataio.hangeul_rules():
        for ex in r["examples"]:
            lafal, terpakai = pronounce_trace(ex["ko"])
            if r["rule"] not in terpakai:
                salah.append(f"{r['id']}: {ex['ko']} -> {lafal}, aturan {r['rule']} tidak terpakai")
    assert not salah, "\n".join(salah)


def test_semua_id_aturan_di_data_dikenal_mesin():
    tidak_dikenal = [r["rule"] for r in dataio.hangeul_rules() if r["rule"] not in RULES]
    assert not tidak_dikenal, f"id aturan tidak ada di pronounce.RULES: {tidak_dikenal}"


def test_setiap_aturan_mesin_punya_kartu_di_data():
    """Aturan yang bisa dipicu mesin harus bisa dipelajari pengguna."""
    terdaftar = {r["rule"] for r in dataio.hangeul_rules()}
    hilang = sorted(set(RULES) - terdaftar)
    assert not hilang, f"aturan tanpa kartu di data/hangeul.json: {hilang}"


def test_daftar_pengecualian_konsisten():
    """Kata pengecualian harus memang tidak bisa diturunkan oleh aturan biasa."""
    for tulisan, lafal in EXCEPTIONS.items():
        assert pronounce(tulisan) == lafal
        assert is_hangeul_text(lafal)


def test_differs():
    assert differs("한국어")
    assert not differs("안녕하세요")


def test_rule_labels():
    label = rule_labels(["yeoneum", "bieumhwa"])
    assert label == ["Penyambungan bunyi (연음)", "Penyengauan (비음화)"]
    assert rule_labels(["tidak-ada"]) == []
