"""Sistem Leitner lima kotak dengan jadwal berbasis tanggal.

Setiap kartu berada di salah satu dari lima kotak. Jawaban benar memindahkan
kartu ke kotak berikutnya (jeda ulangan makin panjang), jawaban salah
mengembalikannya ke kotak 1. Inilah bentuk paling sederhana dari spaced
repetition dan cukup untuk pemakaian pribadi.

Jeda antar ulangan (hari):
    kotak 1 -> 0   (diulang pada sesi yang sama atau hari itu juga)
    kotak 2 -> 1
    kotak 3 -> 3
    kotak 4 -> 7
    kotak 5 -> 16

Angka-angka ini adalah pilihan praktis yang lazim dipakai pada kartu Leitner,
bukan hasil pengukuran pada pengguna tertentu. Ubah INTERVALS bila jadwal lain
lebih sesuai.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field

PROGRESS_VERSION = 2
MIN_BOX = 1
MAX_BOX = 5
INTERVALS = {1: 0, 2: 1, 3: 3, 4: 7, 5: 16}


def today() -> _dt.date:
    return _dt.date.today()


def _iso(d: _dt.date) -> str:
    return d.isoformat()


@dataclass
class CardState:
    box: int = MIN_BOX
    due: str = ""
    seen: int = 0
    correct: int = 0
    wrong: int = 0
    last: str = ""

    def __post_init__(self) -> None:
        if not self.due:
            self.due = _iso(today())

    def is_due(self, on: _dt.date | None = None) -> bool:
        on = on or today()
        return _dt.date.fromisoformat(self.due) <= on

    def answer(self, ok: bool, on: _dt.date | None = None) -> None:
        on = on or today()
        self.seen += 1
        if ok:
            self.correct += 1
            self.box = min(self.box + 1, MAX_BOX)
        else:
            self.wrong += 1
            self.box = MIN_BOX
        self.last = _iso(on)
        self.due = _iso(on + _dt.timedelta(days=INTERVALS[self.box]))


@dataclass
class Progress:
    version: int = PROGRESS_VERSION
    created: str = field(default_factory=lambda: _iso(today()))
    settings: dict = field(default_factory=lambda: {"romaja": False})
    cards: dict = field(default_factory=dict)
    sessions: list = field(default_factory=list)

    # ------------------------------------------------------------- berkas ---
    @classmethod
    def load(cls, path: str) -> "Progress":
        if not os.path.exists(path):
            return cls()
        with open(path, encoding="utf-8") as f:
            raw = json.load(f)
        if raw.get("version") != PROGRESS_VERSION:
            # Berkas versi lain tidak ditafsirkan paksa; kartu yang dikenali
            # tetap dipakai, sisanya diabaikan.
            raw.setdefault("cards", {})
        p = cls(
            version=PROGRESS_VERSION,
            created=raw.get("created") or _iso(today()),
            settings=raw.get("settings") or {"romaja": False},
            sessions=raw.get("sessions") or [],
        )
        for cid, st in (raw.get("cards") or {}).items():
            if not isinstance(st, dict):
                continue
            p.cards[cid] = CardState(
                box=int(st.get("box", MIN_BOX)),
                due=str(st.get("due") or _iso(today())),
                seen=int(st.get("seen", 0)),
                correct=int(st.get("correct", 0)),
                wrong=int(st.get("wrong", 0)),
                last=str(st.get("last") or ""),
            )
        return p

    def save(self, path: str) -> None:
        """Tulis atomik: tulis ke berkas sementara lalu ganti nama."""
        data = {
            "version": self.version,
            "created": self.created,
            "settings": self.settings,
            "cards": {cid: asdict(st) for cid, st in sorted(self.cards.items())},
            "sessions": self.sessions[-200:],
        }
        directory = os.path.dirname(os.path.abspath(path)) or "."
        os.makedirs(directory, exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.write("\n")
            os.replace(tmp, path)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise

    # -------------------------------------------------------------- kartu ---
    def state(self, card_id: str) -> CardState:
        if card_id not in self.cards:
            self.cards[card_id] = CardState()
        return self.cards[card_id]

    def is_new(self, card_id: str) -> bool:
        return card_id not in self.cards

    def due_ids(self, card_ids: list[str], on: _dt.date | None = None) -> list[str]:
        on = on or today()
        return [c for c in card_ids if c in self.cards and self.cards[c].is_due(on)]

    def new_ids(self, card_ids: list[str]) -> list[str]:
        return [c for c in card_ids if c not in self.cards]

    def record_answer(self, card_id: str, ok: bool, on: _dt.date | None = None) -> CardState:
        st = self.state(card_id)
        st.answer(ok, on)
        return st

    def box_counts(self, card_ids: list[str] | None = None) -> dict[int, int]:
        ids = card_ids if card_ids is not None else list(self.cards)
        counts = {b: 0 for b in range(MIN_BOX, MAX_BOX + 1)}
        for c in ids:
            st = self.cards.get(c)
            if st:
                counts[st.box] += 1
        return counts

    def log_session(self, entry: dict) -> None:
        self.sessions.append(entry)


__all__ = [
    "CardState",
    "INTERVALS",
    "MAX_BOX",
    "MIN_BOX",
    "PROGRESS_VERSION",
    "Progress",
    "today",
]
