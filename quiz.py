#!/usr/bin/env python3
"""Latihan Bahasa Korea di terminal, untuk pemula yang mulai dari nol.

Contoh pemakaian:

    python quiz.py                          sesi campuran 20 menit
    python quiz.py --mode hangeul           hanya huruf dan suku kata
    python quiz.py --mode kosakata-ko       Korea ke Indonesia, jawaban ditulis
    python quiz.py --mode baca --stage 3    membaca dan pelafalan, tahap 1-3
    python quiz.py --romaja                 tampilkan alih huruf Latin
    python quiz.py --stats                  ringkasan kemajuan
    python quiz.py --reset                  hapus progress.json

Progres disimpan di progress.json di folder proyek.
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from koreadrill import dataio  # noqa: E402
from koreadrill.hangeul import is_syllable  # noqa: E402
from koreadrill.leitner import MAX_BOX, MIN_BOX, Progress  # noqa: E402
from koreadrill.pronounce import pronounce  # noqa: E402
from koreadrill.questions import MODE_LABELS, MODES, Question  # noqa: E402
from koreadrill.romaja import romanize  # noqa: E402
from koreadrill.session import (  # noqa: E402
    DEFAULT_MINUTES,
    DEFAULT_NEW_PER_SESSION,
    plan_session,
    upcoming_counts,
)

PROGRESS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "progress.json")
RULE = "─" * 62


# ------------------------------------------------------------- tampilan ---

class Style:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def _wrap(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.enabled else text

    def bold(self, t: str) -> str:
        return self._wrap("1", t)

    def dim(self, t: str) -> str:
        return self._wrap("2", t)

    def ok(self, t: str) -> str:
        return self._wrap("32", t)

    def bad(self, t: str) -> str:
        return self._wrap("31", t)

    def info(self, t: str) -> str:
        return self._wrap("36", t)


def setup_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def prompt(text: str) -> str | None:
    """Baca satu masukan pengguna.

    Mengembalikan None bila masukan berakhir (EOF, misalnya saat dijalankan
    dengan masukan dari pipa) atau dihentikan dengan Ctrl+C, sehingga sesi
    berhenti rapi tanpa jejak galat.
    """
    try:
        return input(text)
    except (EOFError, KeyboardInterrupt):
        print()
        return None


def show_ko(text: str, *, use_romaja: bool) -> str:
    """Tampilkan teks Korea, dengan alih huruf di bawahnya bila diminta.

    Teks yang bukan suku kata Hangeul (misalnya angka pada modul angka, atau
    huruf tunggal) tidak dialihhurufkan di baris kedua, karena hasilnya tidak
    menambah apa pun.
    """
    if use_romaja and any(is_syllable(c) for c in text):
        return f"{text}\n   {romanize(text)}"
    return text


# ----------------------------------------------------------- satu soal ---

def ask(q: Question, st: Style, *, use_romaja: bool, index: int, total: int) -> str | None:
    """Tanyakan satu soal. Kembalikan 'benar', 'salah', 'lewat', atau None (keluar)."""
    print()
    tag = " · ulangan" if q.repeat else ""
    print(st.dim(f"[{index}/{total}] {MODE_LABELS[q.mode]}{tag}"))
    print(st.bold(q.question))
    if q.stimulus_ko:
        print()
        print("   " + show_ko(q.stimulus_ko, use_romaja=use_romaja))
    if q.stimulus_label:
        print("   " + st.dim(q.stimulus_label))

    if q.kind == "mcq":
        return _ask_mcq(q, st, use_romaja=use_romaja)
    if q.kind == "typed":
        return _ask_typed(q, st, use_romaja=use_romaja)
    return _ask_selfcheck(q, st, use_romaja=use_romaja)


def _reveal(q: Question, st: Style, *, use_romaja: bool) -> None:
    if q.reveal:
        label = "Jawaban" if q.kind != "selfcheck" else "Jawabannya"
        print(f"   {st.info(label)}: {show_ko(q.reveal, use_romaja=use_romaja)}")
    if q.reveal_ko and q.reveal_ko not in q.reveal and q.reveal_ko not in (q.explain or ""):
        lafal = pronounce(q.reveal_ko)
        tambahan = f"  [{lafal}]" if lafal != q.reveal_ko else ""
        print(f"   {st.dim('Contoh')}: {q.reveal_ko}{tambahan}")
    if q.explain:
        print(f"   {st.dim(q.explain)}")


def _ask_mcq(q: Question, st: Style, *, use_romaja: bool) -> str | None:
    assert q.options is not None and q.answer is not None
    print()
    for i, opt in enumerate(q.options, 1):
        shown = opt
        if q.options_lang == "ko" and use_romaja:
            shown = f"{opt}   {st.dim(romanize(opt))}"
        print(f"   {i}. {shown}")
    print()
    while True:
        jawab = prompt("   Pilih nomor (atau l=lewat, k=keluar): ")
        if jawab is None:
            return None
        raw = jawab.strip().lower()
        if raw in ("k", "keluar", "q"):
            return None
        if raw in ("l", "lewat", "s"):
            _reveal(q, st, use_romaja=use_romaja)
            return "lewat"
        if raw.isdigit() and 1 <= int(raw) <= len(q.options):
            chosen = int(raw) - 1
            if chosen == q.answer:
                print("   " + st.ok("Benar."))
                if q.explain:
                    print(f"   {st.dim(q.explain)}")
                return "benar"
            print("   " + st.bad(f"Salah. Jawaban: {q.options[q.answer]}"))
            if q.explain:
                print(f"   {st.dim(q.explain)}")
            return "salah"
        print("   " + st.dim("Masukan tidak dikenali."))


def _ask_typed(q: Question, st: Style, *, use_romaja: bool) -> str | None:
    print()
    while True:
        jawab = prompt(f"   {q.input_hint} (?=lihat, l=lewat, k=keluar): ")
        if jawab is None:
            return None
        raw = jawab.strip()
        low = raw.lower()
        if low in ("k", "keluar", "q"):
            return None
        if low in ("l", "lewat", "s"):
            _reveal(q, st, use_romaja=use_romaja)
            return "lewat"
        if low in ("?", "lihat"):
            _reveal(q, st, use_romaja=use_romaja)
            return "salah"
        if not raw:
            continue
        if q.is_correct_text(raw):
            print("   " + st.ok("Benar."))
            _reveal(q, st, use_romaja=use_romaja)
            return "benar"
        print("   " + st.bad("Belum tepat."))
        _reveal(q, st, use_romaja=use_romaja)
        return "salah"


def _ask_selfcheck(q: Question, st: Style, *, use_romaja: bool) -> str | None:
    print()
    jawab = prompt("   Tekan Enter untuk melihat jawaban (k=keluar): ")
    if jawab is None or jawab.strip().lower() in ("k", "keluar", "q"):
        return None
    _reveal(q, st, use_romaja=use_romaja)
    while True:
        jawab = prompt("   Jawaban Anda tepat? (b=benar, s=salah, l=lewat): ")
        if jawab is None:
            return None
        raw = jawab.strip().lower()
        if raw in ("b", "benar"):
            return "benar"
        if raw in ("s", "salah"):
            return "salah"
        if raw in ("l", "lewat"):
            return "lewat"
        print("   " + st.dim("Masukan tidak dikenali."))


# ------------------------------------------------------------- ringkasan ---

def print_stats(progress: Progress, st: Style) -> None:
    ids = dataio.all_card_ids()
    counts = upcoming_counts(progress, ids)
    boxes = progress.box_counts(ids)
    print(RULE)
    print(st.bold("Ringkasan kemajuan"))
    print(RULE)
    print(f"  Total kartu di seluruh modul : {len(ids)}")
    print(f"  Belum pernah dilatih         : {counts['baru']}")
    print(f"  Jatuh tempo hari ini         : {counts['jatuh_tempo']}")
    print(f"  Belum jatuh tempo            : {counts['belum_jatuh_tempo']}")
    print()
    print("  Sebaran kotak Leitner:")
    for b in range(MIN_BOX, MAX_BOX + 1):
        bar = "█" * min(40, boxes[b])
        print(f"    kotak {b}: {boxes[b]:4d}  {bar}")
    seen = [s for s in progress.cards.values() if s.seen]
    if seen:
        total_seen = sum(s.seen for s in seen)
        total_ok = sum(s.correct for s in seen)
        pct = (total_ok / total_seen * 100) if total_seen else 0.0
        print()
        print(f"  Jawaban tercatat: {total_seen}, benar {total_ok} ({pct:.0f}%)")
    if progress.sessions:
        print()
        print("  Lima sesi terakhir:")
        for s in progress.sessions[-5:]:
            print(
                f"    {s.get('tanggal', '?')}  {s.get('soal', 0):3d} soal, "
                f"benar {s.get('benar', 0):3d}, {s.get('menit', 0):.0f} menit"
            )
    print(RULE)


# ------------------------------------------------------------------ main ---

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        prog="quiz.py",
        description="Latihan Bahasa Korea untuk penutur Bahasa Indonesia, mulai dari nol.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Mode yang tersedia: " + ", ".join(MODES),
    )
    p.add_argument(
        "--mode", action="append", default=None,
        help="mode latihan; boleh diulang atau dipisah koma. Bawaan: semua mode.",
    )
    p.add_argument("--stage", type=int, default=None, metavar="N",
                   help="batasi materi sampai tahap N (1-6). Bawaan: semua tahap.")
    p.add_argument("--minutes", type=int, default=DEFAULT_MINUTES, metavar="M",
                   help=f"lama sesi dalam menit (bawaan {DEFAULT_MINUTES}).")
    p.add_argument("--limit", type=int, default=None, metavar="N",
                   help="batas jumlah soal dalam satu sesi.")
    p.add_argument("--new", type=int, default=DEFAULT_NEW_PER_SESSION, metavar="N",
                   help=f"kartu baru per sesi (bawaan {DEFAULT_NEW_PER_SESSION}); 0 = hanya ulangan.")
    p.add_argument("--romaja", action="store_true",
                   help="tampilkan alih huruf Latin (bawaan: mati).")
    p.add_argument("--seed", type=int, default=None,
                   help="seed acak, untuk mengulang susunan sesi yang sama.")
    p.add_argument("--progress", default=PROGRESS_PATH, metavar="BERKAS",
                   help="lokasi berkas progres.")
    p.add_argument("--stats", action="store_true", help="tampilkan ringkasan lalu keluar.")
    p.add_argument("--reset", action="store_true", help="hapus berkas progres.")
    p.add_argument("--no-color", action="store_true", help="matikan warna.")
    return p.parse_args(argv)


def resolve_modes(raw: list[str] | None) -> list[str]:
    if not raw:
        return list(MODES)
    out: list[str] = []
    for chunk in raw:
        for m in chunk.split(","):
            m = m.strip()
            if not m:
                continue
            if m not in MODES:
                raise SystemExit(
                    f"Mode tidak dikenal: {m}\nMode yang tersedia: " + ", ".join(MODES)
                )
            if m not in out:
                out.append(m)
    return out


def main(argv: list[str] | None = None) -> int:
    setup_stdout()
    args = parse_args(argv)
    st = Style(enabled=not args.no_color and sys.stdout.isatty())

    if args.reset:
        if os.path.exists(args.progress):
            ans = prompt(f"Hapus {args.progress}? Semua progres hilang. (ya/tidak): ")
            if ans is None or ans.strip().lower() not in ("ya", "y"):
                print("Dibatalkan.")
                return 0
            os.remove(args.progress)
            print("Berkas progres dihapus.")
        else:
            print("Tidak ada berkas progres untuk dihapus.")
        return 0

    progress = Progress.load(args.progress)
    if args.stats:
        print_stats(progress, st)
        return 0

    if args.stage is not None and not (1 <= args.stage <= dataio.MAX_STAGE):
        raise SystemExit(f"--stage harus antara 1 dan {dataio.MAX_STAGE}")

    use_romaja = args.romaja or bool(progress.settings.get("romaja"))
    modes = resolve_modes(args.mode)

    plan = plan_session(
        progress,
        modes=modes,
        stage=args.stage,
        minutes=args.minutes,
        new_per_session=args.new,
        limit=args.limit,
        seed=args.seed,
    )

    print(RULE)
    print(st.bold("Latihan Bahasa Korea"))
    print(RULE)
    print(f"  Mode   : {', '.join(modes)}")
    print(f"  Tahap  : {args.stage if args.stage else 'semua'}")
    print(f"  Target : {args.minutes} menit, {len(plan)} soal tersusun")
    print(f"  Kartu  : {plan.n_due} jatuh tempo, {plan.n_new} baru dalam sesi ini")
    if use_romaja:
        print("  " + st.dim("Alih huruf Latin: aktif (mengikuti bunyi, bukan tulisan)"))
    print(RULE)

    if not plan.questions:
        print()
        print("Tidak ada soal yang jatuh tempo hari ini.")
        print("Pilihan: naikkan --new untuk menambah kartu baru, atau jalankan --stats.")
        return 0

    start = time.monotonic()
    deadline = start + args.minutes * 60
    tally = {"benar": 0, "salah": 0, "lewat": 0}
    asked = 0
    quit_early = False
    # Satu kartu hanya sekali menggerakkan kotak Leitner per sesi; kemunculan
    # berikutnya dalam sesi yang sama adalah latihan tambahan saja.
    scored: set[str] = set()

    for i, q in enumerate(plan.questions, 1):
        if asked and time.monotonic() > deadline:
            print()
            print(st.info("Waktu sesi habis."))
            break
        result = ask(q, st, use_romaja=use_romaja, index=i, total=len(plan))
        if result is None:
            quit_early = True
            break
        asked += 1
        tally[result] += 1
        if result in ("benar", "salah") and q.card_id not in scored:
            scored.add(q.card_id)
            progress.record_answer(q.card_id, result == "benar")

    minutes = (time.monotonic() - start) / 60
    if asked:
        progress.log_session({
            "tanggal": dt.date.today().isoformat(),
            "mode": ",".join(modes),
            "soal": asked,
            "benar": tally["benar"],
            "salah": tally["salah"],
            "lewat": tally["lewat"],
            "menit": round(minutes, 1),
        })
    progress.settings["romaja"] = bool(args.romaja) or bool(progress.settings.get("romaja"))
    progress.save(args.progress)

    print()
    print(RULE)
    print(st.bold("Sesi selesai" + (" (dihentikan)" if quit_early else "")))
    print(RULE)
    print(f"  Soal dikerjakan : {asked}")
    print(f"  Benar           : {tally['benar']}")
    print(f"  Salah           : {tally['salah']}")
    print(f"  Dilewati        : {tally['lewat']}")
    print(f"  Lama            : {minutes:.1f} menit")
    print(f"  Progres         : {args.progress}")
    print(RULE)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print()
        print("Dihentikan.")
        raise SystemExit(130)
