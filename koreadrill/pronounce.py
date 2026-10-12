"""Aturan pelafalan: dari tulisan Hangeul ke bunyi sebenarnya.

Hangeul hampir selalu dibaca sesuai tulisannya, tetapi "hampir" itulah yang
membuat pemula tersandung: 좋아요 dibaca 조아요, 한국말 dibaca 한궁말, dan
학교 dibaca 학꾜. Tulisannya tetap mengikuti bentuk kata aslinya (morfem),
sedangkan bunyinya menyesuaikan diri dengan huruf di sekitarnya.

Berkas ini menerapkan sembilan aturan baku (표준 발음법) dalam urutan tetap.
Urutannya penting: 못해요 harus melewati penetralan batchim (ㅅ menjadi ㄷ)
sebelum aturan pengaspiratan, supaya hasilnya 모태요 dan bukan 몯해요.

    pronounce("좋아요")  ->  조아요
    pronounce("한국말")  ->  한궁말
    pronounce("학교")    ->  학꾜

`pronounce_trace` mengembalikan daftar aturan yang benar-benar terpakai pada
sebuah kata, sehingga aplikasi kartu dan quiz.py bisa MENJELASKAN bunyinya,
bukan hanya menampilkannya.

Batasan yang disengaja:

* Aturan diterapkan di dalam satu kata dan antar kata yang berdampingan,
  kecuali penyambungan bunyi (연음) yang hanya berlaku di dalam satu kata
  (tanpa spasi). Membaca 옷 안 sebagai 오단 memang baku dalam ucapan
  bersambung, tetapi pelajar pemula lebih baik membacanya per kata.
* Sisipan ㄴ/ㅅ pada kata gabungan (한여름 -> 한녀름, 나뭇잎 -> 나문닙) TIDAK
  diterapkan karena pemicunya adalah batas morfem yang tidak terlihat dari
  tulisannya. Kata semacam itu dicatat satu per satu di data bila diperlukan.
* 경음화 karena akhiran tata bahasa (할 것 -> 할 껀, 갈 데 -> 갈 떼) dan
  pengerasan di dalam frasa yang melekat erat (몇 시 -> 멷 씨, 할 수 -> 할 쑤)
  juga tidak diterapkan, karena pemicunya bukan huruf melainkan jenis
  akhiran dan kedekatan maknanya. Di dalam satu kata, pengerasan tetap
  diterapkan (학교 -> 학꾜).
"""

from __future__ import annotations

from dataclasses import dataclass

from .hangeul import CLUSTERS, compose, decompose, is_syllable

#: Penetralan batchim di akhir suku kata (음절의 끝소리 규칙): tujuh bunyi
#: akhir yang mungkin hanyalah ㄱ ㄴ ㄷ ㄹ ㅁ ㅂ ㅇ.
NEUTRAL = {
    "ㄲ": "ㄱ", "ㅋ": "ㄱ",
    "ㅅ": "ㄷ", "ㅆ": "ㄷ", "ㅈ": "ㄷ", "ㅊ": "ㄷ", "ㅌ": "ㄷ", "ㅎ": "ㄷ",
    "ㅍ": "ㅂ",
}

#: Penyederhanaan batchim ganda bila tidak ada vokal sesudahnya.
SIMPLIFY = {
    "ㄳ": "ㄱ", "ㄵ": "ㄴ", "ㄶ": "ㄴ", "ㄺ": "ㄱ", "ㄻ": "ㅁ",
    "ㄼ": "ㄹ", "ㄽ": "ㄹ", "ㄾ": "ㄹ", "ㄿ": "ㅂ", "ㅀ": "ㄹ", "ㅄ": "ㅂ",
}

#: Pasangan huruf biasa dan huruf beraspirat (거센소리).
ASPIRATE = {"ㄱ": "ㅋ", "ㄷ": "ㅌ", "ㅂ": "ㅍ", "ㅈ": "ㅊ"}

#: Pasangan huruf biasa dan huruf kembar (된소리).
TENSE = {"ㄱ": "ㄲ", "ㄷ": "ㄸ", "ㅂ": "ㅃ", "ㅅ": "ㅆ", "ㅈ": "ㅉ"}

#: Padanan sengau untuk batchim letup.
NASAL = {"ㄱ": "ㅇ", "ㄷ": "ㄴ", "ㅂ": "ㅁ"}

#: Batchim ganda yang tetap mengeraskan huruf sesudahnya walaupun huruf
#: pengerasnya sendiri sudah hilang (표준 발음법 pasal 24 dan 25):
#: 앉다 dibaca 안따, 삶다 dibaca 삼따, 넓다 dibaca 널따, 핥다 dibaca 할따.
#: Aturan ini sebenarnya MORFOLOGIS (hanya berlaku pada akhiran yang menempel
#: pada kata kerja dan kata sifat), bukan semata bunyi. Keempat batchim ini
#: dalam praktiknya hanya muncul pada kata kerja dan kata sifat, sehingga
#: penerapannya di sini aman untuk materi A1-A2.
TENSE_AFTER_CLUSTER = {"ㄵ", "ㄻ", "ㄼ", "ㄾ"}

#: Kata yang lafalnya TIDAK bisa diturunkan dari hurufnya saja karena ada
#: sisipan ㄴ di batas kata gabungan (ㄴ 첨가). Pemicunya batas morfem yang
#: tidak terlihat dari tulisan, jadi kata semacam ini didaftar satu per satu.
#: Daftar ini sengaja pendek; bila sebuah kata tidak ada di sini dan lafalnya
#: menyimpang, lafalnya ditulis langsung di data lewat field `pron`.
EXCEPTIONS = {
    "십육": "심뉵",
    "육십육": "육씸뉵",
    "꽃잎": "꼰닙",
    "색연필": "생년필",
    "한여름": "한녀름",
    "무슨 일": "무슨 닐",
}

#: Nama aturan dalam Bahasa Indonesia dan Bahasa Korea. Id-nya dipakai di
#: data/hangeul.json dan diperiksa oleh tests/.
RULES = {
    "gugae": ("Palatalisasi", "구개음화",
              "ㄷ dan ㅌ di batchim bertemu 이 atau 히 berubah menjadi ㅈ dan ㅊ."),
    "gyeokeum": ("Pengaspiratan", "격음화",
                 "ㅎ bertemu ㄱ ㄷ ㅂ ㅈ (dari arah mana pun) melebur menjadi ㅋ ㅌ ㅍ ㅊ."),
    "h_talak": ("Penghilangan ㅎ", "ㅎ 탈락",
                "ㅎ di batchim hilang bila suku kata berikutnya dimulai vokal."),
    "yeoneum": ("Penyambungan bunyi", "연음",
                "Batchim berpindah menjadi bunyi awal suku kata berikutnya yang dimulai ㅇ."),
    "jaeumgun": ("Penyederhanaan batchim ganda", "자음군 단순화",
                 "Batchim ganda hanya dibunyikan satu huruf bila tidak ada vokal sesudahnya."),
    "kkeutsori": ("Penetralan batchim", "음절의 끝소리 규칙",
                  "Batchim hanya berbunyi tujuh: ㄱ ㄴ ㄷ ㄹ ㅁ ㅂ ㅇ."),
    "bieumhwa": ("Penyengauan", "비음화",
                 "ㄱ ㄷ ㅂ menjadi ㅇ ㄴ ㅁ bila bertemu ㄴ atau ㅁ."),
    "yueumhwa": ("Peleburan ke ㄹ", "유음화",
                 "ㄴ bertemu ㄹ (atau sebaliknya) dibunyikan ㄹㄹ."),
    "gyeongeum": ("Pengerasan", "경음화",
                  "ㄱ ㄷ ㅂ di batchim mengubah ㄱ ㄷ ㅂ ㅅ ㅈ sesudahnya menjadi huruf kembar."),
    "n_chamga": ("Sisipan ㄴ", "ㄴ 첨가",
                 "Pada sebagian kata gabungan muncul bunyi ㄴ yang tidak tertulis. "
                 "Kata semacam ini dihafal satu per satu, tidak ada aturan yang bisa diterapkan "
                 "hanya dari hurufnya."),
}


@dataclass
class Syl:
    """Satu suku kata yang isinya bisa diubah oleh aturan."""
    l: str
    v: str
    t: str

    def text(self) -> str:
        return compose(self.l, self.v, self.t)


def _parse(text: str) -> tuple[list[object], list[int]]:
    """Pecah teks menjadi token; kembalikan juga indeks token suku kata."""
    tokens: list[object] = []
    idx: list[int] = []
    for ch in text:
        if is_syllable(ch):
            l, v, t = decompose(ch)
            idx.append(len(tokens))
            tokens.append(Syl(l, v, t))
        else:
            tokens.append(ch)
    return tokens, idx


def _render(tokens: list[object]) -> str:
    return "".join(t.text() if isinstance(t, Syl) else t for t in tokens)


def pronounce_trace(text: str, *, tensify: bool = True) -> tuple[str, list[str]]:
    """Lafal sebenarnya beserta daftar id aturan yang terpakai.

    `tensify=False` melewatkan aturan pengerasan (경음화). Dipakai oleh
    romaja.py karena alih huruf RR resmi tidak menuliskan pengerasan:
    학교 dialihhurufkan hakgyo, bukan hakkyo.

    Urutan aturan di bawah bukan selera: hasilnya berbeda bila ditukar.
    Penetralan batchim harus mendahului pengerasan, dan penyambungan bunyi
    harus mendahului penetralan (supaya 꽃이 menjadi 꼬치, bukan 꼳이).
    """
    if text in EXCEPTIONS:
        return EXCEPTIONS[text], ["n_chamga"]

    tokens, idx = _parse(text)
    fired: list[str] = []
    #: Suku kata yang batchim gandanya memicu pengerasan di langkah 9.
    pemicu_keras: set[int] = set()

    def mark(rule: str) -> None:
        if rule not in fired:
            fired.append(rule)

    def pairs():
        """Pasangan suku kata beserta penanda apakah keduanya berdampingan.

        Tidak berdampingan berarti ada spasi atau tanda baca di antaranya;
        penyambungan bunyi tidak melompati batas itu.
        """
        for k in range(len(idx) - 1):
            a, b = idx[k], idx[k + 1]
            yield tokens[a], tokens[b], b == a + 1

    # 1. Palatalisasi: 같이 -> 가치, 굳이 -> 구지, 닫히다 -> 다치다.
    for cur, nxt, joined in pairs():
        if not joined or nxt.v != "ㅣ":
            continue
        if cur.t in ("ㄷ", "ㅌ") and nxt.l in ("ㅇ", "ㅎ"):
            nxt.l = "ㅈ" if (cur.t == "ㄷ" and nxt.l == "ㅇ") else "ㅊ"
            cur.t = ""
            mark("gugae")
        elif cur.t == "ㄾ" and nxt.l == "ㅇ":
            cur.t = "ㄹ"
            nxt.l = "ㅊ"
            mark("gugae")

    # 2. Pengaspiratan: ㅎ melebur dengan ㄱ ㄷ ㅂ ㅈ, dari kedua arah.
    for cur, nxt, _adj in pairs():
        # 2a. batchim ㅎ (termasuk ㄶ dan ㅀ) + huruf awal ㄱ ㄷ ㅂ ㅈ
        if cur.t in ("ㅎ", "ㄶ", "ㅀ"):
            if nxt.l in ASPIRATE or nxt.l == "ㅅ":
                nxt.l = "ㅆ" if nxt.l == "ㅅ" else ASPIRATE[nxt.l]
                cur.t = "" if cur.t == "ㅎ" else CLUSTERS[cur.t][0]
                mark("gyeokeum")
            continue
        # 2b. batchim letup (termasuk yang netral menjadi ㄷ) + huruf awal ㅎ
        if nxt.l == "ㅎ" and cur.t:
            sisa = ""
            dasar = cur.t
            if cur.t in CLUSTERS:
                sisa, dasar = CLUSTERS[cur.t]
            dasar = NEUTRAL.get(dasar, dasar)
            if dasar in ASPIRATE:
                nxt.l = ASPIRATE[dasar]
                cur.t = sisa
                mark("gyeokeum")

    # 3. Penghilangan ㅎ sebelum vokal: 좋아요 -> 조아요, 많아요 -> 마나요.
    for cur, nxt, joined in pairs():
        if not joined or nxt.l != "ㅇ":
            continue
        if cur.t == "ㅎ":
            cur.t = ""
            mark("h_talak")
        elif cur.t in ("ㄶ", "ㅀ"):
            cur.t = CLUSTERS[cur.t][0]
            mark("h_talak")

    # 4. Penyambungan bunyi: 한국어 -> 한구거, 읽어요 -> 일거요.
    #    Batchim ㅇ tidak berpindah (영어 tetap 영어).
    for cur, nxt, joined in pairs():
        if not joined or nxt.l != "ㅇ" or not cur.t or cur.t == "ㅇ":
            continue
        if cur.t in CLUSTERS:
            cur.t, nxt.l = CLUSTERS[cur.t]
        else:
            nxt.l, cur.t = cur.t, ""
        mark("yeoneum")

    # 5. Penyederhanaan batchim ganda yang masih tersisa: 읽다 -> 익다.
    for i in idx:
        s = tokens[i]
        if s.t in SIMPLIFY:
            if s.t in TENSE_AFTER_CLUSTER:
                pemicu_keras.add(i)
            s.t = SIMPLIFY[s.t]
            mark("jaeumgun")

    # 6. Penetralan batchim: 꽃 -> 꼳, 있 -> 읻, 부엌 -> 부억.
    for i in idx:
        s = tokens[i]
        if s.t in NEUTRAL:
            s.t = NEUTRAL[s.t]
            mark("kkeutsori")

    # 7. Penyengauan: 한국말 -> 한궁말, 입니다 -> 임니다, 국립 -> 궁닙.
    for cur, nxt, _adj in pairs():
        if cur.t in NASAL and nxt.l in ("ㄴ", "ㅁ"):
            cur.t = NASAL[cur.t]
            mark("bieumhwa")
        elif nxt.l == "ㄹ" and cur.t in ("ㅁ", "ㅇ"):
            nxt.l = "ㄴ"
            mark("bieumhwa")
        elif nxt.l == "ㄹ" and cur.t in ("ㄱ", "ㅂ"):
            nxt.l = "ㄴ"
            cur.t = NASAL[cur.t]
            mark("bieumhwa")

    # 8. Peleburan ke ㄹ: 신라 -> 실라, 설날 -> 설랄.
    #    Hanya di DALAM satu kata: 오늘 날씨 tetap 오늘 날씨, bukan 오늘 랄씨.
    for cur, nxt, adj in pairs():
        if not adj:
            continue
        if cur.t == "ㄴ" and nxt.l == "ㄹ":
            cur.t = "ㄹ"
            mark("yueumhwa")
        elif cur.t == "ㄹ" and nxt.l == "ㄴ":
            nxt.l = "ㄹ"
            mark("yueumhwa")

    # 9. Pengerasan: 학교 -> 학꾜, 있다 -> 읻따, 입구 -> 입꾸, 앉다 -> 안따.
    #    Hanya di DALAM satu kata. Melintasi spasi, pengerasan tidak terjadi:
    #    한국 사람 dibaca 한국 사람, bukan 한국 싸람.
    for k in range(len(idx) - 1) if tensify else ():
        cur, nxt = tokens[idx[k]], tokens[idx[k + 1]]
        if nxt.l not in TENSE or idx[k + 1] != idx[k] + 1:
            continue
        if cur.t in ("ㄱ", "ㄷ", "ㅂ") or idx[k] in pemicu_keras:
            nxt.l = TENSE[nxt.l]
            mark("gyeongeum")

    return _render(tokens), fired


def pronounce(text: str, *, tensify: bool = True) -> str:
    """Lafal sebenarnya dari sebuah kata atau kalimat Hangeul."""
    return pronounce_trace(text, tensify=tensify)[0]


def differs(text: str) -> bool:
    """True bila lafalnya berbeda dari tulisannya."""
    return pronounce(text) != text


def rule_names(ids: list[str]) -> list[str]:
    """Nama Indonesia dari daftar id aturan."""
    return [RULES[r][0] for r in ids if r in RULES]


def rule_labels(ids: list[str]) -> list[str]:
    """Nama Indonesia beserta istilah Koreanya, untuk ditampilkan di kartu."""
    return [f"{RULES[r][0]} ({RULES[r][1]})" for r in ids if r in RULES]


__all__ = [
    "ASPIRATE",
    "EXCEPTIONS",
    "NASAL",
    "NEUTRAL",
    "RULES",
    "SIMPLIFY",
    "TENSE",
    "TENSE_AFTER_CLUSTER",
    "differs",
    "pronounce",
    "pronounce_trace",
    "rule_labels",
    "rule_names",
]
