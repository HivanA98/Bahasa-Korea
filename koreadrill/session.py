"""Penyusun sesi latihan: kartu jatuh tempo, materi baru, dan interleaving.

Empat prinsip yang diterapkan di sini:

* Spaced repetition. Kartu hanya muncul bila sudah jatuh tempo menurut kotak
  Leitner-nya (lihat leitner.py).
* Ulangan didahulukan. Materi baru dibatasi paling banyak NEW_SHARE dari satu
  sesi bila masih ada kartu jatuh tempo. Tanpa pembatasan ini, materi baru
  akan memakan seluruh sesi dan kartu lama tidak pernah naik kotak.
* Interleaving. Soal dari mode berbeda disilang bergantian, dan materi lama
  disisipkan di antara materi baru kira-kira 2 lama : 1 baru. Mencampur
  materi terbukti lebih baik daripada mengerjakan satu blok materi sejenis
  berturut-turut, meski terasa lebih sulit saat dikerjakan.
* Retrieval berulang untuk materi baru. Bila sesi masih longgar (umumnya pada
  hari-hari pertama ketika belum ada kartu jatuh tempo), kartu baru diulang
  sekali lagi di akhir sesi. Pengulangan itu TIDAK menaikkan kotak Leitner
  lagi: quiz.py hanya mencatat jawaban pertama untuk setiap kartu per sesi.

Jatah kartu baru dibagi per KELOMPOK MATERI, bukan per mode. Satu kata baru
yang sama lalu dilatih dua arah (Korea ke Indonesia dan Indonesia ke Korea),
bukan dua kata berbeda untuk masing-masing arah.
"""

from __future__ import annotations

import datetime as _dt
import random
from dataclasses import dataclass, replace

from .leitner import Progress
from .questions import MODES, Question, build_pool

DEFAULT_MINUTES = 20
DEFAULT_NEW_PER_SESSION = 8

#: Bagian sesi paling besar yang boleh diisi materi baru selama masih ada
#: kartu jatuh tempo.
NEW_SHARE = 0.45

#: Mode yang berbagi satu kumpulan kartu, sehingga jatah kartu barunya dibagi
#: sebagai satu kelompok.
MODE_GROUPS = {
    "hangeul": "hangeul",
    "kosakata-ko": "kosakata",
    "kosakata-id": "kosakata",
    "tatabahasa": "tatabahasa",
    "angka": "angka",
    "baca": "baca",
}

#: Bobot pembagian jatah kartu baru antar kelompok materi. Kosakata diberi
#: bobot terbesar karena jumlah kartunya paling banyak (180 kata berbanding
#: 94 kartu hangeul, 141 kartu tata bahasa, 60 kartu angka, dan 32 butir
#: latihan baca), sehingga pembagian rata akan membuat kosakata tertinggal.
#: Hangeul diberi bobot kedua karena seluruh modul lain bergantung padanya.
GROUP_WEIGHTS = {"hangeul": 2, "kosakata": 3, "tatabahasa": 2, "angka": 1, "baca": 1}


@dataclass
class SessionPlan:
    questions: list[Question]
    n_due: int
    n_new: int
    minutes: int

    def __len__(self) -> int:
        return len(self.questions)


def _apportion(total: int, groups: list[str], rng: random.Random) -> dict[str, int]:
    """Bagi jatah kartu baru antar kelompok materi, berbobot dan TEPAT berjumlah
    `total`.

    Pembulatan ke atas per kelompok akan membuat jumlahnya selalu melebihi
    yang diminta: dengan lima kelompok, `--new 5` justru memasukkan delapan
    kartu. Karena itu pembagiannya memakai metode sisa terbesar: setiap
    kelompok mendapat bagian bulatnya dahulu, lalu sisa jatah dibagikan
    menurut pecahan terbesar. Seri dipecah secara acak, sehingga kelompok yang
    tidak kebagian pada satu sesi akan kebagian pada sesi berikutnya.
    """
    if total <= 0 or not groups:
        return {g: 0 for g in groups}
    bobot = {g: GROUP_WEIGHTS.get(g, 1) for g in groups}
    jumlah_bobot = sum(bobot.values())
    mentah = {g: total * bobot[g] / jumlah_bobot for g in groups}
    quotas = {g: int(mentah[g]) for g in groups}
    sisa = total - sum(quotas.values())
    urut = sorted(groups, key=lambda g: (-(mentah[g] - int(mentah[g])), rng.random()))
    for g in urut[:sisa]:
        quotas[g] += 1
    return quotas


def _round_robin(queues: list[list[Question]]) -> list[Question]:
    """Ambil satu soal bergiliran dari setiap antrean (interleaving antar mode)."""
    queues = [list(q) for q in queues if q]
    out: list[Question] = []
    idx = 0
    while queues:
        idx %= len(queues)
        out.append(queues[idx].pop(0))
        if not queues[idx]:
            queues.pop(idx)
        else:
            idx += 1
    return out


def _weave(due: list[Question], new: list[Question]) -> list[Question]:
    """Satukan dua daftar dengan perbandingan kira-kira 2 lama : 1 baru.

    Urutan di dalam masing-masing daftar dipertahankan, karena keduanya sudah
    disilang antar mode oleh _round_robin.
    """
    out: list[Question] = []
    di = ni = 0
    while di < len(due) or ni < len(new):
        for _ in range(2):
            if di < len(due):
                out.append(due[di])
                di += 1
        if ni < len(new):
            out.append(new[ni])
            ni += 1
    return out


def plan_session(
    progress: Progress,
    *,
    modes: list[str] | None = None,
    stage: int | None = None,
    minutes: int = DEFAULT_MINUTES,
    new_per_session: int = DEFAULT_NEW_PER_SESSION,
    limit: int | None = None,
    seed: int | None = None,
    on: _dt.date | None = None,
) -> SessionPlan:
    """Susun daftar soal untuk satu sesi.

    `on` adalah tanggal acuan jatuh tempo; bawaannya hari ini. Parameter ini
    ada supaya jadwal bisa diuji tanpa menunggu hari berganti.
    """
    modes = list(modes or MODES)
    rng = random.Random(seed)

    pools: dict[str, list[Question]] = {m: build_pool(m, stage, rng) for m in modes}

    if limit is None:
        # Perkiraan kasar: sekitar 2,5 soal per menit. Batas ini hanya pagar;
        # sesi tetap berhenti ketika waktunya habis.
        limit = max(10, int(minutes * 2.5))

    # --- pilih kartu baru, jatahnya dibagi per kelompok materi -------------
    groups: list[str] = []
    for m in modes:
        g = MODE_GROUPS[m]
        if g not in groups:
            groups.append(g)
    quotas = _apportion(new_per_session, groups, rng)

    # Materi baru diperkenalkan MENURUT URUTAN TAHAP, bukan acak dari seluruh
    # materi. Di dalam satu tahap urutannya diacak supaya sesi tidak monoton.
    chosen_new: set[str] = set()
    for g in (groups if new_per_session > 0 else []):
        candidates: dict[str, int] = {}
        for m in modes:
            if MODE_GROUPS[m] != g:
                continue
            for q in pools[m]:
                if progress.is_new(q.card_id) and q.card_id not in candidates:
                    candidates[q.card_id] = q.stage if q.stage is not None else 99
        urut = sorted(candidates, key=lambda cid: (candidates[cid], rng.random()))
        chosen_new.update(urut[: quotas[g]])

    # --- pisahkan soal jatuh tempo dan soal materi baru --------------------
    due_queues: list[list[Question]] = []
    new_queues: list[list[Question]] = []
    n_due_available = 0
    for m in modes:
        due: list[Question] = []
        new: list[Question] = []
        used_new: set[str] = set()
        for q in pools[m]:
            if progress.is_new(q.card_id):
                if q.card_id in chosen_new and q.card_id not in used_new:
                    used_new.add(q.card_id)
                    new.append(q)
            elif progress.state(q.card_id).is_due(on):
                due.append(q)
        rng.shuffle(due)
        rng.shuffle(new)
        n_due_available += len(due)
        due_queues.append(due)
        new_queues.append(new)

    due_all = _round_robin(due_queues)
    new_all = _round_robin(new_queues)

    # --- bagi kuota sesi: ulangan didahulukan ------------------------------
    if due_all:
        new_budget = min(len(new_all), max(1, int(limit * NEW_SHARE)))
    else:
        new_budget = min(len(new_all), limit)
    new_sel = new_all[:new_budget]
    due_sel = due_all[: max(0, limit - len(new_sel))]

    questions = _weave(due_sel, new_sel)

    # --- lintasan kedua untuk materi baru, hanya bila sesi masih longgar ---
    if len(questions) < limit and new_sel:
        second = [replace(q, repeat=True) for q in new_sel]
        rng.shuffle(second)
        questions += second[: limit - len(questions)]

    questions = questions[:limit]
    return SessionPlan(
        questions=questions,
        n_due=n_due_available,
        n_new=len({q.card_id for q in new_sel}),
        minutes=minutes,
    )


def upcoming_counts(
    progress: Progress, card_ids: list[str], on: _dt.date | None = None
) -> dict[str, int]:
    """Ringkasan: berapa kartu baru, jatuh tempo, dan belum jatuh tempo."""
    new = sum(1 for c in card_ids if progress.is_new(c))
    due = sum(
        1 for c in card_ids if not progress.is_new(c) and progress.state(c).is_due(on)
    )
    return {"baru": new, "jatuh_tempo": due, "belum_jatuh_tempo": len(card_ids) - new - due}


__all__ = [
    "DEFAULT_MINUTES",
    "DEFAULT_NEW_PER_SESSION",
    "GROUP_WEIGHTS",
    "MODE_GROUPS",
    "NEW_SHARE",
    "SessionPlan",
    "plan_session",
    "upcoming_counts",
]
